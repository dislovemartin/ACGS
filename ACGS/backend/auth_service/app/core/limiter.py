# ACGS/backend/auth_service/app/core/limiter.py
from fastapi import Request
from slowapi import Limiter, _rate_limit_exceeded_handler 
from slowapi.errors import RateLimitExceeded 
from slowapi.util import get_remote_address

from .security import get_user_id_from_request_optional

def get_request_identifier_for_auth(request: Request) -> str:
    user_identifier = get_user_id_from_request_optional(request) 
    if user_identifier:
        return f"user:{user_identifier}" 
    
    remote_ip = get_remote_address(request)
    return f"ip:{remote_ip}" if remote_ip else "unknown_ip"

limiter = Limiter(key_func=get_request_identifier_for_auth, default_limits=["200 per minute"])
