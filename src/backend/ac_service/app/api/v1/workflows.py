"""
LangGraph Workflow API Endpoints for Constitutional Council

This module provides REST API endpoints for managing LangGraph workflows
in the Constitutional Council, including workflow creation, monitoring,
and status management.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import logging

from shared.auth import get_current_active_user as get_current_user
from shared.database import get_async_db
from app.workflows.workflow_manager import get_workflow_manager
from app.workflows.constitutional_council_graph import (
    execute_constitutional_council_workflow,
    AmendmentProposalInput
)
from shared.models import User
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflows", tags=["workflows"])


# Request/Response Models
class WorkflowInitRequest(BaseModel):
    """Request model for initializing a new workflow."""
    workflow_type: str = Field(..., description="Type of workflow to create")
    initial_data: Dict[str, Any] = Field(..., description="Initial data for the workflow")
    session_id: Optional[str] = Field(None, description="Optional session identifier")


class WorkflowStatusResponse(BaseModel):
    """Response model for workflow status."""
    workflow_id: str
    type: str
    status: str
    created_at: str
    current_phase: Optional[str] = None
    refinement_iterations: int = 0
    requires_human_review: bool = False
    metadata: Dict[str, Any] = {}


class WorkflowUpdateRequest(BaseModel):
    """Request model for updating workflow state."""
    state_updates: Dict[str, Any] = Field(..., description="State updates to apply")


class WorkflowCapabilitiesResponse(BaseModel):
    """Response model for workflow capabilities."""
    langgraph_available: bool
    supported_workflow_types: List[str]
    active_workflow_count: int
    configuration: Dict[str, Any]
    council_config: Dict[str, Any]


@router.get("/capabilities", response_model=WorkflowCapabilitiesResponse)
async def get_workflow_capabilities():
    """
    Get information about workflow capabilities and configuration.
    
    Returns:
        Workflow capabilities and configuration information
    """
    try:
        workflow_manager = get_workflow_manager()
        capabilities = workflow_manager.get_workflow_capabilities()
        
        return WorkflowCapabilitiesResponse(**capabilities)
        
    except Exception as e:
        logger.error(f"Failed to get workflow capabilities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve workflow capabilities"
        )


@router.post("/initialize", response_model=Dict[str, str])
async def initialize_workflow(
    request: WorkflowInitRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Initialize a new LangGraph workflow.
    
    Args:
        request: Workflow initialization request
        current_user: Current authenticated user
        
    Returns:
        Workflow ID for tracking
    """
    try:
        workflow_manager = get_workflow_manager()
        
        # Validate workflow type
        capabilities = workflow_manager.get_workflow_capabilities()
        if request.workflow_type not in capabilities["supported_workflow_types"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported workflow type: {request.workflow_type}"
            )
        
        # Initialize workflow
        workflow_id = await workflow_manager.initialize_workflow(
            workflow_type=request.workflow_type,
            initial_data=request.initial_data,
            user_id=str(current_user.id),
            session_id=request.session_id
        )
        
        logger.info(f"User {current_user.id} initialized workflow {workflow_id}")
        
        return {"workflow_id": workflow_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to initialize workflow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize workflow"
        )


@router.get("/{workflow_id}/status", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    workflow_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get the current status of a workflow.
    
    Args:
        workflow_id: Workflow identifier
        current_user: Current authenticated user
        
    Returns:
        Workflow status information
    """
    try:
        workflow_manager = get_workflow_manager()
        status_info = await workflow_manager.get_workflow_status(workflow_id)
        
        if not status_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )
        
        # Check if user has access to this workflow
        if status_info["metadata"].get("user_id") != str(current_user.id):
            # Allow admins to view any workflow
            if not current_user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this workflow"
                )
        
        return WorkflowStatusResponse(**status_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve workflow status"
        )


@router.put("/{workflow_id}/update")
async def update_workflow_state(
    workflow_id: str,
    request: WorkflowUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Update the state of an active workflow.
    
    Args:
        workflow_id: Workflow identifier
        request: State update request
        current_user: Current authenticated user
        
    Returns:
        Success confirmation
    """
    try:
        workflow_manager = get_workflow_manager()
        
        # Check if workflow exists and user has access
        status_info = await workflow_manager.get_workflow_status(workflow_id)
        if not status_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )
        
        if status_info["metadata"].get("user_id") != str(current_user.id):
            if not current_user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this workflow"
                )
        
        # Update workflow state
        success = await workflow_manager.update_workflow_state(
            workflow_id, request.state_updates
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update workflow state"
            )
        
        logger.info(f"User {current_user.id} updated workflow {workflow_id}")
        
        return {"message": "Workflow state updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update workflow state: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update workflow state"
        )


@router.get("/", response_model=List[WorkflowStatusResponse])
async def list_workflows(
    workflow_type: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    List active workflows for the current user.
    
    Args:
        workflow_type: Optional workflow type filter
        current_user: Current authenticated user
        
    Returns:
        List of workflow status information
    """
    try:
        workflow_manager = get_workflow_manager()
        
        # Admins can see all workflows, regular users only their own
        user_filter = None if current_user.is_admin else str(current_user.id)
        
        workflows = await workflow_manager.list_active_workflows(
            workflow_type=workflow_type,
            user_id=user_filter
        )
        
        return [WorkflowStatusResponse(**workflow) for workflow in workflows]
        
    except Exception as e:
        logger.error(f"Failed to list workflows: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list workflows"
        )


@router.delete("/cleanup")
async def cleanup_completed_workflows(
    max_age_hours: int = 24,
    current_user: User = Depends(get_current_user)
):
    """
    Clean up completed workflows older than specified age.
    
    Args:
        max_age_hours: Maximum age in hours for completed workflows
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Number of workflows cleaned up
    """
    # Only admins can perform cleanup
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required for workflow cleanup"
        )
    
    try:
        workflow_manager = get_workflow_manager()
        cleaned_count = await workflow_manager.cleanup_completed_workflows(max_age_hours)
        
        logger.info(f"Admin {current_user.id} cleaned up {cleaned_count} workflows")
        
        return {"cleaned_workflows": cleaned_count}

    except Exception as e:
        logger.error(f"Failed to cleanup workflows: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup workflows"
        )


# Constitutional Council specific endpoints
class ConstitutionalCouncilWorkflowRequest(BaseModel):
    """Request model for Constitutional Council workflow execution."""
    principle_id: int = Field(..., description="ID of the principle to amend")
    amendment_type: str = Field(..., description="Type of amendment")
    proposed_changes: str = Field(..., description="Description of proposed changes")
    justification: str = Field(..., description="Rationale for the amendment")
    proposed_content: Optional[str] = Field(None, description="New content if modifying/adding")
    urgency_level: str = Field("normal", description="Urgency level for processing")
    stakeholder_groups: Optional[List[str]] = Field(None, description="Specific stakeholder groups to involve")


class ConstitutionalCouncilWorkflowResponse(BaseModel):
    """Response model for Constitutional Council workflow execution."""
    workflow_id: str
    amendment_id: Optional[str] = None
    status: str
    current_phase: str
    constitutional_analysis: Optional[Dict[str, Any]] = None
    voting_results: Optional[Dict[str, Any]] = None
    finalization_summary: Optional[Dict[str, Any]] = None
    messages: List[Dict[str, Any]] = []


@router.post("/constitutional-council/execute", response_model=ConstitutionalCouncilWorkflowResponse)
async def execute_constitutional_council_workflow_endpoint(
    request: ConstitutionalCouncilWorkflowRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Execute a Constitutional Council amendment workflow.

    This endpoint creates and executes a complete Constitutional Council workflow
    for processing constitutional amendments through the democratic governance process.

    Args:
        request: Constitutional Council workflow request
        db: Database session
        current_user: Current authenticated user

    Returns:
        Workflow execution results
    """
    try:
        # Validate amendment proposal input
        try:
            amendment_proposal = AmendmentProposalInput(
                principle_id=request.principle_id,
                amendment_type=request.amendment_type,
                proposed_changes=request.proposed_changes,
                justification=request.justification,
                proposed_content=request.proposed_content,
                urgency_level=request.urgency_level,
                stakeholder_groups=request.stakeholder_groups
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid amendment proposal: {e}"
            )

        # Execute the Constitutional Council workflow
        logger.info(f"User {current_user.id} executing Constitutional Council workflow for principle {request.principle_id}")

        final_state = await execute_constitutional_council_workflow(
            db_session=db,
            amendment_proposal=amendment_proposal.dict(),
            user_id=str(current_user.id),
            workflow_config={
                "user_role": getattr(current_user, 'role', 'user'),
                "user_permissions": getattr(current_user, 'permissions', [])
            }
        )

        # Extract key information for response
        response_data = {
            "workflow_id": final_state.get("workflow_id", ""),
            "amendment_id": final_state.get("amendment_id"),
            "status": final_state.get("status", "unknown"),
            "current_phase": final_state.get("current_phase", "unknown"),
            "constitutional_analysis": final_state.get("constitutional_analysis"),
            "voting_results": final_state.get("voting_results"),
            "finalization_summary": final_state.get("finalization_summary"),
            "messages": final_state.get("messages", [])
        }

        logger.info(f"Constitutional Council workflow completed for user {current_user.id} with status: {final_state.get('status')}")

        return ConstitutionalCouncilWorkflowResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute Constitutional Council workflow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute Constitutional Council workflow: {str(e)}"
        )


@router.get("/constitutional-council/{workflow_id}/state")
async def get_constitutional_council_workflow_state(
    workflow_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the current state of a Constitutional Council workflow.

    Args:
        workflow_id: Workflow identifier
        db: Database session
        current_user: Current authenticated user

    Returns:
        Current workflow state
    """
    try:
        from app.workflows.constitutional_council_graph import create_constitutional_council_graph

        # Create graph instance
        graph = await create_constitutional_council_graph(db)

        # Get workflow state
        workflow_state = await graph.get_workflow_state(workflow_id)

        if not workflow_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )

        # Check access permissions
        if workflow_state.get("user_id") != str(current_user.id):
            if not getattr(current_user, 'is_admin', False):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this workflow"
                )

        return workflow_state

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get Constitutional Council workflow state: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve workflow state"
        )
