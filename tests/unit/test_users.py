from uuid import uuid4  # For generating unique emails
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient  # Use TestClient from FastAPI

# Add the src directory to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "src/backend"))

try:
    from backend.auth_service.app.core.config import settings
except ImportError:
    # Fallback for testing without full backend setup
    settings = None

# The client fixture and DB setup are now handled by conftest.py
# No need for override_get_async_db_users or local client fixture here.


@pytest.fixture
def random_user_payload() -> dict:
    test_email = f"testuser_{uuid4()}@example.com"
    return {"email": test_email, "password": "testpassword123"}


@pytest.mark.asyncio
async def test_create_user(client: TestClient, random_user_payload: dict):
    url = f"{settings.API_V1_STR}/users/"
    response = client.post(url, json=random_user_payload)
    assert response.status_code == 200  # Or 201 if API created
    data = response.json()
    assert data["email"] == random_user_payload["email"]
    assert "id" in data
    assert "hashed_password" not in data  # Ensure no password hash


@pytest.mark.asyncio
async def test_create_user_existing_email(
    client: TestClient, random_user_payload: dict
):
    url = f"{settings.API_V1_STR}/users/"
    client.post(url, json=random_user_payload)  # Create user first
    response = client.post(url, json=random_user_payload)  # Try again
    assert response.status_code == 400
    # Expected: {"detail": "Email already registered"}


@pytest.mark.asyncio
async def test_login_for_access_token(client: TestClient, random_user_payload: dict):
    user_creation_url = f"{settings.API_V1_STR}/users/"
    client.post(user_creation_url, json=random_user_payload)  # Create user

    login_data = {
        "username": random_user_payload["email"],
        "password": random_user_payload["password"],
    }
    login_url = f"{settings.API_V1_STR}/login/access-token"
    response = client.post(login_url, data=login_data)
    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens
    assert tokens["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: TestClient, random_user_payload: dict):
    user_creation_url = f"{settings.API_V1_STR}/users/"
    client.post(user_creation_url, json=random_user_payload)  # Create user

    login_data = {
        "username": random_user_payload["email"],
        "password": "wrongtestpassword",
    }
    login_url = f"{settings.API_V1_STR}/login/access-token"
    response = client.post(login_url, data=login_data)
    assert response.status_code == 401  # Unauthorized


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: TestClient):
    login_data = {"username": "nonexistent@example.com", "password": "testpassword123"}
    login_url = f"{settings.API_V1_STR}/login/access-token"
    response = client.post(login_url, data=login_data)
    assert response.status_code == 401  # Unauthorized


# Using AsyncClient for new tests to align with cookie-based auth flow
# as seen in test_auth_flows.py and used by the /auth/me endpoint.
# The TestClient used above for /users/ and /login/access-token might
# need to be re-evaluated if those endpoints also switch to HttpOnly cookie auth.

# API Prefixes (assuming they are consistent, /api/v1 used by settings)
API_V1_AUTH_PREFIX = f"{settings.API_V1_STR}/auth"


@pytest.mark.asyncio
async def test_read_current_user_success(
    async_client: TestClient, random_user_payload: dict
):
    # Step 1: Register the user (using the /auth/register endpoint)
    # Assuming random_user_payload provides 'email' and 'password',
    # but /auth/register expects 'username', 'email', 'password', 'full_name'
    # We'll adapt random_user_payload or create a new one.
    user_data_for_registration = {
        "username": random_user_payload["email"].split("@")[0] + "_usr", # Create a unique username
        "email": random_user_payload["email"],
        "password": random_user_payload["password"],
        "full_name": "Test User Me"
    }
    register_url = f"{API_V1_AUTH_PREFIX}/register"
    response = await async_client.post(register_url, json=user_data_for_registration)
    assert response.status_code == 201
    created_user_data = response.json()

    # Step 2: Log in to set HttpOnly cookies
    login_payload = {
        "username": user_data_for_registration["username"],
        "password": user_data_for_registration["password"],
    }
    login_url = f"{API_V1_AUTH_PREFIX}/token"
    response = await async_client.post(login_url, data=login_payload)
    assert response.status_code == 200
    # Cookies (access_token_cookie, refresh_token_cookie, csrf_access_token) are now set in async_client

    # Step 3: Request the /me endpoint
    me_url = f"{API_V1_AUTH_PREFIX}/me"
    response = await async_client.get(me_url)
    assert response.status_code == 200
    user_me_data = response.json()

    assert user_me_data["email"] == user_data_for_registration["email"]
    assert user_me_data["username"] == user_data_for_registration["username"] # Assuming /me returns username
    assert user_me_data["full_name"] == user_data_for_registration["full_name"]
    assert user_me_data["id"] == created_user_data["id"]
    assert user_me_data["is_active"] is True
    assert "hashed_password" not in user_me_data


@pytest.mark.asyncio
async def test_read_current_user_unauthenticated(async_client: TestClient):
    me_url = f"{API_V1_AUTH_PREFIX}/me"
    response = await async_client.get(me_url)
    assert response.status_code == 401
    # Based on test_auth_flows.py, detail is "Could not validate credentials"
    # but security.get_current_active_user raises "Not authenticated" if no token.
    # Let's check the actual error message from security.py if possible,
    # otherwise, "Not authenticated" is a common one.
    # The `Depends(security.get_current_active_user)` ultimately uses `authenticate_user_from_cookie`
    # which calls `get_user_from_token_cookie`. If token is missing, it raises:
    # HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token missing or invalid")
    # If token is invalid (e.g. bad JTI), it's "Could not validate credentials".
    # If no cookie, it's "Access token missing or invalid".
    assert "Access token missing or invalid" in response.json()["detail"]

# Note on user update tests:
# The current `auth_service/app/api/v1/endpoints.py` does not define
# standard user update endpoints (e.g., PUT/PATCH to /auth/me or /auth/users/{user_id}).
# User creation is via /auth/register.
# If such endpoints were added, tests would be structured similarly to
# test_read_current_user_success, by first authenticating and then sending
# PUT/PATCH requests with valid and invalid payloads, and checking for
# unauthenticated access.
# For example:
# async def test_update_current_user_full_name(async_client: TestClient, registered_user_cookies):
#     update_payload = {"full_name": "Updated Test User"}
#     # Assume registered_user_cookies has set up the client with auth cookies
#     # and returns the initial user data.
#     # csrf_token = async_client.cookies.get("csrf_access_token")
#     # headers = {"X-CSRF-TOKEN": csrf_token}
#     # response = await async_client.patch(f"{API_V1_AUTH_PREFIX}/me", json=update_payload, headers=headers)
#     # assert response.status_code == 200
#     # updated_data = response.json()
#     # assert updated_data["full_name"] == "Updated Test User"
#     # assert updated_data["email"] == registered_user_cookies["email"] # Ensure other fields are not changed unless specified
# Pass for now as no update endpoint for users defined in endpoints.py
pass
