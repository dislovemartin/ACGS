"""
violation_escalation_service.py

Constitutional Violation Escalation Service for automatic escalation workflows.
Implements escalation rules, notification dispatch, and integration with
Constitutional Council workflows for critical violations.

Classes:
    ViolationEscalationService: Main service for violation escalation
    EscalationLevel: Enumeration of escalation levels
    EscalationRule: Configuration for escalation rules
    EscalationResult: Result structure for escalation operations
"""

import asyncio
import logging
import time
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload

from shared.models import (
    ConstitutionalViolation, ViolationAlert, ViolationEscalation,
    User, ACAmendment
)
from shared.database import get_async_db

# Import notification services
from src.backend.gs_service.app.services.stakeholder_engagement import (
    StakeholderNotificationService,
    NotificationChannel,
    StakeholderRole
)

# Import Constitutional Council integration
from src.backend.gs_service.app.core.constitutional_council_scalability import (
    ConstitutionalCouncilScalabilityFramework,
    CoEvolutionMode
)

logger = logging.getLogger(__name__)


class EscalationLevel(Enum):
    """Escalation levels for violations."""
    POLICY_MANAGER = "policy_manager"
    CONSTITUTIONAL_COUNCIL = "constitutional_council"
    EMERGENCY_RESPONSE = "emergency_response"
    TECHNICAL_REVIEW = "technical_review"
    STAKEHOLDER_REVIEW = "stakeholder_review"


class EscalationTrigger(Enum):
    """Triggers for escalation."""
    SEVERITY_THRESHOLD = "severity_threshold"
    VIOLATION_COUNT = "violation_count"
    TIME_THRESHOLD = "time_threshold"
    MANUAL_ESCALATION = "manual_escalation"
    SYSTEM_FAILURE = "system_failure"


@dataclass
class EscalationRule:
    """Configuration for escalation rules."""
    rule_id: str
    trigger_type: EscalationTrigger
    trigger_conditions: Dict[str, Any]
    target_level: EscalationLevel
    timeout_minutes: int
    required_roles: List[str]
    notification_channels: List[NotificationChannel]
    priority_boost: float
    auto_assign: bool = True
    description: str = ""


@dataclass
class EscalationResult:
    """Result of escalation operation."""
    escalation_id: str
    escalated: bool
    escalation_level: EscalationLevel
    assigned_to: Optional[str]
    notification_sent: bool
    response_time_target: int  # minutes
    escalation_metadata: Dict[str, Any]
    error_message: Optional[str] = None


class ViolationEscalationService:
    """
    Constitutional Violation Escalation Service.
    
    Provides automatic escalation workflows for critical violations with
    integration to Constitutional Council and stakeholder notification systems.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the violation escalation service.
        
        Args:
            config: Configuration dictionary for escalation settings
        """
        self.config = config or self._get_default_config()
        
        # Initialize services
        self.notification_service = StakeholderNotificationService()
        self.council_framework = ConstitutionalCouncilScalabilityFramework()
        
        # Escalation rules
        self.escalation_rules = self._initialize_escalation_rules()
        
        # Escalation state
        self.active_escalations: Dict[str, ViolationEscalation] = {}
        self.escalation_queue: List[str] = []
        
        logger.info("Violation Escalation Service initialized")
    
    async def evaluate_escalation(
        self,
        violation: ConstitutionalViolation,
        db: AsyncSession
    ) -> Optional[EscalationResult]:
        """
        Evaluate if a violation requires escalation.
        
        Args:
            violation: Constitutional violation to evaluate
            db: Database session
            
        Returns:
            EscalationResult if escalation is required, None otherwise
        """
        try:
            # Check if already escalated
            if violation.escalated:
                logger.debug(f"Violation {violation.id} already escalated")
                return None
            
            # Evaluate escalation rules
            for rule in self.escalation_rules:
                if await self._evaluate_rule(rule, violation, db):
                    logger.info(f"Escalation rule {rule.rule_id} triggered for violation {violation.id}")
                    return await self._execute_escalation(rule, violation, db)
            
            logger.debug(f"No escalation rules triggered for violation {violation.id}")
            return None
            
        except Exception as e:
            logger.error(f"Error evaluating escalation for violation {violation.id}: {e}")
            return EscalationResult(
                escalation_id="",
                escalated=False,
                escalation_level=EscalationLevel.TECHNICAL_REVIEW,
                assigned_to=None,
                notification_sent=False,
                response_time_target=60,
                escalation_metadata={"error": str(e)},
                error_message=str(e)
            )
    
    async def escalate_violation(
        self,
        violation: ConstitutionalViolation,
        escalation_level: EscalationLevel,
        reason: str,
        escalated_by: Optional[User] = None,
        db: Optional[AsyncSession] = None
    ) -> EscalationResult:
        """
        Manually escalate a violation.
        
        Args:
            violation: Violation to escalate
            escalation_level: Target escalation level
            reason: Reason for escalation
            escalated_by: User who initiated escalation
            db: Database session
            
        Returns:
            EscalationResult with escalation details
        """
        if db is None:
            async for db_session in get_async_db():
                return await self.escalate_violation(
                    violation, escalation_level, reason, escalated_by, db_session
                )
        
        try:
            # Create escalation record
            escalation = ViolationEscalation(
                violation_id=violation.id,
                escalation_type="manual",
                escalation_level=escalation_level.value,
                escalation_reason=reason,
                escalated_by=escalated_by.id if escalated_by else None,
                trigger_conditions={"manual_escalation": True, "reason": reason},
                escalation_rules={"manual": True}
            )
            
            db.add(escalation)
            await db.flush()
            
            # Update violation
            violation.escalated = True
            violation.escalation_level = escalation_level.value
            violation.escalated_at = datetime.now(timezone.utc)
            violation.escalated_by = escalated_by.id if escalated_by else None
            
            # Assign to appropriate personnel
            assigned_user = await self._assign_escalation(escalation_level, db)
            if assigned_user:
                escalation.assigned_to = assigned_user.id
                escalation.assigned_role = assigned_user.role
            
            # Send notifications
            notification_sent = await self._send_escalation_notifications(
                escalation, violation, assigned_user
            )
            escalation.notification_sent = notification_sent
            
            await db.commit()
            
            # Add to active escalations
            self.active_escalations[str(escalation.id)] = escalation
            
            result = EscalationResult(
                escalation_id=str(escalation.id),
                escalated=True,
                escalation_level=escalation_level,
                assigned_to=assigned_user.username if assigned_user else None,
                notification_sent=notification_sent,
                response_time_target=self._get_response_time_target(escalation_level),
                escalation_metadata={
                    "escalation_type": "manual",
                    "escalated_by": escalated_by.username if escalated_by else "system",
                    "escalated_at": datetime.now(timezone.utc).isoformat()
                }
            )
            
            logger.info(f"Violation {violation.id} escalated to {escalation_level.value}")
            return result
            
        except Exception as e:
            logger.error(f"Error escalating violation {violation.id}: {e}")
            await db.rollback()
            return EscalationResult(
                escalation_id="",
                escalated=False,
                escalation_level=escalation_level,
                assigned_to=None,
                notification_sent=False,
                response_time_target=60,
                escalation_metadata={"error": str(e)},
                error_message=str(e)
            )
    
    async def check_escalation_timeouts(self, db: AsyncSession) -> List[str]:
        """
        Check for escalation timeouts and take appropriate action.
        
        Args:
            db: Database session
            
        Returns:
            List of escalation IDs that timed out
        """
        timed_out = []
        
        try:
            # Get active escalations
            result = await db.execute(
                select(ViolationEscalation).where(
                    and_(
                        ViolationEscalation.status == "pending",
                        ViolationEscalation.escalated_at < datetime.now(timezone.utc) - timedelta(hours=1)
                    )
                )
            )
            escalations = result.scalars().all()
            
            for escalation in escalations:
                # Check if timeout exceeded
                timeout_minutes = self._get_response_time_target(
                    EscalationLevel(escalation.escalation_level)
                )
                timeout_threshold = escalation.escalated_at + timedelta(minutes=timeout_minutes)
                
                if datetime.now(timezone.utc) > timeout_threshold:
                    # Handle timeout
                    await self._handle_escalation_timeout(escalation, db)
                    timed_out.append(str(escalation.id))
            
            if timed_out:
                await db.commit()
                logger.warning(f"Handled {len(timed_out)} escalation timeouts")
            
        except Exception as e:
            logger.error(f"Error checking escalation timeouts: {e}")
        
        return timed_out
    
    async def _evaluate_rule(
        self,
        rule: EscalationRule,
        violation: ConstitutionalViolation,
        db: AsyncSession
    ) -> bool:
        """Evaluate if an escalation rule should trigger."""
        try:
            conditions = rule.trigger_conditions
            
            if rule.trigger_type == EscalationTrigger.SEVERITY_THRESHOLD:
                required_severity = conditions.get("severity", "critical")
                return violation.severity == required_severity
            
            elif rule.trigger_type == EscalationTrigger.VIOLATION_COUNT:
                # Count recent violations of same type
                time_window = conditions.get("time_window_hours", 1)
                threshold_time = datetime.now(timezone.utc) - timedelta(hours=time_window)
                
                result = await db.execute(
                    select(func.count(ConstitutionalViolation.id)).where(
                        and_(
                            ConstitutionalViolation.violation_type == violation.violation_type,
                            ConstitutionalViolation.detected_at >= threshold_time
                        )
                    )
                )
                count = result.scalar()
                return count >= conditions.get("count_threshold", 5)
            
            elif rule.trigger_type == EscalationTrigger.TIME_THRESHOLD:
                # Check if violation has been unresolved for too long
                max_unresolved_minutes = conditions.get("max_unresolved_minutes", 30)
                threshold_time = datetime.now(timezone.utc) - timedelta(minutes=max_unresolved_minutes)
                return violation.detected_at <= threshold_time and violation.status != "resolved"
            
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating escalation rule {rule.rule_id}: {e}")
            return False

    async def _execute_escalation(
        self,
        rule: EscalationRule,
        violation: ConstitutionalViolation,
        db: AsyncSession
    ) -> EscalationResult:
        """Execute escalation based on triggered rule."""
        try:
            # Create escalation record
            escalation = ViolationEscalation(
                violation_id=violation.id,
                escalation_type="automatic",
                escalation_level=rule.target_level.value,
                escalation_reason=f"Triggered by rule: {rule.rule_id}",
                trigger_conditions=rule.trigger_conditions,
                escalation_rules={"rule_id": rule.rule_id, "rule_description": rule.description}
            )

            db.add(escalation)
            await db.flush()

            # Update violation
            violation.escalated = True
            violation.escalation_level = rule.target_level.value
            violation.escalated_at = datetime.now(timezone.utc)

            # Assign to appropriate personnel
            assigned_user = None
            if rule.auto_assign:
                assigned_user = await self._assign_escalation(rule.target_level, db)
                if assigned_user:
                    escalation.assigned_to = assigned_user.id
                    escalation.assigned_role = assigned_user.role

            # Send notifications
            notification_sent = await self._send_escalation_notifications(
                escalation, violation, assigned_user, rule.notification_channels
            )
            escalation.notification_sent = notification_sent

            await db.commit()

            # Add to active escalations
            self.active_escalations[str(escalation.id)] = escalation

            return EscalationResult(
                escalation_id=str(escalation.id),
                escalated=True,
                escalation_level=rule.target_level,
                assigned_to=assigned_user.username if assigned_user else None,
                notification_sent=notification_sent,
                response_time_target=rule.timeout_minutes,
                escalation_metadata={
                    "rule_id": rule.rule_id,
                    "trigger_type": rule.trigger_type.value,
                    "escalated_at": datetime.now(timezone.utc).isoformat()
                }
            )

        except Exception as e:
            logger.error(f"Error executing escalation: {e}")
            await db.rollback()
            return EscalationResult(
                escalation_id="",
                escalated=False,
                escalation_level=rule.target_level,
                assigned_to=None,
                notification_sent=False,
                response_time_target=rule.timeout_minutes,
                escalation_metadata={"error": str(e)},
                error_message=str(e)
            )

    async def _assign_escalation(
        self,
        escalation_level: EscalationLevel,
        db: AsyncSession
    ) -> Optional[User]:
        """Assign escalation to appropriate user based on level."""
        try:
            role_mapping = {
                EscalationLevel.POLICY_MANAGER: "policy_manager",
                EscalationLevel.CONSTITUTIONAL_COUNCIL: "constitutional_council",
                EscalationLevel.EMERGENCY_RESPONSE: "admin",
                EscalationLevel.TECHNICAL_REVIEW: "admin",
                EscalationLevel.STAKEHOLDER_REVIEW: "constitutional_council"
            }

            required_role = role_mapping.get(escalation_level)
            if not required_role:
                return None

            # Find available user with required role
            result = await db.execute(
                select(User).where(
                    and_(
                        User.role == required_role,
                        User.is_active == True
                    )
                ).limit(1)
            )

            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Error assigning escalation: {e}")
            return None

    async def _send_escalation_notifications(
        self,
        escalation: ViolationEscalation,
        violation: ConstitutionalViolation,
        assigned_user: Optional[User],
        channels: Optional[List[NotificationChannel]] = None
    ) -> bool:
        """Send escalation notifications."""
        try:
            if not assigned_user:
                logger.warning(f"No assigned user for escalation {escalation.id}")
                return False

            # Default notification channels
            if channels is None:
                channels = [NotificationChannel.EMAIL, NotificationChannel.WEBSOCKET]

            # Prepare notification content
            notification_content = {
                "subject": f"Constitutional Violation Escalation - {violation.violation_type}",
                "violation_id": str(violation.id),
                "escalation_id": str(escalation.id),
                "severity": violation.severity,
                "escalation_level": escalation.escalation_level,
                "description": violation.violation_description,
                "escalation_reason": escalation.escalation_reason,
                "assigned_to": assigned_user.username,
                "escalated_at": escalation.escalated_at.isoformat()
            }

            # Send notifications through each channel
            success = True
            for channel in channels:
                try:
                    if channel == NotificationChannel.EMAIL:
                        # Use stakeholder notification service for email
                        await self.notification_service._send_email_notification_direct(
                            recipient_email=assigned_user.email,
                            subject=notification_content["subject"],
                            content=notification_content
                        )
                    elif channel == NotificationChannel.WEBSOCKET:
                        # Send WebSocket notification (would integrate with existing WebSocket system)
                        await self._send_websocket_escalation_notification(notification_content)

                except Exception as e:
                    logger.error(f"Failed to send notification via {channel.value}: {e}")
                    success = False

            return success

        except Exception as e:
            logger.error(f"Error sending escalation notifications: {e}")
            return False

    async def _send_websocket_escalation_notification(self, content: Dict[str, Any]):
        """Send WebSocket notification for escalation."""
        # This would integrate with the existing WebSocket system
        # For now, just log the notification
        logger.info(f"WebSocket escalation notification: {content['subject']}")

    async def _handle_escalation_timeout(
        self,
        escalation: ViolationEscalation,
        db: AsyncSession
    ):
        """Handle escalation timeout by escalating to next level."""
        try:
            current_level = EscalationLevel(escalation.escalation_level)

            # Determine next escalation level
            next_level = self._get_next_escalation_level(current_level)
            if next_level:
                # Update escalation
                escalation.status = "timeout"

                # Create new escalation at higher level
                new_escalation = ViolationEscalation(
                    violation_id=escalation.violation_id,
                    escalation_type="timeout_escalation",
                    escalation_level=next_level.value,
                    escalation_reason=f"Timeout from {current_level.value} level",
                    trigger_conditions={"timeout_escalation": True, "previous_level": current_level.value}
                )

                db.add(new_escalation)

                # Assign and notify
                assigned_user = await self._assign_escalation(next_level, db)
                if assigned_user:
                    new_escalation.assigned_to = assigned_user.id
                    new_escalation.assigned_role = assigned_user.role

                logger.warning(f"Escalation {escalation.id} timed out, escalated to {next_level.value}")

        except Exception as e:
            logger.error(f"Error handling escalation timeout: {e}")

    def _get_next_escalation_level(self, current_level: EscalationLevel) -> Optional[EscalationLevel]:
        """Get next escalation level for timeout handling."""
        escalation_hierarchy = {
            EscalationLevel.TECHNICAL_REVIEW: EscalationLevel.POLICY_MANAGER,
            EscalationLevel.POLICY_MANAGER: EscalationLevel.CONSTITUTIONAL_COUNCIL,
            EscalationLevel.STAKEHOLDER_REVIEW: EscalationLevel.CONSTITUTIONAL_COUNCIL,
            EscalationLevel.CONSTITUTIONAL_COUNCIL: EscalationLevel.EMERGENCY_RESPONSE,
            EscalationLevel.EMERGENCY_RESPONSE: None  # Highest level
        }
        return escalation_hierarchy.get(current_level)

    def _get_response_time_target(self, escalation_level: EscalationLevel) -> int:
        """Get response time target in minutes for escalation level."""
        targets = {
            EscalationLevel.TECHNICAL_REVIEW: 60,
            EscalationLevel.POLICY_MANAGER: 30,
            EscalationLevel.STAKEHOLDER_REVIEW: 120,
            EscalationLevel.CONSTITUTIONAL_COUNCIL: 15,
            EscalationLevel.EMERGENCY_RESPONSE: 5
        }
        return targets.get(escalation_level, 30)

    def _initialize_escalation_rules(self) -> List[EscalationRule]:
        """Initialize escalation rules configuration."""
        return [
            # Critical severity immediate escalation
            EscalationRule(
                rule_id="critical_severity_immediate",
                trigger_type=EscalationTrigger.SEVERITY_THRESHOLD,
                trigger_conditions={"severity": "critical"},
                target_level=EscalationLevel.EMERGENCY_RESPONSE,
                timeout_minutes=5,
                required_roles=["admin"],
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.WEBSOCKET],
                priority_boost=1.0,
                description="Immediate escalation for critical violations"
            ),

            # High severity escalation
            EscalationRule(
                rule_id="high_severity_escalation",
                trigger_type=EscalationTrigger.SEVERITY_THRESHOLD,
                trigger_conditions={"severity": "high"},
                target_level=EscalationLevel.CONSTITUTIONAL_COUNCIL,
                timeout_minutes=15,
                required_roles=["constitutional_council"],
                notification_channels=[NotificationChannel.EMAIL],
                priority_boost=0.8,
                description="Escalation for high severity violations"
            ),

            # Violation count threshold
            EscalationRule(
                rule_id="violation_count_threshold",
                trigger_type=EscalationTrigger.VIOLATION_COUNT,
                trigger_conditions={"count_threshold": 5, "time_window_hours": 1},
                target_level=EscalationLevel.POLICY_MANAGER,
                timeout_minutes=30,
                required_roles=["policy_manager"],
                notification_channels=[NotificationChannel.EMAIL],
                priority_boost=0.6,
                description="Escalation when violation count exceeds threshold"
            ),

            # Time-based escalation
            EscalationRule(
                rule_id="unresolved_time_threshold",
                trigger_type=EscalationTrigger.TIME_THRESHOLD,
                trigger_conditions={"max_unresolved_minutes": 30},
                target_level=EscalationLevel.TECHNICAL_REVIEW,
                timeout_minutes=60,
                required_roles=["admin"],
                notification_channels=[NotificationChannel.EMAIL],
                priority_boost=0.4,
                description="Escalation for long-unresolved violations"
            )
        ]

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for escalation service."""
        return {
            "enable_automatic_escalation": True,
            "enable_timeout_escalation": True,
            "max_escalation_level": "emergency_response",
            "default_response_time_minutes": 30,
            "notification_retry_attempts": 3,
            "notification_retry_delay_seconds": 60
        }
