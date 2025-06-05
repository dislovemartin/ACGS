"""
Dependency Injection Framework for ACGS-PGP Services

This module provides a comprehensive dependency injection system that eliminates
hard-coded dependencies and improves testability across the ACGS microservices.
"""

from .container import DIContainer, Scope, LifecycleManager, get_container
from .decorators import inject, injectable, singleton, transient
from .interfaces import ServiceInterface, DatabaseInterface, CacheInterface
from .providers import ServiceProvider, DatabaseProvider, CacheProvider
from .registry import ServiceRegistry as DIServiceRegistry

__all__ = [
    "DIContainer",
    "Scope",
    "LifecycleManager",
    "get_container",
    "inject",
    "injectable",
    "singleton",
    "transient",
    "ServiceInterface",
    "DatabaseInterface",
    "CacheInterface",
    "ServiceProvider",
    "DatabaseProvider",
    "CacheProvider",
    "DIServiceRegistry"
]
