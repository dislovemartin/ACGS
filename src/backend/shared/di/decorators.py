"""
Dependency Injection Decorators for ACGS-PGP Services

Provides decorators for automatic dependency injection, service registration,
and lifecycle management to simplify service development and testing.
"""

import functools
import inspect
import logging
from typing import Type, TypeVar, Callable, Any, get_type_hints, get_origin, get_args, Union

from .container import get_container, Scope

logger = logging.getLogger(__name__)

T = TypeVar('T')


def injectable(cls: Type[T]) -> Type[T]:
    """
    Mark a class as injectable, enabling automatic dependency resolution.
    
    This decorator analyzes the class constructor and automatically resolves
    dependencies from the DI container when the class is instantiated.
    
    Args:
        cls: Class to make injectable
        
    Returns:
        Modified class with dependency injection support
    """
    original_init = cls.__init__
    
    # Get type hints for constructor parameters
    type_hints = get_type_hints(original_init)
    signature = inspect.signature(original_init)
    
    @functools.wraps(original_init)
    def new_init(self, *args, **kwargs):
        container = get_container()
        
        # Resolve dependencies not provided in args/kwargs
        param_names = list(signature.parameters.keys())[1:]  # Skip 'self'
        provided_params = set(kwargs.keys())
        
        # Add positional arguments to provided params
        for i, arg in enumerate(args):
            if i < len(param_names):
                provided_params.add(param_names[i])
        
        # Resolve missing dependencies
        for param_name, param in signature.parameters.items():
            if param_name == 'self' or param_name in provided_params:
                continue
            
            param_type = type_hints.get(param_name, param.annotation)
            
            if param_type != inspect.Parameter.empty:
                # Handle Optional types
                origin = get_origin(param_type)
                is_optional = False
                
                if origin is Union:
                    args_types = get_args(param_type)
                    if len(args_types) == 2 and type(None) in args_types:
                        # Optional type
                        param_type = args_types[0] if args_types[1] is type(None) else args_types[1]
                        is_optional = True
                
                # Try to resolve dependency
                try:
                    dependency = container.resolve(param_type)
                    kwargs[param_name] = dependency
                    logger.debug(f"Injected {param_type} into {cls.__name__}.{param_name}")
                except ValueError as e:
                    if not is_optional and param.default == inspect.Parameter.empty:
                        logger.error(f"Failed to inject {param_type} into {cls.__name__}: {e}")
                        raise
                    # Optional dependency or has default value
                    logger.debug(f"Optional dependency {param_type} not available for {cls.__name__}")
        
        original_init(self, *args, **kwargs)
    
    cls.__init__ = new_init
    cls._injectable = True
    
    return cls


def inject(*dependencies: Type) -> Callable:
    """
    Decorator for injecting specific dependencies into a function or method.
    
    Args:
        *dependencies: Types to inject as function arguments
        
    Returns:
        Decorated function with dependency injection
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            container = get_container()
            
            # Resolve dependencies and add to kwargs
            for dep_type in dependencies:
                if dep_type not in kwargs:
                    try:
                        dependency = container.resolve(dep_type)
                        # Use the type name as parameter name (lowercase)
                        param_name = dep_type.__name__.lower()
                        kwargs[param_name] = dependency
                        logger.debug(f"Injected {dep_type} into {func.__name__}")
                    except ValueError as e:
                        logger.error(f"Failed to inject {dep_type} into {func.__name__}: {e}")
                        raise
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def singleton(interface: Type[T] = None):
    """
    Decorator to register a class as a singleton service.
    
    Args:
        interface: Optional interface type to register against
        
    Returns:
        Decorated class registered as singleton
    """
    def decorator(cls: Type[T]) -> Type[T]:
        container = get_container()
        registration_interface = interface or cls
        
        container.register_singleton(registration_interface, cls)
        logger.debug(f"Registered {cls} as singleton for {registration_interface}")
        
        return injectable(cls)
    
    return decorator


def transient(interface: Type[T] = None):
    """
    Decorator to register a class as a transient service.
    
    Args:
        interface: Optional interface type to register against
        
    Returns:
        Decorated class registered as transient
    """
    def decorator(cls: Type[T]) -> Type[T]:
        container = get_container()
        registration_interface = interface or cls
        
        container.register_transient(registration_interface, cls)
        logger.debug(f"Registered {cls} as transient for {registration_interface}")
        
        return injectable(cls)
    
    return decorator


def scoped(interface: Type[T] = None):
    """
    Decorator to register a class as a scoped service.
    
    Args:
        interface: Optional interface type to register against
        
    Returns:
        Decorated class registered as scoped
    """
    def decorator(cls: Type[T]) -> Type[T]:
        container = get_container()
        registration_interface = interface or cls
        
        container.register_scoped(registration_interface, cls)
        logger.debug(f"Registered {cls} as scoped for {registration_interface}")
        
        return injectable(cls)
    
    return decorator


def factory(interface: Type[T], scope: Scope = Scope.TRANSIENT):
    """
    Decorator to register a function as a factory for a service.
    
    Args:
        interface: Interface type to register factory for
        scope: Service scope
        
    Returns:
        Decorated factory function
    """
    def decorator(func: Callable[[], T]) -> Callable[[], T]:
        container = get_container()
        
        container.register_factory(interface, func, scope)
        logger.debug(f"Registered factory {func.__name__} for {interface} ({scope.value})")
        
        return func
    
    return decorator


def startup_callback(func: Callable) -> Callable:
    """
    Decorator to register a function as a startup callback.
    
    Args:
        func: Function to call during container startup
        
    Returns:
        Original function
    """
    container = get_container()
    container._lifecycle_manager.add_startup_callback(func)
    logger.debug(f"Registered startup callback: {func.__name__}")
    
    return func


def shutdown_callback(func: Callable) -> Callable:
    """
    Decorator to register a function as a shutdown callback.
    
    Args:
        func: Function to call during container shutdown
        
    Returns:
        Original function
    """
    container = get_container()
    container._lifecycle_manager.add_shutdown_callback(func)
    logger.debug(f"Registered shutdown callback: {func.__name__}")
    
    return func


def auto_register(scope: Scope = Scope.TRANSIENT, interface: Type = None):
    """
    Decorator to automatically register a class with the DI container.
    
    Args:
        scope: Service scope
        interface: Optional interface to register against
        
    Returns:
        Decorated class registered with container
    """
    def decorator(cls: Type[T]) -> Type[T]:
        container = get_container()
        registration_interface = interface or cls
        
        container.register(registration_interface, cls, scope)
        logger.debug(f"Auto-registered {cls} for {registration_interface} ({scope.value})")
        
        return injectable(cls)
    
    return decorator


class DIProperty:
    """
    Property descriptor for dependency injection.
    
    Allows lazy resolution of dependencies as class properties.
    """
    
    def __init__(self, interface: Type, optional: bool = False):
        """
        Initialize DI property.
        
        Args:
            interface: Interface type to resolve
            optional: Whether dependency is optional
        """
        self.interface = interface
        self.optional = optional
        self._instance = None
    
    def __get__(self, obj, objtype=None):
        """Get the dependency instance."""
        if obj is None:
            return self
        
        if self._instance is None:
            container = get_container()
            
            try:
                self._instance = container.resolve(self.interface)
            except ValueError as e:
                if self.optional:
                    return None
                raise
        
        return self._instance
    
    def __set__(self, obj, value):
        """Set the dependency instance."""
        self._instance = value


def di_property(interface: Type, optional: bool = False) -> DIProperty:
    """
    Create a dependency injection property.
    
    Args:
        interface: Interface type to resolve
        optional: Whether dependency is optional
        
    Returns:
        DI property descriptor
    """
    return DIProperty(interface, optional)


# Utility functions for testing

def with_test_container(test_func: Callable) -> Callable:
    """
    Decorator to run a test with a fresh DI container.
    
    Args:
        test_func: Test function to decorate
        
    Returns:
        Decorated test function
    """
    @functools.wraps(test_func)
    async def wrapper(*args, **kwargs):
        from .container import DIContainer, configure_container
        
        # Save current container
        original_container = get_container()
        
        # Create test container
        test_container = DIContainer()
        configure_container(test_container)
        
        try:
            await test_container.startup()
            result = await test_func(*args, **kwargs)
            return result
        finally:
            await test_container.shutdown()
            configure_container(original_container)
    
    return wrapper


def mock_dependency(interface: Type, mock_instance: Any):
    """
    Register a mock instance for testing.
    
    Args:
        interface: Interface to mock
        mock_instance: Mock instance to register
    """
    container = get_container()
    container.register_instance(interface, mock_instance)
