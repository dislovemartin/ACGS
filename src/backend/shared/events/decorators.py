"""
Event Decorators for ACGS-PGP Event System

Provides decorators for event handling and publishing to simplify
event-driven development patterns.
"""

import functools
import logging
from typing import Callable, Any, Dict, Optional

from .types import EventType, EventPriority
from .bus import get_event_bus

logger = logging.getLogger(__name__)


def event_handler(
    event_type: EventType,
    priority: EventPriority = EventPriority.NORMAL,
    filters: Dict[str, Any] = None
):
    """
    Decorator to register a function as an event handler.
    
    Args:
        event_type: Type of events to handle
        priority: Handler priority
        filters: Optional event filters
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        # Mark function as event handler
        wrapper._is_event_handler = True
        wrapper._event_type = event_type
        wrapper._priority = priority
        wrapper._filters = filters or {}
        
        # Auto-register with event bus if available
        try:
            import asyncio
            
            async def register_handler():
                event_bus = await get_event_bus()
                await event_bus.subscribe(event_type.value, wrapper)
            
            # Schedule registration
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(register_handler())
            except RuntimeError:
                # No event loop running, registration will happen later
                pass
        except Exception as e:
            logger.warning(f"Could not auto-register event handler: {e}")
        
        return wrapper
    
    return decorator


def event_publisher(
    event_type: EventType,
    source_service: str = None,
    priority: EventPriority = EventPriority.NORMAL
):
    """
    Decorator to automatically publish events from function results.
    
    Args:
        event_type: Type of event to publish
        source_service: Source service name
        priority: Event priority
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            # Publish event with result
            try:
                event_bus = await get_event_bus()
                await event_bus.publish(
                    event_type.value,
                    {"result": result, "function": func.__name__},
                    {
                        "source_service": source_service or func.__module__,
                        "priority": priority.value
                    }
                )
            except Exception as e:
                logger.error(f"Failed to publish event from {func.__name__}: {e}")
            
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # Publish event with result (sync version)
            try:
                import asyncio
                
                async def publish_event():
                    event_bus = await get_event_bus()
                    await event_bus.publish(
                        event_type.value,
                        {"result": result, "function": func.__name__},
                        {
                            "source_service": source_service or func.__module__,
                            "priority": priority.value
                        }
                    )
                
                # Schedule event publishing
                try:
                    loop = asyncio.get_event_loop()
                    loop.create_task(publish_event())
                except RuntimeError:
                    # No event loop running
                    pass
            except Exception as e:
                logger.error(f"Failed to publish event from {func.__name__}: {e}")
            
            return result
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def on_event(event_type: EventType, filters: Dict[str, Any] = None):
    """
    Simple decorator for event handling.
    
    Args:
        event_type: Type of events to handle
        filters: Optional event filters
        
    Returns:
        Decorated function
    """
    return event_handler(event_type, filters=filters)


def publish_event(event_type: EventType, source_service: str = None):
    """
    Simple decorator for event publishing.
    
    Args:
        event_type: Type of event to publish
        source_service: Source service name
        
    Returns:
        Decorated function
    """
    return event_publisher(event_type, source_service=source_service)


def event_listener(event_types: list, filters: Dict[str, Any] = None):
    """
    Decorator for listening to multiple event types.
    
    Args:
        event_types: List of event types to listen for
        filters: Optional event filters
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        # Apply event_handler decorator for each event type
        for event_type in event_types:
            func = event_handler(event_type, filters=filters)(func)
        
        return func
    
    return decorator


class EventHandlerRegistry:
    """Registry for managing event handlers."""
    
    def __init__(self):
        """Initialize handler registry."""
        self.handlers = {}
    
    def register_handler(self, event_type: EventType, handler: Callable):
        """Register an event handler."""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        
        self.handlers[event_type].append(handler)
        logger.debug(f"Registered handler for {event_type.value}")
    
    def get_handlers(self, event_type: EventType) -> list:
        """Get handlers for an event type."""
        return self.handlers.get(event_type, [])
    
    def unregister_handler(self, event_type: EventType, handler: Callable):
        """Unregister an event handler."""
        if event_type in self.handlers:
            try:
                self.handlers[event_type].remove(handler)
                logger.debug(f"Unregistered handler for {event_type.value}")
            except ValueError:
                pass
    
    def clear_handlers(self, event_type: EventType = None):
        """Clear handlers for an event type or all handlers."""
        if event_type:
            self.handlers.pop(event_type, None)
        else:
            self.handlers.clear()


# Global handler registry
_handler_registry = EventHandlerRegistry()


def get_handler_registry() -> EventHandlerRegistry:
    """Get the global handler registry."""
    return _handler_registry
