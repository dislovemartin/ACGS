# ACGS-PGP Integration Tests Configuration
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

# Set environment variables for testing
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://acgs_user:acgs_password@localhost:5434/acgs_test")

try:
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker
    ASYNC_DEPS_AVAILABLE = True
except ImportError:
    ASYNC_DEPS_AVAILABLE = False

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def anyio_backend():
    return "asyncio"

# Mock database session for tests that don't need real database
@pytest.fixture
async def mock_db_session():
    """Mock database session for testing without real database."""
    class MockSession:
        async def execute(self, query):
            class MockResult:
                def scalar(self): return 0
                def scalars(self): return []
                def fetchall(self): return []
                def fetchone(self): return None
            return MockResult()
        
        async def get(self, model, id): 
            return None
        
        def add(self, obj): 
            pass
        
        async def commit(self): 
            pass
        
        async def refresh(self, obj): 
            pass
        
        async def rollback(self):
            pass
        
        async def close(self):
            pass
    
    return MockSession()

# Test client fixture for HTTP testing
@pytest.fixture
async def test_client():
    """Create test HTTP client."""
    if ASYNC_DEPS_AVAILABLE:
        async with AsyncClient() as client:
            yield client
    else:
        yield None
