"""
Event Types and Enums for ACGS-PGP Event System

Defines standard event types, priorities, and status values used
throughout the event-driven architecture.
"""

from enum import Enum
from typing import Dict, Any
from dataclasses import dataclass
from datetime import datetime, timezone
import uuid


class EventType(Enum):
    """Standard ACGS event types."""
    
    # Authentication Events
    USER_AUTHENTICATED = "user.authenticated"
    USER_LOGIN_FAILED = "user.login_failed"
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    TOKEN_EXPIRED = "token.expired"
    
    # Principle Events
    PRINCIPLE_CREATED = "principle.created"
    PRINCIPLE_UPDATED = "principle.updated"
    PRINCIPLE_DELETED = "principle.deleted"
    PRINCIPLE_VOTED = "principle.voted"
    PRINCIPLE_APPROVED = "principle.approved"
    PRINCIPLE_REJECTED = "principle.rejected"
    
    # Governance Events
    GOVERNANCE_SYNTHESIZED = "governance.synthesized"
    POLICY_GENERATED = "policy.generated"
    POLICY_UPDATED = "policy.updated"
    POLICY_ACTIVATED = "policy.activated"
    POLICY_DEACTIVATED = "policy.deactivated"
    
    # Verification Events
    POLICY_VERIFIED = "policy.verified"
    POLICY_VERIFICATION_FAILED = "policy.verification_failed"
    CONSISTENCY_CHECK_COMPLETED = "consistency.check_completed"
    RULES_VALIDATED = "rules.validated"
    
    # Compliance Events
    POLICY_COMPILED = "policy.compiled"
    POLICY_EVALUATED = "policy.evaluated"
    POLICY_ENFORCED = "policy.enforced"
    COMPLIANCE_VIOLATION = "compliance.violation"
    
    # Integrity Events
    DATA_SIGNED = "data.signed"
    SIGNATURE_VERIFIED = "signature.verified"
    INTEGRITY_CHECK_PASSED = "integrity.check_passed"
    INTEGRITY_CHECK_FAILED = "integrity.check_failed"
    
    # System Events
    SERVICE_STARTED = "service.started"
    SERVICE_STOPPED = "service.stopped"
    SERVICE_HEALTH_CHECK = "service.health_check"
    SYSTEM_ERROR = "system.error"
    PERFORMANCE_ALERT = "performance.alert"
    
    # Audit Events
    AUDIT_LOG_CREATED = "audit.log_created"
    SECURITY_EVENT = "security.event"
    ACCESS_GRANTED = "access.granted"
    ACCESS_DENIED = "access.denied"
    
    # Workflow Events
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    TASK_ASSIGNED = "task.assigned"
    TASK_COMPLETED = "task.completed"


class EventPriority(Enum):
    """Event priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class EventStatus(Enum):
    """Event processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


@dataclass
class EventMetadata:
    """Event metadata information."""
    event_id: str
    event_type: EventType
    priority: EventPriority
    status: EventStatus
    created_at: datetime
    updated_at: datetime
    source_service: str
    correlation_id: str = None
    user_id: str = None
    session_id: str = None
    retry_count: int = 0
    max_retries: int = 3
    tags: Dict[str, str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = {}
        
        if self.correlation_id is None:
            self.correlation_id = str(uuid.uuid4())


@dataclass
class EventData:
    """Event payload data."""
    payload: Dict[str, Any]
    schema_version: str = "1.0"
    content_type: str = "application/json"
    encoding: str = "utf-8"
    
    def __post_init__(self):
        if self.payload is None:
            self.payload = {}


class EventCategory(Enum):
    """Event categories for organization."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    GOVERNANCE = "governance"
    COMPLIANCE = "compliance"
    VERIFICATION = "verification"
    INTEGRITY = "integrity"
    AUDIT = "audit"
    SYSTEM = "system"
    WORKFLOW = "workflow"
    NOTIFICATION = "notification"


class EventSeverity(Enum):
    """Event severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# Event type to category mapping
EVENT_CATEGORIES = {
    # Authentication
    EventType.USER_AUTHENTICATED: EventCategory.AUTHENTICATION,
    EventType.USER_LOGIN_FAILED: EventCategory.AUTHENTICATION,
    EventType.USER_CREATED: EventCategory.AUTHENTICATION,
    EventType.USER_UPDATED: EventCategory.AUTHENTICATION,
    EventType.USER_DELETED: EventCategory.AUTHENTICATION,
    EventType.TOKEN_EXPIRED: EventCategory.AUTHENTICATION,
    
    # Governance
    EventType.PRINCIPLE_CREATED: EventCategory.GOVERNANCE,
    EventType.PRINCIPLE_UPDATED: EventCategory.GOVERNANCE,
    EventType.PRINCIPLE_DELETED: EventCategory.GOVERNANCE,
    EventType.PRINCIPLE_VOTED: EventCategory.GOVERNANCE,
    EventType.PRINCIPLE_APPROVED: EventCategory.GOVERNANCE,
    EventType.PRINCIPLE_REJECTED: EventCategory.GOVERNANCE,
    EventType.GOVERNANCE_SYNTHESIZED: EventCategory.GOVERNANCE,
    EventType.POLICY_GENERATED: EventCategory.GOVERNANCE,
    EventType.POLICY_UPDATED: EventCategory.GOVERNANCE,
    EventType.POLICY_ACTIVATED: EventCategory.GOVERNANCE,
    EventType.POLICY_DEACTIVATED: EventCategory.GOVERNANCE,
    
    # Verification
    EventType.POLICY_VERIFIED: EventCategory.VERIFICATION,
    EventType.POLICY_VERIFICATION_FAILED: EventCategory.VERIFICATION,
    EventType.CONSISTENCY_CHECK_COMPLETED: EventCategory.VERIFICATION,
    EventType.RULES_VALIDATED: EventCategory.VERIFICATION,
    
    # Compliance
    EventType.POLICY_COMPILED: EventCategory.COMPLIANCE,
    EventType.POLICY_EVALUATED: EventCategory.COMPLIANCE,
    EventType.POLICY_ENFORCED: EventCategory.COMPLIANCE,
    EventType.COMPLIANCE_VIOLATION: EventCategory.COMPLIANCE,
    
    # Integrity
    EventType.DATA_SIGNED: EventCategory.INTEGRITY,
    EventType.SIGNATURE_VERIFIED: EventCategory.INTEGRITY,
    EventType.INTEGRITY_CHECK_PASSED: EventCategory.INTEGRITY,
    EventType.INTEGRITY_CHECK_FAILED: EventCategory.INTEGRITY,
    
    # System
    EventType.SERVICE_STARTED: EventCategory.SYSTEM,
    EventType.SERVICE_STOPPED: EventCategory.SYSTEM,
    EventType.SERVICE_HEALTH_CHECK: EventCategory.SYSTEM,
    EventType.SYSTEM_ERROR: EventCategory.SYSTEM,
    EventType.PERFORMANCE_ALERT: EventCategory.SYSTEM,
    
    # Audit
    EventType.AUDIT_LOG_CREATED: EventCategory.AUDIT,
    EventType.SECURITY_EVENT: EventCategory.AUDIT,
    EventType.ACCESS_GRANTED: EventCategory.AUDIT,
    EventType.ACCESS_DENIED: EventCategory.AUDIT,
    
    # Workflow
    EventType.WORKFLOW_STARTED: EventCategory.WORKFLOW,
    EventType.WORKFLOW_COMPLETED: EventCategory.WORKFLOW,
    EventType.WORKFLOW_FAILED: EventCategory.WORKFLOW,
    EventType.TASK_ASSIGNED: EventCategory.WORKFLOW,
    EventType.TASK_COMPLETED: EventCategory.WORKFLOW,
}


# Event type to severity mapping
EVENT_SEVERITIES = {
    # Info level events
    EventType.USER_AUTHENTICATED: EventSeverity.INFO,
    EventType.USER_CREATED: EventSeverity.INFO,
    EventType.PRINCIPLE_CREATED: EventSeverity.INFO,
    EventType.PRINCIPLE_VOTED: EventSeverity.INFO,
    EventType.GOVERNANCE_SYNTHESIZED: EventSeverity.INFO,
    EventType.POLICY_GENERATED: EventSeverity.INFO,
    EventType.POLICY_VERIFIED: EventSeverity.INFO,
    EventType.POLICY_COMPILED: EventSeverity.INFO,
    EventType.DATA_SIGNED: EventSeverity.INFO,
    EventType.SIGNATURE_VERIFIED: EventSeverity.INFO,
    EventType.SERVICE_STARTED: EventSeverity.INFO,
    EventType.SERVICE_HEALTH_CHECK: EventSeverity.INFO,
    EventType.WORKFLOW_STARTED: EventSeverity.INFO,
    EventType.WORKFLOW_COMPLETED: EventSeverity.INFO,
    
    # Warning level events
    EventType.TOKEN_EXPIRED: EventSeverity.WARNING,
    EventType.PRINCIPLE_REJECTED: EventSeverity.WARNING,
    EventType.POLICY_DEACTIVATED: EventSeverity.WARNING,
    EventType.PERFORMANCE_ALERT: EventSeverity.WARNING,
    EventType.ACCESS_DENIED: EventSeverity.WARNING,
    
    # Error level events
    EventType.USER_LOGIN_FAILED: EventSeverity.ERROR,
    EventType.POLICY_VERIFICATION_FAILED: EventSeverity.ERROR,
    EventType.COMPLIANCE_VIOLATION: EventSeverity.ERROR,
    EventType.INTEGRITY_CHECK_FAILED: EventSeverity.ERROR,
    EventType.WORKFLOW_FAILED: EventSeverity.ERROR,
    EventType.SYSTEM_ERROR: EventSeverity.ERROR,
    
    # Critical level events
    EventType.SERVICE_STOPPED: EventSeverity.CRITICAL,
    EventType.SECURITY_EVENT: EventSeverity.CRITICAL,
}


def get_event_category(event_type: EventType) -> EventCategory:
    """Get category for an event type."""
    return EVENT_CATEGORIES.get(event_type, EventCategory.SYSTEM)


def get_event_severity(event_type: EventType) -> EventSeverity:
    """Get severity for an event type."""
    return EVENT_SEVERITIES.get(event_type, EventSeverity.INFO)


def is_critical_event(event_type: EventType) -> bool:
    """Check if event type is critical."""
    return get_event_severity(event_type) == EventSeverity.CRITICAL


def is_error_event(event_type: EventType) -> bool:
    """Check if event type indicates an error."""
    severity = get_event_severity(event_type)
    return severity in [EventSeverity.ERROR, EventSeverity.CRITICAL]
