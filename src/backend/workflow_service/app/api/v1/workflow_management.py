"""
Workflow Management API Endpoints
Provides comprehensive workflow orchestration, monitoring, and management
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from ...core.workflow_engine import workflow_engine, WorkflowType, WorkflowStatus
from ...monitoring.workflow_monitor import workflow_monitor, AlertSeverity
from ...recovery.workflow_recovery import recovery_manager, RecoveryAction, CheckpointType
from ...testing.automated_validator import automated_validator, TestType
from shared.database import get_async_db
from shared.auth import get_current_active_user, User

logger = logging.getLogger(__name__)
router = APIRouter()

# Workflow Management Endpoints

@router.post("/workflows", status_code=status.HTTP_201_CREATED)
async def create_workflow(
    workflow_type: WorkflowType,
    name: str,
    description: str,
    input_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new workflow instance"""
    
    try:
        workflow_id = await workflow_engine.create_workflow(
            workflow_type=workflow_type,
            name=name,
            description=description,
            input_data=input_data,
            created_by=current_user.username
        )
        
        # Start monitoring
        workflow_monitor.start_workflow_monitoring(workflow_id, workflow_engine)
        
        # Create initial checkpoint
        await recovery_manager.create_checkpoint(
            workflow_id=workflow_id,
            checkpoint_type=CheckpointType.WORKFLOW_START,
            state_data=input_data,
            metadata={"created_by": current_user.username}
        )
        
        return {
            "workflow_id": workflow_id,
            "status": "created",
            "message": f"Workflow {name} created successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to create workflow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create workflow: {str(e)}"
        )

@router.post("/workflows/{workflow_id}/start")
async def start_workflow(
    workflow_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
):
    """Start workflow execution"""
    
    try:
        success = await workflow_engine.start_workflow(workflow_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to start workflow"
            )
        
        return {
            "workflow_id": workflow_id,
            "status": "started",
            "message": "Workflow execution started"
        }
        
    except Exception as e:
        logger.error(f"Failed to start workflow {workflow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start workflow: {str(e)}"
        )

@router.get("/workflows/{workflow_id}/status")
async def get_workflow_status(
    workflow_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get workflow status and progress"""
    
    status_info = workflow_engine.get_workflow_status(workflow_id)
    
    if not status_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    # Add recovery information
    recovery_status = recovery_manager.get_recovery_status(workflow_id)
    status_info["recovery"] = recovery_status
    
    return status_info

@router.get("/workflows")
async def list_workflows(
    status_filter: Optional[WorkflowStatus] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user)
):
    """List workflows with optional filtering"""
    
    workflows = workflow_engine.list_workflows(status=status_filter)
    
    # Apply pagination
    total = len(workflows)
    workflows = workflows[offset:offset + limit]
    
    return {
        "workflows": workflows,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.post("/workflows/{workflow_id}/pause")
async def pause_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Pause workflow execution"""
    
    success = await workflow_engine.pause_workflow(workflow_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to pause workflow"
        )
    
    return {
        "workflow_id": workflow_id,
        "status": "paused",
        "message": "Workflow execution paused"
    }

@router.post("/workflows/{workflow_id}/resume")
async def resume_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Resume paused workflow"""
    
    success = await workflow_engine.resume_workflow(workflow_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to resume workflow"
        )
    
    return {
        "workflow_id": workflow_id,
        "status": "resumed",
        "message": "Workflow execution resumed"
    }

# Monitoring Endpoints

@router.get("/monitoring/dashboard")
async def get_monitoring_dashboard(
    current_user: User = Depends(get_current_active_user)
):
    """Get comprehensive monitoring dashboard data"""
    
    dashboard_data = workflow_monitor.get_dashboard_data()
    return dashboard_data

@router.get("/monitoring/metrics/{metric_name}")
async def get_metrics(
    metric_name: str,
    hours: int = 1,
    current_user: User = Depends(get_current_active_user)
):
    """Get metrics for a specific name and time range"""
    
    time_range = timedelta(hours=hours)
    metrics = workflow_monitor.get_metrics(metric_name, time_range)
    
    return {
        "metric_name": metric_name,
        "time_range_hours": hours,
        "data_points": len(metrics),
        "metrics": metrics
    }

@router.get("/monitoring/alerts")
async def get_alerts(
    severity: Optional[AlertSeverity] = None,
    resolved: Optional[bool] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user)
):
    """Get alerts with optional filtering"""
    
    alerts = workflow_monitor.get_alerts(severity=severity, resolved=resolved)
    
    # Apply pagination
    total = len(alerts)
    alerts = alerts[:limit]
    
    return {
        "alerts": alerts,
        "total": total,
        "limit": limit
    }

@router.post("/monitoring/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Mark an alert as resolved"""
    
    success = workflow_monitor.resolve_alert(alert_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    return {
        "alert_id": alert_id,
        "status": "resolved",
        "resolved_by": current_user.username,
        "resolved_at": datetime.utcnow().isoformat()
    }

# Recovery Endpoints

@router.post("/recovery/checkpoints")
async def create_checkpoint(
    workflow_id: str,
    step_id: Optional[str] = None,
    checkpoint_type: CheckpointType = CheckpointType.USER_DEFINED,
    state_data: Dict[str, Any] = None,
    metadata: Dict[str, Any] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Create a workflow checkpoint"""
    
    try:
        checkpoint_id = await recovery_manager.create_checkpoint(
            workflow_id=workflow_id,
            step_id=step_id,
            checkpoint_type=checkpoint_type,
            state_data=state_data or {},
            metadata={**(metadata or {}), "created_by": current_user.username}
        )
        
        return {
            "checkpoint_id": checkpoint_id,
            "workflow_id": workflow_id,
            "status": "created",
            "message": "Checkpoint created successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to create checkpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create checkpoint: {str(e)}"
        )

@router.post("/recovery/plans")
async def create_recovery_plan(
    workflow_id: str,
    failed_step_id: str,
    error_type: str,
    error_message: str,
    current_user: User = Depends(get_current_active_user)
):
    """Create a recovery plan for a failed workflow"""
    
    try:
        recovery_plan = await recovery_manager.create_recovery_plan(
            workflow_id=workflow_id,
            failed_step_id=failed_step_id,
            error_type=error_type,
            error_message=error_message
        )
        
        return {
            "recovery_plan_id": recovery_plan.id,
            "workflow_id": workflow_id,
            "recovery_action": recovery_plan.recovery_action.value,
            "status": "created",
            "message": "Recovery plan created successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to create recovery plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create recovery plan: {str(e)}"
        )

@router.post("/recovery/plans/{plan_id}/execute")
async def execute_recovery_plan(
    plan_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Execute a recovery plan"""
    
    try:
        success = await recovery_manager.execute_recovery(plan_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to execute recovery plan"
            )
        
        return {
            "recovery_plan_id": plan_id,
            "status": "executed",
            "message": "Recovery plan executed successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to execute recovery plan {plan_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute recovery plan: {str(e)}"
        )

# Testing Endpoints

@router.post("/testing/suites/{suite_id}/run")
async def run_test_suite(
    suite_id: str,
    context: Dict[str, Any] = None,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
):
    """Run a test suite"""
    
    try:
        # Run test suite in background
        background_tasks.add_task(
            automated_validator.run_test_suite,
            suite_id,
            context or {}
        )
        
        return {
            "suite_id": suite_id,
            "status": "started",
            "message": f"Test suite {suite_id} execution started"
        }
        
    except Exception as e:
        logger.error(f"Failed to start test suite {suite_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start test suite: {str(e)}"
        )

@router.get("/testing/suites/{suite_id}/results")
async def get_test_results(
    suite_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get test results for a suite"""
    
    results = automated_validator.get_test_results(suite_id)
    
    if results is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test results not found"
        )
    
    return {
        "suite_id": suite_id,
        "results": results
    }

# Health Check Endpoint

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "workflow_service",
        "version": "1.0.0"
    }
