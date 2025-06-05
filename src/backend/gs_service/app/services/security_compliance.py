"""
Security Compliance Service for ACGS Governance Synthesis

This service implements comprehensive security compliance measures including
authentication, authorization, input validation, rate limiting, and audit logging.

Phase 3: Performance Optimization and Security Compliance
"""

import asyncio
import time
import logging
import hashlib
import hmac
import secrets
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from functools import wraps
import json
import re
from ipaddress import ip_address, ip_network
import threading

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator, Field
import jwt
from passlib.context import CryptContext
import structlog

logger = structlog.get_logger(__name__)

# Security configuration
SECURITY_CONFIG = {
    'jwt_algorithm': 'HS256',
    'jwt_expiry_minutes': 30,
    'max_login_attempts': 5,
    'lockout_duration_minutes': 15,
    'password_min_length': 8,
    'rate_limit_requests': 100,
    'rate_limit_window_minutes': 1,
    'audit_log_retention_days': 90
}

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT security
security = HTTPBearer()


@dataclass
class SecurityEvent:
    """Security event for audit logging."""
    event_type: str
    user_id: Optional[str]
    ip_address: str
    user_agent: str
    endpoint: str
    timestamp: datetime
    details: Dict[str, Any]
    severity: str  # low, medium, high, critical
    success: bool


@dataclass
class RateLimitInfo:
    """Rate limiting information."""
    requests: int
    window_start: datetime
    blocked: bool
    reset_time: datetime


class InputValidator:
    """Comprehensive input validation and sanitization."""
    
    # Common injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
        r"(--|#|/\*|\*/)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\bUNION\s+SELECT\b)",
        r"(\b(SCRIPT|JAVASCRIPT|VBSCRIPT)\b)",
        r"(\'\s*(OR|AND)\s*\'\d+\'\s*=\s*\'\d+)",  # '1'='1' pattern
        r"(\'\s*OR\s*\d+\s*=\s*\d+)",  # ' OR 1=1 pattern
        r"(\d+\'\s*OR\s*\'\d+\'\s*=\s*\'\d+)",  # 1' OR '1'='1 pattern
        r"(\'\s*;\s*DROP\s+TABLE)",  # '; DROP TABLE pattern
        r"(\'\s*--)",  # admin'-- pattern
        r"(\'\s*OR\s*\d+\s*=\s*\d+\s*#)",  # ' OR 1=1# pattern
        r"(\'\s*;\s*EXEC\s+)"  # '; EXEC pattern
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>.*?</iframe>",
        r"<object[^>]*>.*?</object>",
        r"<embed[^>]*>.*?</embed>"
    ]
    
    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$(){}[\]\\]",
        r"\b(cat|ls|pwd|whoami|id|uname|ps|netstat|ifconfig)\b",
        r"(\.\.\/|\.\.\\)",
        r"(\|\s*(cat|ls|pwd|whoami|id|uname|ps|netstat|ifconfig))"
    ]
    
    @classmethod
    def validate_input(cls, input_data: Any, input_type: str = "general") -> bool:
        """Validate input against injection patterns."""
        if not isinstance(input_data, str):
            input_data = str(input_data)
        
        input_lower = input_data.lower()
        
        # Check SQL injection
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, input_lower, re.IGNORECASE):
                logger.warning("SQL injection attempt detected", input=input_data[:100], pattern=pattern)
                return False
        
        # Check XSS
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, input_lower, re.IGNORECASE):
                logger.warning("XSS attempt detected", input=input_data[:100], pattern=pattern)
                return False
        
        # Check command injection
        for pattern in cls.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, input_data, re.IGNORECASE):
                logger.warning("Command injection attempt detected", input=input_data[:100], pattern=pattern)
                return False
        
        return True
    
    @classmethod
    def sanitize_input(cls, input_data: str) -> str:
        """Sanitize input by removing dangerous characters."""
        # Remove null bytes and replace with 'Null' for visibility
        sanitized = input_data.replace('\x00', 'Null')

        # Remove other control characters except newline and tab
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in '\n\t')

        # Limit length
        if len(sanitized) > 10000:
            sanitized = sanitized[:10000]
            logger.warning("Input truncated due to length", original_length=len(input_data))

        return sanitized


class RateLimiter:
    """Advanced rate limiting with sliding window."""
    
    def __init__(self):
        self.requests: Dict[str, List[float]] = {}
        self.blocked_ips: Dict[str, datetime] = {}
        self._lock = threading.Lock()
    
    def is_allowed(self, identifier: str, max_requests: int = 100, window_minutes: int = 1) -> RateLimitInfo:
        """Check if request is allowed under rate limit."""
        current_time = time.time()
        window_seconds = window_minutes * 60
        
        with self._lock:
            # Check if IP is blocked
            if identifier in self.blocked_ips:
                if datetime.now() < self.blocked_ips[identifier]:
                    return RateLimitInfo(
                        requests=max_requests,
                        window_start=datetime.fromtimestamp(current_time - window_seconds),
                        blocked=True,
                        reset_time=self.blocked_ips[identifier]
                    )
                else:
                    # Unblock IP
                    del self.blocked_ips[identifier]
            
            # Initialize or clean old requests
            if identifier not in self.requests:
                self.requests[identifier] = []
            
            # Remove old requests outside the window
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if current_time - req_time < window_seconds
            ]
            
            # Check rate limit
            if len(self.requests[identifier]) >= max_requests:
                # Block IP for lockout duration
                lockout_duration = timedelta(minutes=SECURITY_CONFIG['lockout_duration_minutes'])
                self.blocked_ips[identifier] = datetime.now() + lockout_duration
                
                logger.warning("Rate limit exceeded, IP blocked", 
                             identifier=identifier, 
                             requests=len(self.requests[identifier]),
                             max_requests=max_requests)
                
                return RateLimitInfo(
                    requests=len(self.requests[identifier]),
                    window_start=datetime.fromtimestamp(current_time - window_seconds),
                    blocked=True,
                    reset_time=self.blocked_ips[identifier]
                )
            
            # Add current request
            self.requests[identifier].append(current_time)
            
            return RateLimitInfo(
                requests=len(self.requests[identifier]),
                window_start=datetime.fromtimestamp(current_time - window_seconds),
                blocked=False,
                reset_time=datetime.fromtimestamp(current_time + window_seconds)
            )


class AuditLogger:
    """Security audit logging service."""
    
    def __init__(self):
        self.events: List[SecurityEvent] = []
        self._lock = threading.Lock()
    
    def log_event(self, event_type: str, user_id: Optional[str], ip_address: str, 
                  user_agent: str, endpoint: str, details: Dict[str, Any], 
                  severity: str = "medium", success: bool = True):
        """Log security event."""
        event = SecurityEvent(
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            endpoint=endpoint,
            timestamp=datetime.now(),
            details=details,
            severity=severity,
            success=success
        )
        
        with self._lock:
            self.events.append(event)
            
            # Keep only recent events
            cutoff_time = datetime.now() - timedelta(days=SECURITY_CONFIG['audit_log_retention_days'])
            self.events = [e for e in self.events if e.timestamp > cutoff_time]
        
        # Log to structured logger
        logger.info("Security event", 
                   event_type=event_type,
                   user_id=user_id,
                   ip_address=ip_address,
                   endpoint=endpoint,
                   severity=severity,
                   success=success,
                   details=details)
    
    def get_events(self, hours: int = 24, severity: Optional[str] = None, 
                   event_type: Optional[str] = None) -> List[SecurityEvent]:
        """Get security events with filtering."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            filtered_events = [
                event for event in self.events
                if event.timestamp > cutoff_time
            ]
            
            if severity:
                filtered_events = [e for e in filtered_events if e.severity == severity]
            
            if event_type:
                filtered_events = [e for e in filtered_events if e.event_type == event_type]
            
            return filtered_events


class JWTManager:
    """JWT token management with enhanced security."""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.algorithm = SECURITY_CONFIG['jwt_algorithm']
        self.expiry_minutes = SECURITY_CONFIG['jwt_expiry_minutes']
        self.revoked_tokens: set = set()
    
    def create_token(self, user_id: str, roles: List[str], additional_claims: Optional[Dict[str, Any]] = None) -> str:
        """Create JWT token with user information."""
        now = datetime.utcnow()
        payload = {
            'user_id': user_id,
            'roles': roles,
            'iat': now,
            'exp': now + timedelta(minutes=self.expiry_minutes),
            'jti': secrets.token_urlsafe(32)  # JWT ID for revocation
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        logger.info("JWT token created", user_id=user_id, roles=roles)
        return token
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token."""
        try:
            # Validate token format first
            if not token or not isinstance(token, str):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token format"
                )

            # Remove Bearer prefix if present
            if token.startswith('Bearer '):
                token = token[7:]

            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Check if token is revoked
            jti = payload.get('jti')
            if jti in self.revoked_tokens:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked"
                )

            return payload

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token signature"
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
    
    def revoke_token(self, token: str):
        """Revoke JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm], options={"verify_exp": False})
            jti = payload.get('jti')
            if jti:
                self.revoked_tokens.add(jti)
                logger.info("JWT token revoked", jti=jti, user_id=payload.get('user_id'))
        except jwt.InvalidTokenError:
            logger.warning("Attempted to revoke invalid token")


class SecurityComplianceService:
    """Main security compliance service."""
    
    def __init__(self, secret_key: str):
        self.jwt_manager = JWTManager(secret_key)
        self.rate_limiter = RateLimiter()
        self.audit_logger = AuditLogger()
        self.input_validator = InputValidator()
    
    def get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded headers
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def validate_request(self, request: Request, max_requests: int = None, window_minutes: int = None) -> bool:
        """Validate incoming request for security compliance."""
        client_ip = self.get_client_ip(request)
        user_agent = request.headers.get('User-Agent', 'unknown')
        
        # Rate limiting
        max_req = max_requests or SECURITY_CONFIG['rate_limit_requests']
        window_min = window_minutes or SECURITY_CONFIG['rate_limit_window_minutes']
        
        rate_limit_info = self.rate_limiter.is_allowed(client_ip, max_req, window_min)
        
        if rate_limit_info.blocked:
            self.audit_logger.log_event(
                event_type="rate_limit_exceeded",
                user_id=None,
                ip_address=client_ip,
                user_agent=user_agent,
                endpoint=str(request.url),
                details={"requests": rate_limit_info.requests, "max_requests": max_req},
                severity="high",
                success=False
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again after {rate_limit_info.reset_time}"
            )
        
        return True
    
    async def authenticate_request(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
        """Authenticate request using JWT token."""
        try:
            payload = self.jwt_manager.verify_token(credentials.credentials)
            return payload
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Authentication error", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )
    
    def authorize_request(self, user_payload: Dict[str, Any], required_roles: List[str]) -> bool:
        """Authorize request based on user roles."""
        user_roles = user_payload.get('roles', [])
        
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return True
    
    def validate_input_data(self, data: Any, input_type: str = "general") -> Any:
        """Validate and sanitize input data."""
        if isinstance(data, str):
            if not self.input_validator.validate_input(data, input_type):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid input detected"
                )
            return self.input_validator.sanitize_input(data)
        
        elif isinstance(data, dict):
            return {
                key: self.validate_input_data(value, input_type)
                for key, value in data.items()
            }
        
        elif isinstance(data, list):
            return [self.validate_input_data(item, input_type) for item in data]
        
        return data
    
    def get_security_summary(self) -> Dict[str, Any]:
        """Get security compliance summary."""
        recent_events = self.audit_logger.get_events(hours=24)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_events_24h': len(recent_events),
            'security_events_by_severity': {
                'critical': len([e for e in recent_events if e.severity == 'critical']),
                'high': len([e for e in recent_events if e.severity == 'high']),
                'medium': len([e for e in recent_events if e.severity == 'medium']),
                'low': len([e for e in recent_events if e.severity == 'low'])
            },
            'failed_events': len([e for e in recent_events if not e.success]),
            'rate_limit_violations': len([e for e in recent_events if e.event_type == 'rate_limit_exceeded']),
            'authentication_failures': len([e for e in recent_events if e.event_type == 'authentication_failed']),
            'authorization_failures': len([e for e in recent_events if e.event_type == 'authorization_failed'])
        }


# Global security service instance
_security_service: Optional[SecurityComplianceService] = None


def get_security_service() -> SecurityComplianceService:
    """Get global security service instance."""
    global _security_service
    if _security_service is None:
        # This should be initialized with proper secret key from config
        _security_service = SecurityComplianceService("your-secret-key-here")
    return _security_service


def security_required(required_roles: List[str] = None):
    """Decorator for endpoints requiring authentication and authorization."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request and credentials from function arguments
            request = None
            credentials = None
            
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                elif isinstance(arg, HTTPAuthorizationCredentials):
                    credentials = arg
            
            if not request or not credentials:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            security_service = get_security_service()
            
            # Validate request
            security_service.validate_request(request)
            
            # Authenticate
            user_payload = await security_service.authenticate_request(credentials)
            
            # Authorize if roles specified
            if required_roles:
                security_service.authorize_request(user_payload, required_roles)
            
            # Add user payload to kwargs
            kwargs['user_payload'] = user_payload
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator
