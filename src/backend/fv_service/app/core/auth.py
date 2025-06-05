# Local authentication utilities to avoid shared module dependencies
from typing import Optional, List
from fastapi import HTTPException, status
from pydantic import BaseModel

# Mock User class as Pydantic model
class User(BaseModel):
    id: int = 1
    username: str = "mock_user"
    email: str = "mock@example.com"
    roles: List[str] = ["user"]
    is_active: bool = True

# Mock authentication functions
async def get_current_user_from_token(token: str = None) -> User:
    """Mock function to get current user from token."""
    return User(roles=["admin", "fv_admin"])

async def get_current_active_user(user: User = None) -> User:
    """Mock function to get current active user."""
    if not user:
        user = User(roles=["admin", "fv_admin"])
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return user

# Mock role checker class
class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = None) -> User:
        if not user:
            user = User(roles=["admin", "fv_admin"])

        if not any(role in user.roles for role in self.allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return user

# Mock role checkers
async def require_admin(user: User = None) -> User:
    """Mock admin role checker."""
    if not user:
        user = User(roles=["admin"])
    return user

async def require_fv_admin(user: User = None) -> User:
    """Mock FV admin role checker."""
    if not user:
        user = User(roles=["fv_admin", "admin"])
    return user

async def require_internal_service(user: User = None) -> User:
    """Mock internal service role checker."""
    if not user:
        user = User(roles=["internal_service"])
    return user

# FV service specific role checkers
require_verification_triggerer = RoleChecker(allowed_roles=["fv_admin", "internal_service", "admin"])

# Backward compatibility aliases for existing code
get_current_user_placeholder = get_current_user_from_token
get_current_active_user_placeholder = get_current_active_user
