from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer # Or APIKeyHeader, etc.
from typing import List, Optional

from ..schemas import User # Using the placeholder User schema from ac_service schemas

# This is a placeholder. In a real scenario, this would call the auth_service
# or validate a JWT token passed in the request.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False) # auto_error=False to allow optional auth

# Placeholder current user - for development without real auth_service integration
# In a real app, this user would be derived from a validated JWT token.
mock_admin_user = User(id=1, username="mockadmin", roles=["ac_admin"])
mock_normal_user = User(id=2, username="mockuser", roles=["user"])
mock_constitutional_council_user = User(id=3, username="mockcouncil", roles=["constitutional_council"])

async def get_current_user_placeholder(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[User]:
    """
    Placeholder for current user. If a token "admin" is passed, returns admin user.
    If token "user" is passed, returns normal user. Otherwise, no user.
    This allows testing endpoints with and without simulated authentication.
    """
    if token == "admin_token": # Simulate admin token
        return mock_admin_user
    elif token == "user_token": # Simulate normal user token
        return mock_normal_user
    elif token == "council_token": # Simulate constitutional council token
        return mock_constitutional_council_user
    # For actual JWT, you would decode token here and fetch user
    # If no token or invalid, can return None or raise HTTPException
    return None # No authentication by default for now

async def get_current_active_user_placeholder(current_user: Optional[User] = Depends(get_current_user_placeholder)) -> Optional[User]:
    # In a real app, you might check if user is active in the database
    # For now, just passes through the user from get_current_user_placeholder
    return current_user

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: Optional[User] = Depends(get_current_user_placeholder)):
        # If no user is returned by the placeholder (e.g. no token or invalid token for real auth)
        # and roles are required, then it's an unauthorized access.
        if not user:
            print("RoleChecker: No user found, raising 401 (simulated).")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        
        print(f"RoleChecker: User '{user.username}' with roles {user.roles}. Allowed: {self.allowed_roles}")
        
        # Check if user has any of the allowed roles
        if not any(role in user.roles for role in self.allowed_roles):
            print(f"RoleChecker: User '{user.username}' does not have required roles. Raising 403.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have the required roles: {', '.join(self.allowed_roles)}"
            )
        return user

# Specific dependency instances for roles
require_admin_role = RoleChecker(allowed_roles=["ac_admin"])
require_user_role = RoleChecker(allowed_roles=["user", "ac_admin"]) # Example: user or admin can access
require_constitutional_council_role = RoleChecker(allowed_roles=["constitutional_council", "ac_admin"]) # Constitutional Council members or admins

# Example of how to protect an endpoint:
# @router.post("/", dependencies=[Depends(require_admin_role)])
# async def create_item(...):
#    ...

# If you need the user object in your path operation function:
# @router.post("/")
# async def create_item(..., current_user: User = Depends(require_admin_role)):
#    # current_user will be the authenticated user object
#    ...
