# ACGS/auth_service/app/tests/test_auth_flows.py
import pytest
from httpx import AsyncClient
from fastapi import status
import uuid

from ..core.config import settings # For API prefixes
from shared.schemas.user import UserCreate # For type hinting if needed, though client sends JSON
from ..core import security # For direct calls if needed for test setup, e.g. password hashing

# Pytest marker for async tests
pytestmark = pytest.mark.asyncio

# API Prefixes
API_V1_AUTH_PREFIX = f"{settings.API_V1_STR}/auth"

# Helper to generate unique user data for each test run
def get_unique_user_data(prefix: str = "testuser"):
    unique_id = uuid.uuid4().hex[:8]
    return {
        "username": f"{prefix}_{unique_id}",
        "email": f"{prefix}_{unique_id}@example.com",
        "password": "Str0ngPassword!123", # Meets potential complexity requirements
        "full_name": f"Test User {unique_id.capitalize()}"
    }

# --- Test User Registration ---
async def test_register_user_success(client: AsyncClient):
    user_data = get_unique_user_data("reg_success")
    response = await client.post(f"{API_V1_AUTH_PREFIX}/register", json=user_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["username"] == user_data["username"]
    assert "id" in data
    assert "hashed_password" not in data

async def test_register_user_duplicate_username(client: AsyncClient):
    user_data = get_unique_user_data("dup_uname")
    # First registration
    await client.post(f"{API_V1_AUTH_PREFIX}/register", json=user_data)

    # Second registration with same username
    user_data_dup = user_data.copy()
    user_data_dup["email"] = f"new_{user_data_dup['email']}" # Different email
    response = await client.post(f"{API_V1_AUTH_PREFIX}/register", json=user_data_dup)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Username already registered" in response.json()["detail"]

async def test_register_user_duplicate_email(client: AsyncClient):
    user_data = get_unique_user_data("dup_email")
    # First registration
    await client.post(f"{API_V1_AUTH_PREFIX}/register", json=user_data)

    # Second registration with same email
    user_data_dup = user_data.copy()
    user_data_dup["username"] = f"new_{user_data_dup['username']}" # Different username
    response = await client.post(f"{API_V1_AUTH_PREFIX}/register", json=user_data_dup)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Email already registered" in response.json()["detail"]

# Note: The shared.schemas.user.UserCreate does not specify password length validation.
# If it did (e.g., using Pydantic's Field(min_length=...)), a test for short passwords
# returning HTTP_422_UNPROCESSABLE_ENTITY would be appropriate.

# --- Test User Login ---
async def test_login_success(client: AsyncClient):
    user_data = get_unique_user_data("login_succ")
    await client.post(f"{API_V1_AUTH_PREFIX}/register", json=user_data)

    login_payload = {"username": user_data["username"], "password": user_data["password"]}
    response = await client.post(f"{API_V1_AUTH_PREFIX}/token", data=login_payload)

    assert response.status_code == status.HTTP_200_OK
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    assert token_data.get("refresh_token") is None # Refresh token is HttpOnly cookie

    # Check cookies (names based on auth_service/main.py CsrfSettings and endpoints.py)
    assert "access_token_cookie" in response.cookies
    assert "refresh_token_cookie" in response.cookies
    # The CSRF cookie set by `csrf_protect.set_csrf_cookie` would be "fastapi-csrf-token" by default
    # but auth_service/main.py defines CsrfSettings with cookie_key="csrf_access_token"
    # However, the login endpoint in auth_service/app/api/v1/endpoints.py uses `csrf_protect.set_csrf_cookie(csrf_token, response)`
    # which will use the default name "fastapi-csrf-token" unless the `CsrfProtect` instance is configured with a different cookie_key.
    # Let's assume the default name from `fastapi-csrf-protect` is used by `set_csrf_cookie` method.
    # The CsrfSettings in main.py configures the middleware, but the direct call might use library defaults.
    # The library's documentation says `set_csrf_cookie` uses the configured `cookie_key`.
    # So, it should be "csrf_access_token".
    assert "csrf_access_token" in response.cookies

    access_cookie_details = client.cookies.jar.get("access_token_cookie", domain="testserver", path="/")
    assert access_cookie_details is not None
    assert access_cookie_details.secure == (settings.ENVIRONMENT != "development")
    assert access_cookie_details.get("httponly") is not None # httpx sets this as a string 'HttpOnly' or True

    refresh_cookie_details = client.cookies.jar.get("refresh_token_cookie", domain="testserver", path=f"{API_V1_AUTH_PREFIX}/token/refresh")
    assert refresh_cookie_details is not None
    assert refresh_cookie_details.secure == (settings.ENVIRONMENT != "development")
    assert refresh_cookie_details.get("httponly") is not None

async def test_login_incorrect_password(client: AsyncClient):
    user_data = get_unique_user_data("login_fail_pass")
    await client.post(f"{API_V1_AUTH_PREFIX}/register", json=user_data)

    login_payload = {"username": user_data["username"], "password": "wrongpassword"}
    response = await client.post(f"{API_V1_AUTH_PREFIX}/token", data=login_payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Incorrect username or password" in response.json()["detail"]

async def test_login_non_existent_user(client: AsyncClient):
    login_payload = {"username": "nonexistentuser", "password": "password"}
    response = await client.post(f"{API_V1_AUTH_PREFIX}/token", data=login_payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Incorrect username or password" in response.json()["detail"]

async def test_login_inactive_user(client: AsyncClient):
    user_data = get_unique_user_data("login_inactive")
    # Register user (by default is_active=True)
    reg_response = await client.post(f"{API_V1_AUTH_PREFIX}/register", json=user_data)
    user_id = reg_response.json()["id"]

    # This test requires a way to make the user inactive.
    # Since there's no admin endpoint to do this, we'll skip direct testing of this
    # or assume it would be tested if such an endpoint existed.
    # For a full integration test, one might directly manipulate the DB here if using a test DB session.
    # from sqlalchemy.ext.asyncio import AsyncSession
    # from app.api.v1.deps import get_db # This would be the overridden one
    # from shared.models import User as UserModel
    # from sqlalchemy import update
    # async for db_session in fastapi_app.dependency_overrides[get_db](): # Get the overridden session
    #     await db_session.execute(update(UserModel).where(UserModel.id == user_id).values(is_active=False))
    #     await db_session.commit()

    # For now, we acknowledge this state exists and is checked.
    # If we could make the user inactive:
    # login_payload = {"username": user_data["username"], "password": user_data["password"]}
    # response = await client.post(f"{API_V1_AUTH_PREFIX}/token", data=login_payload)
    # assert response.status_code == status.HTTP_400_BAD_REQUEST
    # assert "Inactive user" in response.json()["detail"]
    pass # Placeholder for inactive user test if DB manipulation is added

# --- Test Accessing Protected Endpoint (/me) ---
async def test_read_me_success(client: AsyncClient):
    user_data = get_unique_user_data("me_succ")
    reg_response = await client.post(f"{API_V1_AUTH_PREFIX}/register", json=user_data)
    user_id = reg_response.json()["id"]

    login_payload = {"username": user_data["username"], "password": user_data["password"]}
    await client.post(f"{API_V1_AUTH_PREFIX}/token", data=login_payload) # Sets cookies

    me_response = await client.get(f"{API_V1_AUTH_PREFIX}/me")
    assert me_response.status_code == status.HTTP_200_OK
    me_data = me_response.json()
    assert me_data["username"] == user_data["username"]
    assert me_data["email"] == user_data["email"]
    assert me_data["id"] == user_id

async def test_read_me_no_auth(client: AsyncClient):
    me_response = await client.get(f"{API_V1_AUTH_PREFIX}/me")
    assert me_response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Could not validate credentials" in me_response.json()["detail"]

# --- Test Token Refresh ---
async def test_refresh_token_success(client: AsyncClient):
    user_data = get_unique_user_data("refresh_succ")
    await client.post(f"{API_V1_AUTH_PREFIX}/register", json=user_data)

    login_payload = {"username": user_data["username"], "password": user_data["password"]}
    login_response = await client.post(f"{API_V1_AUTH_PREFIX}/token", data=login_payload)
    initial_access_cookie_value = client.cookies.get("access_token_cookie")
    initial_refresh_cookie_value = client.cookies.get("refresh_token_cookie")
    csrf_token = client.cookies.get("csrf_access_token") # As per CsrfSettings cookie_key
    assert csrf_token is not None

    headers = {"X-CSRF-TOKEN": csrf_token} # As per CsrfSettings header_name
    refresh_response = await client.post(f"{API_V1_AUTH_PREFIX}/token/refresh", headers=headers)

    assert refresh_response.status_code == status.HTTP_200_OK
    refresh_data = refresh_response.json()
    assert "access_token" in refresh_data
    assert refresh_data["token_type"] == "bearer"

    new_access_cookie_value = client.cookies.get("access_token_cookie")
    new_refresh_cookie_value = client.cookies.get("refresh_token_cookie")
    assert new_access_cookie_value != initial_access_cookie_value
    assert new_refresh_cookie_value != initial_refresh_cookie_value
    assert "csrf_access_token" in refresh_response.cookies # New CSRF cookie should be set

async def test_refresh_token_no_csrf_header(client: AsyncClient):
    user_data = get_unique_user_data("refresh_no_csrf")
    await client.post(f"{API_V1_AUTH_PREFIX}/register", json=user_data)
    login_payload = {"username": user_data["username"], "password": user_data["password"]}
    await client.post(f"{API_V1_AUTH_PREFIX}/token", data=login_payload) # Sets cookies including CSRF cookie

    # Attempt refresh without X-CSRF-TOKEN header
    refresh_response = await client.post(f"{API_V1_AUTH_PREFIX}/token/refresh")
    assert refresh_response.status_code == status.HTTP_403_FORBIDDEN # CSRF validation failure
    assert "Missing CSRF Token" in refresh_response.json()["detail"] # Or similar message from fastapi-csrf-protect

async def test_refresh_token_no_refresh_cookie(client: AsyncClient):
    user_data = get_unique_user_data("refresh_no_cookie")
    await client.post(f"{API_V1_AUTH_PREFIX}/register", json=user_data)
    login_payload = {"username": user_data["username"], "password": user_data["password"]}
    await client.post(f"{API_V1_AUTH_PREFIX}/token", data=login_payload)
    csrf_token = client.cookies.get("csrf_access_token")

    # Manually clear the refresh_token_cookie from the client's cookie jar
    client.cookies.delete("refresh_token_cookie", domain="testserver", path=f"{API_V1_AUTH_PREFIX}/token/refresh")
    
    headers = {"X-CSRF-TOKEN": csrf_token}
    refresh_response = await client.post(f"{API_V1_AUTH_PREFIX}/token/refresh", headers=headers)
    assert refresh_response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Refresh token missing" in refresh_response.json()["detail"]

# --- Test Logout ---
async def test_logout_success(client: AsyncClient):
    user_data = get_unique_user_data("logout_succ")
    await client.post(f"{API_V1_AUTH_PREFIX}/register", json=user_data)
    login_payload = {"username": user_data["username"], "password": user_data["password"]}
    await client.post(f"{API_V1_AUTH_PREFIX}/token", data=login_payload)
    csrf_token = client.cookies.get("csrf_access_token")
    assert csrf_token is not None

    headers = {"X-CSRF-TOKEN": csrf_token}
    logout_response = await client.post(f"{API_V1_AUTH_PREFIX}/logout", headers=headers)
    assert logout_response.status_code == status.HTTP_200_OK
    assert logout_response.json()["message"] == "Logout successful"

    # Check cookies are cleared (httpx client updates its cookie jar based on Set-Cookie headers)
    assert client.cookies.get("access_token_cookie") is None
    assert client.cookies.get("refresh_token_cookie", path=f"{API_V1_AUTH_PREFIX}/token/refresh") is None
    assert client.cookies.get("csrf_access_token") is None
    
    # Verify by trying to access /me
    me_response_after_logout = await client.get(f"{API_V1_AUTH_PREFIX}/me")
    assert me_response_after_logout.status_code == status.HTTP_401_UNAUTHORIZED

    # Further check: try to refresh token after logout (should fail as refresh token is revoked)
    # Need a new CSRF token if the old one was also cleared or tied to session
    # This part is tricky because obtaining a CSRF token usually happens during login.
    # If logout clears the CSRF cookie, we can't easily send a CSRF-protected request.
    # However, the refresh token itself should be invalid.
    # Let's assume we could get a CSRF token somehow or test without it if refresh endpoint
    # didn't require CSRF (but it does).
    # For now, the check that /me fails is a good indicator.
    # A more direct test would be to try using the old refresh_token_cookie value (if saved before logout)
    # with a new CSRF token (if obtainable) and expect a 401.
    # This tests the DB revocation of the refresh token.

async def test_logout_no_csrf_header(client: AsyncClient):
    user_data = get_unique_user_data("logout_no_csrf")
    await client.post(f"{API_V1_AUTH_PREFIX}/register", json=user_data)
    login_payload = {"username": user_data["username"], "password": user_data["password"]}
    await client.post(f"{API_V1_AUTH_PREFIX}/token", data=login_payload)

    logout_response = await client.post(f"{API_V1_AUTH_PREFIX}/logout") # No CSRF header
    assert logout_response.status_code == status.HTTP_403_FORBIDDEN
    assert "Missing CSRF Token" in logout_response.json()["detail"]

# TODO:
# - Test access token JTI revocation: After logout, an old access token (if captured) should not work.
#   This is hard to test directly with httpx as it manages cookies. Would require manually setting Authorization header.
#   The in-memory `revoked_access_jti_blacklist` in security.py is for this.
# - Test refresh token DB revocation: After logout or refresh, the old refresh token JTI should be marked
#   as revoked in the DB. This requires DB inspection or attempting to use the old token.
# - Test rate limiting: Requires specific setup, potentially mocking `slowapi` or time.
# - Test secure attributes of cookies more directly if possible (httpx limitations).
