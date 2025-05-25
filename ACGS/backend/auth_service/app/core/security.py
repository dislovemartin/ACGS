# ACGS/backend/auth_service/app/core/security.py
import os
import sys 
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union, List

from pydantic import ValidationError
from fastapi import Depends, HTTPException, status, Request
from jose import JWTError, jwt
from argon2 import PasswordHasher, exceptions as argon2_exceptions
from sqlalchemy.ext.asyncio import AsyncSession 

from .config import settings

try:
    from shared.database import get_async_db
    from shared.models import User, RefreshToken as RefreshTokenModel
    from shared.schemas.token import TokenPayload as SharedTokenPayload 
except ImportError:
    project_root_shared = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))
    if project_root_shared not in sys.path:
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))) 
    from shared.database import get_async_db
    from shared.models import User, RefreshToken as RefreshTokenModel
    from shared.schemas.token import TokenPayload as SharedTokenPayload


ph = PasswordHasher(time_cost=2, memory_cost=65536, parallelism=4)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return ph.verify(hashed_password, plain_password)
    except argon2_exceptions.VerifyMismatchError:
        return False
    except argon2_exceptions.InvalidHashError:
        # Consider logging this error securely
        # settings.PROJECT_NAME.logger.error("Invalid hash format encountered...") 
        return False
    except Exception:
        # settings.PROJECT_NAME.logger.error(f"Unexpected error during password verification: {e}")
        return False

def get_password_hash(password: str) -> str:
    return ph.hash(password)

revoked_access_jti_blacklist: set[str] = set()

def create_access_token(
    subject: str, user_id: int, roles: List[str]
) -> tuple[str, str]: 
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + expires_delta
    jti = uuid.uuid4().hex
    to_encode = {
        "exp": int(expire.timestamp()), "sub": subject, "user_id": user_id,
        "roles": roles, "type": "access", "jti": jti,
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt, jti

def create_refresh_token(
    subject: str, user_id: int, roles: List[str]
) -> tuple[str, str, datetime]: 
    expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    expire_datetime_utc = datetime.now(timezone.utc) + expires_delta
    jti = uuid.uuid4().hex
    to_encode = {
        "exp": int(expire_datetime_utc.timestamp()), "sub": subject, "user_id": user_id,
        "roles": roles, "type": "refresh", "jti": jti,
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt, jti, expire_datetime_utc

def revoke_access_jti(jti: str):
    revoked_access_jti_blacklist.add(jti)

def is_access_jti_revoked(jti: str) -> bool:
    return jti in revoked_access_jti_blacklist

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"},
)
token_expired_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Token has expired", headers={"WWW-Authenticate": "Bearer"},
)

def _decode_jwt_token(token_str: str) -> SharedTokenPayload:
    try:
        payload = jwt.decode(token_str, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        # Ensure 'roles' is present in payload, default to empty list if not
        if 'roles' not in payload:
            payload['roles'] = []
        token_payload = SharedTokenPayload(**payload)
        return token_payload
    except JWTError as e: 
        if "expired" in str(e).lower():
             raise token_expired_exception from e
        raise credentials_exception from e
    except ValidationError: 
        raise credentials_exception from e
    except Exception: 
        raise credentials_exception from e

async def get_current_user_from_cookie(
    request: Request, db: AsyncSession = Depends(get_async_db)
) -> User:
    access_token_cookie = request.cookies.get("access_token_cookie")
    if not access_token_cookie:
        raise credentials_exception
    
    token_payload = _decode_jwt_token(access_token_cookie)

    if token_payload.type != "access":
        raise credentials_exception 
    if not token_payload.jti or is_access_jti_revoked(token_payload.jti):
        raise credentials_exception 

    if token_payload.user_id is None: 
        raise credentials_exception

    from ..crud import crud_user # Deferred import
    user = await crud_user.get_user(db, user_id=token_payload.user_id)
    if user is None:
        raise credentials_exception 
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user_from_cookie),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user

async def get_current_active_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if not getattr(current_user, 'is_superuser', False): 
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges (superuser required).",
        )
    return current_user

def get_user_id_from_request_optional(request: Request) -> Optional[str]:
    token_str = request.cookies.get("access_token_cookie")
    if not token_str:
        return None
    try:
        payload = jwt.decode(token_str, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options={"verify_signature": True, "verify_exp": True})
        # Ensure 'roles' is present in payload, default to empty list if not
        if 'roles' not in payload:
            payload['roles'] = []
        token_data = SharedTokenPayload(**payload)
        if token_data.user_id and token_data.type == "access" and (not token_data.jti or not is_access_jti_revoked(token_data.jti)):
            return str(token_data.user_id)
    except (JWTError, ValidationError):
        return None 
    return None
