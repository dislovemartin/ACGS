"""
Event Bus Implementation for ACGS-PGP Services

Provides a comprehensive event bus for decoupled communication between
microservices, replacing direct HTTP calls with event-driven patterns.
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, List, Callable, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone
from collections import defaultdict
import json

from .types import EventType, EventPriority, EventStatus, EventMetadata, EventData
from .store import EventStore, InMemoryEventStore
from ..common.error_handling import ACGSException, handle_service_error
from ..di.interfaces import EventBusInterface

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """Event object containing metadata and data."""
    metadata: EventMetadata
    data: EventData
    
    @classmethod
    def create(
        cls,
        event_type: EventType,
        payload: Dict[str, Any],
        source_service: str,
        priority: EventPriority = EventPriority.NORMAL,
        user_id: str = None,
        correlation_id: str = None,
        tags: Dict[str, str] = None
    ) -> 'Event':
        """
        Create a new event.
        
        Args:
            event_type: Type of event
            payload: Event payload data
            source_service: Service that created the event
            priority: Event priority
            user_id: User associated with event
            correlation_id: Correlation ID for tracing
            tags: Additional tags
            
        Returns:
            New event instance
        """
        now = datetime.now(timezone.utc)
        
        metadata = EventMetadata(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            priority=priority,
            status=EventStatus.PENDING,
            created_at=now,
            updated_at=now,
            source_service=source_service,
            correlation_id=correlation_id,
            user_id=user_id,
            tags=tags or {}
        )
        
        data = EventData(payload=payload)
        
        return cls(metadata=metadata, data=data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "metadata": {
                "event_id": self.metadata.event_id,
                "event_type": self.metadata.event_type.value,
                "priority": self.metadata.priority.value,
                "status": self.metadata.status.value,
                "created_at": self.metadata.created_at.isoformat(),
                "updated_at": self.metadata.updated_at.isoformat(),
                "source_service": self.metadata.source_service,
                "correlation_id": self.metadata.correlation_id,
                "user_id": self.metadata.user_id,
                "retry_count": self.metadata.retry_count,
                "max_retries": self.metadata.max_retries,
                "tags": self.metadata.tags
            },
            "data": {
                "payload": self.data.payload,
                "schema_version": self.data.schema_version,
                "content_type": self.data.content_type,
                "encoding": self.data.encoding
            }
        }
    
    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict(), default=str)


@dataclass
class EventHandler:
    """Event handler registration."""
    handler_id: str
    event_type: EventType
    handler_func: Callable[[Event], Any]
    service_name: str
    is_async: bool = True
    max_retries: int = 3
    timeout: float = 30.0
    filters: Dict[str, Any] = field(default_factory=dict)
    
    async def handle(self, event: Event) -> Any:
        """Handle an event."""
        try:
            if self.is_async:
                if asyncio.iscoroutinefunction(self.handler_func):
                    return await asyncio.wait_for(
                        self.handler_func(event),
                        timeout=self.timeout
                    )
                else:
                    # Run sync function in thread pool
                    loop = asyncio.get_event_loop()
                    return await loop.run_in_executor(
                        None, self.handler_func, event
                    )
            else:
                return self.handler_func(event)
        
        except asyncio.TimeoutError:
            raise ACGSException(
                f"Event handler {self.handler_id} timed out",
                "HANDLER_TIMEOUT"
            )
        except Exception as e:
            raise handle_service_error(
                e, self.service_name, f"handle_event_{event.metadata.event_type.value}"
            )
    
    def matches_filters(self, event: Event) -> bool:
        """Check if event matches handler filters."""
        if not self.filters:
            return True
        
        for filter_key, filter_value in self.filters.items():
            if filter_key == "source_service":
                if event.metadata.source_service != filter_value:
                    return False
            elif filter_key == "user_id":
                if event.metadata.user_id != filter_value:
                    return False
            elif filter_key == "priority":
                if event.metadata.priority != filter_value:
                    return False
            elif filter_key.startswith("tag."):
                tag_name = filter_key[4:]  # Remove "tag." prefix
                if event.metadata.tags.get(tag_name) != filter_value:
                    return False
            elif filter_key.startswith("payload."):
                payload_key = filter_key[8:]  # Remove "payload." prefix
                if event.data.payload.get(payload_key) != filter_value:
                    return False
        
        return True


class EventBus(EventBusInterface):
    """
    Event bus implementation for ACGS services.
    
    Provides publish/subscribe functionality with support for event persistence,
    retry logic, and middleware processing.
    """
    
    def __init__(self, event_store: EventStore = None):
        """
        Initialize event bus.
        
        Args:
            event_store: Event store for persistence (defaults to in-memory)
        """
        self.event_store = event_store or InMemoryEventStore()
        self.handlers: Dict[EventType, List[EventHandler]] = defaultdict(list)
        self.middleware: List[Callable] = []
        self.running = False
        self.processing_tasks: Set[asyncio.Task] = set()
        
        # Metrics
        self.metrics = {
            "events_published": 0,
            "events_processed": 0,
            "events_failed": 0,
            "handlers_registered": 0
        }
    
    async def start(self):
        """Start the event bus."""
        if self.running:
            return
        
        self.running = True
        await self.event_store.initialize()
        
        # Start background processing
        asyncio.create_task(self._process_events())
        
        logger.info("Event bus started")
    
    async def stop(self):
        """Stop the event bus."""
        if not self.running:
            return
        
        self.running = False
        
        # Wait for processing tasks to complete
        if self.processing_tasks:
            await asyncio.gather(*self.processing_tasks, return_exceptions=True)
        
        await self.event_store.close()
        
        logger.info("Event bus stopped")
    
    async def publish(
        self,
        event_type: str,
        data: Dict[str, Any],
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Publish an event to the bus.
        
        Args:
            event_type: Type of event to publish
            data: Event data payload
            metadata: Optional event metadata
            
        Returns:
            True if event was published successfully
        """
        try:
            # Convert string to EventType enum
            if isinstance(event_type, str):
                event_type_enum = EventType(event_type)
            else:
                event_type_enum = event_type
            
            # Extract metadata
            metadata = metadata or {}
            source_service = metadata.get("source_service", "unknown")
            priority = EventPriority(metadata.get("priority", "normal"))
            user_id = metadata.get("user_id")
            correlation_id = metadata.get("correlation_id")
            tags = metadata.get("tags", {})
            
            # Create event
            event = Event.create(
                event_type=event_type_enum,
                payload=data,
                source_service=source_service,
                priority=priority,
                user_id=user_id,
                correlation_id=correlation_id,
                tags=tags
            )
            
            # Apply middleware
            for middleware in self.middleware:
                event = await middleware(event)
                if event is None:
                    logger.warning(f"Event {event_type_enum.value} filtered by middleware")
                    return False
            
            # Store event
            await self.event_store.store_event(event)
            
            # Update metrics
            self.metrics["events_published"] += 1
            
            logger.debug(f"Published event {event.metadata.event_id}: {event_type_enum.value}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to publish event {event_type}: {e}")
            return False
    
    async def subscribe(self, event_type: str, handler: callable) -> str:
        """
        Subscribe to events of a specific type.
        
        Args:
            event_type: Type of events to subscribe to
            handler: Handler function for events
            
        Returns:
            Subscription ID
        """
        try:
            # Convert string to EventType enum
            if isinstance(event_type, str):
                event_type_enum = EventType(event_type)
            else:
                event_type_enum = event_type
            
            # Create handler registration
            handler_id = str(uuid.uuid4())
            service_name = getattr(handler, '__module__', 'unknown')
            
            event_handler = EventHandler(
                handler_id=handler_id,
                event_type=event_type_enum,
                handler_func=handler,
                service_name=service_name,
                is_async=asyncio.iscoroutinefunction(handler)
            )
            
            # Register handler
            self.handlers[event_type_enum].append(event_handler)
            self.metrics["handlers_registered"] += 1
            
            logger.debug(f"Registered handler {handler_id} for {event_type_enum.value}")
            return handler_id
        
        except Exception as e:
            logger.error(f"Failed to subscribe to {event_type}: {e}")
            raise
    
    async def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from events.
        
        Args:
            subscription_id: Subscription ID to remove
            
        Returns:
            True if subscription was removed
        """
        for event_type, handlers in self.handlers.items():
            for i, handler in enumerate(handlers):
                if handler.handler_id == subscription_id:
                    del handlers[i]
                    self.metrics["handlers_registered"] -= 1
                    logger.debug(f"Unsubscribed handler {subscription_id}")
                    return True
        
        return False
    
    async def get_events(
        self,
        event_type: str = None,
        since: datetime = None
    ) -> List[Dict[str, Any]]:
        """
        Get events from the bus.
        
        Args:
            event_type: Optional event type filter
            since: Optional timestamp filter
            
        Returns:
            List of events
        """
        events = await self.event_store.get_events(
            event_type=EventType(event_type) if event_type else None,
            since=since
        )
        
        return [event.to_dict() for event in events]
    
    def add_middleware(self, middleware: Callable[[Event], Event]):
        """Add middleware to the event processing pipeline."""
        self.middleware.append(middleware)
        logger.debug(f"Added middleware: {middleware.__name__}")
    
    async def _process_events(self):
        """Background task to process pending events."""
        while self.running:
            try:
                # Get pending events
                pending_events = await self.event_store.get_pending_events()
                
                for event in pending_events:
                    if not self.running:
                        break
                    
                    # Create processing task
                    task = asyncio.create_task(self._process_event(event))
                    self.processing_tasks.add(task)
                    
                    # Clean up completed tasks
                    self.processing_tasks = {
                        t for t in self.processing_tasks if not t.done()
                    }
                
                # Wait before next iteration
                await asyncio.sleep(1.0)
            
            except Exception as e:
                logger.error(f"Error in event processing loop: {e}")
                await asyncio.sleep(5.0)
    
    async def _process_event(self, event: Event):
        """Process a single event."""
        try:
            # Update event status
            event.metadata.status = EventStatus.PROCESSING
            event.metadata.updated_at = datetime.now(timezone.utc)
            await self.event_store.update_event(event)
            
            # Get handlers for event type
            handlers = self.handlers.get(event.metadata.event_type, [])
            
            if not handlers:
                logger.debug(f"No handlers for event {event.metadata.event_type.value}")
                event.metadata.status = EventStatus.COMPLETED
                await self.event_store.update_event(event)
                return
            
            # Process with each handler
            handler_results = []
            for handler in handlers:
                if handler.matches_filters(event):
                    try:
                        result = await handler.handle(event)
                        handler_results.append({"handler_id": handler.handler_id, "result": result})
                    except Exception as e:
                        logger.error(f"Handler {handler.handler_id} failed for event {event.metadata.event_id}: {e}")
                        handler_results.append({"handler_id": handler.handler_id, "error": str(e)})
            
            # Update event status
            event.metadata.status = EventStatus.COMPLETED
            event.metadata.updated_at = datetime.now(timezone.utc)
            await self.event_store.update_event(event)
            
            self.metrics["events_processed"] += 1
            
        except Exception as e:
            logger.error(f"Failed to process event {event.metadata.event_id}: {e}")
            
            # Update event status to failed
            event.metadata.status = EventStatus.FAILED
            event.metadata.updated_at = datetime.now(timezone.utc)
            await self.event_store.update_event(event)
            
            self.metrics["events_failed"] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get event bus metrics."""
        return {
            **self.metrics,
            "handlers_by_type": {
                event_type.value: len(handlers)
                for event_type, handlers in self.handlers.items()
            },
            "active_processing_tasks": len(self.processing_tasks)
        }


# Global event bus instance
_event_bus: Optional[EventBus] = None


async def get_event_bus() -> EventBus:
    """
    Get the global event bus instance.
    
    Returns:
        Event bus instance
    """
    global _event_bus
    
    if _event_bus is None:
        _event_bus = EventBus()
        await _event_bus.start()
    
    return _event_bus
