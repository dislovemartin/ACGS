"""
Consolidated HTTP client patterns for ACGS-PGP services.

This module eliminates duplicate HTTP client implementations across services
and provides a unified interface for inter-service communication.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from .error_handling import ACGSException, ServiceUnavailableError
from .validation import validate_response

logger = logging.getLogger(__name__)


class ServiceType(Enum):
    """ACGS service types for client configuration."""
    AUTH = "auth_service"
    AC = "ac_service"
    FV = "fv_service"
    GS = "gs_service"
    PGC = "pgc_service"
    INTEGRITY = "integrity_service"
    EC = "ec_service"


@dataclass
class ServiceConfig:
    """Configuration for service HTTP clients."""
    base_url: str
    timeout: float = 30.0
    retry_attempts: int = 3
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 60.0


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker implementation for service resilience."""
    
    def __init__(self, threshold: int = 5, timeout: float = 60.0):
        self.threshold = threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = CircuitBreakerState.CLOSED
    
    def can_execute(self) -> bool:
        """Check if request can be executed based on circuit breaker state."""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            if time.time() - self.last_failure_time > self.timeout:
                self.state = CircuitBreakerState.HALF_OPEN
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def record_success(self):
        """Record successful request."""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED
    
    def record_failure(self):
        """Record failed request."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.threshold:
            self.state = CircuitBreakerState.OPEN


class ACGSHttpClient:
    """
    Unified HTTP client for ACGS services with circuit breaker,
    retry logic, and standardized error handling.
    """
    
    def __init__(self, service_config: ServiceConfig):
        self.config = service_config
        self.circuit_breaker = CircuitBreaker(
            threshold=service_config.circuit_breaker_threshold,
            timeout=service_config.circuit_breaker_timeout
        )
        self.client = httpx.AsyncClient(
            base_url=service_config.base_url,
            timeout=service_config.timeout,
            headers={"User-Agent": "ACGS-PGP-Client/1.0"}
        )
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request with circuit breaker and retry logic.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters
            headers: Additional headers
            auth_token: Authentication token
            
        Returns:
            Response data as dictionary
            
        Raises:
            ServiceUnavailableError: When service is unavailable
            ACGSException: For other service errors
        """
        if not self.circuit_breaker.can_execute():
            raise ServiceUnavailableError(
                f"Circuit breaker open for {self.config.base_url}",
                "CIRCUIT_BREAKER_OPEN"
            )
        
        # Prepare headers
        request_headers = headers or {}
        if auth_token:
            request_headers["Authorization"] = f"Bearer {auth_token}"
        
        try:
            start_time = time.time()
            
            response = await self.client.request(
                method=method,
                url=endpoint,
                json=data,
                params=params,
                headers=request_headers
            )
            
            duration = time.time() - start_time
            
            # Log request metrics
            logger.info(
                f"HTTP {method} {endpoint} - {response.status_code} - {duration:.3f}s"
            )
            
            if response.status_code >= 400:
                self.circuit_breaker.record_failure()
                error_data = response.json() if response.content else {}
                raise ACGSException(
                    f"HTTP {response.status_code}: {error_data.get('detail', 'Unknown error')}",
                    f"HTTP_{response.status_code}",
                    error_data
                )
            
            self.circuit_breaker.record_success()
            
            # Validate and return response
            response_data = response.json() if response.content else {}
            return validate_response(response_data)
            
        except httpx.RequestError as e:
            self.circuit_breaker.record_failure()
            logger.error(f"Request error for {endpoint}: {e}")
            raise ServiceUnavailableError(
                f"Service unavailable: {str(e)}",
                "SERVICE_UNAVAILABLE"
            )
        except Exception as e:
            self.circuit_breaker.record_failure()
            logger.error(f"Unexpected error for {endpoint}: {e}")
            raise


class ServiceClient:
    """
    High-level service client that manages multiple HTTP clients
    for different ACGS services.
    """
    
    def __init__(self):
        self.clients: Dict[ServiceType, ACGSHttpClient] = {}
        self._setup_default_configs()
    
    def _setup_default_configs(self):
        """Setup default service configurations."""
        default_configs = {
            ServiceType.AUTH: ServiceConfig("http://localhost:8000"),
            ServiceType.AC: ServiceConfig("http://localhost:8001"),
            ServiceType.FV: ServiceConfig("http://localhost:8003"),
            ServiceType.GS: ServiceConfig("http://localhost:8004"),
            ServiceType.PGC: ServiceConfig("http://localhost:8005"),
            ServiceType.INTEGRITY: ServiceConfig("http://localhost:8006"),
            ServiceType.EC: ServiceConfig("http://localhost:8007"),
        }
        
        for service_type, config in default_configs.items():
            self.clients[service_type] = ACGSHttpClient(config)
    
    async def call_service(
        self,
        service: ServiceType,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call a specific ACGS service.
        
        Args:
            service: Target service type
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request parameters
            
        Returns:
            Service response data
        """
        if service not in self.clients:
            raise ACGSException(
                f"Unknown service: {service}",
                "UNKNOWN_SERVICE"
            )
        
        client = self.clients[service]
        return await client.request(method, endpoint, **kwargs)
    
    async def close_all(self):
        """Close all HTTP clients."""
        for client in self.clients.values():
            await client.close()


# Global service client instance
service_client = ServiceClient()


async def get_service_client() -> ServiceClient:
    """Get the global service client instance."""
    return service_client
