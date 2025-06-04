"""
LangGraph Workflow Manager for Constitutional Council

This module provides the foundation for managing LangGraph workflows in the
AC service, including workflow initialization, state management, and integration
with the existing Constitutional Council infrastructure.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import uuid

try:
    from langgraph.graph import StateGraph, START, END
    from langgraph.types import Send
    LANGGRAPH_AVAILABLE = True
except ImportError:
    # Graceful fallback when LangGraph is not available
    LANGGRAPH_AVAILABLE = False
    StateGraph = None
    START = "START"
    END = "END"
    Send = None

from src.backend.shared.langgraph_states import (
    ConstitutionalCouncilState,
    WorkflowStatus,
    create_workflow_metadata,
    update_workflow_status
)
from src.backend.shared.langgraph_config import (
    get_langgraph_config,
    ConstitutionalCouncilConfig,
    ModelRole
)

logger = logging.getLogger(__name__)


class WorkflowManager:
    """
    Manages LangGraph workflows for the Constitutional Council.
    
    Provides a unified interface for workflow creation, execution, and monitoring
    while maintaining compatibility with existing AC service infrastructure.
    """
    
    def __init__(self):
        self.config = get_langgraph_config()
        self.council_config = ConstitutionalCouncilConfig()
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.workflow_graphs: Dict[str, Any] = {}
        
        if not LANGGRAPH_AVAILABLE:
            logger.warning("LangGraph not available. Workflow functionality will be limited.")
    
    async def initialize_workflow(
        self,
        workflow_type: str,
        initial_data: Dict[str, Any],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> str:
        """
        Initialize a new LangGraph workflow.
        
        Args:
            workflow_type: Type of workflow to create
            initial_data: Initial data for the workflow
            user_id: Optional user identifier
            session_id: Optional session identifier
            
        Returns:
            Workflow ID for tracking
        """
        workflow_id = str(uuid.uuid4())
        
        # Create workflow metadata
        metadata = create_workflow_metadata(
            workflow_type=workflow_type,
            user_id=user_id,
            session_id=session_id,
            configuration={
                "langgraph_available": LANGGRAPH_AVAILABLE,
                "council_config": self.council_config.dict()
            }
        )
        
        # Initialize workflow state based on type
        if workflow_type == "constitutional_council":
            initial_state = self._create_constitutional_council_state(
                initial_data, metadata
            )
        else:
            raise ValueError(f"Unknown workflow type: {workflow_type}")
        
        # Store workflow information
        self.active_workflows[workflow_id] = {
            "type": workflow_type,
            "state": initial_state,
            "metadata": metadata,
            "created_at": datetime.now(timezone.utc),
            "status": WorkflowStatus.PENDING
        }
        
        logger.info(f"Initialized {workflow_type} workflow {workflow_id}")
        return workflow_id
    
    def _create_constitutional_council_state(
        self,
        initial_data: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> ConstitutionalCouncilState:
        """Create initial state for Constitutional Council workflow."""
        return ConstitutionalCouncilState(
            messages=[],
            user_id=metadata.get("user_id"),
            session_id=metadata.get("session_id"),
            workflow_id=initial_data.get("workflow_id"),
            created_at=metadata["created_at"],
            updated_at=metadata["updated_at"],
            status=WorkflowStatus.PENDING.value,
            metadata=metadata,
            configuration=metadata.get("configuration", {}),
            
            # Constitutional Council specific fields
            amendment_proposal=initial_data.get("amendment_proposal"),
            amendment_id=initial_data.get("amendment_id"),
            amendment_type=initial_data.get("amendment_type", "principle_modification"),
            stakeholder_feedback=[],
            stakeholder_notifications=[],
            required_stakeholders=self.council_config.required_stakeholder_roles,
            constitutional_analysis=None,
            compliance_score=None,
            identified_conflicts=[],
            voting_results=None,
            voting_deadline=None,
            quorum_met=None,
            refinement_iterations=0,
            max_refinement_iterations=self.council_config.amendment_review_period_hours,
            is_constitutional=None,
            requires_refinement=None,
            escalation_required=False,
            current_phase="proposal",
            phase_deadlines={},
            automated_processing=self.council_config.enable_automated_analysis
        )
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current status of a workflow.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Workflow status information or None if not found
        """
        if workflow_id not in self.active_workflows:
            return None
        
        workflow = self.active_workflows[workflow_id]
        return {
            "workflow_id": workflow_id,
            "type": workflow["type"],
            "status": workflow["status"].value if hasattr(workflow["status"], "value") else workflow["status"],
            "created_at": workflow["created_at"].isoformat(),
            "current_phase": workflow["state"].get("current_phase"),
            "refinement_iterations": workflow["state"].get("refinement_iterations", 0),
            "requires_human_review": workflow["state"].get("escalation_required", False),
            "metadata": workflow["metadata"]
        }
    
    async def update_workflow_state(
        self,
        workflow_id: str,
        state_updates: Dict[str, Any]
    ) -> bool:
        """
        Update the state of an active workflow.
        
        Args:
            workflow_id: Workflow identifier
            state_updates: State updates to apply
            
        Returns:
            True if update was successful, False otherwise
        """
        if workflow_id not in self.active_workflows:
            logger.error(f"Workflow {workflow_id} not found")
            return False
        
        try:
            workflow = self.active_workflows[workflow_id]
            
            # Update state
            workflow["state"].update(state_updates)
            
            # Update metadata
            workflow["metadata"]["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            # Update status if provided
            if "status" in state_updates:
                workflow["status"] = state_updates["status"]
            
            logger.info(f"Updated workflow {workflow_id} state")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update workflow {workflow_id}: {e}")
            return False
    
    async def list_active_workflows(
        self,
        workflow_type: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List active workflows with optional filtering.
        
        Args:
            workflow_type: Optional workflow type filter
            user_id: Optional user ID filter
            
        Returns:
            List of workflow status information
        """
        workflows = []
        
        for workflow_id, workflow in self.active_workflows.items():
            # Apply filters
            if workflow_type and workflow["type"] != workflow_type:
                continue
            if user_id and workflow["state"].get("user_id") != user_id:
                continue
            
            status_info = await self.get_workflow_status(workflow_id)
            if status_info:
                workflows.append(status_info)
        
        return workflows
    
    async def cleanup_completed_workflows(self, max_age_hours: int = 24) -> int:
        """
        Clean up completed workflows older than specified age.
        
        Args:
            max_age_hours: Maximum age in hours for completed workflows
            
        Returns:
            Number of workflows cleaned up
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        cleaned_count = 0
        
        workflows_to_remove = []
        for workflow_id, workflow in self.active_workflows.items():
            if (workflow["status"] in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED] and
                workflow["created_at"] < cutoff_time):
                workflows_to_remove.append(workflow_id)
        
        for workflow_id in workflows_to_remove:
            del self.active_workflows[workflow_id]
            cleaned_count += 1
            logger.info(f"Cleaned up completed workflow {workflow_id}")
        
        return cleaned_count
    
    def get_workflow_capabilities(self) -> Dict[str, Any]:
        """
        Get information about workflow capabilities and configuration.
        
        Returns:
            Workflow capabilities information
        """
        return {
            "langgraph_available": LANGGRAPH_AVAILABLE,
            "supported_workflow_types": ["constitutional_council"],
            "active_workflow_count": len(self.active_workflows),
            "configuration": {
                "constitutional_fidelity_threshold": self.config.constitutional_fidelity_threshold,
                "max_refinement_iterations": self.config.max_refinement_iterations,
                "redis_configured": bool(self.config.redis_url),
                "api_keys_available": self.config.validate_api_keys()
            },
            "council_config": self.council_config.dict()
        }


# Global workflow manager instance
_workflow_manager: Optional[WorkflowManager] = None


def get_workflow_manager() -> WorkflowManager:
    """Get the global workflow manager instance."""
    global _workflow_manager
    if _workflow_manager is None:
        _workflow_manager = WorkflowManager()
    return _workflow_manager
