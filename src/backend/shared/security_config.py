"""
ACGS-PGP Security Configuration Module

Centralized security configuration and utilities for the ACGS-PGP framework.
Provides secure defaults, environment-based configuration, and security utilities.

Phase 2.1: Security Hardening Implementation
"""

import os
import secrets
import hashlib
import hmac
import base64
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    """Security level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityThresholds:
    """Security threshold configuration."""
    rate_limit_requests_per_minute: int = 100
    rate_limit_burst_size: int = 20
    max_failed_attempts: int = 5
    block_duration_minutes: int = 15
    max_request_size_mb: int = 10
    jwt_expiry_minutes: int = 30
    refresh_token_expiry_days: int = 7
    password_min_length: int = 12
    session_timeout_minutes: int = 60

@dataclass
class CryptographicConfig:
    """Cryptographic configuration."""
    jwt_algorithm: str = "HS256"
    hash_algorithm: str = "SHA256"
    key_derivation_iterations: int = 100000
    salt_length: int = 32
    token_length: int = 64

class SecurityConfigManager:
    """Centralized security configuration manager."""
    
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.debug_mode = os.getenv("DEBUG", "false").lower() == "true"
        self.thresholds = SecurityThresholds()
        self.crypto_config = CryptographicConfig()
        self._load_configuration()
    
    def _load_configuration(self):
        """Load security configuration from environment variables."""
        # Rate limiting configuration
        self.thresholds.rate_limit_requests_per_minute = int(
            os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "100")
        )
        self.thresholds.rate_limit_burst_size = int(
            os.getenv("RATE_LIMIT_BURST_SIZE", "20")
        )
        self.thresholds.max_failed_attempts = int(
            os.getenv("MAX_FAILED_ATTEMPTS", "5")
        )
        self.thresholds.block_duration_minutes = int(
            os.getenv("RATE_LIMIT_BLOCK_DURATION_MINUTES", "15")
        )
        
        # Request validation configuration
        self.thresholds.max_request_size_mb = int(
            os.getenv("MAX_REQUEST_SIZE_MB", "10")
        )
        
        # Authentication configuration
        self.thresholds.jwt_expiry_minutes = int(
            os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
        )
        self.thresholds.refresh_token_expiry_days = int(
            os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7")
        )
        self.thresholds.password_min_length = int(
            os.getenv("PASSWORD_MIN_LENGTH", "12")
        )
        
        # Cryptographic configuration
        self.crypto_config.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        
        logger.info(f"Security configuration loaded - Environment: {self.environment}, Rate limit: {self.thresholds.rate_limit_requests_per_minute}")
    
    def get_security_level(self) -> SecurityLevel:
        """Determine security level based on environment."""
        if self.environment == "production":
            return SecurityLevel.CRITICAL
        elif self.environment == "staging":
            return SecurityLevel.HIGH
        elif self.environment == "testing":
            return SecurityLevel.MEDIUM
        else:
            return SecurityLevel.LOW
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"
    
    def get_cors_origins(self) -> List[str]:
        """Get CORS origins based on environment."""
        cors_origins = os.getenv("BACKEND_CORS_ORIGINS", "")
        if not cors_origins:
            if self.environment == "production":
                return ["https://acgs-pgp.com"]  # Production domain
            else:
                return ["http://localhost:3000", "http://localhost:3001"]
        
        return [origin.strip() for origin in cors_origins.split(",")]
    
    def validate_secret_key(self, key: str) -> bool:
        """Validate secret key strength."""
        if not key or len(key) < 32:
            return False
        
        # Check for default/weak keys
        weak_keys = [
            "your-secret-key",
            "change-in-production",
            "development-key",
            "test-key"
        ]
        
        for weak_key in weak_keys:
            if weak_key in key.lower():
                return False
        
        return True

class SecurityUtils:
    """Security utility functions."""
    
    @staticmethod
    def generate_secure_key(length: int = 64) -> str:
        """Generate a cryptographically secure random key."""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_salt(length: int = 32) -> bytes:
        """Generate a cryptographic salt."""
        return secrets.token_bytes(length)
    
    @staticmethod
    def hash_password(password: str, salt: Optional[bytes] = None) -> tuple[str, bytes]:
        """Hash a password with salt."""
        if salt is None:
            salt = SecurityUtils.generate_salt()
        
        # Use PBKDF2 for password hashing
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000  # iterations
        )
        
        return base64.b64encode(key).decode('utf-8'), salt
    
    @staticmethod
    def verify_password(password: str, hashed_password: str, salt: bytes) -> bool:
        """Verify a password against its hash."""
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000
        )
        
        return hmac.compare_digest(
            base64.b64encode(key).decode('utf-8'),
            hashed_password
        )
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """Sanitize user input to prevent XSS and injection attacks."""
        if not text:
            return ""
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', '\x00', '\r', '\n']
        sanitized = text
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        return sanitized.strip()
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, List[str]]:
        """Validate password strength and return issues."""
        issues = []
        
        if len(password) < 12:
            issues.append("Password must be at least 12 characters long")
        
        if not any(c.isupper() for c in password):
            issues.append("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            issues.append("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            issues.append("Password must contain at least one digit")
        
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            issues.append("Password must contain at least one special character")
        
        # Check for common weak patterns
        weak_patterns = ["123", "abc", "password", "admin", "user"]
        for pattern in weak_patterns:
            if pattern.lower() in password.lower():
                issues.append(f"Password should not contain common patterns like '{pattern}'")
        
        return len(issues) == 0, issues

# Global security configuration instance
security_config = SecurityConfigManager()
security_utils = SecurityUtils()

# Security constants
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "SAMEORIGIN",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": (
        "camera=(), microphone=(), geolocation=(), payment=(), "
        "usb=(), magnetometer=(), gyroscope=(), accelerometer=()"
    )
}

# Content Security Policy
CSP_POLICY = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: https:; "
    "font-src 'self' data:; "
    "connect-src 'self' ws: wss:; "
    "object-src 'none'; "
    "frame-ancestors 'self'; "
    "form-action 'self'; "
    "base-uri 'self';"
)

# Rate limiting patterns
RATE_LIMIT_PATTERNS = {
    "auth": {"requests": 10, "window": 60},  # 10 requests per minute for auth
    "api": {"requests": 100, "window": 60},  # 100 requests per minute for API
    "upload": {"requests": 5, "window": 300},  # 5 uploads per 5 minutes
}
