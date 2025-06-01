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
    """Create test HTTP client with proper cleanup."""
    if ASYNC_DEPS_AVAILABLE:
        async with AsyncClient() as client:
            yield client
    else:
        yield None


@pytest.fixture(autouse=True)
async def integration_test_cleanup():
    """Cleanup for integration tests to prevent pollution."""
    import gc
    import tempfile
    from pathlib import Path

    # Track resources
    temp_files = []
    temp_dirs = []

    yield {
        'temp_files': temp_files,
        'temp_dirs': temp_dirs
    }

    # Cleanup temporary files created during integration tests
    for temp_file in temp_files:
        try:
            if Path(temp_file).exists():
                Path(temp_file).unlink()
        except Exception as e:
            print(f"Warning: Failed to remove temp file {temp_file}: {e}")

    # Cleanup temporary directories
    for temp_dir in temp_dirs:
        try:
            if Path(temp_dir).exists():
                import shutil
                shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Warning: Failed to remove temp directory {temp_dir}: {e}")

    # Clean up integration test result files
    result_files = [
        "phase2_test_results.json",
        "phase3_test_results.json",
        "integration_test_results.json",
        "alphaevolve_test_results.json"
    ]

    for result_file in result_files:
        try:
            if Path(result_file).exists():
                Path(result_file).unlink()
        except Exception as e:
            print(f"Warning: Failed to remove result file {result_file}: {e}")

    # Force garbage collection
    gc.collect()


@pytest.fixture
def integration_temp_manager(integration_test_cleanup):
    """Temporary file manager for integration tests."""
    import tempfile
    from pathlib import Path

    def create_temp_file(suffix="", prefix="integration_test_", content=None):
        """Create temporary file for integration testing."""
        fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
        os.close(fd)

        if content is not None:
            Path(path).write_text(content)

        integration_test_cleanup['temp_files'].append(path)
        return path

    def create_temp_dir(suffix="", prefix="integration_test_"):
        """Create temporary directory for integration testing."""
        path = tempfile.mkdtemp(suffix=suffix, prefix=prefix)
        integration_test_cleanup['temp_dirs'].append(path)
        return path

    return {
        'create_file': create_temp_file,
        'create_dir': create_temp_dir
    }
