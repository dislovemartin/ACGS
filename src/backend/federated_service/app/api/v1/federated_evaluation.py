"""
Federated Evaluation API Endpoints

REST API endpoints for managing federated evaluation tasks,
node registration, and evaluation status monitoring.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Optional, Any
import logging
import asyncio

from shared.database import get_async_db
from shared.auth import get_current_user_from_token, get_current_active_user
from ...core.federated_evaluator import federated_evaluator
from ...schemas import (
    FederatedEvaluationRequest, FederatedEvaluationResponse,
    EvaluationStatusResponse, NodeConfiguration, NodeStatusResponse,
    FederatedMetricsResponse, ErrorResponse, PlatformType
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/submit", response_model=FederatedEvaluationResponse)
async def submit_federated_evaluation(
    request: FederatedEvaluationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_active_user)
):
    """Submit a new federated evaluation task."""
    try:
        logger.info(f"Submitting federated evaluation for user: {current_user.get('username', 'unknown')}")
        
        # Submit evaluation to federated evaluator
        task_id = await federated_evaluator.submit_evaluation(request)
        
        return FederatedEvaluationResponse(
            task_id=task_id,
            status="pending",
            message=f"Federated evaluation submitted successfully. Task ID: {task_id}",
            estimated_completion_time=None  # Would calculate based on current load
        )
        
    except ValueError as e:
        logger.error(f"Invalid evaluation request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid evaluation request: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to submit federated evaluation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit evaluation: {str(e)}"
        )


@router.get("/status/{task_id}", response_model=EvaluationStatusResponse)
async def get_evaluation_status(
    task_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Get the status of a federated evaluation task."""
    try:
        status_info = await federated_evaluator.get_evaluation_status(task_id)
        
        if not status_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Evaluation task not found: {task_id}"
            )
        
        return EvaluationStatusResponse(**status_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get evaluation status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get evaluation status: {str(e)}"
        )


@router.post("/nodes/register", response_model=Dict[str, str])
async def register_federated_node(
    node_config: NodeConfiguration,
    current_user: dict = Depends(get_current_active_user)
):
    """Register a new federated evaluation node."""
    try:
        logger.info(f"Registering federated node: {node_config.platform_type.value}")
        
        # Check user permissions (admin only for node registration)
        if current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can register federated nodes"
            )
        
        node_id = await federated_evaluator.register_node(node_config)
        
        return {
            "node_id": node_id,
            "message": f"Federated node registered successfully: {node_id}",
            "platform_type": node_config.platform_type.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to register federated node: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register node: {str(e)}"
        )


@router.get("/nodes", response_model=List[NodeStatusResponse])
async def list_federated_nodes(
    platform_type: Optional[PlatformType] = Query(None, description="Filter by platform type"),
    status_filter: Optional[str] = Query(None, description="Filter by node status"),
    current_user: dict = Depends(get_current_active_user)
):
    """List all registered federated nodes."""
    try:
        nodes = []
        
        for node_id, node in federated_evaluator.nodes.items():
            # Apply filters
            if platform_type and node.platform_type != platform_type:
                continue
            if status_filter and node.status != status_filter:
                continue
            
            node_status = await federated_evaluator.get_node_status(node_id)
            if node_status:
                nodes.append(NodeStatusResponse(**node_status))
        
        return nodes
        
    except Exception as e:
        logger.error(f"Failed to list federated nodes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list nodes: {str(e)}"
        )


@router.get("/nodes/{node_id}", response_model=NodeStatusResponse)
async def get_node_status(
    node_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Get the status of a specific federated node."""
    try:
        node_status = await federated_evaluator.get_node_status(node_id)
        
        if not node_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Federated node not found: {node_id}"
            )
        
        return NodeStatusResponse(**node_status)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get node status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get node status: {str(e)}"
        )


@router.delete("/nodes/{node_id}")
async def unregister_federated_node(
    node_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Unregister a federated evaluation node."""
    try:
        # Check user permissions (admin only)
        if current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can unregister federated nodes"
            )
        
        if node_id not in federated_evaluator.nodes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Federated node not found: {node_id}"
            )
        
        # Remove node
        del federated_evaluator.nodes[node_id]
        
        return {
            "message": f"Federated node unregistered successfully: {node_id}",
            "node_id": node_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unregister federated node: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unregister node: {str(e)}"
        )


@router.get("/metrics", response_model=FederatedMetricsResponse)
async def get_federated_metrics(
    current_user: dict = Depends(get_current_active_user)
):
    """Get comprehensive federated evaluation metrics."""
    try:
        # Get metrics from all components
        evaluation_metrics = await federated_evaluator.get_evaluation_metrics()
        aggregation_metrics = await federated_evaluator.secure_aggregator.get_aggregation_metrics()
        privacy_metrics = await federated_evaluator.privacy_manager.get_privacy_metrics()
        
        # Collect node metrics
        node_metrics = {}
        for node_id in federated_evaluator.nodes:
            node_status = await federated_evaluator.get_node_status(node_id)
            if node_status:
                node_metrics[node_id] = node_status
        
        # System health summary
        system_health = {
            "total_nodes": len(federated_evaluator.nodes),
            "active_nodes": len([n for n in federated_evaluator.nodes.values() if n.status == "active"]),
            "active_evaluations": len(federated_evaluator.active_evaluations),
            "privacy_budget_remaining": privacy_metrics["privacy_budget"]["epsilon_remaining"],
            "overall_success_rate": evaluation_metrics.get("successful_evaluations", 0) / max(1, evaluation_metrics.get("total_evaluations", 1))
        }
        
        return FederatedMetricsResponse(
            evaluation_metrics=evaluation_metrics,
            aggregation_metrics=aggregation_metrics,
            privacy_metrics=privacy_metrics,
            node_metrics=node_metrics,
            system_health=system_health
        )
        
    except Exception as e:
        logger.error(f"Failed to get federated metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics: {str(e)}"
        )


@router.get("/platforms")
async def list_supported_platforms():
    """List all supported platform types."""
    return {
        "platforms": [
            {
                "type": platform.value,
                "name": platform.value.replace("_", " ").title(),
                "description": f"Evaluation on {platform.value.replace('_', ' ')} platform"
            }
            for platform in PlatformType
        ]
    }
