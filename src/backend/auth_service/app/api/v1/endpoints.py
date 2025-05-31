# backend/auth_service/app/api/v1/endpoints.py
import secrets
from datetime import timedelta, timezone, datetime as dt # Use dt alias for datetime objects

from fastapi import (APIRouter, Depends, HTTPException, Request, Response,
                     status)
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_csrf_protect import CsrfProtect
from jose import JWTError, jwt # For decoding in /logout and /token/refresh
from sqlalchemy.ext.asyncio import AsyncSession

# Application-specific imports
from app.core import security
from app.core.config import settings
from app.api.v1 import deps # Assuming deps.get_db is correctly defined for AsyncSession
from app.crud import crud_refresh_token, crud_user # crud_refresh_token was created earlier
from shared.models import User # RefreshToken model not directly used here, but in crud
from shared.schemas.token import Token # Token schema now includes refresh_token
from shared.schemas.user import UserCreate, UserInDB

router = APIRouter()

# Determine if cookies should be secure based on environment setting
# Fallback to True if not explicitly set to "development"
SECURE_COOKIE = getattr(settings, "ENVIRONMENT", "production") != "development"


@router.post("/register", response_model=UserInDB, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: AsyncSession = Depends(deps.get_db)):
    db_user_by_username = await crud_user.get_user_by_username(db, username=user.username)
    if db_user_by_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    db_user_by_email = await crud_user.get_user_by_email(db, email=user.email)
    if db_user_by_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    created_user = await crud_user.create_user(db=db, obj_in=user)
    return created_user


@router.post("/token", response_model=Token)
async def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(deps.get_db),
    csrf_protect: CsrfProtect = Depends(),
):
    user_obj = await crud_user.get_user_by_username(db, username=form_data.username)
    if not user_obj or not security.verify_password(
        form_data.password, user_obj.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user_obj.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    # Create access token
    access_token_str, access_jti = security.create_access_token(
        subject=user_obj.username, user_id=user_obj.id, roles=[user_obj.role]
    )

    # Create refresh token
    refresh_token_str, refresh_jti, refresh_expires_at = security.create_refresh_token(
        subject=user_obj.username, user_id=user_obj.id, roles=[user_obj.role]
    )
    await crud_refresh_token.create_refresh_token(
        db, user_id=user_obj.id, token=refresh_token_str, jti=refresh_jti, expires_at=refresh_expires_at
    )

    # Set CSRF token using correct API
    csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
    csrf_protect.set_csrf_cookie(signed_token, response)

    # Set HttpOnly cookies for tokens
    access_token_expires_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    refresh_token_expires_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

    response.set_cookie(
        key="access_token_cookie",
        value=access_token_str,
        httponly=True,
        max_age=access_token_expires_seconds,
        expires=access_token_expires_seconds, # For older browsers
        path="/",
        secure=SECURE_COOKIE,
        samesite="lax", # Or "strict"
    )
    response.set_cookie(
        key="refresh_token_cookie",
        value=refresh_token_str,
        httponly=True,
        max_age=refresh_token_expires_seconds,
        expires=refresh_token_expires_seconds, # For older browsers
        path="/auth/token/refresh", # Path specific to refresh endpoint
        secure=SECURE_COOKIE,
        samesite="lax", # Or "strict"
    )
    # The response model Token schema has refresh_token field, but we're not sending it in the body
    return Token(access_token=access_token_str, token_type="bearer", refresh_token=None)


@router.post("/token/refresh", response_model=Token)
async def refresh_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(deps.get_db),
    csrf_protect: CsrfProtect = Depends(),
):
    await csrf_protect.validate_csrf(request)

    refresh_token_cookie = request.cookies.get("refresh_token_cookie")
    if not refresh_token_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing"
        )

    try:
        payload = jwt.decode(
            refresh_token_cookie,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": True} # Ensure token is not expired
        )
        token_data = security.TokenPayload(**payload) # Validate payload structure
        if token_data.type != "refresh" or token_data.user_id is None or token_data.jti is None or token_data.sub is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token type")

    except JWTError: # Catches expired signature, invalid signature, etc.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token"
        )

    is_valid = await crud_refresh_token.is_valid_refresh_token(
        db, user_id=token_data.user_id, jti=token_data.jti
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked or invalid"
        )

    await crud_refresh_token.revoke_refresh_token(db, jti=token_data.jti, user_id=token_data.user_id)

    # Issue new tokens
    user_obj = await crud_user.get_user(db, user_id=token_data.user_id) # Fetch user for roles
    if not user_obj or not user_obj.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    new_access_token_str, new_access_jti = security.create_access_token(
        subject=user_obj.username, user_id=user_obj.id, roles=[user_obj.role]
    )
    new_refresh_token_str, new_refresh_jti, new_refresh_expires_at = security.create_refresh_token(
        subject=user_obj.username, user_id=user_obj.id, roles=[user_obj.role]
    )
    await crud_refresh_token.create_refresh_token(
        db, user_id=user_obj.id, token=new_refresh_token_str, jti=new_refresh_jti, expires_at=new_refresh_expires_at
    )

    # Set new CSRF token using correct API
    new_csrf_token, new_signed_token = csrf_protect.generate_csrf_tokens()
    csrf_protect.set_csrf_cookie(new_signed_token, response)

    # Set new HttpOnly cookies
    access_token_expires_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    refresh_token_expires_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

    response.set_cookie(
        key="access_token_cookie",
        value=new_access_token_str,
        httponly=True,
        max_age=access_token_expires_seconds,
        expires=access_token_expires_seconds,
        path="/",
        secure=SECURE_COOKIE,
        samesite="lax",
    )
    response.set_cookie(
        key="refresh_token_cookie",
        value=new_refresh_token_str,
        httponly=True,
        max_age=refresh_token_expires_seconds,
        expires=refresh_token_expires_seconds,
        path="/auth/token/refresh",
        secure=SECURE_COOKIE,
        samesite="lax",
    )
    return Token(access_token=new_access_token_str, token_type="bearer", refresh_token=None)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(deps.get_db),
    csrf_protect: CsrfProtect = Depends(),
):
    await csrf_protect.validate_csrf(request)

    access_token_cookie = request.cookies.get("access_token_cookie")
    if access_token_cookie:
        try:
            # Decode access token to get JTI, ignore expiration for revocation
            payload = jwt.decode(access_token_cookie, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options={"verify_exp": False})
            token_data = security.TokenPayload(**payload)
            if token_data.type == "access" and token_data.jti:
                security.revoke_access_jti(token_data.jti)
        except JWTError:
            pass # Ignore if token is invalid, just try to delete cookie

    refresh_token_cookie = request.cookies.get("refresh_token_cookie")
    if refresh_token_cookie:
        try:
            # Decode refresh token to get JTI and user_id for targeted revocation
            payload = jwt.decode(refresh_token_cookie, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options={"verify_exp": False})
            token_data = security.TokenPayload(**payload)
            if token_data.type == "refresh" and token_data.jti and token_data.user_id:
                await crud_refresh_token.revoke_refresh_token(db, jti=token_data.jti, user_id=token_data.user_id)
        except JWTError:
            pass # Ignore if token is invalid

    # Delete cookies
    response.delete_cookie(key="access_token_cookie", path="/", secure=SECURE_COOKIE, httponly=True, samesite="lax")
    response.delete_cookie(key="refresh_token_cookie", path="/auth/token/refresh", secure=SECURE_COOKIE, httponly=True, samesite="lax")
    csrf_protect.unset_csrf_cookie(response) # Deletes CSRF cookie to prevent token reuse

    return {"message": "Logout successful"}


@router.get("/me", response_model=UserInDB)
async def read_users_me(current_user: User = Depends(security.get_current_active_user)):
    # security.get_current_active_user now uses cookie-based authentication
    return current_user

# Include this router in the main FastAPI app
# Example: app.include_router(endpoints.router, prefix="/api/v1/auth", tags=["auth"])
