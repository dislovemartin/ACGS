# backend/auth_service/app/api/v1/__init__.py
from . import endpoints, deps, api_router

__all__ = ["endpoints", "deps", "api_router"]