import os
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from argon2 import PasswordHasher, exceptions as argon2_exceptions # Import PasswordHasher and exceptions
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordBearer

load_dotenv() # Load environment variables from .env

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token") # Adjusted tokenUrl to include /auth prefix

# Password Hashing with Argon2id
# Recommended parameters: time_cost=2, memory_cost=65536 (64MB), parallelism=4
ph = PasswordHasher(time_cost=2, memory_cost=65536, parallelism=4)

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-keep-it-secret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")) # Default 7 days


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        # Verify the hash against the password
        ph.verify(hashed_password, plain_password)
        # Optionally, check if the hash needs re-hashing with new parameters
        # if ph.check_needs_rehash(hashed_password):
        #     # Logic to rehash and update the stored hash would go here
        #     # This is usually done during login if verification is successful
        #     print("INFO: Password hash needs re-hashing ( Argon2 parameters changed).")
        return True
    except argon2_exceptions.VerifyMismatchError:
        return False # Password does not match
    except argon2_exceptions.VerificationError: # Catches various other verification issues
        print(f"WARN: VerificationError encountered for hash: {hashed_password[:20]}...") # Log safely
        return False
    except Exception as e: # Catch any other unexpected errors during verification
        print(f"ERROR: Unexpected error during password verification: {e}")
        return False

def get_password_hash(password: str) -> str:
    return ph.hash(password)


import uuid # Import uuid for jti generation

# JWT Token Handling
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> tuple[str, str]:
    """Creates an access token. Returns the token string and its JTI."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    jti = uuid.uuid4().hex
    to_encode.update({
        "exp": expire,
        "jti": jti, # Add jti claim
        "type": "access" # Explicitly mark as access token
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, jti

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> tuple[str, str, datetime]:
    """Creates a refresh token. Returns the token string, its JTI, and its expiry datetime."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    jti = uuid.uuid4().hex
    to_encode.update({
        "exp": expire,
        "jti": jti, # Add jti claim for refresh token
        "type": "refresh" # Explicitly mark as refresh token
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, jti, expire


from fastapi import Request, HTTPException, status, Depends # Added Request, HTTPException, status, Depends
from .. import crud # For user retrieval
from shared import models # For user models
from ..db.database import get_async_db # For DB session in dependency
from sqlalchemy.ext.asyncio import AsyncSession # For type hinting DB session

# In-memory set for storing revoked JTIs.
# For production, a persistent store like Redis or a database table is recommended.
revoked_tokens: set[str] = set()

# Placeholder for CSRF settings if we were to manage them here (fastapi-csrf-protect will handle this)
# CSRF_SECRET_KEY = os.getenv("CSRF_SECRET_KEY", "another-super-secret-for-csrf")

# Custom dependency to get token from HttpOnly cookie
async def get_access_token_from_cookie(request: Request) -> Optional[str]:
    return request.cookies.get("access_token")

async def get_current_user_from_cookie(
    token: Optional[str] = Depends(get_access_token_from_cookie),
    db: AsyncSession = Depends(get_async_db)
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials from cookie",
        headers={"WWW-Authenticate": "Bearer"}, # Keep Bearer for consistency, though not strictly Bearer scheme
    )
    if not token:
        raise credentials_exception
        
    payload = decode_access_token(token) # decode_access_token already checks blacklist for access tokens
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    user = await crud.get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user_from_cookie(
    current_user: models.User = Depends(get_current_user_from_cookie)
) -> models.User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Optional: If you still need an OAuth2PasswordBearer-like scheme for other purposes,
# but it won't be used for the primary cookie authentication.
# oauth2_scheme_from_header = OAuth2PasswordBearer(tokenUrl="/auth/token") 
# The existing oauth2_scheme can be used if some endpoints still expect header tokens.
# The /logout endpoint in endpoints.py was also updated to use a custom scheme for optional token.
def oauth2_scheme_from_cookie_optional(cookie_name: str):
    async def _get_token_from_cookie_optional(request: Request) -> Optional[str]:
        return request.cookies.get(cookie_name)
    return _get_token_from_cookie_optional


def revoke_token(jti: str) -> None:
    """Adds a JTI to the revocation list."""
    revoked_tokens.add(jti)

def is_token_revoked(jti: str) -> bool:
    """Checks if a JTI is in the revocation list."""
    return jti in revoked_tokens

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check if the access token's JTI is revoked (for access tokens only)
        # Refresh token revocation is handled by checking DB `revoked` field.
        token_type = payload.get("type")
        if token_type == "access":
            jti = payload.get("jti")
            if jti and is_token_revoked(jti): # is_token_revoked is for access token JTI blacklist
                print(f"Attempt to use revoked access token JTI: {jti}") 
                return None 
            
        return payload
    except JWTError: # Covers various JWT errors like expiration, invalid signature, etc.
        return None

def get_user_id_from_request_optional(request: Request) -> Optional[str]:
    """
    Synchronously attempts to extract user identifier (username) from the access token in cookies.
    Returns username string if successful, None otherwise.
    This is intended for use in contexts like rate limiting key functions
    where async dependencies cannot be easily resolved.
    """
    token = request.cookies.get("access_token")
    if not token:
        return None
    
    payload = decode_access_token(token) # decode_access_token handles JWT errors and blacklist
    if payload is None:
        return None
    
    # Assuming 'sub' claim stores the username, which acts as a unique identifier here.
    # If user ID were directly in the token and preferred, that could be used.
    user_identifier = payload.get("sub") 
    return user_identifier
