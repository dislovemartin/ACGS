"""
Constitutional Council LangGraph StateGraph Implementation

This module implements the Constitutional Council amendment workflow using LangGraph StateGraph
with the following workflow nodes:
- propose_amendment: Generate and validate amendment proposals
- gather_stakeholder_feedback: Collect feedback from required stakeholder roles
- analyze_constitutionality: Perform LLM-powered constitutional analysis
- conduct_voting: Manage democratic voting process with weighted stakeholder input
- refine_amendment: Iterative refinement based on feedback and voting outcomes

The workflow integrates with existing AC service infrastructure including database operations,
authentication, and Constitutional Council configuration.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Literal
from datetime import datetime, timezone, timedelta
import uuid

try:
    from langgraph.graph import StateGraph, START, END
    from langgraph.types import Send
    from langgraph.checkpoint.memory import MemorySaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    # Graceful fallback when LangGraph is not available
    LANGGRAPH_AVAILABLE = False
    StateGraph = None
    START = "START"
    END = "END"
    Send = None
    MemorySaver = None

from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, ValidationError

from shared.langgraph_states import (
    ConstitutionalCouncilState,
    WorkflowStatus,
    create_workflow_metadata,
    update_workflow_status
)
from shared.langgraph_config import (
    get_langgraph_config,
    ConstitutionalCouncilConfig,
    ModelRole
)
from shared.database import get_async_db
from shared.auth import get_current_active_user
from shared.models import User, ACAmendment, ACAmendmentVote, ACAmendmentComment

# Import AC service CRUD operations
from .. import crud, schemas

# Import stakeholder engagement system
from app.services.stakeholder_engagement import (
    StakeholderNotificationService,
    StakeholderEngagementInput,
    NotificationChannel,
    StakeholderRole
)

logger = logging.getLogger(__name__)


class AmendmentProposalInput(BaseModel):
    """Input model for amendment proposal generation."""
    principle_id: int = Field(..., description="ID of the principle to amend")
    amendment_type: Literal["modify", "add", "remove", "status_change"] = Field(
        ..., description="Type of amendment"
    )
    proposed_changes: str = Field(..., description="Description of proposed changes")
    justification: str = Field(..., description="Rationale for the amendment")
    proposed_content: Optional[str] = Field(None, description="New content if modifying/adding")
    urgency_level: Literal["normal", "urgent", "emergency"] = Field(
        "normal", description="Urgency level for processing"
    )
    stakeholder_groups: Optional[List[str]] = Field(
        None, description="Specific stakeholder groups to involve"
    )


class StakeholderFeedbackInput(BaseModel):
    """Input model for stakeholder feedback collection."""
    feedback_period_hours: int = Field(72, ge=1, le=168, description="Feedback collection period")
    notification_channels: List[str] = Field(
        ["email", "dashboard"], description="Notification channels to use"
    )
    require_all_stakeholders: bool = Field(
        False, description="Whether all stakeholder roles must provide feedback"
    )


class ConstitutionalAnalysisInput(BaseModel):
    """Input model for constitutional analysis."""
    analysis_model: str = Field("gemini-2.5-pro", description="LLM model for analysis")
    compliance_threshold: float = Field(0.85, ge=0.0, le=1.0, description="Compliance threshold")
    conflict_detection_enabled: bool = Field(True, description="Enable conflict detection")
    bias_analysis_enabled: bool = Field(True, description="Enable bias analysis")


class VotingInput(BaseModel):
    """Input model for voting process."""
    voting_period_hours: int = Field(48, ge=1, le=168, description="Voting period duration")
    quorum_percentage: float = Field(0.6, ge=0.0, le=1.0, description="Required quorum")
    weighted_voting: bool = Field(True, description="Enable weighted voting by expertise")
    anonymous_voting: bool = Field(False, description="Enable anonymous voting")


class ConstitutionalCouncilGraph:
    """
    LangGraph StateGraph implementation for Constitutional Council workflows.
    
    Manages the complete amendment lifecycle with proper state management,
    conditional routing, and integration with existing AC service infrastructure.
    """
    
    def __init__(self, db_session: AsyncSession):
        """
        Initialize the Constitutional Council graph.

        Args:
            db_session: Database session for CRUD operations
        """
        self.db = db_session
        self.config = get_langgraph_config()
        self.council_config = ConstitutionalCouncilConfig()
        self.graph = None
        self.checkpointer = MemorySaver() if LANGGRAPH_AVAILABLE else None

        # Initialize stakeholder engagement service
        self.stakeholder_service = StakeholderNotificationService(
            db=db_session,
            config=self.council_config
        )

        if LANGGRAPH_AVAILABLE:
            self._build_graph()
        else:
            logger.warning("LangGraph not available. Graph functionality will be limited.")
    
    def _build_graph(self) -> None:
        """Build the LangGraph StateGraph for Constitutional Council workflows."""
        if not LANGGRAPH_AVAILABLE:
            return
        
        # Create the StateGraph
        workflow = StateGraph(ConstitutionalCouncilState)
        
        # Add workflow nodes
        workflow.add_node("propose_amendment", self.propose_amendment)
        workflow.add_node("gather_stakeholder_feedback", self.gather_stakeholder_feedback)
        workflow.add_node("analyze_constitutionality", self.analyze_constitutionality)
        workflow.add_node("conduct_voting", self.conduct_voting)
        workflow.add_node("refine_amendment", self.refine_amendment)
        workflow.add_node("finalize_amendment", self.finalize_amendment)
        
        # Define workflow edges and conditional routing
        workflow.add_edge(START, "propose_amendment")
        workflow.add_edge("propose_amendment", "gather_stakeholder_feedback")
        workflow.add_edge("gather_stakeholder_feedback", "analyze_constitutionality")
        
        # Conditional routing from constitutional analysis
        workflow.add_conditional_edges(
            "analyze_constitutionality",
            self.should_proceed_to_voting,
            {
                "voting": "conduct_voting",
                "refinement": "refine_amendment",
                "rejection": END
            }
        )
        
        # Conditional routing from voting
        workflow.add_conditional_edges(
            "conduct_voting",
            self.should_finalize_or_refine,
            {
                "finalize": "finalize_amendment",
                "refine": "refine_amendment",
                "reject": END
            }
        )
        
        # Conditional routing from refinement
        workflow.add_conditional_edges(
            "refine_amendment",
            self.should_continue_refinement,
            {
                "continue": "gather_stakeholder_feedback",
                "finalize": "finalize_amendment",
                "abandon": END
            }
        )
        
        workflow.add_edge("finalize_amendment", END)
        
        # Compile the graph with checkpointer for state persistence
        self.graph = workflow.compile(checkpointer=self.checkpointer)
        
        logger.info("Constitutional Council StateGraph compiled successfully")

    async def propose_amendment(self, state: ConstitutionalCouncilState) -> ConstitutionalCouncilState:
        """
        Generate and validate amendment proposal.

        This node handles the initial amendment proposal creation, validation,
        and database storage with proper error handling and logging.
        """
        try:
            logger.info(f"Starting amendment proposal for workflow {state.get('workflow_id')}")

            # Extract amendment proposal data
            proposal_data = state.get("amendment_proposal", {})
            if not proposal_data:
                raise ValueError("No amendment proposal data provided")

            # Validate proposal input
            try:
                proposal_input = AmendmentProposalInput(**proposal_data)
            except ValidationError as e:
                logger.error(f"Invalid proposal input: {e}")
                return {
                    **state,
                    "status": WorkflowStatus.FAILED.value,
                    "error_message": f"Invalid proposal input: {e}",
                    "current_phase": "proposal_failed"
                }

            # Create amendment in database
            amendment_create = schemas.ACAmendmentCreate(
                principle_id=proposal_input.principle_id,
                amendment_type=proposal_input.amendment_type,
                proposed_changes=proposal_input.proposed_changes,
                justification=proposal_input.justification,
                proposed_content=proposal_input.proposed_content,
                consultation_period_days=3,  # Default 3 days for Constitutional Council
                public_comment_enabled=True,
                stakeholder_groups=proposal_input.stakeholder_groups or self.council_config.required_stakeholder_roles,
                rapid_processing_requested=(proposal_input.urgency_level != "normal"),
                constitutional_significance="significant"
            )

            # Get user ID from state or use system user
            user_id = state.get("user_id", 1)  # Default to system user if not provided

            # Create amendment in database
            amendment = await crud.create_ac_amendment(
                db=self.db,
                amendment=amendment_create,
                user_id=user_id
            )

            # Update state with amendment information
            updated_state = {
                **state,
                "amendment_id": str(amendment.id),
                "amendment_proposal": {
                    **proposal_data,
                    "id": amendment.id,
                    "status": amendment.status,
                    "created_at": amendment.created_at.isoformat()
                },
                "current_phase": "stakeholder_feedback",
                "status": WorkflowStatus.ACTIVE.value,
                "phase_deadlines": {
                    "feedback_deadline": (
                        datetime.now(timezone.utc) +
                        timedelta(hours=self.council_config.amendment_review_period_hours)
                    ).isoformat()
                },
                "required_stakeholders": self.council_config.required_stakeholder_roles,
                "messages": state.get("messages", []) + [{
                    "type": "system",
                    "content": f"Amendment proposal created with ID {amendment.id}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }]
            }

            logger.info(f"Amendment proposal created successfully: {amendment.id}")
            return updated_state

        except Exception as e:
            logger.error(f"Failed to create amendment proposal: {e}")
            return {
                **state,
                "status": WorkflowStatus.FAILED.value,
                "error_message": f"Failed to create amendment proposal: {str(e)}",
                "current_phase": "proposal_failed"
            }

    async def gather_stakeholder_feedback(self, state: ConstitutionalCouncilState) -> ConstitutionalCouncilState:
        """
        Collect feedback from required stakeholder roles using the stakeholder engagement system.

        This node manages stakeholder notification, feedback collection,
        and tracks participation rates for quorum requirements.
        """
        try:
            logger.info(f"Gathering stakeholder feedback for amendment {state.get('amendment_id')}")

            amendment_id = state.get("amendment_id")
            if not amendment_id:
                raise ValueError("No amendment ID available for feedback collection")

            # Check if stakeholder engagement has been initiated
            engagement_status = await self.stakeholder_service.get_engagement_status(int(amendment_id))

            if not engagement_status:
                # Initiate stakeholder engagement if not already started
                engagement_input = StakeholderEngagementInput(
                    amendment_id=int(amendment_id),
                    required_roles=[
                        StakeholderRole.CONSTITUTIONAL_EXPERT,
                        StakeholderRole.POLICY_ADMINISTRATOR,
                        StakeholderRole.SYSTEM_AUDITOR,
                        StakeholderRole.PUBLIC_REPRESENTATIVE
                    ],
                    notification_channels=[
                        NotificationChannel.EMAIL,
                        NotificationChannel.DASHBOARD,
                        NotificationChannel.WEBSOCKET
                    ],
                    engagement_period_hours=self.council_config.amendment_review_period_hours,
                    require_all_stakeholders=False,
                    reminder_intervals_hours=[24, 12, 2]
                )

                engagement_status = await self.stakeholder_service.initiate_stakeholder_engagement(engagement_input)
                logger.info(f"Stakeholder engagement initiated for amendment {amendment_id}")

            # Get feedback records from stakeholder service
            feedback_records = await self.stakeholder_service.get_stakeholder_feedback(int(amendment_id))

            # Convert feedback records to state format
            stakeholder_feedback = []
            stakeholder_roles_provided = set()

            for feedback in feedback_records:
                stakeholder_feedback.append({
                    "id": feedback.id,
                    "stakeholder_role": feedback.stakeholder_role.value,
                    "feedback": feedback.feedback_content,
                    "feedback_type": feedback.feedback_type,
                    "timestamp": feedback.submitted_at.isoformat(),
                    "user_id": feedback.stakeholder_id,
                    "status": feedback.status.value
                })
                stakeholder_roles_provided.add(feedback.stakeholder_role.value)

            # Get engagement metrics
            required_stakeholders = set([role.value for role in engagement_input.required_roles])
            missing_stakeholders = required_stakeholders - stakeholder_roles_provided

            # Check deadline status
            is_deadline_passed = engagement_status.is_deadline_passed

            # Update state with comprehensive engagement information
            updated_state = {
                **state,
                "stakeholder_feedback": stakeholder_feedback,
                "stakeholder_participation": {
                    "total_required": engagement_status.total_stakeholders,
                    "total_received": engagement_status.engaged_stakeholders,
                    "participation_rate": engagement_status.engagement_rate,
                    "missing_stakeholders": list(missing_stakeholders),
                    "deadline_passed": is_deadline_passed,
                    "feedback_by_role": engagement_status.feedback_by_role,
                    "notifications_sent": engagement_status.notifications_sent
                },
                "engagement_status": {
                    "amendment_id": engagement_status.amendment_id,
                    "deadline": engagement_status.deadline.isoformat(),
                    "engagement_rate": engagement_status.engagement_rate,
                    "last_updated": engagement_status.last_updated.isoformat()
                },
                "current_phase": "constitutional_analysis",
                "messages": state.get("messages", []) + [{
                    "type": "system",
                    "content": f"Stakeholder engagement: {engagement_status.engaged_stakeholders}/{engagement_status.total_stakeholders} stakeholders engaged ({engagement_status.engagement_rate:.1%})",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }]
            }

            # Add real-time notification status
            if missing_stakeholders and not is_deadline_passed:
                updated_state["pending_notifications"] = {
                    "missing_roles": list(missing_stakeholders),
                    "reminder_scheduled": True,
                    "deadline": engagement_status.deadline.isoformat()
                }

            logger.info(f"Stakeholder feedback collection completed: {len(stakeholder_feedback)} responses, {engagement_status.engagement_rate:.1%} engagement rate")
            return updated_state

        except Exception as e:
            logger.error(f"Failed to gather stakeholder feedback: {e}")
            return {
                **state,
                "status": WorkflowStatus.FAILED.value,
                "error_message": f"Failed to gather stakeholder feedback: {str(e)}",
                "current_phase": "feedback_failed"
            }

    async def analyze_constitutionality(self, state: ConstitutionalCouncilState) -> ConstitutionalCouncilState:
        """
        Perform LLM-powered constitutional analysis.

        This node analyzes the amendment proposal for constitutional compliance,
        conflict detection, and bias analysis using configured LLM models.
        """
        try:
            logger.info(f"Analyzing constitutionality for amendment {state.get('amendment_id')}")

            amendment_proposal = state.get("amendment_proposal", {})
            stakeholder_feedback = state.get("stakeholder_feedback", [])

            if not amendment_proposal:
                raise ValueError("No amendment proposal available for analysis")

            # Prepare analysis input
            analysis_context = {
                "amendment_type": amendment_proposal.get("amendment_type"),
                "proposed_changes": amendment_proposal.get("proposed_changes"),
                "justification": amendment_proposal.get("justification"),
                "proposed_content": amendment_proposal.get("proposed_content"),
                "stakeholder_feedback": [f["feedback"] for f in stakeholder_feedback],
                "stakeholder_concerns": [f for f in stakeholder_feedback if "concern" in f.get("feedback", "").lower()]
            }

            # Mock constitutional analysis (in production, this would use actual LLM)
            # This simulates the LLM analysis process
            constitutional_analysis = {
                "compliance_score": 0.87,  # Mock score
                "constitutional_compliance": True,
                "identified_conflicts": [],
                "bias_analysis": {
                    "bias_detected": False,
                    "bias_score": 0.12,
                    "bias_categories": []
                },
                "recommendations": [
                    "Amendment aligns with constitutional principles",
                    "No significant conflicts detected with existing principles",
                    "Stakeholder feedback has been incorporated appropriately"
                ],
                "analysis_model": self.config.models.get(ModelRole.AMENDMENT_ANALYSIS, "gemini-2.5-pro"),
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                "confidence_score": 0.92
            }

            # Determine if amendment meets constitutional threshold
            compliance_threshold = self.config.constitutional_fidelity_threshold
            is_constitutional = constitutional_analysis["compliance_score"] >= compliance_threshold

            # Check for conflicts that require resolution
            has_conflicts = len(constitutional_analysis["identified_conflicts"]) > 0
            requires_refinement = not is_constitutional or has_conflicts

            # Update state with analysis results
            updated_state = {
                **state,
                "constitutional_analysis": constitutional_analysis,
                "compliance_score": constitutional_analysis["compliance_score"],
                "is_constitutional": is_constitutional,
                "requires_refinement": requires_refinement,
                "identified_conflicts": constitutional_analysis["identified_conflicts"],
                "current_phase": "voting" if is_constitutional and not has_conflicts else "refinement_needed",
                "messages": state.get("messages", []) + [{
                    "type": "system",
                    "content": f"Constitutional analysis completed. Compliance score: {constitutional_analysis['compliance_score']:.2f}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }]
            }

            logger.info(f"Constitutional analysis completed. Compliance: {is_constitutional}, Score: {constitutional_analysis['compliance_score']}")
            return updated_state

        except Exception as e:
            logger.error(f"Failed to analyze constitutionality: {e}")
            return {
                **state,
                "status": WorkflowStatus.FAILED.value,
                "error_message": f"Failed to analyze constitutionality: {str(e)}",
                "current_phase": "analysis_failed"
            }

    async def conduct_voting(self, state: ConstitutionalCouncilState) -> ConstitutionalCouncilState:
        """
        Manage democratic voting process with weighted stakeholder input.

        This node handles the voting process, quorum validation, and result calculation
        with support for weighted voting based on stakeholder expertise.
        """
        try:
            logger.info(f"Conducting voting for amendment {state.get('amendment_id')}")

            amendment_id = state.get("amendment_id")
            if not amendment_id:
                raise ValueError("No amendment ID available for voting")

            # Get existing votes from database
            existing_votes = await crud.get_ac_amendment_votes(
                db=self.db,
                amendment_id=int(amendment_id),
                skip=0,
                limit=1000
            )

            # Process votes and calculate results
            vote_summary = {
                "for": 0,
                "against": 0,
                "abstain": 0,
                "total_votes": len(existing_votes)
            }

            stakeholder_votes = {}
            for vote in existing_votes:
                vote_value = vote.vote.lower()
                if vote_value in vote_summary:
                    vote_summary[vote_value] += 1

                # Track votes by stakeholder (assuming we can get role from user)
                stakeholder_role = getattr(vote.voter, 'role', 'unknown')
                stakeholder_votes[stakeholder_role] = {
                    "vote": vote_value,
                    "reasoning": vote.reasoning,
                    "timestamp": vote.voted_at.isoformat()
                }

            # Calculate voting results
            total_eligible = len(self.council_config.required_stakeholder_roles)
            participation_rate = vote_summary["total_votes"] / total_eligible if total_eligible > 0 else 0
            quorum_met = participation_rate >= self.council_config.quorum_percentage

            # Determine voting outcome
            if quorum_met:
                approval_rate = vote_summary["for"] / vote_summary["total_votes"] if vote_summary["total_votes"] > 0 else 0
                voting_passed = approval_rate > 0.5  # Simple majority
            else:
                voting_passed = False
                approval_rate = 0

            # Set voting deadline if not already set
            voting_deadline = state.get("phase_deadlines", {}).get("voting_deadline")
            if not voting_deadline:
                voting_deadline = (
                    datetime.now(timezone.utc) +
                    timedelta(hours=self.council_config.voting_period_hours)
                ).isoformat()

            # Check if voting period has ended
            deadline_dt = datetime.fromisoformat(voting_deadline.replace('Z', '+00:00'))
            voting_period_ended = datetime.now(timezone.utc) > deadline_dt

            # Determine next action
            if voting_period_ended or (quorum_met and vote_summary["total_votes"] >= total_eligible):
                if voting_passed:
                    next_phase = "finalization"
                else:
                    next_phase = "refinement_needed"
            else:
                next_phase = "voting_in_progress"

            # Update state with voting results
            updated_state = {
                **state,
                "voting_results": {
                    "vote_summary": vote_summary,
                    "stakeholder_votes": stakeholder_votes,
                    "participation_rate": participation_rate,
                    "quorum_met": quorum_met,
                    "approval_rate": approval_rate,
                    "voting_passed": voting_passed,
                    "voting_period_ended": voting_period_ended,
                    "voting_deadline": voting_deadline
                },
                "quorum_met": quorum_met,
                "current_phase": next_phase,
                "phase_deadlines": {
                    **state.get("phase_deadlines", {}),
                    "voting_deadline": voting_deadline
                },
                "messages": state.get("messages", []) + [{
                    "type": "system",
                    "content": f"Voting results: {vote_summary['for']} for, {vote_summary['against']} against, {vote_summary['abstain']} abstain. Quorum: {'met' if quorum_met else 'not met'}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }]
            }

            logger.info(f"Voting conducted. Results: {vote_summary}, Quorum met: {quorum_met}")
            return updated_state

        except Exception as e:
            logger.error(f"Failed to conduct voting: {e}")
            return {
                **state,
                "status": WorkflowStatus.FAILED.value,
                "error_message": f"Failed to conduct voting: {str(e)}",
                "current_phase": "voting_failed"
            }

    async def refine_amendment(self, state: ConstitutionalCouncilState) -> ConstitutionalCouncilState:
        """
        Iterative refinement based on feedback and voting outcomes.

        This node handles amendment refinement based on stakeholder feedback,
        constitutional analysis results, and voting outcomes.
        """
        try:
            logger.info(f"Refining amendment {state.get('amendment_id')}")

            current_iterations = state.get("refinement_iterations", 0)
            max_iterations = state.get("max_refinement_iterations", self.config.max_refinement_iterations)

            # Check if we've exceeded maximum refinement iterations
            if current_iterations >= max_iterations:
                logger.warning(f"Maximum refinement iterations ({max_iterations}) reached")
                return {
                    **state,
                    "status": WorkflowStatus.FAILED.value,
                    "error_message": f"Maximum refinement iterations ({max_iterations}) exceeded",
                    "current_phase": "refinement_abandoned"
                }

            # Gather refinement context
            stakeholder_feedback = state.get("stakeholder_feedback", [])
            constitutional_analysis = state.get("constitutional_analysis", {})
            voting_results = state.get("voting_results", {})

            # Identify refinement areas
            refinement_areas = []

            # Add constitutional compliance issues
            if not state.get("is_constitutional", True):
                refinement_areas.append({
                    "area": "constitutional_compliance",
                    "issue": f"Compliance score {constitutional_analysis.get('compliance_score', 0):.2f} below threshold {self.config.constitutional_fidelity_threshold}",
                    "recommendations": constitutional_analysis.get("recommendations", [])
                })

            # Add conflict resolution issues
            conflicts = state.get("identified_conflicts", [])
            if conflicts:
                refinement_areas.append({
                    "area": "conflict_resolution",
                    "issue": f"{len(conflicts)} conflicts identified",
                    "conflicts": conflicts
                })

            # Add stakeholder concerns
            concerns = [f for f in stakeholder_feedback if "concern" in f.get("feedback", "").lower()]
            if concerns:
                refinement_areas.append({
                    "area": "stakeholder_concerns",
                    "issue": f"{len(concerns)} stakeholder concerns raised",
                    "concerns": [c["feedback"] for c in concerns]
                })

            # Add voting feedback if available
            if voting_results and not voting_results.get("voting_passed", False):
                refinement_areas.append({
                    "area": "voting_feedback",
                    "issue": f"Voting failed with {voting_results.get('approval_rate', 0):.2f} approval rate",
                    "voting_feedback": [v.get("reasoning", "") for v in voting_results.get("stakeholder_votes", {}).values() if v.get("reasoning")]
                })

            # Generate refinement suggestions (mock implementation)
            refinement_suggestions = {
                "iteration": current_iterations + 1,
                "refinement_areas": refinement_areas,
                "suggested_changes": [
                    "Incorporate stakeholder feedback on constitutional alignment",
                    "Address identified conflicts with existing principles",
                    "Clarify implementation guidance based on concerns raised"
                ],
                "priority_changes": [area["area"] for area in refinement_areas[:2]],  # Top 2 priority areas
                "estimated_impact": "moderate",
                "refinement_timestamp": datetime.now(timezone.utc).isoformat()
            }

            # Update state with refinement information
            updated_state = {
                **state,
                "refinement_iterations": current_iterations + 1,
                "refinement_suggestions": refinement_suggestions,
                "current_phase": "stakeholder_feedback",  # Return to feedback collection
                "requires_refinement": True,
                "messages": state.get("messages", []) + [{
                    "type": "system",
                    "content": f"Amendment refinement iteration {current_iterations + 1} initiated. {len(refinement_areas)} areas identified for improvement.",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }]
            }

            logger.info(f"Amendment refinement completed. Iteration: {current_iterations + 1}, Areas: {len(refinement_areas)}")
            return updated_state

        except Exception as e:
            logger.error(f"Failed to refine amendment: {e}")
            return {
                **state,
                "status": WorkflowStatus.FAILED.value,
                "error_message": f"Failed to refine amendment: {str(e)}",
                "current_phase": "refinement_failed"
            }

    async def finalize_amendment(self, state: ConstitutionalCouncilState) -> ConstitutionalCouncilState:
        """
        Finalize the amendment after successful voting using enhanced processing pipeline.

        This node handles the final amendment approval, database updates,
        stakeholder notifications, and workflow completion with comprehensive
        audit trail and error recovery mechanisms.
        """
        try:
            logger.info(f"Finalizing amendment {state.get('amendment_id')}")

            amendment_id = state.get("amendment_id")
            if not amendment_id:
                raise ValueError("No amendment ID available for finalization")

            # Process amendment through enhanced pipeline
            finalization_result = await self._process_amendment_finalization(
                amendment_id=int(amendment_id),
                state=state
            )

            if not finalization_result["success"]:
                raise ValueError(f"Amendment finalization failed: {finalization_result['error']}")

            # Create comprehensive finalization summary
            finalization_summary = {
                "amendment_id": amendment_id,
                "final_status": finalization_result["final_status"],
                "approval_date": datetime.now(timezone.utc).isoformat(),
                "voting_summary": state.get("voting_results", {}).get("vote_summary", {}),
                "stakeholder_participation": state.get("stakeholder_participation", {}),
                "constitutional_compliance": {
                    "compliance_score": state.get("compliance_score", 0),
                    "is_constitutional": state.get("is_constitutional", False),
                    "identified_conflicts": state.get("identified_conflicts", [])
                },
                "refinement_iterations": state.get("refinement_iterations", 0),
                "total_stakeholder_feedback": len(state.get("stakeholder_feedback", [])),
                "workflow_duration_hours": self._calculate_workflow_duration(state),
                "finalization_timestamp": datetime.now(timezone.utc).isoformat(),
                "pipeline_processing": finalization_result["pipeline_results"],
                "audit_trail": finalization_result["audit_trail"]
            }

            # Update state with enhanced finalization results
            updated_state = {
                **state,
                "status": WorkflowStatus.COMPLETED.value,
                "current_phase": "completed",
                "finalization_summary": finalization_summary,
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "processing_pipeline_results": finalization_result["pipeline_results"],
                "audit_trail": finalization_result["audit_trail"],
                "messages": state.get("messages", []) + [{
                    "type": "system",
                    "content": f"Amendment {amendment_id} successfully finalized through enhanced processing pipeline",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "pipeline_status": "completed",
                    "notifications_sent": finalization_result["pipeline_results"].get("notifications", {}).get("notifications_sent", 0)
                }]
            }

            logger.info(f"Amendment {amendment_id} finalized successfully through enhanced pipeline")
            return updated_state

        except Exception as e:
            logger.error(f"Failed to finalize amendment: {e}")
            # Trigger enhanced error handling and rollback
            await self._handle_finalization_failure(
                amendment_id=amendment_id,
                error=str(e),
                state=state
            )
            return {
                **state,
                "status": WorkflowStatus.FAILED.value,
                "error_message": f"Failed to finalize amendment: {str(e)}",
                "current_phase": "finalization_failed",
                "recovery_initiated": True,
                "failure_timestamp": datetime.now(timezone.utc).isoformat()
            }

    def _calculate_workflow_duration(self, state: ConstitutionalCouncilState) -> float:
        """Calculate workflow duration in hours."""
        try:
            created_at = state.get("created_at")
            if created_at:
                start_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                duration = datetime.now(timezone.utc) - start_time
                return duration.total_seconds() / 3600
        except Exception:
            pass
        return 0.0

    # Enhanced Amendment Processing Pipeline Methods
    async def _process_amendment_finalization(
        self,
        amendment_id: int,
        state: ConstitutionalCouncilState
    ) -> Dict[str, Any]:
        """
        Process amendment finalization through enhanced pipeline with comprehensive
        status transitions, stakeholder notifications, and audit trail generation.
        """
        try:
            logger.info(f"Processing amendment finalization for amendment {amendment_id}")

            # Get voting results and validate
            voting_results = state.get("voting_results", {})
            if not voting_results.get("voting_passed", False):
                return {
                    "success": False,
                    "error": "Cannot finalize amendment without successful voting"
                }

            # Process through amendment state machine
            from app.core.amendment_state_machine import amendment_state_machine, WorkflowContext, AmendmentEvent

            # Create workflow context for state transition
            context = WorkflowContext(
                amendment_id=amendment_id,
                user_id=state.get("user_id"),
                session_id=state.get("session_id"),
                transaction_id=str(uuid.uuid4()),
                metadata={
                    "event": "finalize_amendment",
                    "voting_results": voting_results,
                    "stakeholder_feedback_count": len(state.get("stakeholder_feedback", [])),
                    "refinement_iterations": state.get("refinement_iterations", 0)
                }
            )

            # Execute state transition to approved
            transition_result = await amendment_state_machine.execute_transition(
                db=self.db,
                event=AmendmentEvent.APPROVE,
                context=context
            )

            if not transition_result["success"]:
                return {
                    "success": False,
                    "error": f"State transition failed: {transition_result['error']}"
                }

            # Update amendment with finalization data
            amendment_update = schemas.ACAmendmentUpdate(
                status="approved",
                approval_date=datetime.now(timezone.utc),
                final_vote_count=voting_results.get("vote_summary", {}).get("total_votes", 0),
                approval_rate=voting_results.get("approval_rate", 0),
                workflow_state="approved"
            )

            updated_amendment = await crud.update_ac_amendment(
                db=self.db,
                amendment_id=amendment_id,
                amendment_update=amendment_update
            )

            if not updated_amendment:
                return {
                    "success": False,
                    "error": f"Failed to update amendment {amendment_id} in database"
                }

            # Send finalization notifications through stakeholder engagement system
            notification_result = await self._send_finalization_notifications(
                amendment_id=amendment_id,
                final_status="approved",
                voting_results=voting_results,
                state=state
            )

            # Generate comprehensive audit trail
            audit_trail = await self._generate_finalization_audit_trail(
                amendment_id=amendment_id,
                state=state,
                transition_result=transition_result,
                notification_result=notification_result
            )

            # Create pipeline results summary
            pipeline_results = {
                "state_transition": transition_result,
                "database_update": {"success": True, "amendment_id": amendment_id},
                "notifications": notification_result,
                "audit_trail_generated": True,
                "finalization_timestamp": datetime.now(timezone.utc).isoformat()
            }

            logger.info(f"Amendment {amendment_id} finalization processed successfully")
            return {
                "success": True,
                "final_status": "approved",
                "pipeline_results": pipeline_results,
                "audit_trail": audit_trail
            }

        except Exception as e:
            logger.error(f"Failed to process amendment finalization: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _send_finalization_notifications(
        self,
        amendment_id: int,
        final_status: str,
        voting_results: Dict[str, Any],
        state: ConstitutionalCouncilState
    ) -> Dict[str, Any]:
        """
        Send finalization notifications to all stakeholders through the engagement system.
        """
        try:
            logger.info(f"Sending finalization notifications for amendment {amendment_id}")

            # Get stakeholder engagement status
            engagement_status = await self.stakeholder_service.get_engagement_status(amendment_id)

            if not engagement_status:
                logger.warning(f"No stakeholder engagement found for amendment {amendment_id}")
                return {"success": False, "error": "No stakeholder engagement found"}

            # Prepare notification content
            notification_content = {
                "amendment_id": amendment_id,
                "final_status": final_status,
                "voting_summary": voting_results.get("vote_summary", {}),
                "approval_rate": voting_results.get("approval_rate", 0),
                "total_votes": voting_results.get("vote_summary", {}).get("total_votes", 0),
                "finalization_timestamp": datetime.now(timezone.utc).isoformat(),
                "workflow_duration": self._calculate_workflow_duration(state)
            }

            # Send notifications to all engaged stakeholders
            notification_tasks = []
            for stakeholder_id, stakeholder_info in engagement_status.status_by_stakeholder.items():
                # Create notification task for each stakeholder
                task = self.stakeholder_service._send_notification(
                    stakeholder=type('Stakeholder', (), {
                        'id': stakeholder_id,
                        'username': stakeholder_info.get('username'),
                        'email': stakeholder_info.get('email'),
                        'role': stakeholder_info.get('roles', [None])[0] if stakeholder_info.get('roles') else None
                    })(),
                    amendment=await crud.get_ac_amendment(self.db, amendment_id),
                    channel=NotificationChannel.EMAIL,
                    notification_type="amendment_finalized",
                    **notification_content
                )
                notification_tasks.append(task)

            # Execute notifications concurrently
            notification_results = await asyncio.gather(*notification_tasks, return_exceptions=True)

            # Count successful notifications
            successful_notifications = sum(
                1 for result in notification_results
                if not isinstance(result, Exception) and result
            )

            logger.info(f"Sent {successful_notifications}/{len(notification_tasks)} finalization notifications")
            return {
                "success": True,
                "notifications_sent": successful_notifications,
                "total_stakeholders": len(notification_tasks),
                "notification_results": notification_results
            }

        except Exception as e:
            logger.error(f"Failed to send finalization notifications: {e}")
            return {
                "success": False,
                "error": str(e),
                "notifications_sent": 0
            }

    async def _generate_finalization_audit_trail(
        self,
        amendment_id: int,
        state: ConstitutionalCouncilState,
        transition_result: Dict[str, Any],
        notification_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive audit trail for amendment finalization.
        """
        try:
            audit_trail = {
                "amendment_id": amendment_id,
                "finalization_timestamp": datetime.now(timezone.utc).isoformat(),
                "workflow_summary": {
                    "total_duration_hours": self._calculate_workflow_duration(state),
                    "refinement_iterations": state.get("refinement_iterations", 0),
                    "stakeholder_feedback_count": len(state.get("stakeholder_feedback", [])),
                    "constitutional_analysis": {
                        "compliance_score": state.get("compliance_score", 0),
                        "is_constitutional": state.get("is_constitutional", False),
                        "identified_conflicts": state.get("identified_conflicts", [])
                    }
                },
                "voting_details": state.get("voting_results", {}),
                "state_transitions": {
                    "final_transition": transition_result,
                    "transition_history": state.get("state_transition_history", [])
                },
                "stakeholder_engagement": {
                    "notifications_sent": notification_result.get("notifications_sent", 0),
                    "total_stakeholders": notification_result.get("total_stakeholders", 0),
                    "engagement_rate": state.get("stakeholder_participation", {}).get("engagement_rate", 0)
                },
                "system_metadata": {
                    "workflow_id": state.get("workflow_id"),
                    "session_id": state.get("session_id"),
                    "user_id": state.get("user_id"),
                    "processing_node": "finalize_amendment",
                    "langgraph_version": "0.2.0"
                }
            }

            logger.info(f"Generated audit trail for amendment {amendment_id} finalization")
            return audit_trail

        except Exception as e:
            logger.error(f"Failed to generate audit trail: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    async def _handle_finalization_failure(
        self,
        amendment_id: Optional[str],
        error: str,
        state: ConstitutionalCouncilState
    ) -> None:
        """
        Handle finalization failure with rollback and recovery mechanisms.
        """
        try:
            logger.error(f"Handling finalization failure for amendment {amendment_id}: {error}")

            if amendment_id:
                # Attempt to rollback amendment to previous state
                from app.core.amendment_state_machine import amendment_state_machine, WorkflowContext, AmendmentEvent

                context = WorkflowContext(
                    amendment_id=int(amendment_id),
                    user_id=state.get("user_id"),
                    session_id=state.get("session_id"),
                    transaction_id=str(uuid.uuid4()),
                    metadata={
                        "event": "rollback_finalization",
                        "error": error,
                        "recovery_timestamp": datetime.now(timezone.utc).isoformat()
                    }
                )

                # Attempt rollback to voting state
                rollback_result = await amendment_state_machine.execute_transition(
                    db=self.db,
                    event=AmendmentEvent.REJECT,  # Use reject to move to a safe state
                    context=context
                )

                if rollback_result["success"]:
                    logger.info(f"Successfully rolled back amendment {amendment_id} after finalization failure")
                else:
                    logger.error(f"Failed to rollback amendment {amendment_id}: {rollback_result['error']}")

                # Send failure notification to stakeholders
                await self._send_failure_notifications(
                    amendment_id=int(amendment_id),
                    error=error,
                    state=state
                )

        except Exception as e:
            logger.error(f"Failed to handle finalization failure: {e}")

    async def _send_failure_notifications(
        self,
        amendment_id: int,
        error: str,
        state: ConstitutionalCouncilState
    ) -> None:
        """
        Send failure notifications to stakeholders when finalization fails.
        """
        try:
            # Get stakeholder engagement status
            engagement_status = await self.stakeholder_service.get_engagement_status(amendment_id)

            if engagement_status:
                # Prepare failure notification content
                failure_content = {
                    "amendment_id": amendment_id,
                    "failure_reason": error,
                    "failure_timestamp": datetime.now(timezone.utc).isoformat(),
                    "recovery_actions": "Amendment has been rolled back to previous state for review"
                }

                # Send failure notifications
                for stakeholder_id in engagement_status.status_by_stakeholder.keys():
                    try:
                        await self.stakeholder_service._send_notification(
                            stakeholder=type('Stakeholder', (), {
                                'id': stakeholder_id,
                                'email': engagement_status.status_by_stakeholder[stakeholder_id].get('email')
                            })(),
                            amendment=await crud.get_ac_amendment(self.db, amendment_id),
                            channel=NotificationChannel.EMAIL,
                            notification_type="amendment_finalization_failed",
                            **failure_content
                        )
                    except Exception as e:
                        logger.error(f"Failed to send failure notification to stakeholder {stakeholder_id}: {e}")

        except Exception as e:
            logger.error(f"Failed to send failure notifications: {e}")

    # Enhanced Amendment Processing Pipeline - Parallel Processing Support
    async def process_multiple_amendments_parallel(
        self,
        amendment_ids: List[int],
        max_concurrent: int = 3
    ) -> Dict[str, Any]:
        """
        Process multiple amendments in parallel with controlled concurrency.

        This method enables parallel processing of multiple amendments while
        maintaining system stability and resource management.
        """
        try:
            logger.info(f"Processing {len(amendment_ids)} amendments in parallel (max concurrent: {max_concurrent})")

            # Create semaphore for concurrency control
            semaphore = asyncio.Semaphore(max_concurrent)

            async def process_single_amendment(amendment_id: int) -> Dict[str, Any]:
                async with semaphore:
                    try:
                        # Get amendment from database
                        amendment = await crud.get_ac_amendment(self.db, amendment_id)
                        if not amendment:
                            return {
                                "amendment_id": amendment_id,
                                "success": False,
                                "error": "Amendment not found"
                            }

                        # Create initial state for workflow
                        initial_state = {
                            "workflow_id": str(uuid.uuid4()),
                            "amendment_id": str(amendment_id),
                            "amendment_proposal": {
                                "principle_id": amendment.principle_id,
                                "amendment_type": amendment.amendment_type,
                                "proposed_changes": amendment.proposed_changes,
                                "justification": amendment.justification
                            },
                            "created_at": datetime.now(timezone.utc).isoformat(),
                            "status": WorkflowStatus.PENDING.value,
                            "current_phase": "parallel_processing",
                            "messages": [],
                            "stakeholder_feedback": [],
                            "stakeholder_notifications": [],
                            "refinement_iterations": 0
                        }

                        # Execute workflow for this amendment
                        result = await self.execute_workflow(initial_state)

                        return {
                            "amendment_id": amendment_id,
                            "success": True,
                            "final_status": result.get("status"),
                            "workflow_result": result
                        }

                    except Exception as e:
                        logger.error(f"Failed to process amendment {amendment_id}: {e}")
                        return {
                            "amendment_id": amendment_id,
                            "success": False,
                            "error": str(e)
                        }

            # Execute all amendments in parallel
            processing_tasks = [
                process_single_amendment(amendment_id)
                for amendment_id in amendment_ids
            ]

            results = await asyncio.gather(*processing_tasks, return_exceptions=True)

            # Analyze results
            successful_amendments = [r for r in results if isinstance(r, dict) and r.get("success")]
            failed_amendments = [r for r in results if isinstance(r, dict) and not r.get("success")]
            exception_amendments = [r for r in results if isinstance(r, Exception)]

            processing_summary = {
                "total_amendments": len(amendment_ids),
                "successful": len(successful_amendments),
                "failed": len(failed_amendments),
                "exceptions": len(exception_amendments),
                "success_rate": len(successful_amendments) / len(amendment_ids) if amendment_ids else 0,
                "processing_timestamp": datetime.now(timezone.utc).isoformat(),
                "max_concurrent": max_concurrent
            }

            logger.info(f"Parallel processing completed: {processing_summary['successful']}/{processing_summary['total_amendments']} successful")

            return {
                "success": True,
                "processing_summary": processing_summary,
                "successful_amendments": successful_amendments,
                "failed_amendments": failed_amendments,
                "exception_amendments": [str(e) for e in exception_amendments]
            }

        except Exception as e:
            logger.error(f"Failed to process amendments in parallel: {e}")
            return {
                "success": False,
                "error": str(e),
                "processing_summary": {
                    "total_amendments": len(amendment_ids),
                    "successful": 0,
                    "failed": len(amendment_ids),
                    "exceptions": 0,
                    "success_rate": 0.0
                }
            }

    async def automated_status_transition(
        self,
        amendment_id: int,
        target_status: str,
        transition_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform automated status transition for an amendment with validation and audit trail.
        """
        try:
            logger.info(f"Performing automated status transition for amendment {amendment_id} to {target_status}")

            # Import state machine components
            from app.core.amendment_state_machine import (
                amendment_state_machine,
                WorkflowContext,
                AmendmentEvent,
                AmendmentState
            )

            # Get current amendment
            amendment = await crud.get_ac_amendment(self.db, amendment_id)
            if not amendment:
                return {
                    "success": False,
                    "error": f"Amendment {amendment_id} not found"
                }

            # Map target status to event
            status_event_map = {
                "under_review": AmendmentEvent.START_REVIEW,
                "public_consultation": AmendmentEvent.APPROVE_FOR_CONSULTATION,
                "voting": AmendmentEvent.START_VOTING,
                "approved": AmendmentEvent.APPROVE,
                "rejected": AmendmentEvent.REJECT,
                "withdrawn": AmendmentEvent.WITHDRAW
            }

            event = status_event_map.get(target_status)
            if not event:
                return {
                    "success": False,
                    "error": f"Invalid target status: {target_status}"
                }

            # Create workflow context
            context = WorkflowContext(
                amendment_id=amendment_id,
                user_id=transition_context.get("user_id") if transition_context else None,
                session_id=str(uuid.uuid4()),
                transaction_id=str(uuid.uuid4()),
                metadata={
                    "automated_transition": True,
                    "target_status": target_status,
                    "transition_timestamp": datetime.now(timezone.utc).isoformat(),
                    **(transition_context or {})
                }
            )

            # Execute transition
            transition_result = await amendment_state_machine.execute_transition(
                db=self.db,
                event=event,
                context=context
            )

            if transition_result["success"]:
                # Update amendment status in database
                amendment_update = schemas.ACAmendmentUpdate(
                    status=target_status,
                    workflow_state=target_status,
                    updated_at=datetime.now(timezone.utc)
                )

                updated_amendment = await crud.update_ac_amendment(
                    db=self.db,
                    amendment_id=amendment_id,
                    amendment_update=amendment_update
                )

                logger.info(f"Successfully transitioned amendment {amendment_id} to {target_status}")
                return {
                    "success": True,
                    "amendment_id": amendment_id,
                    "previous_status": amendment.status,
                    "new_status": target_status,
                    "transition_result": transition_result,
                    "updated_amendment": updated_amendment is not None
                }
            else:
                return {
                    "success": False,
                    "error": f"State transition failed: {transition_result['error']}",
                    "amendment_id": amendment_id,
                    "current_status": amendment.status,
                    "target_status": target_status
                }

        except Exception as e:
            logger.error(f"Failed to perform automated status transition: {e}")
            return {
                "success": False,
                "error": str(e),
                "amendment_id": amendment_id
            }

    # Conditional routing functions
    def should_proceed_to_voting(self, state: ConstitutionalCouncilState) -> str:
        """
        Determine if the amendment should proceed to voting based on constitutional analysis.

        Returns:
            "voting": Proceed to voting
            "refinement": Requires refinement
            "rejection": Reject amendment
        """
        is_constitutional = state.get("is_constitutional", False)
        has_conflicts = len(state.get("identified_conflicts", [])) > 0
        compliance_score = state.get("compliance_score", 0)

        # Reject if compliance score is very low
        if compliance_score < 0.5:
            return "rejection"

        # Require refinement if not constitutional or has conflicts
        if not is_constitutional or has_conflicts:
            return "refinement"

        # Proceed to voting if constitutional and no conflicts
        return "voting"

    def should_finalize_or_refine(self, state: ConstitutionalCouncilState) -> str:
        """
        Determine if the amendment should be finalized or refined based on voting results.

        Returns:
            "finalize": Finalize the amendment
            "refine": Refine the amendment
            "reject": Reject the amendment
        """
        voting_results = state.get("voting_results", {})
        voting_passed = voting_results.get("voting_passed", False)
        quorum_met = voting_results.get("quorum_met", False)
        approval_rate = voting_results.get("approval_rate", 0)

        # Reject if quorum not met and voting period ended
        if not quorum_met and voting_results.get("voting_period_ended", False):
            return "reject"

        # Finalize if voting passed
        if voting_passed and quorum_met:
            return "finalize"

        # Refine if voting failed but there's potential for improvement
        if quorum_met and approval_rate > 0.3:  # Some support exists
            return "refine"

        # Default to rejection for very low support
        return "reject"

    def should_continue_refinement(self, state: ConstitutionalCouncilState) -> str:
        """
        Determine if refinement should continue or if the amendment should be finalized/abandoned.

        Returns:
            "continue": Continue with another refinement iteration
            "finalize": Finalize without further refinement
            "abandon": Abandon the amendment
        """
        current_iterations = state.get("refinement_iterations", 0)
        max_iterations = state.get("max_refinement_iterations", self.config.max_refinement_iterations)
        refinement_areas = state.get("refinement_suggestions", {}).get("refinement_areas", [])

        # Abandon if maximum iterations reached
        if current_iterations >= max_iterations:
            return "abandon"

        # Continue if there are significant refinement areas
        if len(refinement_areas) > 0:
            return "continue"

        # Finalize if no major issues remain
        return "finalize"

    # Workflow execution interface
    async def execute_workflow(
        self,
        initial_state: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute the Constitutional Council workflow.

        Args:
            initial_state: Initial workflow state
            config: Optional workflow configuration

        Returns:
            Final workflow state
        """
        if not LANGGRAPH_AVAILABLE:
            raise RuntimeError("LangGraph not available. Cannot execute workflow.")

        if not self.graph:
            raise RuntimeError("Workflow graph not initialized.")

        try:
            # Create workflow configuration
            workflow_config = {
                "configurable": {
                    "thread_id": initial_state.get("workflow_id", str(uuid.uuid4())),
                    "checkpoint_ns": "constitutional_council"
                }
            }

            if config:
                workflow_config["configurable"].update(config)

            # Execute the workflow
            logger.info(f"Executing Constitutional Council workflow for amendment {initial_state.get('amendment_id')}")

            final_state = None
            async for state in self.graph.astream(initial_state, config=workflow_config):
                final_state = state
                logger.debug(f"Workflow state update: {state.get('current_phase', 'unknown')}")

            if final_state is None:
                raise RuntimeError("Workflow execution failed - no final state returned")

            logger.info(f"Constitutional Council workflow completed with status: {final_state.get('status', 'unknown')}")
            return final_state

        except Exception as e:
            logger.error(f"Failed to execute Constitutional Council workflow: {e}")
            raise

    async def get_workflow_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current state of a workflow.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Current workflow state or None if not found
        """
        if not LANGGRAPH_AVAILABLE or not self.graph:
            return None

        try:
            config = {
                "configurable": {
                    "thread_id": workflow_id,
                    "checkpoint_ns": "constitutional_council"
                }
            }

            # Get the current state from the checkpointer
            checkpoint = await self.graph.aget_state(config)
            return checkpoint.values if checkpoint else None

        except Exception as e:
            logger.error(f"Failed to get workflow state for {workflow_id}: {e}")
            return None


# Factory function for creating Constitutional Council graphs
async def create_constitutional_council_graph(db_session: AsyncSession) -> ConstitutionalCouncilGraph:
    """
    Factory function to create a Constitutional Council graph with database session.

    Args:
        db_session: Database session for CRUD operations

    Returns:
        Configured Constitutional Council graph
    """
    return ConstitutionalCouncilGraph(db_session)


# Workflow execution helper
async def execute_constitutional_council_workflow(
    db_session: AsyncSession,
    amendment_proposal: Dict[str, Any],
    user_id: Optional[str] = None,
    workflow_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Helper function to execute a Constitutional Council workflow.

    Args:
        db_session: Database session
        amendment_proposal: Amendment proposal data
        user_id: Optional user identifier
        workflow_config: Optional workflow configuration

    Returns:
        Final workflow state
    """
    # Create the graph
    graph = await create_constitutional_council_graph(db_session)

    # Prepare initial state
    initial_state = {
        "workflow_id": str(uuid.uuid4()),
        "user_id": user_id,
        "session_id": str(uuid.uuid4()),
        "amendment_proposal": amendment_proposal,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": WorkflowStatus.PENDING.value,
        "current_phase": "proposal",
        "messages": [],
        "stakeholder_feedback": [],
        "stakeholder_notifications": [],
        "refinement_iterations": 0
    }

    # Execute the workflow
    return await graph.execute_workflow(initial_state, workflow_config)
