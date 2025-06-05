"""
Shared authentication utilities for ACGS-PGP microservices
Provides JWT token validation and user authentication across all services
"""

import os
import httpx
from typing import Optional, List
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timezone, timedelta # Added timedelta
import uuid # Added uuid
from pydantic import BaseModel

# Environment variables
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth_service:8000")
SECRET_KEY = os.getenv("SECRET_KEY", "acgs-development-secret-key-2024-phase1-infrastructure-stabilization-jwt-token-signing") # Updated default
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

class TokenPayload(BaseModel):
    """JWT token payload structure"""
    sub: Optional[str] = None
    user_id: Optional[int] = None
    roles: Optional[List[str]] = None
    type: Optional[str] = None
    jti: Optional[str] = None
    exp: Optional[int] = None

class User(BaseModel):
    """User model for authentication"""
    id: int
    username: str
    roles: List[str]
    is_active: bool = True

# Exception instances
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

token_expired_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Token has expired",
    headers={"WWW-Authenticate": "Bearer"},
)

def verify_token_and_get_payload(token_str: str) -> TokenPayload:
    """
    Verify JWT token and return payload
    Raises HTTPException if token is invalid or expired
    """
    try:
        payload = jwt.decode(token_str, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Validate expiration
        exp_timestamp = payload.get("exp")
        if exp_timestamp is None or datetime.fromtimestamp(exp_timestamp, timezone.utc) < datetime.now(timezone.utc):
            raise token_expired_exception
            
        token_payload = TokenPayload(**payload)
        
        if token_payload.type == "access":
            # For access tokens, we could check revocation here if needed
            # For now, we'll trust the token if it's valid and not expired
            return token_payload
        else:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    except Exception:
        raise credentials_exception

async def get_current_user_from_token(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[User]:
    """
    Extract and validate JWT token, return User object
    Returns None if no token provided (for optional authentication)
    Raises HTTPException if token is invalid
    """
    if not token:
        return None
    
    try:
        # Remove 'Bearer ' prefix if present
        if token.startswith("Bearer "):
            token = token[7:]
        
        payload = verify_token_and_get_payload(token)
        
        if not payload.sub or not payload.user_id:
            raise credentials_exception
        
        # Create user object from token payload
        user = User(
            id=payload.user_id,
            username=payload.sub,
            roles=payload.roles or [],
            is_active=True
        )
        
        return user
        
    except HTTPException:
        raise
    except Exception:
        raise credentials_exception

async def get_current_active_user(current_user: Optional[User] = Depends(get_current_user_from_token)) -> User:
    """
    Require authenticated user (raises exception if not authenticated)
    """
    if not current_user:
        raise credentials_exception
    
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return current_user

class RoleChecker:
    """
    Dependency class for role-based access control
    """
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_active_user)):
        if not any(role in user.roles for role in self.allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have the required roles: {', '.join(self.allowed_roles)}"
            )
        return user

# Common role checkers
require_admin = RoleChecker(allowed_roles=["admin"])
require_policy_manager = RoleChecker(allowed_roles=["policy_manager", "admin"])
require_auditor = RoleChecker(allowed_roles=["auditor", "admin"])

# Service-specific role checkers
require_ac_admin = RoleChecker(allowed_roles=["ac_admin", "admin"])
require_gs_admin = RoleChecker(allowed_roles=["gs_admin", "admin"])
require_integrity_admin = RoleChecker(allowed_roles=["integrity_admin", "admin"])
require_fv_admin = RoleChecker(allowed_roles=["fv_admin", "admin"])
require_pgc_admin = RoleChecker(allowed_roles=["pgc_admin", "admin"])

# Internal service authentication
require_internal_service = RoleChecker(allowed_roles=["internal_service", "admin"])

async def get_service_token() -> str:
    """
    Generates a long-lived JWT token for internal service-to-service authentication.
    
    The token includes roles for internal service and admin, a unique identifier, and expires in one year.
    
    Returns:
        A JWT token string for authenticating internal service requests.
    """
    # In production, this would authenticate with the auth service
    # and get a proper service token

    # Use the same SECRET_KEY and ALGORITHM as defined globally for consistency
    # Ensure SECRET_KEY uses the updated default if the environment variable is not set
    effective_secret_key = os.getenv("SECRET_KEY", "acgs-development-secret-key-2024-phase1-infrastructure-stabilization-jwt-token-signing")

    expiration_delta = timedelta(days=365)  # Long expiry for this placeholder
    expire = datetime.now(timezone.utc) + expiration_delta
    payload = {
        "sub": "internal_service_user",
        "user_id": 0, # Or a conventional ID for internal services
        "roles": ["internal_service", "admin"], # Include admin as per RoleChecker
        "type": "access", # Mark as an access token
        # python-jose cannot serialize datetimes directly; use a Unix timestamp
        "exp": int(expire.timestamp()),
        "jti": str(uuid.uuid4()) # Unique token identifier
    }
    encoded_jwt = jwt.encode(payload, effective_secret_key, algorithm=ALGORITHM)
    return encoded_jwt

async def get_auth_headers(token: Optional[str] = None) -> dict: # Changed to async
    """
    Asynchronously generates HTTP authorization headers with a Bearer token.
    
    If no token is provided, generates a long-lived internal service JWT token. If a token is provided, ensures it is properly formatted as a Bearer token.
    
    Args:
        token: Optional JWT token string to use for the Authorization header.
    
    Returns:
        A dictionary containing the Authorization header with the Bearer token.
    """
    if not token:
        # Get service token if none provided
        service_token = await get_service_token() # Await the async call
        return {"Authorization": f"Bearer {service_token}"}
    
    if not token.startswith("Bearer "):
        token = f"Bearer {token}"
    
    return {"Authorization": token}

# HTTP client for auth service communication
class AuthServiceClient:
    """Client for communicating with auth service"""
    
    def __init__(self, base_url: str = AUTH_SERVICE_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url, timeout=10.0)
    
    async def validate_token(self, token: str) -> Optional[User]:
        """
        Validate token with auth service
        Returns User object if valid, None if invalid
        """
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = await self.client.get("/api/v1/users/me", headers=headers)
            
            if response.status_code == 200:
                user_data = response.json()
                return User(**user_data)
            else:
                return None
                
        except Exception:
            return None
    
    async def close(self):
        await self.client.aclose()

# Global auth service client
auth_service_client = AuthServiceClient()

# Alias for backward compatibility
get_current_user = get_current_active_user
