# backend/auth_service/app/core/password.py
"""
Password hashing utilities with fallback implementations.
Separated from security.py to avoid circular imports.
"""

import hashlib
import secrets
import os

# Simple password hashing for testing - use proper library in production
SALT_LENGTH = 32

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    try:
        # Extract salt and hash from stored password
        if ':' not in hashed_password:
            return False

        salt_hex, stored_hash = hashed_password.split(':', 1)
        salt = bytes.fromhex(salt_hex)

        # Hash the plain password with the same salt
        computed_hash = hashlib.pbkdf2_hmac('sha256', plain_password.encode(), salt, 100000)
        computed_hash_hex = computed_hash.hex()

        return secrets.compare_digest(computed_hash_hex, stored_hash)
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    """Hash a plain password using PBKDF2."""
    salt = secrets.token_bytes(SALT_LENGTH)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return f"{salt.hex()}:{password_hash.hex()}"
