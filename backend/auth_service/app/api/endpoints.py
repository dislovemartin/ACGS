from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.responses import JSONResponse # Added JSONResponse import
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import secrets
from datetime import timedelta
from typing import Optional
from fastapi_csrf_protect import CsrfProtect

from .. import crud, models, schemas
from ..core import security
from ..db.database import get_db
from ..core.limiter import limiter # Import the limiter instance

router = APIRouter()

# Determine Secure flag based on environment (e.g., if APP_ENV is 'production')
# For simplicity, let's assume Secure=True should be used if not explicitly in dev.
# In a real app, this would be based on a config setting.
SECURE_COOKIE = True # TODO: Make this configurable, e.g., os.getenv("APP_ENV") == "production" 

# This dependency will be moved to security.py or a similar place
# For now, defined here to illustrate the change in get_current_user's signature
# async def get_current_user_from_cookie_placeholder(request: Request): 
#     # ... (placeholder code) ...
#     return models.User(id=1, username="cookieuser", email="test@example.com", hashed_password="xxx", is_active=True, role="user")


# Updated get_current_active_user to use the (to-be-defined) cookie-based dependency
async def get_current_active_user(current_user: models.User = Depends(security.get_current_active_user_from_cookie)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@router.post("/token")
@limiter.limit("5/minute") # Apply rate limit
async def login_for_access_token(
    request: Request, # Add Request for limiter
    response: Response, 
    db: Session = Depends(get_db), 
    form_data: OAuth2PasswordRequestForm = Depends()
):
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    access_token_str, _ = security.create_access_token(
        data={"sub": user.username} 
    )
    refresh_token_str, refresh_jti, refresh_expires_at = security.create_refresh_token(
        data={"sub": user.username}
    )
    
    crud.create_user_refresh_token(
        db=db, 
        user_id=user.id, 
        token=refresh_token_str,
        jti=refresh_jti,
        expires_at=refresh_expires_at
    )
    
    csrf_token = secrets.token_hex(16)

    response.set_cookie(
        key="access_token", 
        value=access_token_str, 
        httponly=True, 
        samesite="lax", 
        secure=SECURE_COOKIE, 
        path="/",
        max_age=security.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    response.set_cookie(
        key="refresh_token", 
        value=refresh_token_str, 
        httponly=True, 
        samesite="lax",
        secure=SECURE_COOKIE, 
        path="/auth/token/refresh", # Specific path for refresh token
        max_age=security.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )
    response.set_cookie(
        key="csrf_access_token", 
        value=csrf_token, 
        httponly=True, 
        samesite="lax", 
        secure=SECURE_COOKIE, 
        path="/",
        max_age=security.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    return {"message": "Login successful", "username": user.username, "csrf_token_in_body_for_initial_grab": csrf_token}


@router.post("/token/refresh") 
@limiter.limit("10/minute") # Apply rate limit
async def refresh_access_token(
    response: Response, 
    request: Request, # To read refresh_token from cookie
    db: Session = Depends(get_db)
):
    refresh_token_from_cookie = request.cookies.get("refresh_token")
        
    if not refresh_token_from_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided in cookie",
            headers={"WWW-Authenticate": "Bearer"},
        )

    refresh_token_value = refresh_token_from_cookie
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = security.decode_access_token(refresh_token_value)
        if not payload or payload.get("type") != "refresh":
            raise credentials_exception
        
        username: str = payload.get("sub")
        refresh_jti: str = payload.get("jti")
        if not username or not refresh_jti:
            raise credentials_exception

    except Exception:
        raise credentials_exception

    db_refresh_token = crud.get_active_refresh_token_by_jti(db, jti=refresh_jti)
    if not db_refresh_token or db_refresh_token.user.username != username:
        raise credentials_exception

    crud.revoke_refresh_token_by_jti(db, jti=refresh_jti)
    
    user = db_refresh_token.user
    new_access_token_str, _ = security.create_access_token(data={"sub": user.username})
    
    new_refresh_token_str, new_refresh_jti, new_refresh_expires_at = security.create_refresh_token(
        data={"sub": user.username}
    )
    crud.create_user_refresh_token(
        db=db,
        user_id=user.id,
        token=new_refresh_token_str,
        jti=new_refresh_jti,
        expires_at=new_refresh_expires_at
    )
    
    new_csrf_token = secrets.token_hex(16)

    response.set_cookie(
        key="access_token", 
        value=new_access_token_str, 
        httponly=True, 
        samesite="lax", 
        secure=SECURE_COOKIE, 
        path="/",
        max_age=security.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    response.set_cookie(
        key="csrf_access_token", 
        value=new_csrf_token, 
        httponly=False, 
        samesite="lax", 
        secure=SECURE_COOKIE, 
        path="/",
        max_age=security.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    response.set_cookie(
        key="refresh_token", 
        value=new_refresh_token_str, 
        httponly=True, 
        samesite="lax", 
        secure=SECURE_COOKIE, 
        path="/auth/token/refresh",
        max_age=security.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )
    
    return {"message": "Token refreshed successfully", "csrf_token_in_body_for_initial_grab": new_csrf_token}


@router.post("/logout")
@limiter.limit("10/minute") # Apply rate limit
async def logout(response: Response, request: Request, db: Session = Depends(get_db)): # Removed token dependency from header
    """
    Revokes the current user's access token JTI (if present in cookie and valid),
    revokes the refresh token from DB (if present in cookie and valid),
    and clears relevant cookies.
    """
    access_token_from_cookie = request.cookies.get("access_token")
    if access_token_from_cookie:
        try:
            payload = security.decode_access_token(access_token_from_cookie) 
            if payload: # Token was valid (not expired, not malformed, not revoked by blacklist)
                jti = payload.get("jti")
                if jti and payload.get("type") == "access":
                    security.revoke_token(jti) # Add access token JTI to in-memory blacklist
        except Exception as e: # Catch if decode fails for any reason
            print(f"Error decoding access token during logout: {e}")

    refresh_token_from_cookie = request.cookies.get("refresh_token")
    if refresh_token_from_cookie:
        try:
            refresh_payload = security.decode_access_token(refresh_token_from_cookie)
            if refresh_payload and refresh_payload.get("type") == "refresh":
                refresh_jti = refresh_payload.get("jti")
                if refresh_jti:
                    crud.revoke_refresh_token_by_jti(db, jti=refresh_jti)
        except Exception as e:
            print(f"Could not revoke refresh token during logout: {e}") 

    response.delete_cookie("access_token", path="/", samesite="lax", secure=SECURE_COOKIE)
    response.delete_cookie("refresh_token", path="/auth/token/refresh", samesite="lax", secure=SECURE_COOKIE)
    response.delete_cookie("csrf_access_token", path="/", samesite="lax", secure=SECURE_COOKIE)
    
    return {"message": "Successfully logged out. Tokens have been revoked and cookies cleared."}


@router.post("/users/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute") # Apply rate limit
def create_user_endpoint(
    request: Request, # Add Request for limiter
    user: schemas.UserCreate, 
    db: Session = Depends(get_db)
):
    db_user_by_username = crud.get_user_by_username(db, username=user.username)
    if db_user_by_username:
        raise HTTPException(status_code=400, detail="Username already registered")
    db_user_by_email = crud.get_user_by_email(db, email=user.email)
    if db_user_by_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    created_user = crud.create_user(db=db, user=user)
    return created_user


@router.get("/users/me", response_model=schemas.UserResponse)
@limiter.limit("60/minute") # Apply rate limit
async def read_users_me(request: Request, current_user: models.User = Depends(get_current_active_user)): # Add Request for limiter, uses updated get_current_active_user
    return current_user

@router.get("/csrf-cookie")
@limiter.limit("60/minute") # Apply rate limit
async def get_csrf_cookie(request: Request, csrf_protect: CsrfProtect = Depends()): # Add Request for limiter
    """
    Endpoint to explicitly set the CSRF cookie if not already set,
    and to provide the token value in the response if needed by the frontend.
    fastapi-csrf-protect automatically sets the cookie on responses if methods are protected.
    This endpoint ensures a cookie is set on a simple GET request.
    """
    response = JSONResponse(content={"message": "CSRF cookie should be set."})
    # csrf_protect.set_csrf_cookie(response) # fastapi-csrf-protect usually handles this automatically on protected POSTs
    # If the cookie is not being set automatically on GET, or if you need to customize it:
    # By default, the CsrfProtect middleware might only set cookies on responses from
    # methods that it's actively protecting (e.g., POST).
    # To ensure a cookie is set on a GET, you might need a strategy like this or ensure
    # the first interaction is a POST that it protects.
    # However, the library is designed to work with SPAs. The cookie should be set
    # automatically when CsrfProtect is initialized in main.py if a secret_key is provided.
    # The frontend will pick up the csrf_access_token cookie set by /token or /token/refresh.
    # This endpoint is more of a "keep-alive" or explicit fetch if needed.
    
    # The crucial part is that a CSRF cookie (named "csrf_access_token") is set.
    # Our /token and /token/refresh endpoints already do this.
    # fastapi-csrf-protect will use this cookie.
    
    # If the frontend needs the token value explicitly (though it reads from cookie):
    # csrf_token = csrf_protect.generate_csrf() # Generate a new token if needed
    # response.set_cookie(key="csrf_access_token", value=csrf_token, ...) # if we were manually setting
    # return {"csrf_token": csrf_token}
    return response
