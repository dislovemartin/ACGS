# ACGS-PGP Unit Tests Configuration
import asyncio
import os
import sys
from typing import AsyncGenerator, Generator
from pathlib import Path

import pytest

# Add the src directory to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "src/backend"))
sys.path.insert(0, str(project_root / "src/alphaevolve_gs_engine/src"))

# Ensure shared module can be found by adding backend directory to path
backend_path = str(project_root / "src" / "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

try:
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker
    ASYNC_DEPS_AVAILABLE = True
except ImportError:
    ASYNC_DEPS_AVAILABLE = False

# Test configuration for ACGS-PGP framework
TEST_DB_URL = os.getenv(
    "TEST_ASYNC_DATABASE_URL", "sqlite+aiosqlite:///./test_acgs_pgp.db"
)

# Initialize async components only if dependencies are available
if ASYNC_DEPS_AVAILABLE:
    async_test_engine = create_async_engine(TEST_DB_URL, echo=False)
    AsyncTestSessionFactory = sessionmaker(
        bind=async_test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
else:
    async_test_engine = None
    AsyncTestSessionFactory = None


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def initialize_test_database():
    """Initialize test DB: creates tables before tests, drops them after."""
    if not ASYNC_DEPS_AVAILABLE or not async_test_engine:
        pytest.skip("Async dependencies not available")

    # For now, skip database initialization as we don't have Base imported
    # This can be enhanced when specific service tests are run
    yield


@pytest.fixture()
def mock_client():
    """Provide a mock client for basic testing."""
    class MockClient:
        def __init__(self):
            self.base_url = "http://testserver"

        async def get(self, url, **kwargs):
            return {"status_code": 200, "json": {"message": "mock response"}}

        async def post(self, url, **kwargs):
            return {"status_code": 201, "json": {"message": "mock created"}}

    return MockClient()


@pytest.fixture()
async def async_client():
    """Get an AsyncClient for testing if dependencies are available."""
    if not ASYNC_DEPS_AVAILABLE:
        pytest.skip("AsyncClient dependencies not available")

    # This would need to be configured per service
    # For now, provide a basic client
    async with AsyncClient(base_url="http://testserver") as c:
        yield c
