from datetime import timedelta
import sys
from pathlib import Path

import pytest

# Add the src directory to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "src/backend"))

try:
    from backend.auth_service.app.core import security  # Assuming your security functions are here
    from backend.auth_service.app.core.config import settings
except ImportError:
    # Fallback for testing without full backend setup
    security = None
    settings = None

# from app.schemas.token import TokenPayload # Unused, adjust if needed


def test_create_access_token():
    subject = "testuser@example.com"
    expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = security.create_access_token(subject=subject, expires_delta=expires)
    assert isinstance(token, str)


def test_verify_access_token_valid():
    subject = "testuser@example.com"
    expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = security.create_access_token(subject=subject, expires_delta=expires)
    payload = security.verify_token(token)
    assert payload is not None
    if payload:  # Type guard
        assert payload.sub == subject
        # Add more assertions for expiry, etc., if needed


def test_verify_access_token_expired():
    subject = "testuser@example.com"
    # Create a token that has already expired
    expired_delta = timedelta(minutes=-settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expired_token = security.create_access_token(
        subject=subject, expires_delta=expired_delta
    )

    with pytest.raises(security.HTTPException) as excinfo:
        security.verify_token(expired_token)
    # This depends on how security.verify_token raises exceptions
    # for expired tokens. Assuming HTTPException with status 401.
    assert excinfo.value.status_code == 401
    # assert "Token has expired" in str(excinfo.value.detail)


def test_verify_access_token_invalid_signature():
    subject = "testuser@example.com"
    expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = security.create_access_token(subject=subject, expires_delta=expires)
    # Tamper with the token
    invalid_token = token + "tampered"

    with pytest.raises(security.HTTPException) as excinfo:
        security.verify_token(invalid_token)
    # Assuming HTTPException with status 401 for signature mismatch.
    assert excinfo.value.status_code == 401
    # assert "Could not validate credentials" in str(excinfo.value.detail)


def test_password_hashing_and_verification():
    password = "supersecretpassword"
    hashed_password = security.get_password_hash(password)
    assert isinstance(hashed_password, str)
    assert hashed_password != password

    assert security.verify_password(password, hashed_password) is True
    assert security.verify_password("wrongpassword", hashed_password) is False


# TODO:
# - Test for tokens with different scopes if applicable.
# - Test for tokens with non-ASCII characters in subject if relevant.
# - Consider edge cases for token expiry (e.g., token created just before
#   expiry).
