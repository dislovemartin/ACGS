"""
Stakeholder Engagement API Endpoints

This module provides REST API endpoints for the stakeholder engagement system,
integrating with the Constitutional Council StateGraph workflows.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from shared.database import get_async_db
from shared.auth import get_current_active_user, User

# Placeholder function for current user
async def get_current_active_user_placeholder() -> User:
    """Placeholder function for current user authentication."""
    return User(
        id=1,
        username="test_user",
        roles=["admin", "constitutional_expert"],
        is_active=True
    )
from shared.langgraph_config import ConstitutionalCouncilConfig
from app.services.stakeholder_engagement import (
    StakeholderNotificationService,
    StakeholderEngagementInput,
    StakeholderEngagementStatus,
    NotificationRecord,
    FeedbackRecord,
    get_stakeholder_engagement_service
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stakeholder-engagement", tags=["stakeholder-engagement"])


class FeedbackSubmissionRequest(BaseModel):
    """Request model for submitting stakeholder feedback."""
    amendment_id: int
    feedback_content: str
    feedback_type: str = "comment"  # comment, vote, suggestion, objection


class NotificationResponse(BaseModel):
    """Response model for notification records."""
    id: str
    stakeholder_id: int
    stakeholder_role: str
    amendment_id: int
    channel: str
    status: str
    sent_at: Optional[str] = None
    delivered_at: Optional[str] = None
    read_at: Optional[str] = None
    content: dict


class FeedbackResponse(BaseModel):
    """Response model for feedback records."""
    id: str
    stakeholder_id: int
    stakeholder_role: str
    amendment_id: int
    feedback_content: str
    feedback_type: str
    status: str
    submitted_at: str
    reviewed_at: Optional[str] = None


@router.post("/initiate", response_model=StakeholderEngagementStatus)
async def initiate_stakeholder_engagement(
    engagement_input: StakeholderEngagementInput,
    current_user: User = Depends(get_current_active_user_placeholder),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Initiate stakeholder engagement for a constitutional amendment.
    
    Requires admin or constitutional council member permissions.
    """
    try:
        # Check permissions (admin or constitutional council member)
        if not (current_user.role in ["admin", "constitutional_expert", "policy_administrator"]):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to initiate stakeholder engagement"
            )
        
        # Create engagement service
        config = ConstitutionalCouncilConfig()
        engagement_service = get_stakeholder_engagement_service(db=db, config=config)

        # Initiate engagement
        engagement_status = await engagement_service.initiate_stakeholder_engagement(engagement_input)
        
        logger.info(f"Stakeholder engagement initiated by {current_user.username} for amendment {engagement_input.amendment_id}")
        
        return engagement_status
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to initiate stakeholder engagement: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/status/{amendment_id}", response_model=StakeholderEngagementStatus)
async def get_engagement_status(
    amendment_id: int,
    current_user: User = Depends(get_current_active_user_placeholder),
    db: AsyncSession = Depends(get_async_db)
):
    """Get current engagement status for an amendment."""
    try:
        # Create engagement service
        config = ConstitutionalCouncilConfig()
        engagement_service = get_stakeholder_engagement_service(db=db, config=config)

        engagement_status = await engagement_service.get_engagement_status(amendment_id)
        
        if not engagement_status:
            raise HTTPException(
                status_code=404,
                detail=f"No active engagement found for amendment {amendment_id}"
            )
        
        return engagement_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get engagement status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_stakeholder_feedback(
    feedback_request: FeedbackSubmissionRequest,
    current_user: User = Depends(get_current_active_user_placeholder),
    db: AsyncSession = Depends(get_async_db)
):
    """Submit feedback for a constitutional amendment."""
    try:
        # Check if user has required stakeholder role
        required_roles = ["constitutional_expert", "policy_administrator", "system_auditor", "public_representative"]
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=403,
                detail="User does not have required stakeholder role for feedback submission"
            )
        
        # Create engagement service
        config = ConstitutionalCouncilConfig()
        engagement_service = get_stakeholder_engagement_service(db=db, config=config)

        # Collect feedback
        feedback_record = await engagement_service.collect_stakeholder_feedback(
            amendment_id=feedback_request.amendment_id,
            stakeholder_id=current_user.id,
            feedback_content=feedback_request.feedback_content,
            feedback_type=feedback_request.feedback_type
        )
        
        # Convert to response model
        feedback_response = FeedbackResponse(
            id=feedback_record.id,
            stakeholder_id=feedback_record.stakeholder_id,
            stakeholder_role=feedback_record.stakeholder_role.value,
            amendment_id=feedback_record.amendment_id,
            feedback_content=feedback_record.feedback_content,
            feedback_type=feedback_record.feedback_type,
            status=feedback_record.status.value,
            submitted_at=feedback_record.submitted_at.isoformat(),
            reviewed_at=feedback_record.reviewed_at.isoformat() if feedback_record.reviewed_at else None
        )
        
        logger.info(f"Feedback submitted by {current_user.username} for amendment {feedback_request.amendment_id}")
        
        return feedback_response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to submit feedback: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/notifications", response_model=List[NotificationResponse])
async def get_stakeholder_notifications(
    amendment_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user_placeholder),
    db: AsyncSession = Depends(get_async_db)
):
    """Get notifications for the current stakeholder."""
    try:
        # Create engagement service
        config = ConstitutionalCouncilConfig()
        engagement_service = get_stakeholder_engagement_service(db=db, config=config)

        notifications = await engagement_service.get_stakeholder_notifications(
            stakeholder_id=current_user.id,
            amendment_id=amendment_id
        )
        
        # Convert to response models
        notification_responses = []
        for notification in notifications:
            notification_response = NotificationResponse(
                id=notification.id,
                stakeholder_id=notification.stakeholder_id,
                stakeholder_role=notification.stakeholder_role.value,
                amendment_id=notification.amendment_id,
                channel=notification.channel.value,
                status=notification.status.value,
                sent_at=notification.sent_at.isoformat() if notification.sent_at else None,
                delivered_at=notification.delivered_at.isoformat() if notification.delivered_at else None,
                read_at=notification.read_at.isoformat() if notification.read_at else None,
                content=notification.content
            )
            notification_responses.append(notification_response)
        
        return notification_responses
        
    except Exception as e:
        logger.error(f"Failed to get stakeholder notifications: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/feedback/{amendment_id}", response_model=List[FeedbackResponse])
async def get_amendment_feedback(
    amendment_id: int,
    current_user: User = Depends(get_current_active_user_placeholder),
    db: AsyncSession = Depends(get_async_db)
):
    """Get all feedback for an amendment (admin/council members only)."""
    try:
        # Check permissions
        if not (current_user.role in ["admin", "constitutional_expert", "policy_administrator"]):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to view all feedback"
            )
        
        # Create engagement service
        config = ConstitutionalCouncilConfig()
        engagement_service = get_stakeholder_engagement_service(db=db, config=config)

        feedback_records = await engagement_service.get_stakeholder_feedback(amendment_id=amendment_id)
        
        # Convert to response models
        feedback_responses = []
        for feedback in feedback_records:
            feedback_response = FeedbackResponse(
                id=feedback.id,
                stakeholder_id=feedback.stakeholder_id,
                stakeholder_role=feedback.stakeholder_role.value,
                amendment_id=feedback.amendment_id,
                feedback_content=feedback.feedback_content,
                feedback_type=feedback.feedback_type,
                status=feedback.status.value,
                submitted_at=feedback.submitted_at.isoformat(),
                reviewed_at=feedback.reviewed_at.isoformat() if feedback.reviewed_at else None
            )
            feedback_responses.append(feedback_response)
        
        return feedback_responses
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get amendment feedback: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.websocket("/ws/{amendment_id}")
async def websocket_engagement_updates(
    websocket: WebSocket,
    amendment_id: int
):
    """
    WebSocket endpoint for real-time stakeholder engagement updates.
    
    Provides real-time updates on:
    - Engagement status changes
    - New feedback submissions
    - Notification delivery status
    - Deadline reminders
    """
    try:
        await websocket.accept()

        # Create engagement service (simplified for WebSocket)
        from shared.database import get_async_db
        async for db in get_async_db():
            config = ConstitutionalCouncilConfig()
            engagement_service = get_stakeholder_engagement_service(db=db, config=config)
            break

        await engagement_service.add_websocket_connection(amendment_id, websocket)
        
        logger.info(f"WebSocket connection established for amendment {amendment_id}")
        
        # Send initial engagement status
        engagement_status = await engagement_service.get_engagement_status(amendment_id)
        if engagement_status:
            await websocket.send_json({
                "type": "initial_status",
                "amendment_id": amendment_id,
                "engagement_status": engagement_status.dict()
            })
        
        # Keep connection alive and handle messages
        while True:
            try:
                data = await websocket.receive_text()
                
                # Handle ping/pong for connection health
                if data == "ping":
                    await websocket.send_text("pong")
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    
    finally:
        await engagement_service.remove_websocket_connection(amendment_id, websocket)
        logger.info(f"WebSocket connection closed for amendment {amendment_id}")
