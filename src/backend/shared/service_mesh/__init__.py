"""
Service mesh implementation for ACGS-PGP microservices.

This module provides a unified service communication layer that eliminates
duplicate HTTP client implementations and provides consistent inter-service
communication patterns.
"""

from .client import ACGSServiceClient, ServiceMesh
from .registry import ServiceRegistry, ServiceConfig
from .discovery import ServiceDiscovery
from .circuit_breaker import CircuitBreaker, CircuitBreakerState

__all__ = [
    "ACGSServiceClient",
    "ServiceMesh", 
    "ServiceRegistry",
    "ServiceConfig",
    "ServiceDiscovery",
    "CircuitBreaker",
    "CircuitBreakerState"
]
