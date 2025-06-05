from datetime import timedelta

from freezegun import freeze_time

import pytest
from ..core import security  # Assuming your security functions are here
from ..core.config import settings

# from app.schemas.token import TokenPayload # Unused, adjust if needed


def test_create_access_token():
    subject = "testuser@example.com"
    expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token, jti = security.create_access_token(
        subject=subject, user_id=1, roles=["user"], expires_delta=expires
    )
    assert isinstance(token, str)
    assert isinstance(jti, str)


def test_verify_access_token_valid():
    subject = "testuser@example.com"
    expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token, _ = security.create_access_token(
        subject=subject, user_id=1, roles=["user"], expires_delta=expires
    )
    payload = security.verify_token_and_get_payload(token)
    assert payload is not None
    if payload:  # Type guard
        assert payload.sub == subject
        # Add more assertions for expiry, etc., if needed


def test_verify_access_token_expired():
    subject = "testuser@example.com"
    # Create a token that has already expired
    expired_delta = timedelta(minutes=-settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expired_token, _ = security.create_access_token(
        subject=subject, user_id=1, roles=["user"], expires_delta=expired_delta
    )

    with pytest.raises(security.HTTPException) as excinfo:
        security.verify_token_and_get_payload(expired_token)
    # This depends on how security.verify_token raises exceptions
    # for expired tokens. Assuming HTTPException with status 401.
    assert excinfo.value.status_code == 401
    # assert "Token has expired" in str(excinfo.value.detail)


def test_verify_access_token_invalid_signature():
    subject = "testuser@example.com"
    expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token, _ = security.create_access_token(
        subject=subject, user_id=1, roles=["user"], expires_delta=expires
    )
    # Tamper with the token
    invalid_token = token + "tampered"

    with pytest.raises(security.HTTPException) as excinfo:
        security.verify_token_and_get_payload(invalid_token)
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


def test_token_with_additional_scopes():
    subject = "scopeduser@example.com"
    roles = ["user", "admin", "auditor"]
    token, _ = security.create_access_token(
        subject=subject, user_id=2, roles=roles, expires_delta=timedelta(minutes=5)
    )

    payload = security.verify_token_and_get_payload(token)
    assert payload is not None
    if payload:
        assert payload.roles == roles


def test_token_with_non_ascii_subject():
    subject = "测试用户@example.com"
    token, _ = security.create_access_token(
        subject=subject, user_id=3, roles=["user"], expires_delta=timedelta(minutes=5)
    )

    payload = security.verify_token_and_get_payload(token)
    assert payload is not None
    if payload:
        assert payload.sub == subject


def test_token_created_right_before_expiry():
    subject = "edgecase@example.com"
    with freeze_time("2024-01-01 00:00:00") as frozen:
        token, _ = security.create_access_token(
            subject=subject,
            user_id=4,
            roles=["user"],
            expires_delta=timedelta(seconds=1),
        )
        frozen.tick(delta=timedelta(seconds=0.9))
        payload = security.verify_token_and_get_payload(token)
        assert payload is not None
        if payload:
            assert payload.sub == subject
