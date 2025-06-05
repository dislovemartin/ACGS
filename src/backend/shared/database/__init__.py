"""
Database Optimization Components for ACGS-PGP Services

This module provides optimized database connection pooling, query performance
enhancements, and unified database access patterns across all services.
"""

from .pool_manager import DatabasePoolManager, ConnectionPool, PoolConfig, get_pool_manager

# Import only implemented components to avoid import errors
__all__ = [
    "DatabasePoolManager",
    "ConnectionPool",
    "PoolConfig",
    "get_pool_manager"
]

# Optional imports for components that may not be implemented yet
try:
    from .query_optimizer import QueryOptimizer, QueryCache, QueryMetrics
    __all__.extend(["QueryOptimizer", "QueryCache", "QueryMetrics"])
except ImportError:
    pass

try:
    from .connection import DatabaseConnection, AsyncDatabaseConnection
    __all__.extend(["DatabaseConnection", "AsyncDatabaseConnection"])
except ImportError:
    pass

try:
    from .migrations import MigrationManager, Migration
    __all__.extend(["MigrationManager", "Migration"])
except ImportError:
    pass

try:
    from .monitoring import DatabaseMonitor, PerformanceMetrics
    __all__.extend(["DatabaseMonitor", "PerformanceMetrics"])
except ImportError:
    pass
