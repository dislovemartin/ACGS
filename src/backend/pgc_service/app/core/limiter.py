from fastapi import Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
# from ..auth import get_current_user_optional # Hypothetical: if pgc has its own auth user lookup

def get_pgc_request_identifier(request: Request) -> str:
    # Placeholder for user-based limiting in pgc_service
    # This assumes that if authentication is present in pgc_service,
    # the user object might be attached to request.state.user or similar.
    # This part will likely need adjustment once pgc_service's auth mechanism for its APIs is clarified.
    # For example, it might use a token passed from auth_service and validated by a dependency.
    
    # FastAPI makes endpoint dependencies available in request.scope.
    # If 'current_user' is a dependency in the endpoint, it should be in scope.
    if 'current_user' in request.scope:
        user = request.scope.get('current_user')
        # Check if user is not None and has an 'id' attribute (as per schemas.User)
        if user and hasattr(user, 'id') and user.id:
            return f"user:{str(user.id)}"

    # Fallback to IP-based limiting, with a prefix
    remote_addr = get_remote_address(request)
    return f"ip:{remote_addr}"

limiter = Limiter(key_func=get_pgc_request_identifier, default_limits=["100 per minute"])
