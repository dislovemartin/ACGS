import pytest
from fastapi.testclient import TestClient

# The client fixture is automatically sourced from conftest.py
# No need to override get_async_db here anymore, conftest.py handles it.


@pytest.mark.asyncio
async def test_read_root(client: TestClient):  # Inject the client fixture
    # The client fixture uses http://testserver as the default base_url
    response = client.get("/")
    # Assuming your root endpoint in auth_service.main returns a health check.
    # Update this assertion based on your actual root endpoint response.
    # For now, let's assume it should be a 200 if the service is up.
    # If you have a specific health check message, assert that too.
    assert response.status_code == 200
    # Example if you have a specific JSON response:
    # assert response.json() == {"message": "Auth Service Online"}
    # If your root path is not meant to be found (returns 404), adjust.
    # Expecting a successful health check at root for now.
