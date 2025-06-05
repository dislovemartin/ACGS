"""
Unified service client for ACGS-PGP microservices.

This module provides a consolidated HTTP client that eliminates duplicate
client implementations across services and provides consistent patterns
for inter-service communication.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Union
from contextlib import asynccontextmanager
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from .registry import ServiceRegistry, ServiceType, ServiceConfig, get_service_registry
from .circuit_breaker import CircuitBreaker
from ..common.error_handling import (
    ACGSException, ServiceUnavailableError, AuthenticationError,
    handle_service_error, log_error
)
from ..common.validation import validate_response
from ..common.formatting import format_response, standardize_timestamps

logger = logging.getLogger(__name__)


class ACGSServiceClient:
    """
    Unified HTTP client for ACGS services with circuit breaker,
    retry logic, authentication, and standardized error handling.
    """
    
    def __init__(self, service_type: ServiceType, registry: Optional[ServiceRegistry] = None):
        self.service_type = service_type
        self.registry = registry or get_service_registry()
        self.config = self.registry.get_service_config(service_type)
        
        if not self.config:
            raise ACGSException(
                f"Service {service_type.value} not found in registry",
                "SERVICE_NOT_FOUND"
            )
        
        self.circuit_breaker = CircuitBreaker(
            threshold=self.config.circuit_breaker_threshold,
            timeout=self.config.circuit_breaker_timeout
        )
        
        self.client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            headers={
                "User-Agent": "ACGS-ServiceMesh/1.0",
                "Content-Type": "application/json"
            }
        )
        
        self._auth_token: Optional[str] = None
        self._request_count = 0
        self._error_count = 0
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    def set_auth_token(self, token: str):
        """
        Set authentication token for requests.
        
        Args:
            token: JWT or other authentication token
        """
        self._auth_token = token
    
    def clear_auth_token(self):
        """Clear authentication token."""
        self._auth_token = None
    
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
        auth_token: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request with circuit breaker and retry logic.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            endpoint: API endpoint path (without base URL)
            data: Request body data
            params: Query parameters
            headers: Additional headers
            auth_token: Override authentication token
            timeout: Override request timeout
            
        Returns:
            Response data as dictionary
            
        Raises:
            ServiceUnavailableError: When service is unavailable
            AuthenticationError: When authentication fails
            ACGSException: For other service errors
        """
        if not self.circuit_breaker.can_execute():
            raise ServiceUnavailableError(
                f"Circuit breaker open for {self.service_type.value}",
                service_name=self.service_type.value
            )
        
        # Prepare headers
        request_headers = headers or {}
        
        # Add authentication if required and available
        if self.config.authentication_required:
            token = auth_token or self._auth_token
            if token:
                request_headers["Authorization"] = f"Bearer {token}"
            else:
                logger.warning(f"No auth token provided for {self.service_type.value}")
        
        # Prepare endpoint URL
        if not endpoint.startswith('/'):
            endpoint = f"/{endpoint}"
        
        try:
            start_time = time.time()
            self._request_count += 1
            
            response = await self.client.request(
                method=method,
                url=endpoint,
                json=data,
                params=params,
                headers=request_headers,
                timeout=timeout or self.config.timeout
            )
            
            duration = time.time() - start_time
            
            # Log request metrics
            logger.debug(
                f"HTTP {method} {self.service_type.value}{endpoint} - "
                f"{response.status_code} - {duration:.3f}s"
            )
            
            # Handle response based on status code
            if response.status_code == 401:
                self.circuit_breaker.record_failure()
                raise AuthenticationError(
                    f"Authentication failed for {self.service_type.value}",
                    details={"endpoint": endpoint, "status_code": 401}
                )
            
            if response.status_code >= 400:
                self.circuit_breaker.record_failure()
                self._error_count += 1
                
                try:
                    error_data = response.json() if response.content else {}
                except:
                    error_data = {"detail": response.text}
                
                raise ACGSException(
                    f"HTTP {response.status_code} from {self.service_type.value}: "
                    f"{error_data.get('detail', 'Unknown error')}",
                    f"HTTP_{response.status_code}",
                    details={
                        "service": self.service_type.value,
                        "endpoint": endpoint,
                        "status_code": response.status_code,
                        **error_data
                    }
                )
            
            self.circuit_breaker.record_success()
            
            # Parse and validate response
            try:
                response_data = response.json() if response.content else {}
            except:
                response_data = {"message": "Success", "data": response.text}
            
            return validate_response(response_data)
            
        except httpx.RequestError as e:
            self.circuit_breaker.record_failure()
            self._error_count += 1
            
            error = ServiceUnavailableError(
                f"Network error connecting to {self.service_type.value}: {str(e)}",
                service_name=self.service_type.value
            )
            
            log_error(
                error,
                service_name=self.service_type.value,
                operation=f"{method} {endpoint}"
            )
            
            raise error
        
        except Exception as e:
            self.circuit_breaker.record_failure()
            self._error_count += 1
            
            error = handle_service_error(
                e,
                service_name=self.service_type.value,
                operation=f"{method} {endpoint}",
                context={"data": data, "params": params}
            )
            
            log_error(
                error,
                service_name=self.service_type.value,
                operation=f"{method} {endpoint}"
            )
            
            raise error
    
    async def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make GET request."""
        return await self.request("GET", endpoint, **kwargs)
    
    async def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Make POST request."""
        return await self.request("POST", endpoint, data=data, **kwargs)
    
    async def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Make PUT request."""
        return await self.request("PUT", endpoint, data=data, **kwargs)
    
    async def patch(self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Make PATCH request."""
        return await self.request("PATCH", endpoint, data=data, **kwargs)
    
    async def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make DELETE request."""
        return await self.request("DELETE", endpoint, **kwargs)
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the service.
        
        Returns:
            Health check response
        """
        try:
            return await self.get(self.config.health_endpoint)
        except Exception as e:
            return {
                "status": "unhealthy",
                "service": self.service_type.value,
                "error": str(e),
                "timestamp": time.time()
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get client metrics.
        
        Returns:
            Client metrics dictionary
        """
        return {
            "service": self.service_type.value,
            "request_count": self._request_count,
            "error_count": self._error_count,
            "error_rate": self._error_count / max(self._request_count, 1),
            "circuit_breaker_state": self.circuit_breaker.state.value,
            "circuit_breaker_failure_count": self.circuit_breaker.failure_count
        }


class ServiceMesh:
    """
    Service mesh manager that provides unified access to all ACGS services.
    
    Manages multiple service clients and provides high-level operations
    for inter-service communication.
    """
    
    def __init__(self, registry: Optional[ServiceRegistry] = None):
        self.registry = registry or get_service_registry()
        self.clients: Dict[ServiceType, ACGSServiceClient] = {}
        self._auth_token: Optional[str] = None
    
    def get_client(self, service_type: ServiceType) -> ACGSServiceClient:
        """
        Get or create client for a specific service.
        
        Args:
            service_type: Type of service to get client for
            
        Returns:
            Service client instance
        """
        if service_type not in self.clients:
            self.clients[service_type] = ACGSServiceClient(service_type, self.registry)
            
            # Set auth token if available
            if self._auth_token:
                self.clients[service_type].set_auth_token(self._auth_token)
        
        return self.clients[service_type]
    
    def set_auth_token(self, token: str):
        """
        Set authentication token for all clients.
        
        Args:
            token: JWT or other authentication token
        """
        self._auth_token = token
        for client in self.clients.values():
            client.set_auth_token(token)
    
    def clear_auth_token(self):
        """Clear authentication token from all clients."""
        self._auth_token = None
        for client in self.clients.values():
            client.clear_auth_token()
    
    async def call_service(
        self,
        service_type: ServiceType,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call a specific service.
        
        Args:
            service_type: Target service type
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request parameters
            
        Returns:
            Service response data
        """
        client = self.get_client(service_type)
        return await client.request(method, endpoint, **kwargs)
    
    async def health_check_all(self) -> Dict[str, Any]:
        """
        Perform health check on all registered services.
        
        Returns:
            Health check results for all services
        """
        results = {}
        
        for service_type in ServiceType:
            if self.registry.is_service_registered(service_type):
                try:
                    client = self.get_client(service_type)
                    health = await client.health_check()
                    results[service_type.value] = health
                except Exception as e:
                    results[service_type.value] = {
                        "status": "error",
                        "error": str(e),
                        "timestamp": time.time()
                    }
        
        return format_response(
            data=results,
            metadata={"total_services": len(results)}
        )
    
    async def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get metrics from all active clients.
        
        Returns:
            Metrics from all service clients
        """
        metrics = {}
        
        for service_type, client in self.clients.items():
            metrics[service_type.value] = client.get_metrics()
        
        return format_response(
            data=metrics,
            metadata={"active_clients": len(self.clients)}
        )
    
    async def close_all(self):
        """Close all service clients."""
        for client in self.clients.values():
            await client.close()
        self.clients.clear()
    
    @asynccontextmanager
    async def managed_clients(self):
        """
        Context manager for automatic client cleanup.
        
        Usage:
            async with service_mesh.managed_clients():
                # Use service mesh
                pass
        """
        try:
            yield self
        finally:
            await self.close_all()


# Global service mesh instance
_service_mesh: Optional[ServiceMesh] = None


def get_service_mesh() -> ServiceMesh:
    """
    Get the global service mesh instance.
    
    Returns:
        Service mesh instance
    """
    global _service_mesh
    
    if _service_mesh is None:
        _service_mesh = ServiceMesh()
    
    return _service_mesh
