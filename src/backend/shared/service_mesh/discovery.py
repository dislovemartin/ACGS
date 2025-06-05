"""
Service discovery for ACGS-PGP microservices.

Provides dynamic service discovery capabilities to eliminate hard-coded
service URLs and enable flexible deployment configurations.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
import httpx

from .registry import ServiceType, ServiceConfig, get_service_registry
from ..common.error_handling import ServiceUnavailableError, log_error

logger = logging.getLogger(__name__)


@dataclass
class ServiceInstance:
    """Represents a discovered service instance."""
    service_type: ServiceType
    instance_id: str
    base_url: str
    port: int
    health_url: str
    status: str = "unknown"  # healthy, unhealthy, unknown
    last_check: Optional[float] = None
    response_time: Optional[float] = None
    metadata: Dict[str, str] = field(default_factory=dict)
    
    @property
    def is_healthy(self) -> bool:
        """Check if service instance is healthy."""
        return self.status == "healthy"
    
    @property
    def age_seconds(self) -> float:
        """Get age of last health check in seconds."""
        if self.last_check is None:
            return float('inf')
        return time.time() - self.last_check


class ServiceDiscovery:
    """
    Service discovery implementation for ACGS-PGP microservices.
    
    Provides dynamic service discovery, health monitoring, and
    load balancing capabilities.
    """
    
    def __init__(self, health_check_interval: float = 30.0):
        """
        Initialize service discovery.
        
        Args:
            health_check_interval: Interval between health checks (seconds)
        """
        self.health_check_interval = health_check_interval
        self.registry = get_service_registry()
        
        # Service instances by type
        self.instances: Dict[ServiceType, List[ServiceInstance]] = {}
        
        # Health check state
        self._health_check_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Callbacks for service events
        self._service_up_callbacks: List[Callable[[ServiceInstance], None]] = []
        self._service_down_callbacks: List[Callable[[ServiceInstance], None]] = []
        
        # HTTP client for health checks
        self._http_client: Optional[httpx.AsyncClient] = None
    
    async def start(self):
        """Start service discovery and health monitoring."""
        if self._running:
            return
        
        self._running = True
        self._http_client = httpx.AsyncClient(timeout=10.0)
        
        # Initialize service instances from registry
        await self._initialize_services()
        
        # Start health check task
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        
        logger.info("Service discovery started")
    
    async def stop(self):
        """Stop service discovery and health monitoring."""
        if not self._running:
            return
        
        self._running = False
        
        # Cancel health check task
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        # Close HTTP client
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
        
        logger.info("Service discovery stopped")
    
    async def _initialize_services(self):
        """Initialize service instances from registry."""
        for service_type in ServiceType:
            config = self.registry.get_service_config(service_type)
            if config:
                instance = ServiceInstance(
                    service_type=service_type,
                    instance_id=f"{service_type.value}-default",
                    base_url=config.base_url,
                    port=config.port,
                    health_url=config.health_url,
                    metadata={"source": "registry"}
                )
                
                if service_type not in self.instances:
                    self.instances[service_type] = []
                
                self.instances[service_type].append(instance)
        
        logger.info(f"Initialized {sum(len(instances) for instances in self.instances.values())} service instances")
    
    async def _health_check_loop(self):
        """Main health check loop."""
        while self._running:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(5.0)  # Short delay before retrying
    
    async def _perform_health_checks(self):
        """Perform health checks on all service instances."""
        tasks = []
        
        for service_type, instances in self.instances.items():
            for instance in instances:
                task = asyncio.create_task(
                    self._check_instance_health(instance)
                )
                tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _check_instance_health(self, instance: ServiceInstance):
        """
        Check health of a single service instance.
        
        Args:
            instance: Service instance to check
        """
        if not self._http_client:
            return
        
        start_time = time.time()
        old_status = instance.status
        
        try:
            response = await self._http_client.get(instance.health_url)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                instance.status = "healthy"
                instance.response_time = response_time
                
                # Notify if service came back up
                if old_status != "healthy":
                    self._notify_service_up(instance)
            else:
                instance.status = "unhealthy"
                
                # Notify if service went down
                if old_status == "healthy":
                    self._notify_service_down(instance)
        
        except Exception as e:
            instance.status = "unhealthy"
            instance.response_time = None
            
            # Notify if service went down
            if old_status == "healthy":
                self._notify_service_down(instance)
            
            logger.debug(f"Health check failed for {instance.instance_id}: {e}")
        
        finally:
            instance.last_check = time.time()
    
    def _notify_service_up(self, instance: ServiceInstance):
        """Notify callbacks that a service came up."""
        logger.info(f"Service {instance.instance_id} is now healthy")
        
        for callback in self._service_up_callbacks:
            try:
                callback(instance)
            except Exception as e:
                logger.error(f"Error in service up callback: {e}")
    
    def _notify_service_down(self, instance: ServiceInstance):
        """Notify callbacks that a service went down."""
        logger.warning(f"Service {instance.instance_id} is now unhealthy")
        
        for callback in self._service_down_callbacks:
            try:
                callback(instance)
            except Exception as e:
                logger.error(f"Error in service down callback: {e}")
    
    def register_service_up_callback(self, callback: Callable[[ServiceInstance], None]):
        """Register callback for service up events."""
        self._service_up_callbacks.append(callback)
    
    def register_service_down_callback(self, callback: Callable[[ServiceInstance], None]):
        """Register callback for service down events."""
        self._service_down_callbacks.append(callback)
    
    def get_healthy_instances(self, service_type: ServiceType) -> List[ServiceInstance]:
        """
        Get all healthy instances of a service type.
        
        Args:
            service_type: Type of service to get instances for
            
        Returns:
            List of healthy service instances
        """
        instances = self.instances.get(service_type, [])
        return [instance for instance in instances if instance.is_healthy]
    
    def get_best_instance(self, service_type: ServiceType) -> Optional[ServiceInstance]:
        """
        Get the best available instance of a service type.
        
        Uses response time as the primary metric for selection.
        
        Args:
            service_type: Type of service to get instance for
            
        Returns:
            Best available service instance or None
        """
        healthy_instances = self.get_healthy_instances(service_type)
        
        if not healthy_instances:
            return None
        
        # Sort by response time (fastest first)
        healthy_instances.sort(key=lambda x: x.response_time or float('inf'))
        
        return healthy_instances[0]
    
    def get_service_url(self, service_type: ServiceType) -> Optional[str]:
        """
        Get URL for the best available instance of a service.
        
        Args:
            service_type: Type of service to get URL for
            
        Returns:
            Service URL or None if no healthy instances
        """
        instance = self.get_best_instance(service_type)
        return instance.base_url if instance else None
    
    def is_service_available(self, service_type: ServiceType) -> bool:
        """
        Check if a service type has any healthy instances.
        
        Args:
            service_type: Type of service to check
            
        Returns:
            True if service has healthy instances
        """
        return len(self.get_healthy_instances(service_type)) > 0
    
    def get_service_status(self, service_type: ServiceType) -> Dict[str, any]:
        """
        Get status information for a service type.
        
        Args:
            service_type: Type of service to get status for
            
        Returns:
            Service status information
        """
        instances = self.instances.get(service_type, [])
        healthy_instances = self.get_healthy_instances(service_type)
        
        if not instances:
            return {
                "service": service_type.value,
                "status": "not_found",
                "instances": 0,
                "healthy_instances": 0
            }
        
        # Calculate average response time for healthy instances
        response_times = [
            instance.response_time for instance in healthy_instances
            if instance.response_time is not None
        ]
        avg_response_time = sum(response_times) / len(response_times) if response_times else None
        
        return {
            "service": service_type.value,
            "status": "available" if healthy_instances else "unavailable",
            "instances": len(instances),
            "healthy_instances": len(healthy_instances),
            "average_response_time": avg_response_time,
            "last_check": max(
                (instance.last_check for instance in instances if instance.last_check),
                default=None
            )
        }
    
    def get_all_services_status(self) -> Dict[str, Dict[str, any]]:
        """
        Get status information for all services.
        
        Returns:
            Status information for all service types
        """
        return {
            service_type.value: self.get_service_status(service_type)
            for service_type in ServiceType
        }
    
    def add_service_instance(self, instance: ServiceInstance):
        """
        Manually add a service instance.
        
        Args:
            instance: Service instance to add
        """
        if instance.service_type not in self.instances:
            self.instances[instance.service_type] = []
        
        # Check if instance already exists
        existing = next(
            (inst for inst in self.instances[instance.service_type]
             if inst.instance_id == instance.instance_id),
            None
        )
        
        if existing:
            # Update existing instance
            existing.base_url = instance.base_url
            existing.port = instance.port
            existing.health_url = instance.health_url
            existing.metadata.update(instance.metadata)
        else:
            # Add new instance
            self.instances[instance.service_type].append(instance)
        
        logger.info(f"Added service instance: {instance.instance_id}")
    
    def remove_service_instance(self, service_type: ServiceType, instance_id: str):
        """
        Remove a service instance.
        
        Args:
            service_type: Type of service
            instance_id: ID of instance to remove
        """
        if service_type in self.instances:
            self.instances[service_type] = [
                instance for instance in self.instances[service_type]
                if instance.instance_id != instance_id
            ]
            logger.info(f"Removed service instance: {instance_id}")


# Global service discovery instance
_service_discovery: Optional[ServiceDiscovery] = None


async def get_service_discovery() -> ServiceDiscovery:
    """
    Get the global service discovery instance.
    
    Returns:
        Service discovery instance
    """
    global _service_discovery
    
    if _service_discovery is None:
        _service_discovery = ServiceDiscovery()
        await _service_discovery.start()
    
    return _service_discovery
