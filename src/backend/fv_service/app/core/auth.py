from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer
from typing import List, Optional

from ..schemas import User # Using the placeholder User schema from fv_service schemas

# This is a placeholder. In a real scenario, this would call the auth_service
# or validate a JWT token passed in the request.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False) 

# Placeholder users
mock_fv_admin_user = User(id="fv_admin_001", roles=["fv_admin"])
mock_internal_caller_user = User(id="internal_caller_001", roles=["internal_caller"]) # e.g., for automated processes like PGC

async def get_current_user_placeholder(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[User]:
    if token == "fv_admin_token":
        return mock_fv_admin_user
    elif token == "internal_caller_token":
        return mock_internal_caller_user
    return None

async def get_current_active_user_placeholder(current_user: Optional[User] = Depends(get_current_user_placeholder)) -> Optional[User]:
    return current_user

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: Optional[User] = Depends(get_current_user_placeholder)):
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated (placeholder for FV Service)"
            )
        
        if not any(role in user.roles for role in self.allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have the required roles: {', '.join(self.allowed_roles)} (placeholder for FV Service)"
            )
        return user

# Specific dependency instances for roles
require_fv_admin = RoleChecker(allowed_roles=["fv_admin"])
# Example: if only specific internal processes or admins can trigger verification
require_verification_triggerer = RoleChecker(allowed_roles=["fv_admin", "internal_caller"])
