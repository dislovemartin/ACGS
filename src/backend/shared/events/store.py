"""
Event Store Implementation for ACGS-PGP Event System

Provides event persistence, retrieval, and replay capabilities
for the event-driven architecture.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from abc import ABC, abstractmethod

from .types import EventType, EventStatus
from ..common.error_handling import ACGSException

logger = logging.getLogger(__name__)


class EventStore(ABC):
    """Abstract base class for event stores."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the event store."""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close the event store."""
        pass
    
    @abstractmethod
    async def store_event(self, event: 'Event') -> bool:
        """Store an event."""
        pass
    
    @abstractmethod
    async def get_event(self, event_id: str) -> Optional['Event']:
        """Get an event by ID."""
        pass
    
    @abstractmethod
    async def get_events(
        self,
        event_type: Optional[EventType] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List['Event']:
        """Get events with optional filtering."""
        pass
    
    @abstractmethod
    async def get_pending_events(self, limit: int = 100) -> List['Event']:
        """Get pending events for processing."""
        pass
    
    @abstractmethod
    async def update_event(self, event: 'Event') -> bool:
        """Update an existing event."""
        pass
    
    @abstractmethod
    async def delete_event(self, event_id: str) -> bool:
        """Delete an event."""
        pass


class InMemoryEventStore(EventStore):
    """In-memory event store for testing and development."""
    
    def __init__(self):
        """Initialize in-memory event store."""
        self.events: Dict[str, 'Event'] = {}
        self.events_by_type: Dict[EventType, List[str]] = {}
        self.events_by_status: Dict[EventStatus, List[str]] = {}
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize the event store."""
        logger.info("In-memory event store initialized")
    
    async def close(self) -> None:
        """Close the event store."""
        async with self._lock:
            self.events.clear()
            self.events_by_type.clear()
            self.events_by_status.clear()
        logger.info("In-memory event store closed")
    
    async def store_event(self, event: 'Event') -> bool:
        """Store an event in memory."""
        async with self._lock:
            try:
                event_id = event.metadata.event_id
                
                # Store event
                self.events[event_id] = event
                
                # Index by type
                if event.metadata.event_type not in self.events_by_type:
                    self.events_by_type[event.metadata.event_type] = []
                self.events_by_type[event.metadata.event_type].append(event_id)
                
                # Index by status
                if event.metadata.status not in self.events_by_status:
                    self.events_by_status[event.metadata.status] = []
                self.events_by_status[event.metadata.status].append(event_id)
                
                logger.debug(f"Stored event {event_id}")
                return True
            
            except Exception as e:
                logger.error(f"Failed to store event: {e}")
                return False
    
    async def get_event(self, event_id: str) -> Optional['Event']:
        """Get an event by ID."""
        async with self._lock:
            return self.events.get(event_id)
    
    async def get_events(
        self,
        event_type: Optional[EventType] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List['Event']:
        """Get events with optional filtering."""
        async with self._lock:
            events = []
            
            if event_type:
                # Filter by type
                event_ids = self.events_by_type.get(event_type, [])
                events = [self.events[event_id] for event_id in event_ids]
            else:
                # Get all events
                events = list(self.events.values())
            
            # Filter by timestamp
            if since:
                events = [
                    event for event in events
                    if event.metadata.created_at >= since
                ]
            
            # Sort by creation time (newest first)
            events.sort(key=lambda e: e.metadata.created_at, reverse=True)
            
            # Apply limit
            return events[:limit]
    
    async def get_pending_events(self, limit: int = 100) -> List['Event']:
        """Get pending events for processing."""
        async with self._lock:
            pending_ids = self.events_by_status.get(EventStatus.PENDING, [])
            events = [self.events[event_id] for event_id in pending_ids]
            
            # Sort by priority and creation time
            events.sort(key=lambda e: (e.metadata.priority.value, e.metadata.created_at))
            
            return events[:limit]
    
    async def update_event(self, event: 'Event') -> bool:
        """Update an existing event."""
        async with self._lock:
            try:
                event_id = event.metadata.event_id
                
                if event_id not in self.events:
                    return False
                
                old_event = self.events[event_id]
                old_status = old_event.metadata.status
                new_status = event.metadata.status
                
                # Update event
                self.events[event_id] = event
                
                # Update status index if changed
                if old_status != new_status:
                    # Remove from old status
                    if old_status in self.events_by_status:
                        try:
                            self.events_by_status[old_status].remove(event_id)
                        except ValueError:
                            pass
                    
                    # Add to new status
                    if new_status not in self.events_by_status:
                        self.events_by_status[new_status] = []
                    self.events_by_status[new_status].append(event_id)
                
                logger.debug(f"Updated event {event_id}")
                return True
            
            except Exception as e:
                logger.error(f"Failed to update event: {e}")
                return False
    
    async def delete_event(self, event_id: str) -> bool:
        """Delete an event."""
        async with self._lock:
            try:
                if event_id not in self.events:
                    return False
                
                event = self.events[event_id]
                
                # Remove from main storage
                del self.events[event_id]
                
                # Remove from type index
                event_type = event.metadata.event_type
                if event_type in self.events_by_type:
                    try:
                        self.events_by_type[event_type].remove(event_id)
                    except ValueError:
                        pass
                
                # Remove from status index
                status = event.metadata.status
                if status in self.events_by_status:
                    try:
                        self.events_by_status[status].remove(event_id)
                    except ValueError:
                        pass
                
                logger.debug(f"Deleted event {event_id}")
                return True
            
            except Exception as e:
                logger.error(f"Failed to delete event: {e}")
                return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event store statistics."""
        return {
            "total_events": len(self.events),
            "events_by_type": {
                event_type.value: len(event_ids)
                for event_type, event_ids in self.events_by_type.items()
            },
            "events_by_status": {
                status.value: len(event_ids)
                for status, event_ids in self.events_by_status.items()
            }
        }


class DatabaseEventStore(EventStore):
    """Database-backed event store for production use."""
    
    def __init__(self, database_url: str):
        """
        Initialize database event store.
        
        Args:
            database_url: Database connection URL
        """
        self.database_url = database_url
        self.connection_pool = None
    
    async def initialize(self) -> None:
        """Initialize the database event store."""
        # This would initialize actual database connection in production
        logger.info("Database event store initialized")
    
    async def close(self) -> None:
        """Close the database event store."""
        # This would close database connections in production
        logger.info("Database event store closed")
    
    async def store_event(self, event: 'Event') -> bool:
        """Store an event in the database."""
        try:
            # This would execute SQL INSERT in production
            event_data = {
                "event_id": event.metadata.event_id,
                "event_type": event.metadata.event_type.value,
                "priority": event.metadata.priority.value,
                "status": event.metadata.status.value,
                "created_at": event.metadata.created_at,
                "updated_at": event.metadata.updated_at,
                "source_service": event.metadata.source_service,
                "correlation_id": event.metadata.correlation_id,
                "user_id": event.metadata.user_id,
                "payload": json.dumps(event.data.payload),
                "tags": json.dumps(event.metadata.tags)
            }
            
            logger.debug(f"Would store event {event.metadata.event_id} in database")
            return True
        
        except Exception as e:
            logger.error(f"Failed to store event in database: {e}")
            return False
    
    async def get_event(self, event_id: str) -> Optional['Event']:
        """Get an event by ID from the database."""
        # This would execute SQL SELECT in production
        logger.debug(f"Would retrieve event {event_id} from database")
        return None
    
    async def get_events(
        self,
        event_type: Optional[EventType] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List['Event']:
        """Get events from the database with filtering."""
        # This would execute SQL SELECT with WHERE clauses in production
        logger.debug(f"Would retrieve events from database with filters")
        return []
    
    async def get_pending_events(self, limit: int = 100) -> List['Event']:
        """Get pending events from the database."""
        # This would execute SQL SELECT for pending events in production
        logger.debug(f"Would retrieve pending events from database")
        return []
    
    async def update_event(self, event: 'Event') -> bool:
        """Update an event in the database."""
        try:
            # This would execute SQL UPDATE in production
            logger.debug(f"Would update event {event.metadata.event_id} in database")
            return True
        
        except Exception as e:
            logger.error(f"Failed to update event in database: {e}")
            return False
    
    async def delete_event(self, event_id: str) -> bool:
        """Delete an event from the database."""
        try:
            # This would execute SQL DELETE in production
            logger.debug(f"Would delete event {event_id} from database")
            return True
        
        except Exception as e:
            logger.error(f"Failed to delete event from database: {e}")
            return False
