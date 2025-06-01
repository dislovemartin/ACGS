# ACGS-PGP Test Teardown Procedures

## Overview

This document describes the comprehensive test teardown procedures implemented in ACGS-PGP to prevent test pollution and ensure clean test isolation between test runs.

## Problem Statement

Before implementing these procedures, ACGS-PGP tests suffered from:
- Test pollution between test runs
- Temporary files and directories not being cleaned up
- Database connections and sessions persisting
- HTTP clients not being properly closed
- Environment variables leaking between tests
- Module imports polluting the namespace
- Mock objects persisting across tests

## Solution Architecture

### 1. Comprehensive Test Teardown Fixture

**Location**: `tests/conftest.py`

The `comprehensive_test_teardown` fixture provides a centralized cleanup mechanism that tracks and cleans up all test resources:

```python
@pytest.fixture(autouse=True)
async def comprehensive_test_teardown():
    """Comprehensive teardown procedures to prevent test pollution."""
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
    
    # Comprehensive cleanup performed automatically
```

### 2. Resource-Specific Cleanup

#### Database Cleanup
- **Mock Database Sessions**: Automatically closed after each test
- **Isolated Database Sessions**: Temporary SQLite databases created and removed
- **Connection Pools**: Properly disposed of to prevent connection leaks

#### HTTP Client Cleanup
- **AsyncClient**: Properly closed using `aclose()` method
- **Mock Clients**: Reset and cleaned up
- **Connection Pools**: Closed to prevent resource leaks

#### Temporary File Management
- **Temporary Files**: Created with `tempfile.mkstemp()` and tracked for cleanup
- **Temporary Directories**: Created with `tempfile.mkdtemp()` and recursively removed
- **Test Artifacts**: JSON result files and test databases automatically cleaned

#### Environment Variable Isolation
- **Initial State Capture**: Environment state captured before tests
- **Variable Restoration**: Environment restored to initial state after tests
- **Test-Specific Variables**: Isolated test environment variables cleaned up

#### Module Import Isolation
- **Module Tracking**: Initial `sys.modules` state captured
- **Import Cleanup**: Test-specific imports removed after tests
- **Namespace Protection**: Prevents module pollution between tests

## Implementation Details

### 3. Fixture Hierarchy

```
comprehensive_test_teardown (autouse, async)
├── temp_file_manager
├── isolated_test_environment
├── isolated_database_session
├── async_client
└── mock_database
```

### 4. Cleanup Sequence

1. **Custom Cleanup Tasks**: Execute registered cleanup functions
2. **HTTP Client Cleanup**: Close all HTTP clients and connections
3. **Database Cleanup**: Close database sessions and connections
4. **Temporary File Cleanup**: Remove temporary files
5. **Temporary Directory Cleanup**: Recursively remove temporary directories
6. **Test Database Cleanup**: Remove test database files
7. **Test Result Cleanup**: Remove test result JSON files
8. **Environment Variable Restoration**: Reset environment to initial state
9. **Module Import Cleanup**: Remove test-specific module imports
10. **Garbage Collection**: Force garbage collection
11. **Configuration Reset**: Reset application configuration

### 5. Error Handling

The teardown procedures include comprehensive error handling:
- Cleanup failures are logged as warnings but don't fail tests
- Each cleanup step is isolated to prevent cascade failures
- Graceful degradation when resources can't be cleaned up

## Usage Examples

### Using Temporary File Manager

```python
def test_with_temp_files(temp_file_manager):
    # Create temporary file
    temp_file = temp_file_manager['create_file'](
        suffix=".json", 
        content='{"test": true}'
    )
    
    # Create temporary directory
    temp_dir = temp_file_manager['create_dir'](prefix="test_data_")
    
    # Files and directories automatically cleaned up
```

### Using Isolated Database Session

```python
async def test_with_database(isolated_database_session):
    session = isolated_database_session
    
    # Use database session for testing
    # Session automatically rolled back and cleaned up
```

### Using Isolated Test Environment

```python
def test_with_isolated_env(isolated_test_environment):
    env = isolated_test_environment
    
    # Access isolated workspace
    workspace = env['workspace']
    data_dir = env['dirs']['data']
    
    # Environment variables automatically restored
```

## Validation and Testing

### Test Teardown Validation Suite

**Location**: `tests/test_teardown_validation.py`

Comprehensive test suite that validates teardown procedures:
- Temporary file cleanup validation
- Temporary directory cleanup validation
- Database session cleanup validation
- HTTP client cleanup validation
- Environment variable isolation validation
- Module import isolation validation
- Error handling validation

### Running Validation Tests

```bash
# Run all teardown validation tests
python -m pytest tests/test_teardown_validation.py -v

# Run specific teardown test
python -m pytest tests/test_teardown_validation.py::TestTeardownValidation::test_temp_file_cleanup -v

# Run teardown procedure validation script
python test_teardown_procedures.py
```

## Integration with ACGS-PGP Services

### Service-Specific Teardown

Each ACGS-PGP service has specific teardown requirements:

- **Auth Service**: JWT tokens, session cleanup
- **AC Service**: Principle data, version cleanup
- **GS Service**: LLM service connections, synthesis cache
- **FV Service**: Z3 solver instances, bias detection data
- **Integrity Service**: Cryptographic keys, signature data
- **PGC Service**: OPA instances, compiled policies

### Integration Test Teardown

**Location**: `tests/integration/conftest.py`

Specialized teardown for integration tests:
- Cross-service communication cleanup
- Test result file cleanup
- Service-specific resource cleanup

## Best Practices

### For Test Authors

1. **Use Provided Fixtures**: Always use `temp_file_manager` for temporary files
2. **Avoid Manual Cleanup**: Let fixtures handle cleanup automatically
3. **Register Resources**: Use fixture registration for custom resources
4. **Test Isolation**: Don't rely on state from other tests

### For Service Developers

1. **Resource Registration**: Register service-specific resources for cleanup
2. **Graceful Shutdown**: Implement proper shutdown procedures
3. **Connection Management**: Properly close connections and sessions
4. **State Reset**: Reset service state between tests

## Monitoring and Metrics

### Cleanup Success Metrics

- **File Cleanup Rate**: Percentage of temporary files successfully cleaned
- **Directory Cleanup Rate**: Percentage of temporary directories successfully cleaned
- **Connection Cleanup Rate**: Percentage of connections properly closed
- **Environment Restoration Rate**: Percentage of environment variables properly restored

### Performance Impact

- **Cleanup Time**: Average time spent on teardown procedures
- **Memory Usage**: Memory freed during cleanup
- **Resource Leaks**: Number of resources not properly cleaned

## Troubleshooting

### Common Issues

1. **Permission Errors**: Files created with restrictive permissions
2. **Resource Locks**: Files or directories locked by other processes
3. **Connection Timeouts**: Database or HTTP connections timing out during cleanup
4. **Module Dependencies**: Modules that can't be safely unloaded

### Debugging Teardown Issues

```bash
# Enable verbose cleanup logging
PYTEST_VERBOSE_CLEANUP=1 python -m pytest tests/ -v

# Check for remaining test artifacts
find . -name "test_*" -type f
find . -name "*_test_results.json"
```

## Future Enhancements

1. **Parallel Test Cleanup**: Cleanup procedures optimized for parallel test execution
2. **Resource Usage Monitoring**: Real-time monitoring of test resource usage
3. **Cleanup Performance Optimization**: Faster cleanup procedures for large test suites
4. **Advanced Error Recovery**: More sophisticated error recovery mechanisms
