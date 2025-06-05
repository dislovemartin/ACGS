"""
Dependency Injection Container for ACGS-PGP Services

Provides a comprehensive DI container that manages service lifecycles,
resolves dependencies, and enables flexible configuration for testing
and production environments.
"""

import asyncio
import inspect
import logging
from typing import (
    Any, Dict, List, Optional, Type, TypeVar, Callable, 
    Union, get_type_hints, get_origin, get_args
)
from enum import Enum
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
import weakref

logger = logging.getLogger(__name__)

T = TypeVar('T')


class Scope(Enum):
    """Dependency injection scopes."""
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"
    REQUEST = "request"


@dataclass
class ServiceRegistration:
    """Service registration information."""
    interface: Type
    implementation: Type
    scope: Scope
    factory: Optional[Callable] = None
    instance: Optional[Any] = None
    dependencies: List[Type] = field(default_factory=list)
    initialized: bool = False


class LifecycleManager:
    """Manages service lifecycle events."""
    
    def __init__(self):
        self._startup_callbacks: List[Callable] = []
        self._shutdown_callbacks: List[Callable] = []
        self._instances: weakref.WeakSet = weakref.WeakSet()
    
    def add_startup_callback(self, callback: Callable):
        """Add startup callback."""
        self._startup_callbacks.append(callback)
    
    def add_shutdown_callback(self, callback: Callable):
        """Add shutdown callback."""
        self._shutdown_callbacks.append(callback)
    
    def register_instance(self, instance: Any):
        """Register instance for lifecycle management."""
        self._instances.add(instance)
    
    async def startup(self):
        """Execute startup callbacks."""
        for callback in self._startup_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                logger.error(f"Error in startup callback: {e}")
    
    async def shutdown(self):
        """Execute shutdown callbacks and cleanup instances."""
        # Execute shutdown callbacks
        for callback in self._shutdown_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                logger.error(f"Error in shutdown callback: {e}")
        
        # Cleanup instances
        for instance in list(self._instances):
            if hasattr(instance, 'close') and asyncio.iscoroutinefunction(instance.close):
                try:
                    await instance.close()
                except Exception as e:
                    logger.error(f"Error closing instance {instance}: {e}")


class DIContainer:
    """
    Dependency Injection Container for ACGS services.
    
    Provides service registration, dependency resolution, and lifecycle management
    with support for different scopes and automatic dependency injection.
    """
    
    def __init__(self):
        self._services: Dict[Type, ServiceRegistration] = {}
        self._instances: Dict[Type, Any] = {}
        self._scoped_instances: Dict[str, Dict[Type, Any]] = {}
        self._lifecycle_manager = LifecycleManager()
        self._current_scope: Optional[str] = None
        self._resolving: set = set()  # Circular dependency detection
    
    def register(
        self,
        interface: Type[T],
        implementation: Optional[Type[T]] = None,
        scope: Scope = Scope.TRANSIENT,
        factory: Optional[Callable[[], T]] = None
    ) -> 'DIContainer':
        """
        Register a service with the container.
        
        Args:
            interface: Service interface or abstract class
            implementation: Concrete implementation class
            scope: Service scope (singleton, transient, etc.)
            factory: Optional factory function for creating instances
            
        Returns:
            Self for method chaining
        """
        if implementation is None and factory is None:
            implementation = interface
        
        if interface in self._services:
            logger.warning(f"Overriding existing registration for {interface}")
        
        # Analyze dependencies
        dependencies = []
        if implementation:
            dependencies = self._analyze_dependencies(implementation)
        
        registration = ServiceRegistration(
            interface=interface,
            implementation=implementation,
            scope=scope,
            factory=factory,
            dependencies=dependencies
        )
        
        self._services[interface] = registration
        logger.debug(f"Registered {interface} -> {implementation or factory} ({scope.value})")
        
        return self
    
    def register_singleton(self, interface: Type[T], implementation: Type[T] = None) -> 'DIContainer':
        """Register a singleton service."""
        return self.register(interface, implementation, Scope.SINGLETON)
    
    def register_transient(self, interface: Type[T], implementation: Type[T] = None) -> 'DIContainer':
        """Register a transient service."""
        return self.register(interface, implementation, Scope.TRANSIENT)
    
    def register_scoped(self, interface: Type[T], implementation: Type[T] = None) -> 'DIContainer':
        """Register a scoped service."""
        return self.register(interface, implementation, Scope.SCOPED)
    
    def register_factory(self, interface: Type[T], factory: Callable[[], T], scope: Scope = Scope.TRANSIENT) -> 'DIContainer':
        """Register a factory function."""
        return self.register(interface, None, scope, factory)
    
    def register_instance(self, interface: Type[T], instance: T) -> 'DIContainer':
        """Register a pre-created instance."""
        registration = ServiceRegistration(
            interface=interface,
            implementation=type(instance),
            scope=Scope.SINGLETON,
            instance=instance,
            initialized=True
        )
        
        self._services[interface] = registration
        self._instances[interface] = instance
        self._lifecycle_manager.register_instance(instance)
        
        logger.debug(f"Registered instance {interface} -> {instance}")
        return self
    
    def _analyze_dependencies(self, implementation: Type) -> List[Type]:
        """Analyze constructor dependencies."""
        dependencies = []
        
        try:
            # Get constructor signature
            init_signature = inspect.signature(implementation.__init__)
            type_hints = get_type_hints(implementation.__init__)
            
            for param_name, param in init_signature.parameters.items():
                if param_name == 'self':
                    continue
                
                # Get type annotation
                param_type = type_hints.get(param_name, param.annotation)
                
                if param_type != inspect.Parameter.empty:
                    # Handle Optional types
                    origin = get_origin(param_type)
                    if origin is Union:
                        args = get_args(param_type)
                        if len(args) == 2 and type(None) in args:
                            # Optional type
                            param_type = args[0] if args[1] is type(None) else args[1]
                    
                    dependencies.append(param_type)
        
        except Exception as e:
            logger.warning(f"Could not analyze dependencies for {implementation}: {e}")
        
        return dependencies
    
    def resolve(self, interface: Type[T]) -> T:
        """
        Resolve a service instance.
        
        Args:
            interface: Service interface to resolve
            
        Returns:
            Service instance
            
        Raises:
            ValueError: If service is not registered or circular dependency detected
        """
        if interface in self._resolving:
            raise ValueError(f"Circular dependency detected for {interface}")
        
        if interface not in self._services:
            raise ValueError(f"Service {interface} is not registered")
        
        registration = self._services[interface]
        
        # Check for existing instance based on scope
        if registration.scope == Scope.SINGLETON:
            if interface in self._instances:
                return self._instances[interface]
        elif registration.scope == Scope.SCOPED:
            if self._current_scope and self._current_scope in self._scoped_instances:
                scoped_instances = self._scoped_instances[self._current_scope]
                if interface in scoped_instances:
                    return scoped_instances[interface]
        
        # Create new instance
        self._resolving.add(interface)
        try:
            instance = self._create_instance(registration)
            
            # Store instance based on scope
            if registration.scope == Scope.SINGLETON:
                self._instances[interface] = instance
            elif registration.scope == Scope.SCOPED and self._current_scope:
                if self._current_scope not in self._scoped_instances:
                    self._scoped_instances[self._current_scope] = {}
                self._scoped_instances[self._current_scope][interface] = instance
            
            self._lifecycle_manager.register_instance(instance)
            return instance
        
        finally:
            self._resolving.discard(interface)
    
    def _create_instance(self, registration: ServiceRegistration) -> Any:
        """Create a new service instance."""
        if registration.instance is not None:
            return registration.instance
        
        if registration.factory:
            # Use factory function
            return registration.factory()
        
        if registration.implementation:
            # Resolve constructor dependencies
            dependencies = []
            for dep_type in registration.dependencies:
                dependency = self.resolve(dep_type)
                dependencies.append(dependency)
            
            # Create instance with dependencies
            instance = registration.implementation(*dependencies)
            
            # Call initialization if available
            if hasattr(instance, 'initialize') and asyncio.iscoroutinefunction(instance.initialize):
                # Schedule async initialization
                asyncio.create_task(instance.initialize())
            elif hasattr(instance, 'initialize'):
                instance.initialize()
            
            return instance
        
        raise ValueError(f"Cannot create instance for {registration.interface}")
    
    def try_resolve(self, interface: Type[T]) -> Optional[T]:
        """
        Try to resolve a service, returning None if not registered.
        
        Args:
            interface: Service interface to resolve
            
        Returns:
            Service instance or None
        """
        try:
            return self.resolve(interface)
        except ValueError:
            return None
    
    def is_registered(self, interface: Type) -> bool:
        """Check if a service is registered."""
        return interface in self._services
    
    def get_registrations(self) -> Dict[Type, ServiceRegistration]:
        """Get all service registrations."""
        return self._services.copy()
    
    @asynccontextmanager
    async def scope(self, scope_name: str):
        """
        Create a dependency injection scope.
        
        Args:
            scope_name: Name of the scope
        """
        old_scope = self._current_scope
        self._current_scope = scope_name
        
        try:
            yield self
        finally:
            # Cleanup scoped instances
            if scope_name in self._scoped_instances:
                scoped_instances = self._scoped_instances[scope_name]
                for instance in scoped_instances.values():
                    if hasattr(instance, 'close') and asyncio.iscoroutinefunction(instance.close):
                        try:
                            await instance.close()
                        except Exception as e:
                            logger.error(f"Error closing scoped instance: {e}")
                
                del self._scoped_instances[scope_name]
            
            self._current_scope = old_scope
    
    async def startup(self):
        """Initialize the container and execute startup callbacks."""
        await self._lifecycle_manager.startup()
        logger.info("DI Container started")
    
    async def shutdown(self):
        """Shutdown the container and cleanup resources."""
        await self._lifecycle_manager.shutdown()
        
        # Clear all instances
        self._instances.clear()
        self._scoped_instances.clear()
        
        logger.info("DI Container shutdown")
    
    def validate_registrations(self) -> List[str]:
        """
        Validate all service registrations for missing dependencies.
        
        Returns:
            List of validation errors
        """
        errors = []
        
        for interface, registration in self._services.items():
            for dep_type in registration.dependencies:
                if not self.is_registered(dep_type):
                    errors.append(f"Service {interface} depends on unregistered {dep_type}")
        
        return errors
    
    def get_dependency_graph(self) -> Dict[Type, List[Type]]:
        """
        Get the dependency graph for all registered services.
        
        Returns:
            Dictionary mapping interfaces to their dependencies
        """
        return {
            interface: registration.dependencies
            for interface, registration in self._services.items()
        }


# Global DI container instance
_container: Optional[DIContainer] = None


def get_container() -> DIContainer:
    """
    Get the global DI container instance.
    
    Returns:
        DI container instance
    """
    global _container
    
    if _container is None:
        _container = DIContainer()
    
    return _container


def configure_container(container: DIContainer):
    """
    Configure the global DI container.
    
    Args:
        container: DI container to set as global
    """
    global _container
    _container = container
