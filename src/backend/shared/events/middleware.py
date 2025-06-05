"""
Event Middleware for ACGS-PGP Event System

Provides middleware components for event processing including
logging, metrics collection, and filtering.
"""

import time
import logging
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

from .types import EventType, EventSeverity, get_event_severity
from ..common.error_handling import log_error

logger = logging.getLogger(__name__)


class EventMiddleware(ABC):
    """Base class for event middleware."""
    
    @abstractmethod
    async def process(self, event: 'Event') -> Optional['Event']:
        """
        Process an event.
        
        Args:
            event: Event to process
            
        Returns:
            Processed event or None to filter out
        """
        pass


class LoggingMiddleware(EventMiddleware):
    """Middleware for logging events."""
    
    def __init__(self, log_level: str = "INFO"):
        """
        Initialize logging middleware.
        
        Args:
            log_level: Logging level for events
        """
        self.log_level = getattr(logging, log_level.upper())
    
    async def process(self, event: 'Event') -> Optional['Event']:
        """Log event information."""
        try:
            severity = get_event_severity(event.metadata.event_type)
            
            # Determine log level based on event severity
            if severity == EventSeverity.CRITICAL:
                log_level = logging.CRITICAL
            elif severity == EventSeverity.ERROR:
                log_level = logging.ERROR
            elif severity == EventSeverity.WARNING:
                log_level = logging.WARNING
            else:
                log_level = self.log_level
            
            # Log event
            logger.log(
                log_level,
                f"Event {event.metadata.event_type.value}: {event.metadata.event_id}",
                extra={
                    "event_id": event.metadata.event_id,
                    "event_type": event.metadata.event_type.value,
                    "source_service": event.metadata.source_service,
                    "user_id": event.metadata.user_id,
                    "correlation_id": event.metadata.correlation_id,
                    "priority": event.metadata.priority.value,
                    "status": event.metadata.status.value
                }
            )
            
            return event
        
        except Exception as e:
            logger.error(f"Error in logging middleware: {e}")
            return event


class MetricsMiddleware(EventMiddleware):
    """Middleware for collecting event metrics."""
    
    def __init__(self):
        """Initialize metrics middleware."""
        self.metrics = {
            "events_processed": 0,
            "events_by_type": {},
            "events_by_service": {},
            "events_by_severity": {},
            "processing_times": []
        }
    
    async def process(self, event: 'Event') -> Optional['Event']:
        """Collect event metrics."""
        try:
            start_time = time.time()
            
            # Update counters
            self.metrics["events_processed"] += 1
            
            # Count by type
            event_type = event.metadata.event_type.value
            self.metrics["events_by_type"][event_type] = \
                self.metrics["events_by_type"].get(event_type, 0) + 1
            
            # Count by service
            service = event.metadata.source_service
            self.metrics["events_by_service"][service] = \
                self.metrics["events_by_service"].get(service, 0) + 1
            
            # Count by severity
            severity = get_event_severity(event.metadata.event_type).value
            self.metrics["events_by_severity"][severity] = \
                self.metrics["events_by_severity"].get(severity, 0) + 1
            
            # Record processing time
            processing_time = (time.time() - start_time) * 1000  # ms
            self.metrics["processing_times"].append(processing_time)
            
            # Keep only last 1000 processing times
            if len(self.metrics["processing_times"]) > 1000:
                self.metrics["processing_times"] = self.metrics["processing_times"][-1000:]
            
            return event
        
        except Exception as e:
            logger.error(f"Error in metrics middleware: {e}")
            return event
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get collected metrics."""
        processing_times = self.metrics["processing_times"]
        
        return {
            "events_processed": self.metrics["events_processed"],
            "events_by_type": self.metrics["events_by_type"],
            "events_by_service": self.metrics["events_by_service"],
            "events_by_severity": self.metrics["events_by_severity"],
            "average_processing_time_ms": sum(processing_times) / len(processing_times) if processing_times else 0,
            "max_processing_time_ms": max(processing_times) if processing_times else 0,
            "min_processing_time_ms": min(processing_times) if processing_times else 0
        }


class FilteringMiddleware(EventMiddleware):
    """Middleware for filtering events."""
    
    def __init__(self, filters: Dict[str, Any]):
        """
        Initialize filtering middleware.
        
        Args:
            filters: Filtering criteria
        """
        self.filters = filters
    
    async def process(self, event: 'Event') -> Optional['Event']:
        """Filter events based on criteria."""
        try:
            # Check each filter
            for filter_key, filter_value in self.filters.items():
                if filter_key == "event_type":
                    if event.metadata.event_type != filter_value:
                        return None
                elif filter_key == "source_service":
                    if event.metadata.source_service != filter_value:
                        return None
                elif filter_key == "priority":
                    if event.metadata.priority != filter_value:
                        return None
                elif filter_key == "user_id":
                    if event.metadata.user_id != filter_value:
                        return None
                elif filter_key.startswith("tag."):
                    tag_name = filter_key[4:]  # Remove "tag." prefix
                    if event.metadata.tags.get(tag_name) != filter_value:
                        return None
                elif filter_key.startswith("payload."):
                    payload_key = filter_key[8:]  # Remove "payload." prefix
                    if event.data.payload.get(payload_key) != filter_value:
                        return None
            
            return event
        
        except Exception as e:
            logger.error(f"Error in filtering middleware: {e}")
            return event


class ValidationMiddleware(EventMiddleware):
    """Middleware for validating events."""
    
    def __init__(self, strict: bool = False):
        """
        Initialize validation middleware.
        
        Args:
            strict: Whether to use strict validation
        """
        self.strict = strict
    
    async def process(self, event: 'Event') -> Optional['Event']:
        """Validate event structure and content."""
        try:
            errors = []
            
            # Validate metadata
            if not event.metadata.event_id:
                errors.append("Missing event ID")
            
            if not event.metadata.event_type:
                errors.append("Missing event type")
            
            if not event.metadata.source_service:
                errors.append("Missing source service")
            
            # Validate data
            if event.data.payload is None:
                errors.append("Missing payload")
            
            # Check for errors
            if errors:
                if self.strict:
                    logger.error(f"Event validation failed: {', '.join(errors)}")
                    return None
                else:
                    logger.warning(f"Event validation warnings: {', '.join(errors)}")
            
            return event
        
        except Exception as e:
            logger.error(f"Error in validation middleware: {e}")
            return event if not self.strict else None


class EnrichmentMiddleware(EventMiddleware):
    """Middleware for enriching events with additional data."""
    
    def __init__(self, enrichment_data: Dict[str, Any] = None):
        """
        Initialize enrichment middleware.
        
        Args:
            enrichment_data: Additional data to add to events
        """
        self.enrichment_data = enrichment_data or {}
    
    async def process(self, event: 'Event') -> Optional['Event']:
        """Enrich event with additional data."""
        try:
            # Add enrichment data to event tags
            for key, value in self.enrichment_data.items():
                event.metadata.tags[f"enriched.{key}"] = str(value)
            
            # Add processing timestamp
            event.metadata.tags["processed_at"] = time.time()
            
            # Add environment information
            event.metadata.tags["environment"] = "development"  # Could be configurable
            
            return event
        
        except Exception as e:
            logger.error(f"Error in enrichment middleware: {e}")
            return event


class RateLimitingMiddleware(EventMiddleware):
    """Middleware for rate limiting events."""
    
    def __init__(self, max_events_per_second: int = 100):
        """
        Initialize rate limiting middleware.
        
        Args:
            max_events_per_second: Maximum events per second
        """
        self.max_events_per_second = max_events_per_second
        self.event_times = []
    
    async def process(self, event: 'Event') -> Optional['Event']:
        """Apply rate limiting to events."""
        try:
            current_time = time.time()
            
            # Remove old timestamps (older than 1 second)
            self.event_times = [
                t for t in self.event_times
                if current_time - t < 1.0
            ]
            
            # Check rate limit
            if len(self.event_times) >= self.max_events_per_second:
                logger.warning(f"Rate limit exceeded, dropping event {event.metadata.event_id}")
                return None
            
            # Add current timestamp
            self.event_times.append(current_time)
            
            return event
        
        except Exception as e:
            logger.error(f"Error in rate limiting middleware: {e}")
            return event


# Global middleware instances
_logging_middleware = LoggingMiddleware()
_metrics_middleware = MetricsMiddleware()


def get_logging_middleware() -> LoggingMiddleware:
    """Get the global logging middleware."""
    return _logging_middleware


def get_metrics_middleware() -> MetricsMiddleware:
    """Get the global metrics middleware."""
    return _metrics_middleware
