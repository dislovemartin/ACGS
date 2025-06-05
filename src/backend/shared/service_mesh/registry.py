"""
Service registry for ACGS-PGP microservices.

Provides centralized service discovery and configuration management
to eliminate hard-coded service URLs and improve maintainability.
"""

import os
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ServiceType(Enum):
    """ACGS service types."""
    AUTH = "auth_service"
    AC = "ac_service"
    FV = "fv_service"
    GS = "gs_service"
    PGC = "pgc_service"
    INTEGRITY = "integrity_service"
    EC = "ec_service"
    FEDERATED = "federated_service"
    RESEARCH = "research_service"
    WORKFLOW = "workflow_service"


class Environment(Enum):
    """Deployment environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


@dataclass
class ServiceConfig:
    """Configuration for a single service."""
    name: str
    base_url: str
    port: int
    health_endpoint: str = "/health"
    api_version: str = "v1"
    timeout: float = 30.0
    retry_attempts: int = 3
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 60.0
    rate_limit: Optional[int] = None
    authentication_required: bool = True
    tags: List[str] = field(default_factory=list)
    
    @property
    def api_base_url(self) -> str:
        """Get the full API base URL."""
        return f"{self.base_url}/api/{self.api_version}"
    
    @property
    def health_url(self) -> str:
        """Get the health check URL."""
        return f"{self.base_url}{self.health_endpoint}"


class ServiceRegistry:
    """
    Centralized service registry for ACGS-PGP microservices.
    
    Manages service configurations, discovery, and environment-specific
    settings to eliminate hard-coded service URLs.
    """
    
    def __init__(self, environment: Environment = Environment.DEVELOPMENT):
        self.environment = environment
        self._services: Dict[ServiceType, ServiceConfig] = {}
        self._load_default_configurations()
        self._load_environment_overrides()
    
    def _load_default_configurations(self):
        """Load default service configurations."""
        default_configs = {
            ServiceType.AUTH: ServiceConfig(
                name="auth_service",
                base_url="http://localhost:8000",
                port=8000,
                tags=["authentication", "authorization"]
            ),
            ServiceType.AC: ServiceConfig(
                name="ac_service", 
                base_url="http://localhost:8001",
                port=8001,
                tags=["audit", "compliance", "principles"]
            ),
            ServiceType.FV: ServiceConfig(
                name="fv_service",
                base_url="http://localhost:8003", 
                port=8003,
                tags=["verification", "formal_methods"]
            ),
            ServiceType.GS: ServiceConfig(
                name="gs_service",
                base_url="http://localhost:8004",
                port=8004,
                tags=["governance", "synthesis", "llm"]
            ),
            ServiceType.PGC: ServiceConfig(
                name="pgc_service",
                base_url="http://localhost:8005",
                port=8005,
                tags=["policy", "governance", "compliance"]
            ),
            ServiceType.INTEGRITY: ServiceConfig(
                name="integrity_service",
                base_url="http://localhost:8006",
                port=8006,
                tags=["cryptography", "integrity", "pgp"]
            ),
            ServiceType.EC: ServiceConfig(
                name="ec_service",
                base_url="http://localhost:8007",
                port=8007,
                tags=["executive", "oversight", "monitoring"]
            ),
            ServiceType.FEDERATED: ServiceConfig(
                name="federated_service",
                base_url="http://localhost:8008",
                port=8008,
                tags=["federated", "evaluation", "privacy"]
            ),
            ServiceType.RESEARCH: ServiceConfig(
                name="research_service",
                base_url="http://localhost:8009",
                port=8009,
                tags=["research", "analytics", "data"]
            ),
            ServiceType.WORKFLOW: ServiceConfig(
                name="workflow_service",
                base_url="http://localhost:8010",
                port=8010,
                tags=["workflow", "orchestration", "langgraph"]
            )
        }
        
        self._services.update(default_configs)
    
    def _load_environment_overrides(self):
        """Load environment-specific configuration overrides."""
        env_prefix = f"ACGS_{self.environment.value.upper()}_"
        
        for service_type in ServiceType:
            service_name = service_type.value.upper()
            
            # Check for environment-specific URL override
            url_key = f"{env_prefix}{service_name}_URL"
            if url_key in os.environ:
                if service_type in self._services:
                    self._services[service_type].base_url = os.environ[url_key]
                    logger.info(f"Override {service_name} URL: {os.environ[url_key]}")
            
            # Check for port override
            port_key = f"{env_prefix}{service_name}_PORT"
            if port_key in os.environ:
                try:
                    port = int(os.environ[port_key])
                    if service_type in self._services:
                        self._services[service_type].port = port
                        # Update base_url if using localhost
                        if "localhost" in self._services[service_type].base_url:
                            self._services[service_type].base_url = f"http://localhost:{port}"
                except ValueError:
                    logger.warning(f"Invalid port value for {port_key}: {os.environ[port_key]}")
    
    def register_service(self, service_type: ServiceType, config: ServiceConfig):
        """
        Register a service configuration.
        
        Args:
            service_type: Type of service to register
            config: Service configuration
        """
        self._services[service_type] = config
        logger.info(f"Registered service {service_type.value}: {config.base_url}")
    
    def get_service_config(self, service_type: ServiceType) -> Optional[ServiceConfig]:
        """
        Get configuration for a specific service.
        
        Args:
            service_type: Type of service to get config for
            
        Returns:
            Service configuration or None if not found
        """
        return self._services.get(service_type)
    
    def get_service_url(self, service_type: ServiceType) -> Optional[str]:
        """
        Get base URL for a specific service.
        
        Args:
            service_type: Type of service to get URL for
            
        Returns:
            Service base URL or None if not found
        """
        config = self.get_service_config(service_type)
        return config.base_url if config else None
    
    def get_api_url(self, service_type: ServiceType) -> Optional[str]:
        """
        Get API base URL for a specific service.
        
        Args:
            service_type: Type of service to get API URL for
            
        Returns:
            Service API base URL or None if not found
        """
        config = self.get_service_config(service_type)
        return config.api_base_url if config else None
    
    def list_services(self, tags: Optional[List[str]] = None) -> List[ServiceConfig]:
        """
        List all registered services, optionally filtered by tags.
        
        Args:
            tags: Optional list of tags to filter by
            
        Returns:
            List of service configurations
        """
        services = list(self._services.values())
        
        if tags:
            filtered_services = []
            for service in services:
                if any(tag in service.tags for tag in tags):
                    filtered_services.append(service)
            return filtered_services
        
        return services
    
    def get_services_by_tag(self, tag: str) -> List[ServiceConfig]:
        """
        Get all services with a specific tag.
        
        Args:
            tag: Tag to filter by
            
        Returns:
            List of service configurations with the specified tag
        """
        return [
            service for service in self._services.values()
            if tag in service.tags
        ]
    
    def is_service_registered(self, service_type: ServiceType) -> bool:
        """
        Check if a service is registered.
        
        Args:
            service_type: Type of service to check
            
        Returns:
            True if service is registered, False otherwise
        """
        return service_type in self._services
    
    def update_service_config(
        self,
        service_type: ServiceType,
        **updates
    ) -> bool:
        """
        Update configuration for an existing service.
        
        Args:
            service_type: Type of service to update
            **updates: Configuration updates
            
        Returns:
            True if service was updated, False if not found
        """
        if service_type not in self._services:
            return False
        
        config = self._services[service_type]
        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)
                logger.info(f"Updated {service_type.value}.{key} = {value}")
        
        return True
    
    def get_environment_info(self) -> Dict[str, any]:
        """
        Get information about the current environment configuration.
        
        Returns:
            Environment information dictionary
        """
        return {
            "environment": self.environment.value,
            "total_services": len(self._services),
            "services": {
                service_type.value: {
                    "url": config.base_url,
                    "port": config.port,
                    "tags": config.tags
                }
                for service_type, config in self._services.items()
            }
        }


# Global service registry instance
_registry: Optional[ServiceRegistry] = None


def get_service_registry(environment: Optional[Environment] = None) -> ServiceRegistry:
    """
    Get the global service registry instance.
    
    Args:
        environment: Environment to use (creates new registry if different)
        
    Returns:
        Service registry instance
    """
    global _registry
    
    if _registry is None or (environment and _registry.environment != environment):
        env = environment or Environment.DEVELOPMENT
        _registry = ServiceRegistry(env)
    
    return _registry


def register_service(service_type: ServiceType, config: ServiceConfig):
    """
    Register a service in the global registry.
    
    Args:
        service_type: Type of service to register
        config: Service configuration
    """
    registry = get_service_registry()
    registry.register_service(service_type, config)
