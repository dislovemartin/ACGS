"""
Service Providers for ACGS-PGP Dependency Injection

Provides factory classes and providers for creating service instances
with proper configuration and lifecycle management.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Type, TypeVar, Callable
from abc import ABC, abstractmethod

from .interfaces import ServiceInterface, DatabaseInterface, CacheInterface
from ..common.error_handling import ACGSException

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceProvider(ABC):
    """Base class for service providers."""
    
    @abstractmethod
    async def create_instance(self, *args, **kwargs) -> Any:
        """Create a service instance."""
        pass
    
    @abstractmethod
    async def configure_instance(self, instance: Any, config: Dict[str, Any]) -> Any:
        """Configure a service instance."""
        pass
    
    @abstractmethod
    async def dispose_instance(self, instance: Any) -> None:
        """Dispose of a service instance."""
        pass


class DatabaseProvider(ServiceProvider):
    """Provider for database service instances."""
    
    def __init__(self, connection_string: str, config: Dict[str, Any] = None):
        """
        Initialize database provider.
        
        Args:
            connection_string: Database connection string
            config: Database configuration
        """
        self.connection_string = connection_string
        self.config = config or {}
    
    async def create_instance(self, *args, **kwargs) -> DatabaseInterface:
        """Create a database service instance."""
        # This would create actual database connection in production
        from ..database.pool_manager import ConnectionPool, PoolConfig
        
        pool_config = PoolConfig(
            min_connections=self.config.get('min_connections', 5),
            max_connections=self.config.get('max_connections', 20),
            pool_timeout=self.config.get('pool_timeout', 30.0)
        )
        
        # Create mock database instance for testing
        class MockDatabaseService(DatabaseInterface):
            async def connect(self):
                pass
            
            async def disconnect(self):
                pass
            
            async def execute_query(self, query: str, params: Dict[str, Any] = None):
                return []
            
            async def execute_command(self, command: str, params: Dict[str, Any] = None):
                return 0
            
            async def begin_transaction(self):
                return None
            
            async def health_check(self):
                return {"status": "healthy"}
        
        return MockDatabaseService()
    
    async def configure_instance(self, instance: DatabaseInterface, config: Dict[str, Any]) -> DatabaseInterface:
        """Configure database instance."""
        await instance.connect()
        return instance
    
    async def dispose_instance(self, instance: DatabaseInterface) -> None:
        """Dispose of database instance."""
        await instance.disconnect()


class CacheProvider(ServiceProvider):
    """Provider for cache service instances."""
    
    def __init__(self, cache_url: str, config: Dict[str, Any] = None):
        """
        Initialize cache provider.
        
        Args:
            cache_url: Cache connection URL
            config: Cache configuration
        """
        self.cache_url = cache_url
        self.config = config or {}
    
    async def create_instance(self, *args, **kwargs) -> CacheInterface:
        """Create a cache service instance."""
        # Create mock cache instance for testing
        class MockCacheService(CacheInterface):
            def __init__(self):
                self._cache = {}
            
            async def get(self, key: str) -> Optional[Any]:
                return self._cache.get(key)
            
            async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
                self._cache[key] = value
                return True
            
            async def delete(self, key: str) -> bool:
                return self._cache.pop(key, None) is not None
            
            async def exists(self, key: str) -> bool:
                return key in self._cache
            
            async def clear(self) -> bool:
                self._cache.clear()
                return True
            
            async def health_check(self) -> Dict[str, Any]:
                return {"status": "healthy", "keys": len(self._cache)}
        
        return MockCacheService()
    
    async def configure_instance(self, instance: CacheInterface, config: Dict[str, Any]) -> CacheInterface:
        """Configure cache instance."""
        # Configuration would be applied here
        return instance
    
    async def dispose_instance(self, instance: CacheInterface) -> None:
        """Dispose of cache instance."""
        await instance.clear()


class ServiceFactory:
    """Factory for creating service instances with providers."""
    
    def __init__(self):
        """Initialize service factory."""
        self.providers: Dict[Type, ServiceProvider] = {}
        self.configurations: Dict[Type, Dict[str, Any]] = {}
    
    def register_provider(self, service_type: Type[T], provider: ServiceProvider, config: Dict[str, Any] = None):
        """
        Register a service provider.
        
        Args:
            service_type: Service type to register provider for
            provider: Service provider instance
            config: Service configuration
        """
        self.providers[service_type] = provider
        self.configurations[service_type] = config or {}
        logger.debug(f"Registered provider for {service_type}")
    
    async def create_service(self, service_type: Type[T]) -> T:
        """
        Create a service instance using registered provider.
        
        Args:
            service_type: Type of service to create
            
        Returns:
            Service instance
            
        Raises:
            ACGSException: If no provider is registered
        """
        if service_type not in self.providers:
            raise ACGSException(
                f"No provider registered for {service_type}",
                "PROVIDER_NOT_FOUND"
            )
        
        provider = self.providers[service_type]
        config = self.configurations[service_type]
        
        try:
            # Create instance
            instance = await provider.create_instance()
            
            # Configure instance
            configured_instance = await provider.configure_instance(instance, config)
            
            logger.debug(f"Created service instance for {service_type}")
            return configured_instance
        
        except Exception as e:
            raise ACGSException(
                f"Failed to create service {service_type}: {str(e)}",
                "SERVICE_CREATION_FAILED"
            )
    
    async def dispose_service(self, service_type: Type[T], instance: T):
        """
        Dispose of a service instance.
        
        Args:
            service_type: Type of service
            instance: Service instance to dispose
        """
        if service_type in self.providers:
            provider = self.providers[service_type]
            try:
                await provider.dispose_instance(instance)
                logger.debug(f"Disposed service instance for {service_type}")
            except Exception as e:
                logger.error(f"Error disposing service {service_type}: {e}")


class ConfigurationProvider:
    """Provider for service configuration management."""
    
    def __init__(self, config_source: str = "environment"):
        """
        Initialize configuration provider.
        
        Args:
            config_source: Source of configuration (environment, file, etc.)
        """
        self.config_source = config_source
        self._config_cache: Dict[str, Any] = {}
    
    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """
        Get configuration for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Service configuration dictionary
        """
        if service_name in self._config_cache:
            return self._config_cache[service_name]
        
        # Load configuration based on source
        config = self._load_config(service_name)
        self._config_cache[service_name] = config
        
        return config
    
    def _load_config(self, service_name: str) -> Dict[str, Any]:
        """Load configuration from source."""
        # Default configuration
        default_config = {
            "timeout": 30.0,
            "retry_attempts": 3,
            "health_check_interval": 60.0
        }
        
        # Service-specific configurations
        service_configs = {
            "database": {
                "min_connections": 5,
                "max_connections": 20,
                "pool_timeout": 30.0,
                "pool_recycle": 3600
            },
            "cache": {
                "ttl": 3600,
                "max_memory": "100MB",
                "eviction_policy": "lru"
            },
            "auth": {
                "token_expiry": 3600,
                "refresh_token_expiry": 86400,
                "password_hash_rounds": 12
            }
        }
        
        config = default_config.copy()
        config.update(service_configs.get(service_name, {}))
        
        return config
    
    def set_config(self, service_name: str, key: str, value: Any):
        """
        Set configuration value for a service.
        
        Args:
            service_name: Name of the service
            key: Configuration key
            value: Configuration value
        """
        if service_name not in self._config_cache:
            self._config_cache[service_name] = {}
        
        self._config_cache[service_name][key] = value
        logger.debug(f"Set config {service_name}.{key} = {value}")
    
    def reload_config(self, service_name: str = None):
        """
        Reload configuration from source.
        
        Args:
            service_name: Specific service to reload, or None for all
        """
        if service_name:
            self._config_cache.pop(service_name, None)
        else:
            self._config_cache.clear()
        
        logger.info(f"Reloaded configuration for {service_name or 'all services'}")


# Global instances
_service_factory: Optional[ServiceFactory] = None
_config_provider: Optional[ConfigurationProvider] = None


def get_service_factory() -> ServiceFactory:
    """
    Get the global service factory instance.
    
    Returns:
        Service factory instance
    """
    global _service_factory
    
    if _service_factory is None:
        _service_factory = ServiceFactory()
    
    return _service_factory


def get_config_provider() -> ConfigurationProvider:
    """
    Get the global configuration provider instance.
    
    Returns:
        Configuration provider instance
    """
    global _config_provider
    
    if _config_provider is None:
        _config_provider = ConfigurationProvider()
    
    return _config_provider
