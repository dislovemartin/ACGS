from uuid import uuid4  # For generating unique emails

import pytest
from app.core.config import settings
from fastapi.testclient import TestClient  # Use TestClient from FastAPI

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


# TODO: Add tests for more user endpoints (read_users_me, update_user).
# These require an authenticated client.

# Example for an authenticated request:
# def get_auth_headers(client: TestClient, user_payload: dict) -> dict:
#     user_url = f"{settings.API_V1_STR}/users/"
#     client.post(user_url, json=user_payload) # Create & login
#     login_data = {
#         "username": user_payload["email"],
#         "password": user_payload["password"]
#     }
#     login_url = f"{settings.API_V1_STR}/login/access-token"
#     response = client.post(login_url, data=login_data)
#     tokens = response.json()
#     return {"Authorization": f"Bearer {tokens['access_token']}"}
#
# @pytest.mark.asyncio
# async def test_read_current_user(client: TestClient, random_user_payload: dict):
#     headers = get_auth_headers(client, random_user_payload)
#     me_url = f"{settings.API_V1_STR}/users/me"
#     response = client.get(me_url, headers=headers)
#     assert response.status_code == 200
#     data = response.json()
#     assert data["email"] == random_user_payload["email"]
