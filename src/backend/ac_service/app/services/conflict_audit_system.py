"""
Conflict Audit System for ACGS-PGP

This module implements comprehensive audit trail and monitoring for all
conflict resolution decisions with full traceability and cryptographic integrity.

Key Features:
- Complete traceability of all conflict resolution decisions
- Cryptographic integrity for audit logs
- Real-time metrics collection
- Performance monitoring and analytics
- Integration with PGP assurance
- Compliance reporting and validation
"""

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from shared.models import ACConflictResolution, User
from .intelligent_conflict_detector import ConflictDetectionResult
from .automated_resolution_engine import ResolutionResult
from .human_escalation_system import EscalationRequest, EscalationResponse

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events."""
    CONFLICT_DETECTED = "conflict_detected"
    RESOLUTION_ATTEMPTED = "resolution_attempted"
    RESOLUTION_SUCCEEDED = "resolution_succeeded"
    RESOLUTION_FAILED = "resolution_failed"
    ESCALATION_TRIGGERED = "escalation_triggered"
    HUMAN_INTERVENTION = "human_intervention"
    VALIDATION_PERFORMED = "validation_performed"
    STATUS_CHANGED = "status_changed"
    PATCH_GENERATED = "patch_generated"
    METRICS_COLLECTED = "metrics_collected"


class AuditLevel(Enum):
    """Audit detail levels."""
    MINIMAL = "minimal"
    STANDARD = "standard"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"


@dataclass
class AuditEntry:
    """Individual audit log entry."""
    entry_id: str
    timestamp: datetime
    event_type: AuditEventType
    conflict_id: int
    user_id: Optional[int]
    event_data: Dict[str, Any]
    integrity_hash: str
    previous_hash: Optional[str]
    audit_level: AuditLevel
    metadata: Dict[str, Any]


@dataclass
class ConflictResolutionTrace:
    """Complete trace of conflict resolution process."""
    conflict_id: int
    detection_trace: Optional[Dict[str, Any]]
    resolution_attempts: List[Dict[str, Any]]
    escalation_trace: Optional[Dict[str, Any]]
    final_outcome: Dict[str, Any]
    total_processing_time: float
    audit_entries: List[AuditEntry]
    integrity_verified: bool


@dataclass
class PerformanceMetrics:
    """Performance metrics for conflict resolution system."""
    detection_accuracy: float
    auto_resolution_rate: float
    average_resolution_time: float
    escalation_rate: float
    human_intervention_rate: float
    system_availability: float
    error_rate: float
    throughput: float
    timestamp: datetime


class ConflictAuditSystem:
    """
    Comprehensive audit system for conflict resolution with cryptographic integrity.
    
    Provides complete traceability, performance monitoring, and compliance
    reporting for all conflict resolution activities.
    """
    
    def __init__(self):
        """Initialize the audit system."""
        self.audit_chain: List[AuditEntry] = []
        self.last_hash: Optional[str] = None
        
        # Performance tracking
        self.metrics_history: List[PerformanceMetrics] = []
        self.current_metrics = {
            "conflicts_detected": 0,
            "resolutions_attempted": 0,
            "resolutions_succeeded": 0,
            "escalations_triggered": 0,
            "total_processing_time": 0.0,
            "errors_encountered": 0
        }
        
        # Audit configuration
        self.default_audit_level = AuditLevel.STANDARD
        self.retention_period = timedelta(days=365)  # 1 year retention
        self.integrity_check_interval = timedelta(hours=1)

    async def log_conflict_detection(
        self,
        db: AsyncSession,
        conflict: ACConflictResolution,
        detection_result: ConflictDetectionResult,
        user_id: Optional[int] = None,
        audit_level: AuditLevel = None
    ) -> AuditEntry:
        """Log conflict detection event."""
        event_data = {
            "conflict_type": detection_result.conflict_type.value,
            "severity": detection_result.severity.value,
            "confidence_score": detection_result.confidence_score,
            "priority_score": detection_result.priority_score,
            "principle_ids": detection_result.principle_ids,
            "detection_method": detection_result.detection_metadata.get("method", "unknown"),
            "recommended_strategy": detection_result.recommended_strategy
        }
        
        audit_entry = await self._create_audit_entry(
            event_type=AuditEventType.CONFLICT_DETECTED,
            conflict_id=conflict.id,
            user_id=user_id,
            event_data=event_data,
            audit_level=audit_level or self.default_audit_level
        )
        
        await self._store_audit_entry(db, audit_entry)
        self.current_metrics["conflicts_detected"] += 1
        
        return audit_entry

    async def log_resolution_attempt(
        self,
        db: AsyncSession,
        conflict: ACConflictResolution,
        resolution_result: ResolutionResult,
        user_id: Optional[int] = None,
        audit_level: AuditLevel = None
    ) -> AuditEntry:
        """Log resolution attempt event."""
        event_data = {
            "strategy_used": resolution_result.strategy_used.value,
            "success": resolution_result.success,
            "confidence_score": resolution_result.confidence_score,
            "validation_passed": resolution_result.validation_passed,
            "processing_time": resolution_result.processing_time,
            "escalation_required": resolution_result.escalation_required,
            "escalation_reason": resolution_result.escalation_reason,
            "resolution_details": resolution_result.resolution_details
        }
        
        event_type = (AuditEventType.RESOLUTION_SUCCEEDED if resolution_result.success 
                     else AuditEventType.RESOLUTION_FAILED)
        
        audit_entry = await self._create_audit_entry(
            event_type=event_type,
            conflict_id=conflict.id,
            user_id=user_id,
            event_data=event_data,
            audit_level=audit_level or self.default_audit_level
        )
        
        await self._store_audit_entry(db, audit_entry)
        self.current_metrics["resolutions_attempted"] += 1
        
        if resolution_result.success:
            self.current_metrics["resolutions_succeeded"] += 1
        
        self.current_metrics["total_processing_time"] += resolution_result.processing_time
        
        return audit_entry

    async def log_escalation_event(
        self,
        db: AsyncSession,
        conflict: ACConflictResolution,
        escalation_request: EscalationRequest,
        escalation_response: Optional[EscalationResponse] = None,
        user_id: Optional[int] = None,
        audit_level: AuditLevel = None
    ) -> AuditEntry:
        """Log escalation event."""
        event_data = {
            "escalation_level": escalation_request.escalation_level.value,
            "escalation_reason": escalation_request.escalation_reason.value,
            "urgency_score": escalation_request.urgency_score,
            "required_roles": escalation_request.required_roles,
            "timeout_deadline": escalation_request.timeout_deadline.isoformat(),
            "notification_channels": [ch.value for ch in escalation_request.notification_channels]
        }
        
        if escalation_response:
            event_data.update({
                "escalation_success": escalation_response.success,
                "assigned_users": escalation_response.assigned_users,
                "estimated_response_time": escalation_response.estimated_response_time.total_seconds()
            })
        
        audit_entry = await self._create_audit_entry(
            event_type=AuditEventType.ESCALATION_TRIGGERED,
            conflict_id=conflict.id,
            user_id=user_id,
            event_data=event_data,
            audit_level=audit_level or self.default_audit_level
        )
        
        await self._store_audit_entry(db, audit_entry)
        self.current_metrics["escalations_triggered"] += 1
        
        return audit_entry

    async def log_human_intervention(
        self,
        db: AsyncSession,
        conflict: ACConflictResolution,
        intervention_data: Dict[str, Any],
        user_id: int,
        audit_level: AuditLevel = None
    ) -> AuditEntry:
        """Log human intervention event."""
        event_data = {
            "intervention_type": intervention_data.get("type", "manual_review"),
            "decision": intervention_data.get("decision"),
            "reasoning": intervention_data.get("reasoning"),
            "override_automated": intervention_data.get("override_automated", False),
            "additional_context": intervention_data.get("context", {})
        }
        
        audit_entry = await self._create_audit_entry(
            event_type=AuditEventType.HUMAN_INTERVENTION,
            conflict_id=conflict.id,
            user_id=user_id,
            event_data=event_data,
            audit_level=audit_level or self.default_audit_level
        )
        
        await self._store_audit_entry(db, audit_entry)
        
        return audit_entry

    async def log_status_change(
        self,
        db: AsyncSession,
        conflict: ACConflictResolution,
        old_status: str,
        new_status: str,
        user_id: Optional[int] = None,
        audit_level: AuditLevel = None
    ) -> AuditEntry:
        """Log conflict status change event."""
        event_data = {
            "old_status": old_status,
            "new_status": new_status,
            "status_change_reason": "automated_resolution" if not user_id else "human_intervention"
        }
        
        audit_entry = await self._create_audit_entry(
            event_type=AuditEventType.STATUS_CHANGED,
            conflict_id=conflict.id,
            user_id=user_id,
            event_data=event_data,
            audit_level=audit_level or self.default_audit_level
        )
        
        await self._store_audit_entry(db, audit_entry)
        
        return audit_entry

    async def generate_conflict_trace(
        self,
        db: AsyncSession,
        conflict_id: int
    ) -> ConflictResolutionTrace:
        """Generate complete trace for a conflict resolution process."""
        try:
            # Get all audit entries for this conflict
            audit_entries = await self._get_conflict_audit_entries(db, conflict_id)
            
            # Organize entries by type
            detection_entries = [e for e in audit_entries if e.event_type == AuditEventType.CONFLICT_DETECTED]
            resolution_entries = [e for e in audit_entries if e.event_type in [
                AuditEventType.RESOLUTION_ATTEMPTED, 
                AuditEventType.RESOLUTION_SUCCEEDED, 
                AuditEventType.RESOLUTION_FAILED
            ]]
            escalation_entries = [e for e in audit_entries if e.event_type == AuditEventType.ESCALATION_TRIGGERED]
            
            # Build trace components
            detection_trace = detection_entries[0].event_data if detection_entries else None
            
            resolution_attempts = []
            for entry in resolution_entries:
                resolution_attempts.append({
                    "timestamp": entry.timestamp.isoformat(),
                    "strategy": entry.event_data.get("strategy_used"),
                    "success": entry.event_data.get("success"),
                    "confidence": entry.event_data.get("confidence_score"),
                    "processing_time": entry.event_data.get("processing_time")
                })
            
            escalation_trace = escalation_entries[0].event_data if escalation_entries else None
            
            # Determine final outcome
            final_outcome = {}
            if resolution_attempts:
                last_attempt = resolution_attempts[-1]
                final_outcome = {
                    "resolved": last_attempt.get("success", False),
                    "final_strategy": last_attempt.get("strategy"),
                    "total_attempts": len(resolution_attempts),
                    "escalated": bool(escalation_trace)
                }
            
            # Calculate total processing time
            total_time = sum(
                attempt.get("processing_time", 0) 
                for attempt in resolution_attempts
            )
            
            # Verify audit chain integrity
            integrity_verified = await self._verify_audit_chain_integrity(audit_entries)
            
            return ConflictResolutionTrace(
                conflict_id=conflict_id,
                detection_trace=detection_trace,
                resolution_attempts=resolution_attempts,
                escalation_trace=escalation_trace,
                final_outcome=final_outcome,
                total_processing_time=total_time,
                audit_entries=audit_entries,
                integrity_verified=integrity_verified
            )
            
        except Exception as e:
            logger.error(f"Failed to generate conflict trace for {conflict_id}: {e}")
            raise

    async def collect_performance_metrics(self, db: AsyncSession) -> PerformanceMetrics:
        """Collect current performance metrics."""
        try:
            # Calculate rates and averages
            total_attempts = self.current_metrics["resolutions_attempted"]
            total_successes = self.current_metrics["resolutions_succeeded"]
            total_escalations = self.current_metrics["escalations_triggered"]
            total_detections = self.current_metrics["conflicts_detected"]
            
            auto_resolution_rate = (total_successes / max(total_attempts, 1)) * 100
            escalation_rate = (total_escalations / max(total_detections, 1)) * 100
            
            avg_resolution_time = (
                self.current_metrics["total_processing_time"] / max(total_attempts, 1)
            )
            
            # Calculate system availability (simplified)
            error_rate = (self.current_metrics["errors_encountered"] / max(total_attempts, 1)) * 100
            system_availability = max(0, 100 - error_rate)
            
            # Calculate throughput (conflicts per hour)
            current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
            recent_conflicts = await self._count_recent_conflicts(db, current_hour)
            throughput = recent_conflicts
            
            metrics = PerformanceMetrics(
                detection_accuracy=85.0,  # This would be calculated from validation data
                auto_resolution_rate=auto_resolution_rate,
                average_resolution_time=avg_resolution_time,
                escalation_rate=escalation_rate,
                human_intervention_rate=escalation_rate,  # Simplified
                system_availability=system_availability,
                error_rate=error_rate,
                throughput=throughput,
                timestamp=datetime.now()
            )
            
            # Store metrics
            self.metrics_history.append(metrics)
            
            # Log metrics collection
            await self._create_audit_entry(
                event_type=AuditEventType.METRICS_COLLECTED,
                conflict_id=0,  # System-level event
                user_id=None,
                event_data=asdict(metrics),
                audit_level=AuditLevel.MINIMAL
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect performance metrics: {e}")
            raise
