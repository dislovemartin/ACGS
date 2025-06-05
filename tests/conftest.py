#!/usr/bin/env python3
"""
Enhanced pytest configuration with comprehensive dependency mocking.
Provides fixtures and utilities for reliable integration testing.
"""

import asyncio
import os
import sys
import tempfile
from typing import Dict, Any, AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import pytest_asyncio
from httpx import AsyncClient
import json
from datetime import datetime, timedelta

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../src/backend/shared'))

from utils import get_config, reset_config


# =============================================================================
# Configuration and Environment Setup
# =============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment with proper configuration."""
    # Set test environment variables
    os.environ.update({
        'ENVIRONMENT': 'testing',
        'TEST_MODE': 'true',
        'DEBUG': 'false',
        'DATABASE_URL': 'postgresql+asyncpg://test_user:test_password@localhost:5433/test_acgs_db',
        'JWT_SECRET_KEY': 'test-secret-key-for-testing-only',
        'CSRF_SECRET_KEY': 'test-csrf-secret-key-for-testing-only',
    })
    
    # Reset configuration to pick up test environment
    reset_config()
    
    yield
    
    # Cleanup
    reset_config()


@pytest.fixture
def test_config():
    """Provide test configuration instance."""
    return get_config()


# =============================================================================
# Database Mocking and Fixtures
# =============================================================================

@pytest_asyncio.fixture
async def mock_database():
    """Mock database session for testing with proper cleanup."""
    from unittest.mock import AsyncMock

    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session.scalar = AsyncMock()
    mock_session.scalars = AsyncMock()

    yield mock_session

    # Cleanup
    await mock_session.close()


@pytest_asyncio.fixture
async def isolated_database_session():
    """Create an isolated database session for testing with automatic cleanup."""
    import tempfile
    from pathlib import Path

    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix=".db", prefix="test_isolated_")
    os.close(db_fd)

    try:
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker

        # Create isolated test database
        test_db_url = f"sqlite+aiosqlite:///{db_path}"
        engine = create_async_engine(test_db_url, echo=False)

        AsyncSessionFactory = sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        async with AsyncSessionFactory() as session:
            yield session

            # Ensure rollback on test completion
            await session.rollback()

        # Close engine
        await engine.dispose()

    except ImportError:
        # Fallback to mock if SQLAlchemy not available
        mock_session = AsyncMock()
        yield mock_session
        await mock_session.close()

    finally:
        # Clean up database file
        try:
            if Path(db_path).exists():
                Path(db_path).unlink()
        except Exception as e:
            print(f"Warning: Failed to remove test DB {db_path}: {e}")


@pytest.fixture
def mock_async_session_factory():
    """Mock async session factory."""
    from unittest.mock import AsyncMock, MagicMock

    mock_factory = MagicMock()
    mock_session = AsyncMock()
    mock_factory.return_value.__aenter__.return_value = mock_session
    mock_factory.return_value.__aexit__.return_value = None

    return mock_factory, mock_session


@pytest_asyncio.fixture
async def db_session():
    """Database session fixture for tests that need it."""
    from unittest.mock import AsyncMock

    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session.scalar = AsyncMock()
    mock_session.scalars = AsyncMock()

    yield mock_session

    await mock_session.close()


# =============================================================================
# HTTP Client Mocking
# =============================================================================

@pytest.fixture
def mock_httpx_client():
    """Mock HTTPX client for external service calls with cleanup."""
    from unittest.mock import AsyncMock, MagicMock

    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "ok"}
    mock_response.text = '{"status": "ok"}'
    mock_response.headers = {}

    mock_client.get.return_value = mock_response
    mock_client.post.return_value = mock_response
    mock_client.put.return_value = mock_response
    mock_client.patch.return_value = mock_response
    mock_client.delete.return_value = mock_response
    mock_client.close = AsyncMock()
    mock_client.aclose = AsyncMock()

    return mock_client


@pytest.fixture
def mock_service_responses():
    """Predefined mock responses for different services."""
    return {
        'auth_service': {
            'health': {'status': 'ok', 'service': 'auth'},
            'login': {'access_token': 'mock_token', 'token_type': 'bearer'},
            'verify': {'valid': True, 'user_id': 'test_user'},
        },
        'ac_service': {
            'health': {'status': 'ok', 'service': 'ac'},
            'principles': [
                {'id': 1, 'title': 'Test Principle', 'content': 'Test content'},
                {'id': 2, 'title': 'Another Principle', 'content': 'More content'},
            ],
            'create_principle': {'id': 3, 'title': 'New Principle', 'content': 'New content'},
        },
        'fv_service': {
            'health': {'status': 'ok', 'service': 'fv'},
            'bias_detection': {
                'overall_bias_score': 0.15,
                'risk_level': 'low',
                'results': [
                    {
                        'metric_id': 'demographic_parity',
                        'bias_detected': False,
                        'bias_score': 0.15,
                        'explanation': 'Low bias detected'
                    }
                ]
            },
        },
        'gs_service': {
            'health': {'status': 'ok', 'service': 'gs'},
            'synthesis': {
                'synthesized_policy': 'Generated policy content',
                'confidence_score': 0.85,
                'reasoning': 'Policy synthesized based on principles'
            },
        },
        'integrity_service': {
            'health': {'status': 'ok', 'service': 'integrity'},
            'verify': {'valid': True, 'signature': 'mock_signature'},
        },
        'pgc_service': {
            'health': {'status': 'ok', 'service': 'pgc'},
            'compile': {'compiled_policy': 'package main\nallow = true'},
        },
    }


# =============================================================================
# External Service Mocking
# =============================================================================

@pytest.fixture
def mock_llm_service():
    """Mock LLM service responses."""
    from unittest.mock import AsyncMock
    
    mock_llm = AsyncMock()
    mock_llm.generate.return_value = {
        'generated_text': 'Mock LLM response',
        'confidence': 0.95,
        'tokens_used': 150,
    }
    mock_llm.embed.return_value = [0.1, 0.2, 0.3, 0.4, 0.5] * 100  # Mock embedding
    
    return mock_llm


@pytest.fixture
def mock_z3_solver():
    """Mock Z3 solver for formal verification."""
    from unittest.mock import MagicMock
    
    mock_solver = MagicMock()
    mock_solver.check.return_value = 'sat'  # satisfiable
    mock_solver.model.return_value = MagicMock()
    mock_solver.add = MagicMock()
    mock_solver.push = MagicMock()
    mock_solver.pop = MagicMock()
    
    return mock_solver


@pytest.fixture
def mock_fairlearn_metrics():
    """Mock fairlearn metrics for bias detection."""
    from unittest.mock import MagicMock
    
    mock_metrics = {
        'demographic_parity_difference': MagicMock(return_value=0.15),
        'selection_rate': MagicMock(return_value={'group_a': 0.7, 'group_b': 0.55}),
        'equalized_odds_difference': MagicMock(return_value=0.08),
    }
    
    return mock_metrics


# =============================================================================
# Authentication and Security Mocking
# =============================================================================

@pytest.fixture
def mock_jwt_token():
    """Mock JWT token for authentication testing."""
    return {
        'access_token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.mock_payload.mock_signature',
        'token_type': 'bearer',
        'expires_in': 3600,
        'user_id': 'test_user_123',
        'roles': ['user', 'policy_manager'],
    }


@pytest.fixture
def mock_auth_headers(mock_jwt_token):
    """Mock authentication headers."""
    return {
        'Authorization': f"Bearer {mock_jwt_token['access_token']}",
        'Content-Type': 'application/json',
    }


@pytest.fixture
def mock_csrf_token():
    """Mock CSRF token for security testing."""
    return 'mock_csrf_token_for_testing'


@pytest.fixture
def test_user():
    """Test user data for authentication tests."""
    return {
        'id': 'test_user_123',
        'username': 'test_user',
        'email': 'test@example.com',
        'roles': ['user', 'policy_manager'],
        'is_active': True,
        'created_at': '2024-01-01T00:00:00Z'
    }


@pytest.fixture
def test_admin_user():
    """Test admin user data for authentication tests."""
    return {
        'id': 'admin_user_456',
        'username': 'admin_user',
        'email': 'admin@example.com',
        'roles': ['admin', 'policy_manager', 'system_admin'],
        'is_active': True,
        'created_at': '2024-01-01T00:00:00Z'
    }


@pytest.fixture
def create_test_principle():
    """Factory function to create test principles."""
    def _create_principle(title="Test Principle", content="Test content", priority_weight=0.8):
        return {
            'title': title,
            'content': content,
            'priority_weight': priority_weight,
            'scope': 'global',
            'normative_statement': 'Test normative statement',
            'constraints': ['test_constraint'],
            'rationale': 'Test rationale',
        }
    return _create_principle


@pytest.fixture
def create_test_policy():
    """Factory function to create test policies."""
    def _create_policy(title="Test Policy", content="Test policy content", version="1.0.0"):
        return {
            'title': title,
            'content': content,
            'version': version,
            'status': 'active',
            'created_by': 'test_user',
            'policy_type': 'rego',
            'enforcement_level': 'strict',
        }
    return _create_policy


# =============================================================================
# Test Data Factories
# =============================================================================

@pytest.fixture
def test_principle_data():
    """Test data for AC principles."""
    return {
        'id': 1,
        'title': 'Test Principle',
        'content': 'This is a test principle for validation',
        'priority_weight': 0.8,
        'scope': 'global',
        'normative_statement': 'Users should be treated fairly',
        'constraints': ['no_discrimination', 'privacy_protection'],
        'rationale': 'Ensures fair treatment of all users',
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat(),
    }


@pytest.fixture
def test_policy_data():
    """Test data for policies."""
    return {
        'id': 1,
        'title': 'Test Policy',
        'content': 'This is a test policy',
        'version': '1.0.0',
        'status': 'active',
        'created_by': 'test_user',
        'created_at': datetime.utcnow().isoformat(),
    }


@pytest.fixture
def test_bias_detection_data():
    """Test data for bias detection."""
    return {
        'policy_rule_ids': ['rule_1', 'rule_2'],
        'bias_metrics': [
            {
                'metric_id': 'demographic_parity',
                'metric_name': 'Demographic Parity',
                'metric_description': 'Tests for demographic parity',
                'metric_type': 'statistical',
                'threshold': 0.1,
            }
        ],
        'protected_attributes': ['ethnicity', 'gender'],
        'dataset': [
            {'age': 25, 'income': 50000, 'ethnicity': 'group_a', 'gender': 'female'},
            {'age': 35, 'income': 75000, 'ethnicity': 'group_b', 'gender': 'male'},
            {'age': 28, 'income': 60000, 'ethnicity': 'group_a', 'gender': 'male'},
            {'age': 45, 'income': 90000, 'ethnicity': 'group_b', 'gender': 'female'},
        ],
    }


# =============================================================================
# Async Testing Utilities
# =============================================================================

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def async_client():
    """Async HTTP client for testing FastAPI applications with cleanup."""
    try:
        from httpx import AsyncClient

        async with AsyncClient() as client:
            yield client

    except ImportError:
        # Fallback to mock client
        mock_client = AsyncMock()
        mock_client.aclose = AsyncMock()
        yield mock_client
        await mock_client.aclose()


# =============================================================================
# Mock Context Managers
# =============================================================================

@pytest.fixture
def mock_service_clients(mock_httpx_client, mock_service_responses):
    """Comprehensive mock for all service clients."""
    
    def create_service_mock(service_name: str):
        """Create a mock for a specific service."""
        mock = AsyncMock()
        responses = mock_service_responses.get(service_name, {})
        
        # Setup method responses based on service
        for method, response in responses.items():
            if hasattr(mock, method):
                getattr(mock, method).return_value = response
        
        mock.close = AsyncMock()
        return mock
    
    return {
        'auth': create_service_mock('auth_service'),
        'ac': create_service_mock('ac_service'),
        'fv': create_service_mock('fv_service'),
        'gs': create_service_mock('gs_service'),
        'integrity': create_service_mock('integrity_service'),
        'pgc': create_service_mock('pgc_service'),
    }


# =============================================================================
# Performance and Monitoring Mocks
# =============================================================================

@pytest.fixture
def mock_prometheus_metrics():
    """Mock Prometheus metrics for monitoring tests."""
    from unittest.mock import MagicMock
    
    mock_counter = MagicMock()
    mock_histogram = MagicMock()
    mock_gauge = MagicMock()
    
    mock_counter.inc = MagicMock()
    mock_histogram.observe = MagicMock()
    mock_gauge.set = MagicMock()
    
    return {
        'counter': mock_counter,
        'histogram': mock_histogram,
        'gauge': mock_gauge,
    }


# =============================================================================
# Cleanup and Teardown
# =============================================================================

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Automatic cleanup after each test."""
    yield

    # Reset any global state
    reset_config()

    # Clear any cached modules
    import sys
    modules_to_clear = [m for m in sys.modules.keys() if m.startswith('app.') or m.startswith('shared.')]
    for module in modules_to_clear:
        if module in sys.modules:
            del sys.modules[module]


@pytest_asyncio.fixture(autouse=True)
async def comprehensive_test_teardown():
    """Comprehensive teardown procedures to prevent test pollution."""
    # Store initial state
    initial_modules = set(sys.modules.keys())
    initial_env = dict(os.environ)

    # Track resources for cleanup
    cleanup_tasks = []
    temp_files = []
    temp_dirs = []
    db_connections = []
    http_clients = []

    yield {
        'cleanup_tasks': cleanup_tasks,
        'temp_files': temp_files,
        'temp_dirs': temp_dirs,
        'db_connections': db_connections,
        'http_clients': http_clients
    }

    # Comprehensive cleanup
    await _perform_comprehensive_cleanup(
        cleanup_tasks, temp_files, temp_dirs,
        db_connections, http_clients,
        initial_modules, initial_env
    )


async def _perform_comprehensive_cleanup(
    cleanup_tasks, temp_files, temp_dirs,
    db_connections, http_clients,
    initial_modules, initial_env
):
    """Perform comprehensive cleanup of all test resources."""
    import gc
    import shutil
    import asyncio
    from pathlib import Path

    # 1. Execute custom cleanup tasks
    for task in cleanup_tasks:
        try:
            if asyncio.iscoroutinefunction(task):
                await task()
            else:
                task()
        except Exception as e:
            print(f"Warning: Cleanup task failed: {e}")

    # 2. Close HTTP clients
    for client in http_clients:
        try:
            if hasattr(client, 'aclose'):
                await client.aclose()
            elif hasattr(client, 'close'):
                if asyncio.iscoroutinefunction(client.close):
                    await client.close()
                else:
                    client.close()
        except Exception as e:
            print(f"Warning: Failed to close HTTP client: {e}")

    # 3. Close database connections
    for conn in db_connections:
        try:
            if hasattr(conn, 'close'):
                if asyncio.iscoroutinefunction(conn.close):
                    await conn.close()
                else:
                    conn.close()
            elif hasattr(conn, 'aclose'):
                await conn.aclose()
        except Exception as e:
            print(f"Warning: Failed to close database connection: {e}")

    # 4. Clean up temporary files
    for temp_file in temp_files:
        try:
            if Path(temp_file).exists():
                Path(temp_file).unlink()
        except Exception as e:
            print(f"Warning: Failed to remove temp file {temp_file}: {e}")

    # 5. Clean up temporary directories
    for temp_dir in temp_dirs:
        try:
            if Path(temp_dir).exists():
                shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Warning: Failed to remove temp directory {temp_dir}: {e}")

    # 6. Clean up test database files
    test_db_patterns = [
        "test_*.db", "test_*.db-*", "*.test.db",
        "test_acgs_pgp.db*", "test_auth_app.db*"
    ]

    for pattern in test_db_patterns:
        for db_file in Path(".").glob(pattern):
            try:
                db_file.unlink()
            except Exception as e:
                print(f"Warning: Failed to remove test DB {db_file}: {e}")

    # 7. Clean up test result files
    result_patterns = [
        "*_test_results.json", "test_*.json",
        "phase*_test_results.json", "*.test.json"
    ]

    for pattern in result_patterns:
        for result_file in Path(".").glob(pattern):
            try:
                result_file.unlink()
            except Exception as e:
                print(f"Warning: Failed to remove result file {result_file}: {e}")

    # 8. Reset environment variables
    for key in list(os.environ.keys()):
        if key not in initial_env:
            del os.environ[key]
        elif os.environ[key] != initial_env[key]:
            os.environ[key] = initial_env[key]

    # 9. Clear imported modules (except initial ones)
    current_modules = set(sys.modules.keys())
    modules_to_remove = current_modules - initial_modules

    for module_name in modules_to_remove:
        if module_name in sys.modules:
            try:
                del sys.modules[module_name]
            except Exception:
                pass  # Some modules can't be safely removed

    # 10. Force garbage collection
    gc.collect()

    # 11. Reset configuration
    reset_config()


# =============================================================================
# Temporary File and Directory Management
# =============================================================================

@pytest.fixture
def temp_file_manager():
    """Manage temporary files with automatic cleanup."""
    import tempfile
    import shutil
    from pathlib import Path

    created_files = []
    created_dirs = []

    def create_temp_file(suffix="", prefix="test_", content=None):
        """Create a temporary file and register for cleanup."""
        fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
        os.close(fd)  # Close the file descriptor

        if content is not None:
            Path(path).write_text(content)

        created_files.append(path)
        return path

    def create_temp_dir(suffix="", prefix="test_"):
        """Create a temporary directory and register for cleanup."""
        path = tempfile.mkdtemp(suffix=suffix, prefix=prefix)
        created_dirs.append(path)
        return path

    yield {
        'create_file': create_temp_file,
        'create_dir': create_temp_dir,
        'files': created_files,
        'dirs': created_dirs
    }

    # Cleanup after test
    for temp_file in created_files:
        try:
            if Path(temp_file).exists():
                Path(temp_file).unlink()
        except Exception as e:
            print(f"Warning: Failed to remove temp file {temp_file}: {e}")

    for temp_dir in created_dirs:
        try:
            if Path(temp_dir).exists():
                shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Warning: Failed to remove temp directory {temp_dir}: {e}")


@pytest.fixture
def isolated_test_environment(temp_file_manager):
    """Create an isolated test environment with temporary workspace."""
    import tempfile
    import shutil
    from pathlib import Path

    # Create isolated workspace
    workspace = temp_file_manager['create_dir'](prefix="acgs_test_workspace_")
    workspace_path = Path(workspace)

    # Create standard test directories
    test_dirs = {
        'data': workspace_path / "data",
        'logs': workspace_path / "logs",
        'temp': workspace_path / "temp",
        'config': workspace_path / "config"
    }

    for dir_path in test_dirs.values():
        dir_path.mkdir(exist_ok=True)

    # Set environment variables for isolated testing
    original_env = {}
    test_env_vars = {
        'ACGS_TEST_WORKSPACE': str(workspace_path),
        'ACGS_TEST_DATA_DIR': str(test_dirs['data']),
        'ACGS_TEST_LOG_DIR': str(test_dirs['logs']),
        'ACGS_TEST_TEMP_DIR': str(test_dirs['temp']),
        'ACGS_TEST_CONFIG_DIR': str(test_dirs['config']),
    }

    for key, value in test_env_vars.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value

    yield {
        'workspace': workspace_path,
        'dirs': test_dirs,
        'env': test_env_vars
    }

    # Restore environment variables
    for key, original_value in original_env.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value
