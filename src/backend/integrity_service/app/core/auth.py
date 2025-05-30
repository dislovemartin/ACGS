from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer
from typing import List, Optional

from ..schemas import User # Using the placeholder User schema from integrity_service schemas

# This is a placeholder. In a real scenario, this would call the auth_service
# or validate a JWT token passed in the request.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

# Placeholder users
mock_integrity_admin_user = User(id="integrity_admin_001", roles=["integrity_admin", "auditor"])
mock_auditor_user = User(id="auditor_001", roles=["auditor"])
mock_internal_service_user = User(id="internal_svc_id", roles=["internal_service"]) # For service-to-service calls

async def get_current_user_placeholder(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[User]:
    if token == "integrity_admin_token":
        return mock_integrity_admin_user
    elif token == "auditor_token":
        return mock_auditor_user
    elif token == "internal_service_token": # Token for internal services
        return mock_internal_service_user
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
                detail="Not authenticated (placeholder)"
            )
        
        if not any(role in user.roles for role in self.allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have the required roles: {', '.join(self.allowed_roles)} (placeholder)"
            )
        return user

# Specific dependency instances for roles
require_integrity_admin = RoleChecker(allowed_roles=["integrity_admin"])
require_auditor = RoleChecker(allowed_roles=["auditor", "integrity_admin"])
require_internal_service = RoleChecker(allowed_roles=["internal_service", "integrity_admin"]) # Allow admin to also act as internal service for testing
