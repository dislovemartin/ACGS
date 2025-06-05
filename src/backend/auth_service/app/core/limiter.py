from fastapi import Request

# Import the new function from security.py
from ..core.security import get_user_id_from_request_optional

# Mock classes for testing
class MockLimiter:
    def __init__(self, key_func=None, default_limits=None):
        self.key_func = key_func
        self.default_limits = default_limits

    def limit(self, rate_limit):
        def decorator(func):
            return func
        return decorator

def mock_get_remote_address(request: Request) -> str:
    return getattr(request.client, 'host', '127.0.0.1') if request.client else '127.0.0.1'

# Try to import slowapi, fall back to mock if not available
try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address
    SLOWAPI_AVAILABLE = True
except ImportError:
    SLOWAPI_AVAILABLE = False
    Limiter = MockLimiter
    get_remote_address = mock_get_remote_address

def get_request_identifier(request: Request) -> str:
    """
    Determines the request identifier for rate limiting.
    If a user is authenticated (determined by a valid JWT in cookies),
    their username is used as the identifier.
    Otherwise, the client's remote IP address is used.
    """
    user_identifier = get_user_id_from_request_optional(request)
    if user_identifier:
        return user_identifier
    return get_remote_address(request)

# Initialize the Limiter with the new key function
# Default limits are kept as "100 per minute" unless specified otherwise on endpoints.
limiter = Limiter(key_func=get_request_identifier, default_limits=["100 per minute"])

# You can still decorate your routes like this:
# @limiter.limit("5/minute")
# async def some_endpoint(...):
#     ...
#
# And the key will be determined by get_request_identifier.
# If different default limits are needed, they can be changed here,
# e.g., default_limits=["100/minute", "1000/hour"]
# For now, keeping it simple as per the requirements.
# Specific endpoint limits will be handled in endpoints.py.
# The core requirement is that the key_func now distinguishes between authenticated users and IPs.
