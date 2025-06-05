"""
Democratic Governance API Endpoints

This module provides REST API endpoints for democratic governance workflows,
including proposal initiation, stage advancement, approval recording, and
finalization with comprehensive audit trails.

Key Features:
- Proposal lifecycle management
- Workflow stage advancement
- Approval routing and recording
- Cryptographic audit trail access
- Real-time governance monitoring
"""

import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_async_db as get_db_session
from ...services.democratic_governance import (
    ApprovalLevel,
    GovernanceDecisionType,
    GovernanceStage,
    democratic_governance,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/democratic-governance", tags=["Democratic Governance"])


# Request/Response Models


class ProposalCreateRequest(BaseModel):
    """Request model for creating governance proposals."""

    title: str = Field(..., description="Proposal title")
    description: str = Field(..., description="Proposal description")
    decision_type: str = Field(
        default="policy_modification", description="Type of governance decision"
    )
    content: Dict = Field(default_factory=dict, description="Proposal content")
    supporting_documents: List[Dict] = Field(
        default_factory=list, description="Supporting documents"
    )
    stakeholder_groups: List[str] = Field(
        default_factory=list, description="Affected stakeholder groups"
    )
    constitutional_implications: Dict = Field(
        default_factory=dict, description="Constitutional implications"
    )


class StageAdvancementRequest(BaseModel):
    """Request model for advancing workflow stages."""

    target_stage: str = Field(..., description="Target workflow stage")
    action_data: Dict = Field(
        default_factory=dict, description="Additional action data"
    )


class ApprovalRequest(BaseModel):
    """Request model for recording approvals."""

    approval_level: str = Field(..., description="Level of approval")
    approved: bool = Field(..., description="Approval decision")
    rationale: str = Field(default="", description="Approval rationale")
    supporting_data: Dict = Field(
        default_factory=dict, description="Supporting approval data"
    )


class FinalizationRequest(BaseModel):
    """Request model for finalizing proposals."""

    final_decision: str = Field(..., description="Final decision")
    rationale: str = Field(..., description="Decision rationale")
    implementation_notes: str = Field(default="", description="Implementation notes")


# API Endpoints


@router.post("/proposals")
async def create_proposal(
    proposal_data: ProposalCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user_id: str = "demo_user",  # Would come from auth
):
    """
    Create a new governance proposal with cryptographic audit trail.

    Initiates a democratic governance proposal with proper workflow routing
    and audit trail initialization.
    """
    try:
        proposal = await democratic_governance.initiate_proposal(
            db=db, proposal_data=proposal_data.model_dump(), proposer_id=current_user_id
        )

        return {
            "message": "Governance proposal created successfully",
            "proposal": {
                "proposal_id": proposal.proposal_id,
                "title": proposal.title,
                "decision_type": proposal.decision_type.value,
                "current_stage": proposal.current_stage.value,
                "created_at": proposal.created_at,
                "integrity_hash": proposal.integrity_hash,
                "required_approvals": [
                    level.value for level in proposal.required_approvals
                ],
            },
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating governance proposal: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/proposals")
async def list_proposals(
    decision_type: Optional[str] = Query(None, description="Filter by decision type"),
    stage: Optional[str] = Query(None, description="Filter by current stage"),
    limit: int = Query(50, description="Maximum number of proposals to return"),
    offset: int = Query(0, description="Number of proposals to skip"),
):
    """
    List governance proposals with optional filtering.

    Returns a paginated list of governance proposals with basic information
    and current status.
    """
    try:
        # Get proposals from orchestrator
        proposals = list(democratic_governance.active_proposals.values())

        # Apply filters
        if decision_type:
            proposals = [p for p in proposals if p.decision_type.value == decision_type]

        if stage:
            proposals = [p for p in proposals if p.current_stage.value == stage]

        # Apply pagination
        total_count = len(proposals)
        paginated_proposals = proposals[offset : offset + limit]

        proposal_summaries = []
        for proposal in paginated_proposals:
            proposal_summaries.append(
                {
                    "proposal_id": proposal.proposal_id,
                    "title": proposal.title,
                    "decision_type": proposal.decision_type.value,
                    "current_stage": proposal.current_stage.value,
                    "proposer_id": proposal.proposer_id,
                    "created_at": proposal.created_at,
                    "updated_at": proposal.updated_at,
                    "approval_progress": {
                        level.value: proposal.current_approvals.get(level, False)
                        for level in proposal.required_approvals
                    },
                }
            )

        return {
            "proposals": proposal_summaries,
            "pagination": {
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count,
            },
        }

    except Exception as e:
        logger.error(f"Error listing governance proposals: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/proposals/{proposal_id}")
async def get_proposal(proposal_id: str):
    """
    Get detailed information about a specific governance proposal.

    Returns comprehensive proposal details including workflow history,
    audit trail, and current status.
    """
    try:
        proposal = democratic_governance.active_proposals.get(proposal_id)
        if not proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")

        return {
            "proposal": {
                "proposal_id": proposal.proposal_id,
                "title": proposal.title,
                "description": proposal.description,
                "decision_type": proposal.decision_type.value,
                "current_stage": proposal.current_stage.value,
                "proposer_id": proposal.proposer_id,
                "created_at": proposal.created_at,
                "updated_at": proposal.updated_at,
                "proposal_content": proposal.proposal_content,
                "supporting_documents": proposal.supporting_documents,
                "stakeholder_groups": proposal.stakeholder_groups,
                "constitutional_implications": proposal.constitutional_implications,
                "workflow_history": proposal.workflow_history,
                "current_approvals": {
                    level.value: approved
                    for level, approved in proposal.current_approvals.items()
                },
                "required_approvals": [
                    level.value for level in proposal.required_approvals
                ],
                "public_comments": proposal.public_comments,
                "voting_sessions": proposal.voting_sessions,
                "decision_rationale": proposal.decision_rationale,
                "audit_trail_count": len(proposal.audit_trail),
                "integrity_hash": proposal.integrity_hash,
            }
        }

    except Exception as e:
        logger.error(f"Error getting governance proposal {proposal_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/proposals/{proposal_id}/advance")
async def advance_proposal_stage(
    proposal_id: str,
    advancement_data: StageAdvancementRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user_id: str = "demo_user",  # Would come from auth
):
    """
    Advance a governance proposal to the next workflow stage.

    Validates approval requirements and advances the proposal through
    the democratic governance workflow with audit trail updates.
    """
    try:
        target_stage = GovernanceStage(advancement_data.target_stage)

        proposal = await democratic_governance.advance_workflow_stage(
            db=db,
            proposal_id=proposal_id,
            target_stage=target_stage,
            actor_id=current_user_id,
            action_data=advancement_data.action_data,
        )

        return {
            "message": f"Proposal advanced to {target_stage.value}",
            "proposal": {
                "proposal_id": proposal.proposal_id,
                "previous_stage": advancement_data.target_stage,
                "current_stage": proposal.current_stage.value,
                "updated_at": proposal.updated_at,
                "integrity_hash": proposal.integrity_hash,
            },
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error advancing proposal {proposal_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/proposals/{proposal_id}/approvals")
async def record_approval(
    proposal_id: str,
    approval_data: ApprovalRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user_id: str = "demo_user",  # Would come from auth
):
    """
    Record an approval decision for a governance proposal.

    Records approval with cryptographic audit trail and checks for
    completion of all required approvals.
    """
    try:
        approval_level = ApprovalLevel(approval_data.approval_level)

        approval_record = await democratic_governance.record_approval(
            db=db,
            proposal_id=proposal_id,
            approval_level=approval_level,
            approver_id=current_user_id,
            approval_data={
                "approved": approval_data.approved,
                "rationale": approval_data.rationale,
                "supporting_data": approval_data.supporting_data,
            },
        )

        return {
            "message": "Approval recorded successfully",
            "approval": approval_record,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error recording approval for proposal {proposal_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/proposals/{proposal_id}/finalize")
async def finalize_proposal(
    proposal_id: str,
    finalization_data: FinalizationRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user_id: str = "demo_user",  # Would come from auth
):
    """
    Finalize a governance proposal with comprehensive audit documentation.

    Completes the democratic governance process with final decision
    recording and audit report generation.
    """
    try:
        finalization_record = await democratic_governance.finalize_proposal(
            db=db,
            proposal_id=proposal_id,
            final_decision=finalization_data.final_decision,
            decision_data={
                "rationale": finalization_data.rationale,
                "implementation_notes": finalization_data.implementation_notes,
            },
            finalizer_id=current_user_id,
        )

        return {
            "message": "Proposal finalized successfully",
            "finalization": finalization_record,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error finalizing proposal {proposal_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/proposals/{proposal_id}/audit-trail")
async def get_audit_trail(proposal_id: str):
    """
    Get the complete cryptographic audit trail for a governance proposal.

    Returns detailed audit information including all workflow actions,
    cryptographic proofs, and integrity verification data.
    """
    try:
        proposal = democratic_governance.active_proposals.get(proposal_id)
        if not proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")

        return {
            "proposal_id": proposal_id,
            "audit_trail": proposal.audit_trail,
            "workflow_history": proposal.workflow_history,
            "integrity_verification": {
                "current_hash": proposal.integrity_hash,
                "audit_entries_count": len(proposal.audit_trail),
                "workflow_actions_count": len(proposal.workflow_history),
            },
        }

    except Exception as e:
        logger.error(f"Error getting audit trail for proposal {proposal_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/workflow-templates")
async def get_workflow_templates():
    """
    Get available workflow templates for different governance decision types.

    Returns template information for understanding governance processes
    and required stages.
    """
    try:
        templates = {}
        for decision_type, template in democratic_governance.workflow_templates.items():
            templates[decision_type.value] = {
                "stages": [
                    {
                        "stage": stage_info["stage"].value,
                        "required_actions": stage_info["required_actions"],
                        "participants": [
                            role.value for role in stage_info["participants"]
                        ],
                        "duration_estimate_days": stage_info["duration_estimate"].days,
                    }
                    for stage_info in template["stages"]
                ],
                "audit_requirements": template["audit_requirements"],
            }

        # Add routing rules information
        routing_info = {}
        for decision_type, rule in democratic_governance.routing_rules.items():
            routing_info[decision_type.value] = {
                "required_levels": [level.value for level in rule.required_levels],
                "parallel_approvals": [
                    [level.value for level in parallel_group]
                    for parallel_group in rule.parallel_approvals
                ],
                "sequential_approvals": [
                    level.value for level in rule.sequential_approvals
                ],
                "timeout_rules": {
                    level.value: timeout.total_seconds()
                    for level, timeout in rule.timeout_rules.items()
                },
            }

        return {
            "workflow_templates": templates,
            "routing_rules": routing_info,
            "available_stages": [stage.value for stage in GovernanceStage],
            "available_decision_types": [
                decision_type.value for decision_type in GovernanceDecisionType
            ],
            "available_approval_levels": [level.value for level in ApprovalLevel],
        }

    except Exception as e:
        logger.error(f"Error getting workflow templates: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/metrics")
async def get_governance_metrics():
    """
    Get governance workflow metrics and statistics.

    Returns real-time metrics about proposal processing, approval rates,
    and workflow performance.
    """
    try:
        proposals = list(democratic_governance.active_proposals.values())

        # Calculate metrics
        total_proposals = len(proposals)
        stage_distribution = {}
        decision_type_distribution = {}
        approval_rates = {}

        for proposal in proposals:
            # Stage distribution
            stage = proposal.current_stage.value
            stage_distribution[stage] = stage_distribution.get(stage, 0) + 1

            # Decision type distribution
            decision_type = proposal.decision_type.value
            decision_type_distribution[decision_type] = (
                decision_type_distribution.get(decision_type, 0) + 1
            )

            # Approval rates
            for level in proposal.required_approvals:
                level_name = level.value
                if level_name not in approval_rates:
                    approval_rates[level_name] = {"approved": 0, "total": 0}

                approval_rates[level_name]["total"] += 1
                if proposal.current_approvals.get(level, False):
                    approval_rates[level_name]["approved"] += 1

        # Calculate approval percentages
        approval_percentages = {}
        for level, stats in approval_rates.items():
            if stats["total"] > 0:
                approval_percentages[level] = stats["approved"] / stats["total"] * 100
            else:
                approval_percentages[level] = 0

        return {
            "governance_metrics": {
                "total_proposals": total_proposals,
                "stage_distribution": stage_distribution,
                "decision_type_distribution": decision_type_distribution,
                "approval_rates": approval_percentages,
                "workflow_statistics": {
                    "average_approval_rate": (
                        sum(approval_percentages.values()) / len(approval_percentages)
                        if approval_percentages
                        else 0
                    ),
                    "most_common_stage": (
                        max(stage_distribution.items(), key=lambda x: x[1])[0]
                        if stage_distribution
                        else None
                    ),
                    "most_common_decision_type": (
                        max(decision_type_distribution.items(), key=lambda x: x[1])[0]
                        if decision_type_distribution
                        else None
                    ),
                },
            }
        }

    except Exception as e:
        logger.error(f"Error getting governance metrics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
