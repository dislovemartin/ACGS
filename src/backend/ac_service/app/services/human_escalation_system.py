"""
Human Escalation System for ACGS-PGP

This module implements smart escalation logic for complex conflicts that cannot
be automatically resolved, with 5-minute escalation target.

Key Features:
- Automatic escalation triggers for complex conflicts
- Role-based escalation routing
- Real-time notification system
- Integration with Constitutional Council workflows
- Escalation timeout monitoring
- Performance tracking and analytics
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import ACConflictResolution, User
from ..schemas import ACConflictResolutionUpdate
from .automated_resolution_engine import ResolutionResult, ResolutionStatus
from .intelligent_conflict_detector import ConflictDetectionResult, ConflictSeverity

logger = logging.getLogger(__name__)


class EscalationLevel(Enum):
    """Escalation levels for conflict resolution."""
    AUTOMATED = "automated"
    TECHNICAL_REVIEW = "technical_review"
    POLICY_MANAGER = "policy_manager"
    CONSTITUTIONAL_COUNCIL = "constitutional_council"
    EMERGENCY_RESPONSE = "emergency_response"


class EscalationReason(Enum):
    """Reasons for escalation."""
    LOW_CONFIDENCE = "low_confidence"
    STRATEGY_FAILURE = "strategy_failure"
    VALIDATION_FAILURE = "validation_failure"
    COMPLEXITY_THRESHOLD = "complexity_threshold"
    CRITICAL_SEVERITY = "critical_severity"
    TIMEOUT_EXCEEDED = "timeout_exceeded"
    STAKEHOLDER_DISPUTE = "stakeholder_dispute"
    CONSTITUTIONAL_VIOLATION = "constitutional_violation"


class NotificationChannel(Enum):
    """Available notification channels."""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    DATABASE = "database"
    REAL_TIME = "real_time"


@dataclass
class EscalationRule:
    """Rule for determining escalation requirements."""
    rule_id: str
    trigger_conditions: Dict[str, Any]
    target_level: EscalationLevel
    timeout_minutes: int
    required_roles: List[str]
    notification_channels: List[NotificationChannel]
    priority_boost: float


@dataclass
class EscalationRequest:
    """Request for human escalation."""
    conflict_id: int
    escalation_level: EscalationLevel
    escalation_reason: EscalationReason
    urgency_score: float
    required_roles: List[str]
    context_data: Dict[str, Any]
    timeout_deadline: datetime
    notification_channels: List[NotificationChannel]
    escalation_metadata: Dict[str, Any]


@dataclass
class EscalationResponse:
    """Response from escalation system."""
    success: bool
    escalation_id: str
    assigned_users: List[int]
    notification_results: Dict[str, bool]
    estimated_response_time: timedelta
    escalation_metadata: Dict[str, Any]


class HumanEscalationSystem:
    """
    Smart escalation system for complex conflicts requiring human intervention.
    
    Implements automatic escalation triggers, role-based routing, and real-time
    notifications to achieve 5-minute escalation target.
    """
    
    def __init__(self):
        """Initialize the escalation system."""
        self.escalation_timeout = timedelta(minutes=5)  # 5-minute target
        self.max_auto_attempts = 3  # Maximum automated resolution attempts
        
        # Escalation rules configuration
        self.escalation_rules = self._initialize_escalation_rules()
        
        # Performance metrics
        self.escalation_stats = {
            "total_escalations": 0,
            "successful_escalations": 0,
            "average_escalation_time": 0.0,
            "timeout_violations": 0,
            "escalation_success_rate": 0.0
        }
        
        # Active escalations tracking
        self.active_escalations: Dict[int, EscalationRequest] = {}

    def _initialize_escalation_rules(self) -> List[EscalationRule]:
        """Initialize escalation rules configuration."""
        return [
            # Critical severity immediate escalation
            EscalationRule(
                rule_id="critical_severity_immediate",
                trigger_conditions={
                    "severity": "critical",
                    "confidence_threshold": 0.9
                },
                target_level=EscalationLevel.EMERGENCY_RESPONSE,
                timeout_minutes=2,
                required_roles=["admin", "constitutional_council"],
                notification_channels=[NotificationChannel.REAL_TIME, NotificationChannel.EMAIL],
                priority_boost=1.0
            ),
            
            # High severity with low confidence
            EscalationRule(
                rule_id="high_severity_low_confidence",
                trigger_conditions={
                    "severity": "high",
                    "confidence_threshold": 0.7
                },
                target_level=EscalationLevel.CONSTITUTIONAL_COUNCIL,
                timeout_minutes=5,
                required_roles=["constitutional_council", "policy_manager"],
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
                priority_boost=0.8
            ),
            
            # Strategy failure escalation
            EscalationRule(
                rule_id="strategy_failure_escalation",
                trigger_conditions={
                    "failed_attempts": 2,
                    "strategy_failure": True
                },
                target_level=EscalationLevel.TECHNICAL_REVIEW,
                timeout_minutes=10,
                required_roles=["policy_manager", "admin"],
                notification_channels=[NotificationChannel.EMAIL],
                priority_boost=0.6
            ),
            
            # Complex multi-principle conflicts
            EscalationRule(
                rule_id="complex_multi_principle",
                trigger_conditions={
                    "principle_count": 3,
                    "complexity_score": 0.8
                },
                target_level=EscalationLevel.POLICY_MANAGER,
                timeout_minutes=15,
                required_roles=["policy_manager"],
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.DATABASE],
                priority_boost=0.4
            ),
            
            # Stakeholder dispute escalation
            EscalationRule(
                rule_id="stakeholder_dispute",
                trigger_conditions={
                    "conflict_type": "stakeholder_conflict",
                    "stakeholder_count": 2
                },
                target_level=EscalationLevel.CONSTITUTIONAL_COUNCIL,
                timeout_minutes=30,
                required_roles=["constitutional_council"],
                notification_channels=[NotificationChannel.EMAIL],
                priority_boost=0.5
            )
        ]

    async def evaluate_escalation_need(
        self,
        db: AsyncSession,
        conflict: ACConflictResolution,
        resolution_result: Optional[ResolutionResult] = None,
        detection_result: Optional[ConflictDetectionResult] = None
    ) -> Optional[EscalationRequest]:
        """
        Evaluate if a conflict requires human escalation.
        
        Args:
            db: Database session
            conflict: The conflict to evaluate
            resolution_result: Result of automated resolution attempt
            detection_result: Original detection result
            
        Returns:
            EscalationRequest if escalation is needed, None otherwise
        """
        try:
            # Check each escalation rule
            for rule in self.escalation_rules:
                if await self._check_escalation_rule(
                    rule, conflict, resolution_result, detection_result
                ):
                    logger.info(f"Escalation triggered by rule: {rule.rule_id}")
                    
                    # Create escalation request
                    escalation_request = await self._create_escalation_request(
                        db, conflict, rule, resolution_result, detection_result
                    )
                    
                    return escalation_request
            
            # No escalation needed
            return None
            
        except Exception as e:
            logger.error(f"Escalation evaluation failed: {e}")
            # In case of error, escalate for safety
            return await self._create_emergency_escalation(
                db, conflict, f"Evaluation error: {str(e)}"
            )

    async def _check_escalation_rule(
        self,
        rule: EscalationRule,
        conflict: ACConflictResolution,
        resolution_result: Optional[ResolutionResult],
        detection_result: Optional[ConflictDetectionResult]
    ) -> bool:
        """Check if an escalation rule is triggered."""
        conditions = rule.trigger_conditions
        
        # Check severity condition
        if "severity" in conditions:
            if conflict.severity != conditions["severity"]:
                return False
        
        # Check confidence threshold
        if "confidence_threshold" in conditions and resolution_result:
            if resolution_result.confidence_score >= conditions["confidence_threshold"]:
                return False
        
        # Check failed attempts
        if "failed_attempts" in conditions:
            # This would be tracked in conflict metadata
            failed_attempts = conflict.resolution_details.get("failed_attempts", 0) if conflict.resolution_details else 0
            if failed_attempts < conditions["failed_attempts"]:
                return False
        
        # Check strategy failure
        if "strategy_failure" in conditions and resolution_result:
            if resolution_result.success:
                return False
        
        # Check principle count
        if "principle_count" in conditions:
            if len(conflict.principle_ids) < conditions["principle_count"]:
                return False
        
        # Check complexity score
        if "complexity_score" in conditions and detection_result:
            # Use priority score as complexity indicator
            if detection_result.priority_score < conditions["complexity_score"]:
                return False
        
        # Check conflict type
        if "conflict_type" in conditions and detection_result:
            if detection_result.conflict_type.value != conditions["conflict_type"]:
                return False
        
        # Check stakeholder count
        if "stakeholder_count" in conditions:
            # This would be derived from principle analysis
            stakeholder_count = len(set(conflict.principle_ids))  # Simplified
            if stakeholder_count < conditions["stakeholder_count"]:
                return False
        
        return True

    async def _create_escalation_request(
        self,
        db: AsyncSession,
        conflict: ACConflictResolution,
        rule: EscalationRule,
        resolution_result: Optional[ResolutionResult],
        detection_result: Optional[ConflictDetectionResult]
    ) -> EscalationRequest:
        """Create an escalation request based on triggered rule."""
        # Calculate urgency score
        urgency_score = await self._calculate_urgency_score(
            conflict, resolution_result, detection_result, rule
        )
        
        # Determine escalation reason
        escalation_reason = self._determine_escalation_reason(
            resolution_result, detection_result, rule
        )
        
        # Set timeout deadline
        timeout_deadline = datetime.now() + timedelta(minutes=rule.timeout_minutes)
        
        # Prepare context data
        context_data = {
            "conflict_id": conflict.id,
            "conflict_type": conflict.conflict_type,
            "severity": conflict.severity,
            "principle_ids": conflict.principle_ids,
            "rule_triggered": rule.rule_id,
            "resolution_attempts": conflict.resolution_details.get("attempts", 0) if conflict.resolution_details else 0
        }
        
        if resolution_result:
            context_data.update({
                "last_strategy": resolution_result.strategy_used.value,
                "last_confidence": resolution_result.confidence_score,
                "last_success": resolution_result.success
            })
        
        if detection_result:
            context_data.update({
                "detection_confidence": detection_result.confidence_score,
                "priority_score": detection_result.priority_score
            })
        
        return EscalationRequest(
            conflict_id=conflict.id,
            escalation_level=rule.target_level,
            escalation_reason=escalation_reason,
            urgency_score=urgency_score,
            required_roles=rule.required_roles,
            context_data=context_data,
            timeout_deadline=timeout_deadline,
            notification_channels=rule.notification_channels,
            escalation_metadata={
                "rule_id": rule.rule_id,
                "created_at": datetime.now().isoformat(),
                "priority_boost": rule.priority_boost
            }
        )

    async def _create_emergency_escalation(
        self,
        db: AsyncSession,
        conflict: ACConflictResolution,
        reason: str
    ) -> EscalationRequest:
        """Create emergency escalation for critical situations."""
        return EscalationRequest(
            conflict_id=conflict.id,
            escalation_level=EscalationLevel.EMERGENCY_RESPONSE,
            escalation_reason=EscalationReason.CONSTITUTIONAL_VIOLATION,
            urgency_score=1.0,
            required_roles=["admin", "constitutional_council"],
            context_data={
                "conflict_id": conflict.id,
                "emergency_reason": reason,
                "severity": conflict.severity
            },
            timeout_deadline=datetime.now() + timedelta(minutes=2),
            notification_channels=[NotificationChannel.REAL_TIME, NotificationChannel.EMAIL],
            escalation_metadata={
                "rule_id": "emergency_escalation",
                "created_at": datetime.now().isoformat(),
                "priority_boost": 1.0,
                "emergency": True
            }
        )
