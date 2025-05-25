# ACGS/shared/security_middleware.py

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseCallNext
from starlette.types import ASGIApp
import uuid # For X-Request-ID example

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseCallNext
    ) -> Response:
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; " # Default policy: only allow content from the same origin
            "script-src 'self' 'unsafe-inline'; " # Allow inline scripts (consider alternatives for stricter CSP)
            "style-src 'self' 'unsafe-inline'; " # Allow inline styles (consider alternatives)
            "img-src 'self' data:; " # Allow images from self and data URIs
            "font-src 'self'; "
            "object-src 'none'; " # Disallow plugins (Flash, etc.)
            "frame-ancestors 'self'; " # Disallow embedding in iframes from other origins (clickjacking protection)
            "form-action 'self'; " # Restrict where forms can submit data
            "base-uri 'self';" # Restricts the <base> URI
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN" # Legacy, frame-ancestors is preferred
        response.headers["X-XSS-Protection"] = "1; mode=block" # Legacy, CSP is preferred
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        # Referrer-Policy helps control how much referrer information is sent with requests
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Permissions-Policy (formerly Feature-Policy) can restrict use of browser features
        response.headers["Permissions-Policy"] = (
            "camera=(), "
            "microphone=(), "
            "geolocation=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()" # Corrected: removed trailing comma inside the string
        )
        # Custom headers for context (example - can be removed or modified)
        # response.headers["X-Request-ID"] = str(uuid.uuid4()) # Added import uuid for this
        return response

def add_security_headers(app: ASGIApp) -> ASGIApp:
    """
    Helper function to add the SecurityHeadersMiddleware to an ASGI app.
    This is not strictly necessary if you add it directly in main.py,
    but can be a convenience.
    """
    app.add_middleware(SecurityHeadersMiddleware)
    return app

# Example usage in a FastAPI main.py:
# from fastapi import FastAPI
# from shared.security_middleware import SecurityHeadersMiddleware
#
# app = FastAPI()
# app.add_middleware(SecurityHeadersMiddleware)
#
# # ... your routes and other app setup
