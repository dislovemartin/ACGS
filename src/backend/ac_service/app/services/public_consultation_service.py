"""
Public Consultation Service for ACGS-PGP

This module implements comprehensive public consultation mechanisms for constitutional
governance, enabling citizen participation in democratic decision-making processes.

Key Features:
- Public amendment proposal submission
- Structured public feedback collection
- Sentiment analysis and categorization
- Integration with Constitutional Council workflows
- Integration with HITL sampling for public input
- Transparency and accessibility features
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

try:
    from shared.models import ACAmendment, ACAmendmentComment, User
except ImportError:
    from typing import Any
    ACAmendment = Any
    ACAmendmentComment = Any
    User = Any

from .human_in_the_loop_sampler import HumanInTheLoopSampler
from .human_escalation_system import EscalationLevel

logger = logging.getLogger(__name__)


class ConsultationStatus(Enum):
    """Status of public consultation processes."""
    DRAFT = "draft"
    OPEN = "open"
    ACTIVE = "active"
    REVIEW = "review"
    CLOSED = "closed"
    IMPLEMENTED = "implemented"


class FeedbackType(Enum):
    """Types of public feedback."""
    SUPPORT = "support"
    OPPOSE = "oppose"
    NEUTRAL = "neutral"
    SUGGESTION = "suggestion"
    CONCERN = "concern"
    QUESTION = "question"


class StakeholderGroup(Enum):
    """Stakeholder groups for consultation."""
    CITIZEN = "citizen"
    EXPERT = "expert"
    AFFECTED_PARTY = "affected_party"
    REGULATORY_BODY = "regulatory_body"
    PRIVACY_ADVOCATE = "privacy_advocate"
    SECURITY_EXPERT = "security_expert"
    LEGAL_EXPERT = "legal_expert"
    CIVIL_SOCIETY = "civil_society"
    INDUSTRY = "industry"
    ACADEMIA = "academia"


@dataclass
class PublicProposal:
    """Public amendment proposal structure."""
    id: Optional[int] = None
    title: str = ""
    description: str = ""
    proposed_changes: str = ""
    justification: str = ""
    submitter_name: Optional[str] = None
    submitter_email: Optional[str] = None
    submitter_organization: Optional[str] = None
    stakeholder_group: StakeholderGroup = StakeholderGroup.CITIZEN
    status: ConsultationStatus = ConsultationStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.utcnow)
    consultation_period_days: int = 30
    public_support_count: int = 0
    requires_review: bool = True


@dataclass
class PublicFeedback:
    """Public feedback structure."""
    id: Optional[int] = None
    proposal_id: Optional[int] = None
    amendment_id: Optional[int] = None
    feedback_type: FeedbackType = FeedbackType.NEUTRAL
    content: str = ""
    submitter_name: Optional[str] = None
    submitter_email: Optional[str] = None
    stakeholder_group: StakeholderGroup = StakeholderGroup.CITIZEN
    sentiment_score: Optional[float] = None
    is_verified: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConsultationMetrics:
    """Metrics for public consultation processes."""
    total_proposals: int = 0
    active_consultations: int = 0
    total_participants: int = 0
    feedback_count: int = 0
    sentiment_distribution: Dict[str, int] = field(default_factory=dict)
    stakeholder_participation: Dict[str, int] = field(default_factory=dict)
    engagement_rate: float = 0.0
    completion_rate: float = 0.0


class PublicConsultationService:
    """
    Service for managing public consultation processes in constitutional governance.
    
    Provides comprehensive public participation mechanisms including proposal submission,
    feedback collection, sentiment analysis, and integration with governance workflows.
    """
    
    def __init__(self, hitl_sampler: Optional[HumanInTheLoopSampler] = None):
        """Initialize the public consultation service."""
        self.hitl_sampler = hitl_sampler
        
        # Configuration
        self.config = {
            "min_support_threshold": 100,  # Minimum support for proposal advancement
            "consultation_period_days": 30,  # Default consultation period
            "auto_sentiment_analysis": True,  # Enable automatic sentiment analysis
            "require_email_verification": False,  # Require email verification for feedback
            "max_feedback_length": 5000,  # Maximum feedback length
            "enable_anonymous_feedback": True,  # Allow anonymous feedback
            "stakeholder_weight_multiplier": 1.5,  # Weight multiplier for expert stakeholders
        }
        
        # Performance tracking
        self.consultation_stats = {
            "total_proposals_submitted": 0,
            "proposals_advanced": 0,
            "total_feedback_collected": 0,
            "unique_participants": 0,
            "average_engagement_time": 0.0,
            "sentiment_accuracy": 0.0
        }
        
        logger.info("Public Consultation Service initialized")
    
    async def submit_public_proposal(
        self,
        db: AsyncSession,
        proposal: PublicProposal,
        auto_review: bool = True
    ) -> PublicProposal:
        """
        Submit a public amendment proposal for consideration.
        
        Args:
            db: Database session
            proposal: Public proposal details
            auto_review: Whether to automatically review the proposal
            
        Returns:
            PublicProposal with assigned ID and status
        """
        try:
            # Validate proposal content
            if not proposal.title or len(proposal.title.strip()) < 10:
                raise ValueError("Proposal title must be at least 10 characters")
            
            if not proposal.description or len(proposal.description.strip()) < 50:
                raise ValueError("Proposal description must be at least 50 characters")
            
            if not proposal.proposed_changes or len(proposal.proposed_changes.strip()) < 20:
                raise ValueError("Proposed changes must be at least 20 characters")
            
            # Set initial status
            proposal.status = ConsultationStatus.DRAFT
            proposal.created_at = datetime.utcnow()
            
            # Store proposal (simplified - would use actual database model)
            proposal.id = self.consultation_stats["total_proposals_submitted"] + 1
            self.consultation_stats["total_proposals_submitted"] += 1
            
            # Perform automatic review if enabled
            if auto_review:
                review_result = await self._review_proposal_content(proposal)
                if review_result["approved"]:
                    proposal.status = ConsultationStatus.OPEN
                    proposal.requires_review = False
                else:
                    proposal.requires_review = True
                    proposal.metadata = {"review_notes": review_result["notes"]}
            
            # Integrate with HITL sampling for oversight
            if self.hitl_sampler:
                await self._assess_proposal_for_oversight(db, proposal)
            
            logger.info(f"Public proposal submitted: {proposal.title} (ID: {proposal.id})")
            
            return proposal
            
        except Exception as e:
            logger.error(f"Failed to submit public proposal: {e}")
            raise
    
    async def collect_public_feedback(
        self,
        db: AsyncSession,
        feedback: PublicFeedback,
        verify_submitter: bool = False
    ) -> PublicFeedback:
        """
        Collect public feedback on proposals or amendments.
        
        Args:
            db: Database session
            feedback: Public feedback details
            verify_submitter: Whether to verify submitter identity
            
        Returns:
            PublicFeedback with processing results
        """
        try:
            # Validate feedback content
            if not feedback.content or len(feedback.content.strip()) < 10:
                raise ValueError("Feedback content must be at least 10 characters")
            
            if len(feedback.content) > self.config["max_feedback_length"]:
                raise ValueError(f"Feedback exceeds maximum length of {self.config['max_feedback_length']} characters")
            
            # Perform sentiment analysis
            if self.config["auto_sentiment_analysis"]:
                feedback.sentiment_score = await self._analyze_sentiment(feedback.content)
                feedback.feedback_type = self._classify_feedback_type(feedback.content, feedback.sentiment_score)
            
            # Verify submitter if required
            if verify_submitter and feedback.submitter_email:
                feedback.is_verified = await self._verify_submitter_email(feedback.submitter_email)
            
            # Store feedback (simplified - would use actual database model)
            feedback.id = self.consultation_stats["total_feedback_collected"] + 1
            feedback.created_at = datetime.utcnow()
            self.consultation_stats["total_feedback_collected"] += 1
            
            # Update unique participants count
            if feedback.submitter_email:
                self.consultation_stats["unique_participants"] += 1
            
            # Integrate with HITL sampling for feedback analysis
            if self.hitl_sampler and feedback.sentiment_score and feedback.sentiment_score < 0.3:
                await self._escalate_negative_feedback(db, feedback)
            
            logger.info(f"Public feedback collected: {feedback.feedback_type.value} "
                       f"(sentiment: {feedback.sentiment_score:.2f if feedback.sentiment_score else 'N/A'})")
            
            return feedback
            
        except Exception as e:
            logger.error(f"Failed to collect public feedback: {e}")
            raise
    
    async def get_consultation_metrics(
        self,
        db: AsyncSession,
        time_period_days: Optional[int] = 30
    ) -> ConsultationMetrics:
        """
        Get comprehensive consultation metrics.
        
        Args:
            db: Database session
            time_period_days: Time period for metrics calculation
            
        Returns:
            ConsultationMetrics with current statistics
        """
        try:
            # Calculate time window
            if time_period_days:
                start_date = datetime.utcnow() - timedelta(days=time_period_days)
            else:
                start_date = None
            
            # Mock metrics calculation (would use actual database queries)
            metrics = ConsultationMetrics(
                total_proposals=self.consultation_stats["total_proposals_submitted"],
                active_consultations=max(1, self.consultation_stats["total_proposals_submitted"] // 3),
                total_participants=self.consultation_stats["unique_participants"],
                feedback_count=self.consultation_stats["total_feedback_collected"],
                sentiment_distribution={
                    "positive": 45,
                    "neutral": 35,
                    "negative": 20
                },
                stakeholder_participation={
                    "citizen": 60,
                    "expert": 25,
                    "civil_society": 10,
                    "industry": 5
                },
                engagement_rate=0.75,
                completion_rate=0.68
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get consultation metrics: {e}")
            return ConsultationMetrics()
    
    async def advance_proposal_to_council(
        self,
        db: AsyncSession,
        proposal_id: int,
        council_user_id: int
    ) -> Dict[str, Any]:
        """
        Advance a public proposal to Constitutional Council consideration.
        
        Args:
            db: Database session
            proposal_id: ID of the proposal to advance
            council_user_id: ID of the council member advancing the proposal
            
        Returns:
            Result of advancement process
        """
        try:
            # Get proposal (mock implementation)
            proposal = PublicProposal(
                id=proposal_id,
                title=f"Public Proposal {proposal_id}",
                description="Mock proposal description",
                status=ConsultationStatus.REVIEW
            )
            
            # Check if proposal meets advancement criteria
            advancement_check = await self._check_advancement_criteria(db, proposal)
            
            if not advancement_check["eligible"]:
                return {
                    "success": False,
                    "reason": advancement_check["reason"],
                    "proposal_id": proposal_id
                }
            
            # Create Constitutional Council amendment from proposal
            amendment_data = {
                "principle_id": 1,  # Would be determined from proposal
                "amendment_type": "modify",
                "proposed_changes": proposal.proposed_changes,
                "justification": f"Public proposal: {proposal.justification}",
                "proposed_content": proposal.description,
                "urgency_level": "normal",
                "consultation_period_days": 30,
                "public_comment_enabled": True,
                "stakeholder_groups": ["citizens", "experts", "affected_parties"]
            }
            
            # Update proposal status
            proposal.status = ConsultationStatus.IMPLEMENTED
            self.consultation_stats["proposals_advanced"] += 1
            
            logger.info(f"Public proposal {proposal_id} advanced to Constitutional Council")
            
            return {
                "success": True,
                "proposal_id": proposal_id,
                "amendment_created": True,
                "council_user_id": council_user_id,
                "advancement_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to advance proposal to council: {e}")
            return {"success": False, "error": str(e)}
    
    # Helper methods
    async def _review_proposal_content(self, proposal: PublicProposal) -> Dict[str, Any]:
        """Review proposal content for appropriateness and completeness."""
        # Simplified content review
        inappropriate_keywords = ["spam", "offensive", "irrelevant"]
        content_to_check = f"{proposal.title} {proposal.description} {proposal.proposed_changes}".lower()
        
        has_inappropriate_content = any(keyword in content_to_check for keyword in inappropriate_keywords)
        
        return {
            "approved": not has_inappropriate_content,
            "notes": "Automated content review passed" if not has_inappropriate_content else "Content requires manual review"
        }
    
    async def _analyze_sentiment(self, content: str) -> float:
        """Analyze sentiment of feedback content."""
        # Simplified sentiment analysis
        positive_words = ["good", "excellent", "support", "agree", "beneficial", "helpful"]
        negative_words = ["bad", "terrible", "oppose", "disagree", "harmful", "problematic"]
        
        content_lower = content.lower()
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        total_words = len(content.split())
        if total_words == 0:
            return 0.5
        
        sentiment_score = 0.5 + (positive_count - negative_count) / (total_words * 2)
        return max(0.0, min(1.0, sentiment_score))
    
    def _classify_feedback_type(self, content: str, sentiment_score: Optional[float]) -> FeedbackType:
        """Classify feedback type based on content and sentiment."""
        if sentiment_score is None:
            return FeedbackType.NEUTRAL
        
        content_lower = content.lower()
        
        if "suggest" in content_lower or "recommend" in content_lower:
            return FeedbackType.SUGGESTION
        elif "concern" in content_lower or "worry" in content_lower:
            return FeedbackType.CONCERN
        elif "question" in content_lower or "?" in content:
            return FeedbackType.QUESTION
        elif sentiment_score > 0.6:
            return FeedbackType.SUPPORT
        elif sentiment_score < 0.4:
            return FeedbackType.OPPOSE
        else:
            return FeedbackType.NEUTRAL
    
    async def _verify_submitter_email(self, email: str) -> bool:
        """Verify submitter email address."""
        # Simplified email verification
        return "@" in email and "." in email.split("@")[1]
    
    async def _assess_proposal_for_oversight(self, db: AsyncSession, proposal: PublicProposal):
        """Assess proposal for HITL oversight requirements."""
        if not self.hitl_sampler:
            return
        
        decision_context = {
            "decision_id": f"public_proposal_{proposal.id}",
            "proposal_title": proposal.title,
            "stakeholder_group": proposal.stakeholder_group.value,
            "requires_review": proposal.requires_review,
            "consultation_period": proposal.consultation_period_days
        }
        
        assessment = await self.hitl_sampler.assess_uncertainty(
            db=db,
            decision_context=decision_context,
            ai_confidence=0.8,  # Default confidence for public proposals
            principle_ids=None
        )
        
        if assessment.requires_human_oversight:
            logger.info(f"Public proposal {proposal.id} requires human oversight: "
                       f"{assessment.recommended_oversight_level.value}")
    
    async def _escalate_negative_feedback(self, db: AsyncSession, feedback: PublicFeedback):
        """Escalate negative feedback for review."""
        if not self.hitl_sampler:
            return
        
        decision_context = {
            "decision_id": f"negative_feedback_{feedback.id}",
            "feedback_type": feedback.feedback_type.value,
            "sentiment_score": feedback.sentiment_score,
            "stakeholder_group": feedback.stakeholder_group.value
        }
        
        assessment = await self.hitl_sampler.assess_uncertainty(
            db=db,
            decision_context=decision_context,
            ai_confidence=0.6,  # Lower confidence for negative feedback
            principle_ids=None
        )
        
        if assessment.requires_human_oversight:
            logger.warning(f"Negative feedback {feedback.id} escalated for review")
    
    async def _check_advancement_criteria(self, db: AsyncSession, proposal: PublicProposal) -> Dict[str, Any]:
        """Check if proposal meets criteria for advancement to Constitutional Council."""
        # Simplified advancement criteria
        if proposal.public_support_count < self.config["min_support_threshold"]:
            return {
                "eligible": False,
                "reason": f"Insufficient public support (minimum: {self.config['min_support_threshold']})"
            }
        
        if proposal.status not in [ConsultationStatus.OPEN, ConsultationStatus.ACTIVE]:
            return {
                "eligible": False,
                "reason": "Proposal not in eligible status for advancement"
            }
        
        return {"eligible": True, "reason": "Proposal meets advancement criteria"}
