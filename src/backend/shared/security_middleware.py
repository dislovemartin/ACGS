# ACGS/shared/security_middleware.py

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import uuid
import time
import json
import os
import logging
from typing import Callable, Dict, Set, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Rate limiting storage
rate_limit_storage: Dict[str, deque] = defaultdict(lambda: deque())
blocked_ips: Dict[str, datetime] = {}

class SecurityConfig:
    """Centralized security configuration."""

    def __init__(self):
        self.enable_security_headers = os.getenv("ENABLE_SECURITY_HEADERS", "true").lower() == "true"
        self.enable_hsts = os.getenv("ENABLE_HSTS", "true").lower() == "true"
        self.hsts_max_age = int(os.getenv("HSTS_MAX_AGE", "31536000"))
        self.enable_csp = os.getenv("ENABLE_CSP", "true").lower() == "true"
        self.csp_report_uri = os.getenv("CSP_REPORT_URI", "/api/v1/security/csp-report")
        self.enable_rate_limiting = os.getenv("ENABLE_RATE_LIMITING", "false").lower() == "true"  # Disabled for now
        self.rate_limit_requests = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "100"))  # Restored default
        self.rate_limit_burst = int(os.getenv("RATE_LIMIT_BURST_SIZE", "20"))  # Restored default
        self.rate_limit_block_duration = int(os.getenv("RATE_LIMIT_BLOCK_DURATION_MINUTES", "5"))
        self.enable_ip_blocking = os.getenv("ENABLE_IP_BLOCKING", "true").lower() == "true"
        self.max_failed_attempts = int(os.getenv("MAX_FAILED_ATTEMPTS", "5"))
        self.max_request_size = int(os.getenv("MAX_REQUEST_SIZE_MB", "10")) * 1024 * 1024
        self.enable_request_validation = os.getenv("ENABLE_REQUEST_VALIDATION", "true").lower() == "true"

security_config = SecurityConfig()

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Advanced rate limiting middleware with IP blocking."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not security_config.enable_rate_limiting:
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        current_time = datetime.now()

        # Check if IP is blocked
        if client_ip in blocked_ips:
            if current_time < blocked_ips[client_ip]:
                logger.warning(f"Blocked IP attempted access: {client_ip}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="IP temporarily blocked due to rate limiting"
                )
            else:
                # Unblock expired IPs
                del blocked_ips[client_ip]

        # Rate limiting logic
        request_times = rate_limit_storage[client_ip]

        # Remove old requests outside the time window
        cutoff_time = current_time - timedelta(minutes=1)
        while request_times and request_times[0] < cutoff_time:
            request_times.popleft()

        # Check rate limit
        if len(request_times) >= security_config.rate_limit_requests:
            # Block IP if enabled
            if security_config.enable_ip_blocking:
                block_until = current_time + timedelta(minutes=security_config.rate_limit_block_duration)
                blocked_ips[client_ip] = block_until
                logger.warning(f"IP blocked for rate limiting: {client_ip} until {block_until}")

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )

        # Add current request
        request_times.append(current_time)

        return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()

        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enhanced security headers middleware."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Add request ID for tracking
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Request size validation
        if security_config.enable_request_validation:
            content_length = request.headers.get('content-length')
            if content_length and int(content_length) > security_config.max_request_size:
                logger.warning(f"Request size exceeded: {content_length} > {security_config.max_request_size}")
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="Request size too large"
                )

        response = await call_next(request)

        if not security_config.enable_security_headers:
            return response

        # Enhanced Content Security Policy
        if security_config.enable_csp:
            csp_policy = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' ws: wss:; "
                "object-src 'none'; "
                "frame-ancestors 'self'; "
                "form-action 'self'; "
                "base-uri 'self'; "
                f"report-uri {security_config.csp_report_uri};"
            )
            response.headers["Content-Security-Policy"] = csp_policy

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # HSTS header
        if security_config.enable_hsts:
            response.headers["Strict-Transport-Security"] = f"max-age={security_config.hsts_max_age}; includeSubDomains; preload"

        # Enhanced Permissions Policy
        response.headers["Permissions-Policy"] = (
            "camera=(), "
            "microphone=(), "
            "geolocation=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=(), "
            "autoplay=(), "
            "encrypted-media=(), "
            "fullscreen=(self), "
            "picture-in-picture=()"
        )

        # Custom security headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Powered-By"] = "ACGS-PGP"
        response.headers["Server"] = "ACGS-PGP/1.0"

        return response

class InputValidationMiddleware(BaseHTTPMiddleware):
    """Input validation and sanitization middleware."""

    # Common SQL injection patterns (enhanced for testing)
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
        r"(--|#|/\*|\*/)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\bUNION\s+SELECT\b)",
        r"(\b(EXEC|EXECUTE)\s*\()",
        r"(';.*DROP.*TABLE)",  # Enhanced pattern for DROP TABLE
        r"('.*OR.*'.*=.*')",   # Enhanced pattern for OR injection
    ]

    # XSS patterns (enhanced for testing)
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
        r"alert\s*\(",  # Enhanced pattern for alert()
        r"<script>",    # Simple script tag
    ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not security_config.enable_request_validation:
            return await call_next(request)

        try:
            # Validate request method
            if request.method not in ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]:
                logger.warning(f"Invalid HTTP method: {request.method}")
                raise HTTPException(
                    status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                    detail="Method not allowed"
                )

            # Special handling for health endpoint - only allow GET
            if request.url.path == "/health" and request.method != "GET":
                logger.warning(f"Invalid method {request.method} for /health endpoint")
                raise HTTPException(
                    status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                    detail="Method not allowed for health endpoint"
                )

            # Validate content type for POST/PUT requests
            if request.method in ["POST", "PUT", "PATCH"]:
                content_type = request.headers.get("content-type", "")
                if not content_type.startswith(("application/json", "application/x-www-form-urlencoded", "multipart/form-data")):
                    logger.warning(f"Invalid content type: {content_type} for method {request.method}")
                    raise HTTPException(
                        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                        detail="Unsupported media type"
                    )

            # Validate query parameters and headers
            await self._validate_request_data(request)

            return await call_next(request)

        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            # Log unexpected errors and convert to HTTP exception
            logger.error(f"Input validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request validation failed"
            )

    async def _validate_request_data(self, request: Request):
        """Validate request data for security threats."""
        import re

        # Check query parameters
        for key, value in request.query_params.items():
            if self._contains_sql_injection(value) or self._contains_xss(value):
                logger.warning(f"Malicious content detected in query params: {key}={value[:100]}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid request data"
                )

        # Check headers for suspicious content
        suspicious_headers = ["user-agent", "referer", "x-forwarded-for"]
        for header in suspicious_headers:
            value = request.headers.get(header, "")
            if self._contains_sql_injection(value) or self._contains_xss(value):
                logger.warning(f"Malicious content detected in headers: {header}={value[:100]}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid request headers"
                )

    def _contains_sql_injection(self, text: str) -> bool:
        """Check if text contains SQL injection patterns."""
        import re
        text_upper = text.upper()
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text_upper, re.IGNORECASE):
                return True
        return False

    def _contains_xss(self, text: str) -> bool:
        """Check if text contains XSS patterns."""
        import re
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

class SecurityAuditMiddleware(BaseHTTPMiddleware):
    """Security audit logging middleware."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))

        # Log security-relevant request details
        security_event = {
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
            "client_ip": client_ip,
            "method": request.method,
            "path": str(request.url.path),
            "user_agent": user_agent,
            "headers": dict(request.headers),
            "query_params": dict(request.query_params)
        }

        try:
            response = await call_next(request)

            # Log successful request
            processing_time = time.time() - start_time
            security_event.update({
                "status_code": response.status_code,
                "processing_time_ms": round(processing_time * 1000, 2),
                "success": True
            })

            # Log suspicious activity
            if response.status_code >= 400:
                logger.warning(f"HTTP error response: {response.status_code} for {security_event['path']}")
            elif processing_time > 5.0:  # Slow requests might indicate attacks
                logger.warning(f"Slow request detected: {processing_time:.2f}s for {security_event['path']}")
            else:
                logger.info(f"Request processed: {response.status_code} for {security_event['path']}")

            return response

        except Exception as e:
            # Log security incidents
            processing_time = time.time() - start_time
            security_event.update({
                "error": str(e),
                "processing_time_ms": round(processing_time * 1000, 2),
                "success": False
            })
            logger.error(f"Request failed: {str(e)} for {security_event['path']}")
            raise

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()

        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

def add_security_middleware(app: ASGIApp) -> ASGIApp:
    """
    Add comprehensive security middleware to an ASGI app.
    Order matters: Rate limiting -> Input validation -> Security headers -> Audit logging
    """
    app.add_middleware(SecurityAuditMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(InputValidationMiddleware)
    app.add_middleware(RateLimitMiddleware)
    return app

def add_security_headers(app: ASGIApp) -> ASGIApp:
    """
    Legacy function for backward compatibility.
    Use add_security_middleware for comprehensive protection.
    """
    app.add_middleware(SecurityHeadersMiddleware)
    return app

# Example usage in a FastAPI main.py:
# from fastapi import FastAPI
# from shared.security_middleware import add_security_middleware
#
# app = FastAPI()
# add_security_middleware(app)
#
# # ... your routes and other app setup
