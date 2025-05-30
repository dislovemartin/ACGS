from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer
from typing import List, Optional

from ..schemas import User # Using the placeholder User schema from gs_service schemas

# This is a placeholder. In a real scenario, this would call the auth_service
# or validate a JWT token passed in the request.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False) 

# Placeholder users
mock_gs_admin_user = User(id="gs_admin_001", roles=["gs_admin"])
mock_internal_user = User(id="internal_user_001", roles=["internal_user"]) # e.g., for automated processes

async def get_current_user_placeholder(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[User]:
    if token == "gs_admin_token":
        return mock_gs_admin_user
    elif token == "internal_user_token":
        return mock_internal_user
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
                detail="Not authenticated (placeholder for GS Service)"
            )
        
        if not any(role in user.roles for role in self.allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have the required roles: {', '.join(self.allowed_roles)} (placeholder for GS Service)"
            )
        return user

# Specific dependency instances for roles
require_gs_admin = RoleChecker(allowed_roles=["gs_admin"])
# Example: if only specific internal processes or admins can trigger synthesis
require_synthesis_triggerer = RoleChecker(allowed_roles=["gs_admin", "internal_user"])
