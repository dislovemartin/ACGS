"""
Public Consultation API Endpoints

This module provides REST API endpoints for public consultation mechanisms,
enabling citizen participation in constitutional governance processes.

Key Features:
- Public amendment proposal submission
- Public feedback collection and analysis
- Consultation metrics and transparency
- Integration with Constitutional Council workflows
- Anonymous and authenticated participation
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_async_db as get_db
from ..schemas import (
    PublicProposalCreate, PublicProposalResponse, PublicFeedbackCreate,
    PublicFeedbackResponse, ConsultationMetricsResponse
)
from ..services.public_consultation_service import (
    PublicConsultationService, PublicProposal, PublicFeedback,
    StakeholderGroup, FeedbackType, ConsultationStatus
)
from ..services.human_in_the_loop_sampler import HumanInTheLoopSampler
from shared.auth import get_current_active_user as get_current_user, require_admin, require_policy_manager
from shared.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public-consultation", tags=["Public Consultation"])

# Global service instances
hitl_sampler = HumanInTheLoopSampler()
consultation_service = PublicConsultationService(hitl_sampler)


@router.post("/proposals", response_model=PublicProposalResponse)
async def submit_public_proposal(
    proposal_data: PublicProposalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Submit a public amendment proposal for constitutional consideration.
    
    This endpoint allows citizens and stakeholders to propose constitutional
    amendments that can be reviewed and potentially advanced to the Constitutional Council.
    """
    try:
        # Create proposal object
        proposal = PublicProposal(
            title=proposal_data.title,
            description=proposal_data.description,
            proposed_changes=proposal_data.proposed_changes,
            justification=proposal_data.justification,
            submitter_name=proposal_data.submitter_name,
            submitter_email=proposal_data.submitter_email,
            submitter_organization=proposal_data.submitter_organization,
            stakeholder_group=StakeholderGroup(proposal_data.stakeholder_group),
            consultation_period_days=proposal_data.consultation_period_days or 30
        )
        
        # Submit proposal
        submitted_proposal = await consultation_service.submit_public_proposal(
            db=db,
            proposal=proposal,
            auto_review=True
        )
        
        # Convert to response format
        response = PublicProposalResponse(
            id=submitted_proposal.id,
            title=submitted_proposal.title,
            description=submitted_proposal.description,
            proposed_changes=submitted_proposal.proposed_changes,
            justification=submitted_proposal.justification,
            submitter_name=submitted_proposal.submitter_name,
            submitter_organization=submitted_proposal.submitter_organization,
            stakeholder_group=submitted_proposal.stakeholder_group.value,
            status=submitted_proposal.status.value,
            created_at=submitted_proposal.created_at,
            consultation_period_days=submitted_proposal.consultation_period_days,
            public_support_count=submitted_proposal.public_support_count,
            requires_review=submitted_proposal.requires_review
        )
        
        logger.info(f"Public proposal submitted: {submitted_proposal.title} (ID: {submitted_proposal.id})")
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to submit public proposal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit proposal: {str(e)}"
        )


@router.post("/feedback", response_model=PublicFeedbackResponse)
async def submit_public_feedback(
    feedback_data: PublicFeedbackCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Submit public feedback on proposals or amendments.
    
    This endpoint allows citizens to provide structured feedback on constitutional
    proposals and amendments, with automatic sentiment analysis and categorization.
    """
    try:
        # Create feedback object
        feedback = PublicFeedback(
            proposal_id=feedback_data.proposal_id,
            amendment_id=feedback_data.amendment_id,
            feedback_type=FeedbackType(feedback_data.feedback_type) if feedback_data.feedback_type else FeedbackType.NEUTRAL,
            content=feedback_data.content,
            submitter_name=feedback_data.submitter_name,
            submitter_email=feedback_data.submitter_email,
            stakeholder_group=StakeholderGroup(feedback_data.stakeholder_group)
        )
        
        # Collect feedback
        processed_feedback = await consultation_service.collect_public_feedback(
            db=db,
            feedback=feedback,
            verify_submitter=feedback_data.submitter_email is not None
        )
        
        # Convert to response format
        response = PublicFeedbackResponse(
            id=processed_feedback.id,
            proposal_id=processed_feedback.proposal_id,
            amendment_id=processed_feedback.amendment_id,
            feedback_type=processed_feedback.feedback_type.value,
            content=processed_feedback.content,
            submitter_name=processed_feedback.submitter_name,
            stakeholder_group=processed_feedback.stakeholder_group.value,
            sentiment_score=processed_feedback.sentiment_score,
            is_verified=processed_feedback.is_verified,
            created_at=processed_feedback.created_at
        )
        
        logger.info(f"Public feedback submitted: {processed_feedback.feedback_type.value} "
                   f"(sentiment: {processed_feedback.sentiment_score:.2f if processed_feedback.sentiment_score else 'N/A'})")
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to submit public feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )


@router.get("/proposals", response_model=List[PublicProposalResponse])
async def get_public_proposals(
    status: Optional[str] = Query(None, description="Filter by proposal status"),
    stakeholder_group: Optional[str] = Query(None, description="Filter by stakeholder group"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of proposals to return"),
    offset: int = Query(0, ge=0, description="Number of proposals to skip"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of public proposals with optional filtering.
    
    This endpoint provides public access to constitutional proposals,
    enabling transparency and public awareness of ongoing consultations.
    """
    try:
        # Mock implementation - would query actual database
        mock_proposals = []
        for i in range(1, min(limit + 1, 6)):  # Return up to 5 mock proposals
            proposal = PublicProposalResponse(
                id=i,
                title=f"Public Proposal {i}: Enhanced Privacy Protection",
                description=f"This proposal aims to strengthen privacy protections for citizens in AI governance systems. Proposal {i} details...",
                proposed_changes=f"Add new privacy principle requiring explicit consent for data processing in governance decisions.",
                justification=f"Current privacy protections are insufficient for modern AI governance needs.",
                submitter_name=f"Citizen {i}",
                submitter_organization=f"Privacy Advocacy Group {i}" if i % 2 == 0 else None,
                stakeholder_group="citizen",
                status="open" if i <= 3 else "review",
                created_at=datetime.utcnow() - timedelta(days=i * 5),
                consultation_period_days=30,
                public_support_count=50 + i * 25,
                requires_review=i > 3
            )
            
            # Apply filters
            if status and proposal.status != status:
                continue
            if stakeholder_group and proposal.stakeholder_group != stakeholder_group:
                continue
                
            mock_proposals.append(proposal)
        
        # Apply pagination
        paginated_proposals = mock_proposals[offset:offset + limit]
        
        return paginated_proposals
        
    except Exception as e:
        logger.error(f"Failed to get public proposals: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve proposals: {str(e)}"
        )


@router.get("/proposals/{proposal_id}", response_model=PublicProposalResponse)
async def get_public_proposal(
    proposal_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a specific public proposal.
    
    This endpoint provides comprehensive details about a constitutional proposal
    including its current status, support metrics, and consultation timeline.
    """
    try:
        # Mock implementation - would query actual database
        if proposal_id < 1 or proposal_id > 10:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Proposal {proposal_id} not found"
            )
        
        proposal = PublicProposalResponse(
            id=proposal_id,
            title=f"Public Proposal {proposal_id}: Enhanced Privacy Protection",
            description=f"Comprehensive proposal for strengthening privacy protections in AI governance. This proposal addresses current gaps in privacy safeguards and proposes specific improvements to ensure citizen data protection.",
            proposed_changes="1. Add explicit consent requirement for all data processing\n2. Implement data minimization principles\n3. Establish citizen data rights framework\n4. Create privacy impact assessment requirements",
            justification="Current privacy protections are insufficient for the complexity of modern AI governance systems. Citizens need stronger safeguards to maintain trust in democratic AI governance.",
            submitter_name="Dr. Privacy Advocate",
            submitter_organization="Digital Rights Foundation",
            stakeholder_group="privacy_advocate",
            status="open" if proposal_id <= 5 else "review",
            created_at=datetime.utcnow() - timedelta(days=proposal_id * 3),
            consultation_period_days=30,
            public_support_count=75 + proposal_id * 15,
            requires_review=proposal_id > 5
        )
        
        return proposal
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get proposal {proposal_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve proposal: {str(e)}"
        )


@router.get("/feedback/{proposal_id}", response_model=List[PublicFeedbackResponse])
async def get_proposal_feedback(
    proposal_id: int,
    feedback_type: Optional[str] = Query(None, description="Filter by feedback type"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of feedback items to return"),
    offset: int = Query(0, ge=0, description="Number of feedback items to skip"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get public feedback for a specific proposal.
    
    This endpoint provides access to public feedback and comments on constitutional
    proposals, enabling transparency and public discourse analysis.
    """
    try:
        # Mock implementation - would query actual database
        mock_feedback = []
        for i in range(1, min(limit + 1, 11)):  # Return up to 10 mock feedback items
            feedback = PublicFeedbackResponse(
                id=i,
                proposal_id=proposal_id,
                amendment_id=None,
                feedback_type=["support", "oppose", "suggestion", "concern"][i % 4],
                content=f"This is feedback item {i} regarding proposal {proposal_id}. The feedback provides detailed analysis and perspective on the proposed changes.",
                submitter_name=f"Citizen {i}" if i % 3 != 0 else None,  # Some anonymous
                stakeholder_group=["citizen", "expert", "civil_society"][i % 3],
                sentiment_score=0.3 + (i % 7) * 0.1,  # Varying sentiment scores
                is_verified=i % 2 == 0,
                created_at=datetime.utcnow() - timedelta(hours=i * 6)
            )
            
            # Apply filters
            if feedback_type and feedback.feedback_type != feedback_type:
                continue
                
            mock_feedback.append(feedback)
        
        # Apply pagination
        paginated_feedback = mock_feedback[offset:offset + limit]
        
        return paginated_feedback
        
    except Exception as e:
        logger.error(f"Failed to get feedback for proposal {proposal_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve feedback: {str(e)}"
        )


@router.get("/metrics", response_model=ConsultationMetricsResponse)
async def get_consultation_metrics(
    time_period_days: Optional[int] = Query(30, ge=1, le=365, description="Time period for metrics calculation"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive public consultation metrics.
    
    This endpoint provides transparency into the public consultation process
    with detailed metrics on participation, engagement, and outcomes.
    """
    try:
        metrics = await consultation_service.get_consultation_metrics(
            db=db,
            time_period_days=time_period_days
        )
        
        response = ConsultationMetricsResponse(
            total_proposals=metrics.total_proposals,
            active_consultations=metrics.active_consultations,
            total_participants=metrics.total_participants,
            feedback_count=metrics.feedback_count,
            sentiment_distribution=metrics.sentiment_distribution,
            stakeholder_participation=metrics.stakeholder_participation,
            engagement_rate=metrics.engagement_rate,
            completion_rate=metrics.completion_rate,
            time_period_days=time_period_days
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to get consultation metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve metrics: {str(e)}"
        )


@router.post("/proposals/{proposal_id}/advance")
async def advance_proposal_to_council(
    proposal_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Advance a public proposal to Constitutional Council consideration.
    
    This endpoint allows Constitutional Council members to advance qualifying
    public proposals to formal amendment consideration.
    """
    try:
        result = await consultation_service.advance_proposal_to_council(
            db=db,
            proposal_id=proposal_id,
            council_user_id=current_user.id
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("reason", "Failed to advance proposal")
            )
        
        logger.info(f"Proposal {proposal_id} advanced to Constitutional Council by user {current_user.id}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to advance proposal {proposal_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to advance proposal: {str(e)}"
        )


@router.get("/transparency-dashboard")
async def get_transparency_dashboard(
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive transparency dashboard data for public consultation processes.
    
    This endpoint provides a complete overview of constitutional governance
    transparency including active consultations, recent decisions, and participation metrics.
    """
    try:
        # Get consultation metrics
        metrics = await consultation_service.get_consultation_metrics(db=db)
        
        # Mock additional transparency data
        dashboard_data = {
            "consultation_metrics": {
                "total_proposals": metrics.total_proposals,
                "active_consultations": metrics.active_consultations,
                "total_participants": metrics.total_participants,
                "engagement_rate": metrics.engagement_rate
            },
            "recent_activity": [
                {
                    "type": "proposal_submitted",
                    "title": "Enhanced Privacy Protection Framework",
                    "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                    "stakeholder_group": "privacy_advocate"
                },
                {
                    "type": "feedback_received",
                    "proposal_id": 3,
                    "feedback_type": "support",
                    "timestamp": (datetime.utcnow() - timedelta(hours=5)).isoformat()
                },
                {
                    "type": "proposal_advanced",
                    "proposal_id": 1,
                    "timestamp": (datetime.utcnow() - timedelta(days=1)).isoformat()
                }
            ],
            "constitutional_council_activity": {
                "active_amendments": 2,
                "recent_votes": 5,
                "public_comments_enabled": True,
                "next_voting_deadline": (datetime.utcnow() + timedelta(days=7)).isoformat()
            },
            "participation_trends": {
                "daily_participants": [15, 23, 18, 31, 27, 19, 25],
                "weekly_proposals": [3, 5, 2, 4, 6, 3, 4],
                "sentiment_trends": {
                    "positive": 0.45,
                    "neutral": 0.35,
                    "negative": 0.20
                }
            }
        }
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Failed to get transparency dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve dashboard data: {str(e)}"
        )
