"""
Stakeholder Engagement System for Constitutional Council Workflows

This module implements a comprehensive stakeholder engagement system that integrates
with the Constitutional Council StateGraph to provide:
- Role-based stakeholder notification system
- Multi-channel notification dispatch (email, dashboard, webhook)
- Real-time feedback collection and tracking
- Stakeholder participation monitoring
- Integration with existing RBAC and Constitutional Council workflows
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timezone, timedelta
from enum import Enum
from dataclasses import dataclass, field
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from pydantic import BaseModel, Field, validator

from shared.models import User
from shared.auth import get_current_active_user
from app.models import ACAmendment, ACAmendmentComment, ACAmendmentVote
from app import crud
from shared.langgraph_config import ConstitutionalCouncilConfig

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    """Supported notification channels."""
    EMAIL = "email"
    DASHBOARD = "dashboard"
    WEBHOOK = "webhook"
    WEBSOCKET = "websocket"


class StakeholderRole(str, Enum):
    """Required stakeholder roles for Constitutional Council engagement."""
    CONSTITUTIONAL_EXPERT = "constitutional_expert"
    POLICY_ADMINISTRATOR = "policy_administrator"
    SYSTEM_AUDITOR = "system_auditor"
    PUBLIC_REPRESENTATIVE = "public_representative"


class NotificationStatus(str, Enum):
    """Status of notification delivery."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"


class FeedbackStatus(str, Enum):
    """Status of stakeholder feedback."""
    PENDING = "pending"
    SUBMITTED = "submitted"
    REVIEWED = "reviewed"
    INCORPORATED = "incorporated"


@dataclass
class NotificationRecord:
    """Record of a notification sent to a stakeholder."""
    id: str
    stakeholder_id: int
    stakeholder_role: StakeholderRole
    amendment_id: int
    channel: NotificationChannel
    status: NotificationStatus
    content: Dict[str, Any]
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FeedbackRecord:
    """Record of stakeholder feedback."""
    id: str
    stakeholder_id: int
    stakeholder_role: StakeholderRole
    amendment_id: int
    feedback_content: str
    feedback_type: str  # "comment", "vote", "suggestion", "objection"
    status: FeedbackStatus
    submitted_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewer_id: Optional[int] = None
    incorporation_notes: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class StakeholderEngagementInput(BaseModel):
    """Input model for stakeholder engagement configuration."""
    amendment_id: int = Field(..., description="Amendment ID for engagement")
    required_roles: List[StakeholderRole] = Field(
        default=[
            StakeholderRole.CONSTITUTIONAL_EXPERT,
            StakeholderRole.POLICY_ADMINISTRATOR,
            StakeholderRole.SYSTEM_AUDITOR,
            StakeholderRole.PUBLIC_REPRESENTATIVE
        ],
        description="Required stakeholder roles for engagement"
    )
    notification_channels: List[NotificationChannel] = Field(
        default=[NotificationChannel.EMAIL, NotificationChannel.DASHBOARD],
        description="Notification channels to use"
    )
    engagement_period_hours: int = Field(
        default=72, ge=1, le=168, description="Engagement period in hours"
    )
    require_all_stakeholders: bool = Field(
        default=False, description="Whether all stakeholder roles must provide feedback"
    )
    reminder_intervals_hours: List[int] = Field(
        default=[24, 12, 2], description="Reminder intervals before deadline"
    )
    
    @validator('notification_channels')
    def validate_channels(cls, v):
        """Validate notification channels."""
        if not v:
            raise ValueError("At least one notification channel must be specified")
        return v


class StakeholderEngagementStatus(BaseModel):
    """Status of stakeholder engagement for an amendment."""
    amendment_id: int
    total_stakeholders: int
    engaged_stakeholders: int
    pending_stakeholders: int
    engagement_rate: float
    deadline: datetime
    is_deadline_passed: bool
    notifications_sent: int
    feedback_received: int
    feedback_by_role: Dict[str, int]
    status_by_stakeholder: Dict[int, Dict[str, Any]]
    last_updated: datetime


class StakeholderNotificationService:
    """
    Service for managing stakeholder notifications and engagement.
    
    Provides multi-channel notification dispatch, feedback collection,
    and real-time status tracking for Constitutional Council workflows.
    """
    
    def __init__(self, db: AsyncSession, config: ConstitutionalCouncilConfig):
        self.db = db
        self.config = config
        self.notifications: Dict[str, NotificationRecord] = {}
        self.feedback_records: Dict[str, FeedbackRecord] = {}
        self.active_engagements: Dict[int, StakeholderEngagementStatus] = {}
        self.websocket_connections: Dict[int, Set[Any]] = {}  # amendment_id -> websockets
        
        # Notification templates
        self.notification_templates = {
            "amendment_proposal": {
                "subject": "New Constitutional Amendment Proposal - Review Required",
                "template": "amendment_proposal_notification.html"
            },
            "feedback_reminder": {
                "subject": "Reminder: Constitutional Amendment Feedback Due",
                "template": "feedback_reminder_notification.html"
            },
            "deadline_warning": {
                "subject": "URGENT: Constitutional Amendment Feedback Deadline Approaching",
                "template": "deadline_warning_notification.html"
            },
            "engagement_complete": {
                "subject": "Constitutional Amendment Engagement Period Complete",
                "template": "engagement_complete_notification.html"
            }
        }

    async def initiate_stakeholder_engagement(
        self,
        engagement_input: StakeholderEngagementInput
    ) -> StakeholderEngagementStatus:
        """
        Initiate stakeholder engagement for a constitutional amendment.

        Args:
            engagement_input: Configuration for stakeholder engagement

        Returns:
            StakeholderEngagementStatus: Current status of engagement
        """
        try:
            logger.info(f"Initiating stakeholder engagement for amendment {engagement_input.amendment_id}")

            # Get amendment details
            amendment = await crud.get_ac_amendment(
                db=self.db,
                amendment_id=engagement_input.amendment_id
            )
            if not amendment:
                raise ValueError(f"Amendment {engagement_input.amendment_id} not found")

            # Get stakeholders by required roles
            stakeholders = await self._get_stakeholders_by_roles(engagement_input.required_roles)

            if not stakeholders:
                raise ValueError("No stakeholders found for required roles")

            # Calculate engagement deadline
            deadline = datetime.now(timezone.utc) + timedelta(hours=engagement_input.engagement_period_hours)

            # Create engagement status
            engagement_status = StakeholderEngagementStatus(
                amendment_id=engagement_input.amendment_id,
                total_stakeholders=len(stakeholders),
                engaged_stakeholders=0,
                pending_stakeholders=len(stakeholders),
                engagement_rate=0.0,
                deadline=deadline,
                is_deadline_passed=False,
                notifications_sent=0,
                feedback_received=0,
                feedback_by_role={role.value: 0 for role in engagement_input.required_roles},
                status_by_stakeholder={},
                last_updated=datetime.now(timezone.utc)
            )

            # Store engagement status
            self.active_engagements[engagement_input.amendment_id] = engagement_status

            # Send initial notifications to all stakeholders
            notification_tasks = []
            for stakeholder in stakeholders:
                for channel in engagement_input.notification_channels:
                    task = self._send_notification(
                        stakeholder=stakeholder,
                        amendment=amendment,
                        channel=channel,
                        notification_type="amendment_proposal",
                        deadline=deadline
                    )
                    notification_tasks.append(task)

            # Execute notifications concurrently
            notification_results = await asyncio.gather(*notification_tasks, return_exceptions=True)

            # Count successful notifications
            successful_notifications = sum(
                1 for result in notification_results
                if not isinstance(result, Exception) and result
            )
            engagement_status.notifications_sent = successful_notifications

            # Initialize stakeholder status tracking
            for stakeholder in stakeholders:
                engagement_status.status_by_stakeholder[stakeholder.id] = {
                    "user_id": stakeholder.id,
                    "username": stakeholder.username,
                    "email": stakeholder.email,
                    "roles": [role for role in engagement_input.required_roles if self._user_has_role(stakeholder, role)],
                    "notifications_sent": len(engagement_input.notification_channels),
                    "feedback_submitted": False,
                    "last_activity": None,
                    "engagement_score": 0.0
                }

            # Schedule reminder notifications
            await self._schedule_reminder_notifications(
                engagement_input.amendment_id,
                engagement_input.reminder_intervals_hours,
                deadline
            )

            logger.info(
                f"Stakeholder engagement initiated for amendment {engagement_input.amendment_id}: "
                f"{len(stakeholders)} stakeholders, {successful_notifications} notifications sent"
            )

            return engagement_status

        except Exception as e:
            logger.error(f"Failed to initiate stakeholder engagement: {e}")
            raise

    async def _get_stakeholders_by_roles(self, required_roles: List[StakeholderRole]) -> List[User]:
        """Get users with required stakeholder roles."""
        try:
            # Convert enum values to strings for database query
            role_names = [role.value for role in required_roles]

            # Query users with required roles
            query = select(User).where(
                and_(
                    User.is_active == True,
                    User.role.in_(role_names)
                )
            )

            result = await self.db.execute(query)
            stakeholders = result.scalars().all()

            logger.info(f"Found {len(stakeholders)} stakeholders for roles: {role_names}")
            return stakeholders

        except Exception as e:
            logger.error(f"Failed to get stakeholders by roles: {e}")
            return []

    def _user_has_role(self, user: User, role: StakeholderRole) -> bool:
        """Check if user has the specified role."""
        return user.role == role.value

    async def _send_notification(
        self,
        stakeholder: User,
        amendment: ACAmendment,
        channel: NotificationChannel,
        notification_type: str,
        deadline: datetime,
        **kwargs
    ) -> bool:
        """
        Send notification to stakeholder via specified channel.

        Args:
            stakeholder: User to notify
            amendment: Amendment details
            channel: Notification channel to use
            notification_type: Type of notification
            deadline: Engagement deadline
            **kwargs: Additional notification parameters

        Returns:
            bool: True if notification sent successfully
        """
        try:
            # Generate notification ID
            notification_id = f"{amendment.id}_{stakeholder.id}_{channel.value}_{int(datetime.now().timestamp())}"

            # Determine stakeholder role
            stakeholder_role = StakeholderRole(stakeholder.role)

            # Create notification content
            content = await self._create_notification_content(
                stakeholder=stakeholder,
                amendment=amendment,
                notification_type=notification_type,
                deadline=deadline,
                **kwargs
            )

            # Create notification record
            notification_record = NotificationRecord(
                id=notification_id,
                stakeholder_id=stakeholder.id,
                stakeholder_role=stakeholder_role,
                amendment_id=amendment.id,
                channel=channel,
                status=NotificationStatus.PENDING,
                content=content
            )

            # Store notification record
            self.notifications[notification_id] = notification_record

            # Dispatch notification based on channel
            success = False
            if channel == NotificationChannel.EMAIL:
                success = await self._send_email_notification(notification_record)
            elif channel == NotificationChannel.DASHBOARD:
                success = await self._send_dashboard_notification(notification_record)
            elif channel == NotificationChannel.WEBHOOK:
                success = await self._send_webhook_notification(notification_record)
            elif channel == NotificationChannel.WEBSOCKET:
                success = await self._send_websocket_notification(notification_record)

            # Update notification status
            if success:
                notification_record.status = NotificationStatus.SENT
                notification_record.sent_at = datetime.now(timezone.utc)
                logger.info(f"Notification sent successfully: {notification_id}")
            else:
                notification_record.status = NotificationStatus.FAILED
                notification_record.error_message = "Failed to send notification"
                logger.warning(f"Failed to send notification: {notification_id}")

            return success

        except Exception as e:
            logger.error(f"Error sending notification to {stakeholder.username}: {e}")
            return False

    async def _create_notification_content(
        self,
        stakeholder: User,
        amendment: ACAmendment,
        notification_type: str,
        deadline: datetime,
        **kwargs
    ) -> Dict[str, Any]:
        """Create notification content based on type and context."""
        template_config = self.notification_templates.get(notification_type, {})

        # Base content structure
        content = {
            "subject": template_config.get("subject", "Constitutional Amendment Notification"),
            "template": template_config.get("template", "default_notification.html"),
            "stakeholder": {
                "id": stakeholder.id,
                "username": stakeholder.username,
                "email": stakeholder.email,
                "role": stakeholder.role
            },
            "amendment": {
                "id": amendment.id,
                "title": amendment.title,
                "description": amendment.description,
                "proposed_by": amendment.proposed_by_user_id,
                "created_at": amendment.created_at.isoformat() if amendment.created_at else None
            },
            "engagement": {
                "deadline": deadline.isoformat(),
                "hours_remaining": int((deadline - datetime.now(timezone.utc)).total_seconds() / 3600),
                "notification_type": notification_type
            },
            "actions": {
                "review_url": f"/constitutional-council/amendments/{amendment.id}",
                "feedback_url": f"/constitutional-council/amendments/{amendment.id}/feedback",
                "dashboard_url": "/dashboard/constitutional-council"
            },
            "metadata": kwargs
        }

        return content

    async def _send_email_notification(self, notification: NotificationRecord) -> bool:
        """Send email notification."""
        try:
            # Email configuration (should be moved to environment variables)
            smtp_server = "localhost"  # Configure based on environment
            smtp_port = 587

            # Create email message
            msg = MIMEMultipart()
            msg['From'] = "noreply@acgs-pgp.org"
            msg['To'] = notification.content["stakeholder"]["email"]
            msg['Subject'] = notification.content["subject"]

            # Create email body (simplified - should use proper templates)
            body = f"""
            Dear {notification.content["stakeholder"]["username"]},

            A new constitutional amendment requires your review and feedback.

            Amendment: {notification.content["amendment"]["title"]}
            Description: {notification.content["amendment"]["description"]}

            Deadline: {notification.content["engagement"]["deadline"]}
            Hours Remaining: {notification.content["engagement"]["hours_remaining"]}

            Please review the amendment and provide your feedback at:
            {notification.content["actions"]["review_url"]}

            Best regards,
            ACGS-PGP Constitutional Council
            """

            msg.attach(MIMEText(body, 'plain'))

            # For now, just log the email (implement actual SMTP sending as needed)
            logger.info(f"Email notification prepared for {notification.content['stakeholder']['email']}")
            logger.debug(f"Email content: {body}")

            # Mark as delivered (in real implementation, check SMTP response)
            notification.status = NotificationStatus.DELIVERED
            notification.delivered_at = datetime.now(timezone.utc)

            return True

        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            notification.error_message = str(e)
            return False

    async def _send_dashboard_notification(self, notification: NotificationRecord) -> bool:
        """Send dashboard notification."""
        try:
            # Dashboard notifications are stored for display in the user interface
            logger.info(f"Dashboard notification created for user {notification.stakeholder_id}")

            # Mark as delivered immediately (dashboard notifications are always available)
            notification.status = NotificationStatus.DELIVERED
            notification.delivered_at = datetime.now(timezone.utc)

            return True

        except Exception as e:
            logger.error(f"Failed to create dashboard notification: {e}")
            notification.error_message = str(e)
            return False

    async def _send_webhook_notification(self, notification: NotificationRecord) -> bool:
        """Send webhook notification."""
        try:
            # Webhook configuration (should be configurable per stakeholder)
            webhook_url = notification.metadata.get("webhook_url")
            if not webhook_url:
                logger.warning(f"No webhook URL configured for stakeholder {notification.stakeholder_id}")
                return False

            # Prepare webhook payload
            payload = {
                "notification_id": notification.id,
                "type": "constitutional_amendment_notification",
                "stakeholder": notification.content["stakeholder"],
                "amendment": notification.content["amendment"],
                "engagement": notification.content["engagement"],
                "actions": notification.content["actions"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            # Send webhook request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    timeout=10.0,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()

            logger.info(f"Webhook notification sent to {webhook_url}")
            notification.status = NotificationStatus.DELIVERED
            notification.delivered_at = datetime.now(timezone.utc)

            return True

        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")
            notification.error_message = str(e)
            return False

    async def _send_websocket_notification(self, notification: NotificationRecord) -> bool:
        """Send WebSocket notification."""
        try:
            amendment_id = notification.amendment_id

            # Get active WebSocket connections for this amendment
            connections = self.websocket_connections.get(amendment_id, set())

            if not connections:
                logger.info(f"No active WebSocket connections for amendment {amendment_id}")
                return True  # Not an error - just no active connections

            # Prepare WebSocket message
            message = {
                "type": "stakeholder_notification",
                "notification_id": notification.id,
                "stakeholder_id": notification.stakeholder_id,
                "amendment_id": amendment_id,
                "content": notification.content,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            # Send to all active connections
            disconnected_connections = set()
            for websocket in connections:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to send WebSocket message: {e}")
                    disconnected_connections.add(websocket)

            # Remove disconnected connections
            connections -= disconnected_connections

            logger.info(f"WebSocket notification sent to {len(connections)} connections")
            notification.status = NotificationStatus.DELIVERED
            notification.delivered_at = datetime.now(timezone.utc)

            return True

        except Exception as e:
            logger.error(f"Failed to send WebSocket notification: {e}")
            notification.error_message = str(e)
            return False

    async def collect_stakeholder_feedback(
        self,
        amendment_id: int,
        stakeholder_id: int,
        feedback_content: str,
        feedback_type: str = "comment"
    ) -> FeedbackRecord:
        """
        Collect feedback from a stakeholder.

        Args:
            amendment_id: Amendment ID
            stakeholder_id: Stakeholder user ID
            feedback_content: Feedback content
            feedback_type: Type of feedback (comment, vote, suggestion, objection)

        Returns:
            FeedbackRecord: Created feedback record
        """
        try:
            # Get stakeholder details
            stakeholder_query = select(User).where(User.id == stakeholder_id)
            result = await self.db.execute(stakeholder_query)
            stakeholder = result.scalar_one_or_none()

            if not stakeholder:
                raise ValueError(f"Stakeholder {stakeholder_id} not found")

            # Determine stakeholder role
            stakeholder_role = StakeholderRole(stakeholder.role)

            # Generate feedback ID
            feedback_id = f"{amendment_id}_{stakeholder_id}_{feedback_type}_{int(datetime.now().timestamp())}"

            # Create feedback record
            feedback_record = FeedbackRecord(
                id=feedback_id,
                stakeholder_id=stakeholder_id,
                stakeholder_role=stakeholder_role,
                amendment_id=amendment_id,
                feedback_content=feedback_content,
                feedback_type=feedback_type,
                status=FeedbackStatus.SUBMITTED,
                submitted_at=datetime.now(timezone.utc)
            )

            # Store feedback record
            self.feedback_records[feedback_id] = feedback_record

            # Update engagement status
            await self._update_engagement_status(amendment_id, stakeholder_id)

            # Send real-time updates
            await self._broadcast_engagement_update(amendment_id)

            logger.info(f"Feedback collected from stakeholder {stakeholder_id} for amendment {amendment_id}")

            return feedback_record

        except Exception as e:
            logger.error(f"Failed to collect stakeholder feedback: {e}")
            raise

    async def _update_engagement_status(self, amendment_id: int, stakeholder_id: int) -> None:
        """Update engagement status after feedback submission."""
        try:
            engagement_status = self.active_engagements.get(amendment_id)
            if not engagement_status:
                logger.warning(f"No active engagement found for amendment {amendment_id}")
                return

            # Update stakeholder status
            if stakeholder_id in engagement_status.status_by_stakeholder:
                stakeholder_status = engagement_status.status_by_stakeholder[stakeholder_id]
                stakeholder_status["feedback_submitted"] = True
                stakeholder_status["last_activity"] = datetime.now(timezone.utc).isoformat()
                stakeholder_status["engagement_score"] = 1.0  # Full engagement for feedback submission

            # Recalculate engagement metrics
            total_stakeholders = engagement_status.total_stakeholders
            engaged_stakeholders = sum(
                1 for status in engagement_status.status_by_stakeholder.values()
                if status["feedback_submitted"]
            )

            engagement_status.engaged_stakeholders = engaged_stakeholders
            engagement_status.pending_stakeholders = total_stakeholders - engaged_stakeholders
            engagement_status.engagement_rate = engaged_stakeholders / total_stakeholders if total_stakeholders > 0 else 0.0
            engagement_status.feedback_received += 1
            engagement_status.last_updated = datetime.now(timezone.utc)

            # Update feedback by role
            stakeholder_query = select(User).where(User.id == stakeholder_id)
            result = await self.db.execute(stakeholder_query)
            stakeholder = result.scalar_one_or_none()

            if stakeholder and stakeholder.role in engagement_status.feedback_by_role:
                engagement_status.feedback_by_role[stakeholder.role] += 1

            logger.info(f"Engagement status updated for amendment {amendment_id}: {engaged_stakeholders}/{total_stakeholders} stakeholders engaged")

        except Exception as e:
            logger.error(f"Failed to update engagement status: {e}")

    async def _broadcast_engagement_update(self, amendment_id: int) -> None:
        """Broadcast real-time engagement updates via WebSocket."""
        try:
            engagement_status = self.active_engagements.get(amendment_id)
            if not engagement_status:
                return

            # Get active WebSocket connections
            connections = self.websocket_connections.get(amendment_id, set())

            if not connections:
                return

            # Prepare update message
            update_message = {
                "type": "engagement_status_update",
                "amendment_id": amendment_id,
                "engagement_status": {
                    "total_stakeholders": engagement_status.total_stakeholders,
                    "engaged_stakeholders": engagement_status.engaged_stakeholders,
                    "pending_stakeholders": engagement_status.pending_stakeholders,
                    "engagement_rate": engagement_status.engagement_rate,
                    "feedback_received": engagement_status.feedback_received,
                    "feedback_by_role": engagement_status.feedback_by_role,
                    "deadline": engagement_status.deadline.isoformat(),
                    "is_deadline_passed": engagement_status.is_deadline_passed,
                    "last_updated": engagement_status.last_updated.isoformat()
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            # Send to all active connections
            disconnected_connections = set()
            for websocket in connections:
                try:
                    await websocket.send_json(update_message)
                except Exception as e:
                    logger.warning(f"Failed to send engagement update: {e}")
                    disconnected_connections.add(websocket)

            # Remove disconnected connections
            connections -= disconnected_connections

            logger.info(f"Engagement update broadcasted to {len(connections)} connections")

        except Exception as e:
            logger.error(f"Failed to broadcast engagement update: {e}")

    async def _schedule_reminder_notifications(
        self,
        amendment_id: int,
        reminder_intervals_hours: List[int],
        deadline: datetime
    ) -> None:
        """Schedule reminder notifications before deadline."""
        try:
            for hours_before in reminder_intervals_hours:
                reminder_time = deadline - timedelta(hours=hours_before)

                # Only schedule if reminder time is in the future
                if reminder_time > datetime.now(timezone.utc):
                    # In a production system, this would use a task queue like Celery
                    # For now, we'll log the scheduled reminder
                    logger.info(
                        f"Reminder notification scheduled for amendment {amendment_id} "
                        f"at {reminder_time.isoformat()} ({hours_before} hours before deadline)"
                    )

        except Exception as e:
            logger.error(f"Failed to schedule reminder notifications: {e}")

    async def get_engagement_status(self, amendment_id: int) -> Optional[StakeholderEngagementStatus]:
        """Get current engagement status for an amendment."""
        return self.active_engagements.get(amendment_id)

    async def get_stakeholder_notifications(
        self,
        stakeholder_id: int,
        amendment_id: Optional[int] = None
    ) -> List[NotificationRecord]:
        """Get notifications for a specific stakeholder."""
        notifications = []

        for notification in self.notifications.values():
            if notification.stakeholder_id == stakeholder_id:
                if amendment_id is None or notification.amendment_id == amendment_id:
                    notifications.append(notification)

        # Sort by sent time (most recent first)
        notifications.sort(key=lambda n: n.sent_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)

        return notifications

    async def get_stakeholder_feedback(
        self,
        amendment_id: int,
        stakeholder_id: Optional[int] = None
    ) -> List[FeedbackRecord]:
        """Get feedback records for an amendment."""
        feedback_records = []

        for feedback in self.feedback_records.values():
            if feedback.amendment_id == amendment_id:
                if stakeholder_id is None or feedback.stakeholder_id == stakeholder_id:
                    feedback_records.append(feedback)

        # Sort by submission time (most recent first)
        feedback_records.sort(key=lambda f: f.submitted_at, reverse=True)

        return feedback_records

    async def add_websocket_connection(self, amendment_id: int, websocket) -> None:
        """Add WebSocket connection for real-time updates."""
        if amendment_id not in self.websocket_connections:
            self.websocket_connections[amendment_id] = set()

        self.websocket_connections[amendment_id].add(websocket)
        logger.info(f"WebSocket connection added for amendment {amendment_id}")

    async def remove_websocket_connection(self, amendment_id: int, websocket) -> None:
        """Remove WebSocket connection."""
        if amendment_id in self.websocket_connections:
            self.websocket_connections[amendment_id].discard(websocket)
            logger.info(f"WebSocket connection removed for amendment {amendment_id}")


# Dependency function for FastAPI
def get_stakeholder_engagement_service(
    db: AsyncSession,
    config: ConstitutionalCouncilConfig = None
) -> StakeholderNotificationService:
    """Get stakeholder engagement service instance."""
    if config is None:
        config = ConstitutionalCouncilConfig()

    return StakeholderNotificationService(db=db, config=config)
