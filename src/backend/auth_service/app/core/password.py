# backend/auth_service/app/core/password.py
"""
Password hashing utilities using Argon2.
Separated from security.py to avoid circular imports.
"""

from argon2 import PasswordHasher, exceptions as argon2_exceptions

# --- Argon2 Password Hashing ---
ph = PasswordHasher(time_cost=2, memory_cost=65536, parallelism=4)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    try:
        ph.verify(hashed_password, plain_password)
        # Optional: check if rehash is needed
        # if ph.check_needs_rehash(hashed_password):
        #     # Trigger rehash logic (e.g., during login)
        #     pass
        return True
    except argon2_exceptions.VerifyMismatchError:
        return False
    except argon2_exceptions.InvalidHashError: # If hash is malformed
        # Log this error, as it indicates a problem with stored hash
        return False
    except Exception: # Catch any other unexpected argon2 errors
        # Log this error
        return False

def get_password_hash(password: str) -> str:
    """Hash a plain password using Argon2."""
    return ph.hash(password)
