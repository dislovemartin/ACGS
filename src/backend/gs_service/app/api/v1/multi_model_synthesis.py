"""
Multi-Model Policy Synthesis API

This module provides API endpoints for the enhanced multi-model policy synthesis
with LangGraph workflow orchestration, constitutional compliance validation,
and reliability enhancement.

Task 18: GS Engine Multi-Model Enhancement
- Extended MultiModelManager with LangGraph StateGraph integration
- Specialized Gemini model configuration
- Structured output validation with constitutional fidelity scoring
- Circuit breaker patterns for >99.9% reliability
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.backend.gs_service.app.workflows.policy_synthesis_workflow import get_policy_synthesis_workflow
from src.backend.gs_service.app.workflows.structured_output_models import (
    PolicySynthesisRequest,
    PolicySynthesisResponse,
    PolicyType,
    ModelSpecializationConfig
)
from src.backend.gs_service.app.workflows.multi_model_manager import get_multi_model_manager
from src.backend.shared.langgraph_config import ModelRole

logger = logging.getLogger(__name__)
router = APIRouter()


class SynthesisRequestAPI(BaseModel):
    """API request model for policy synthesis."""
    principle_ids: List[int] = Field(..., description="Constitutional principle IDs")
    context: str = Field(..., description="Policy context or scenario")
    policy_type: PolicyType = Field(default=PolicyType.REGO)
    
    # Synthesis parameters
    creativity_level: float = Field(default=0.3, ge=0.0, le=1.0)
    strictness_level: float = Field(default=0.8, ge=0.0, le=1.0)
    bias_mitigation_enabled: bool = Field(default=True)
    
    # Target requirements
    target_fidelity_score: float = Field(default=0.85, ge=0.0, le=1.0)
    max_violations: int = Field(default=0, ge=0)
    
    # Optional metadata
    requester: Optional[str] = Field(default="api_user")


class ModelPerformanceResponse(BaseModel):
    """Response model for model performance metrics."""
    model_metrics: Dict[str, Any]
    overall_metrics: Dict[str, Any]
    recommendations: Dict[str, str]
    timestamp: datetime


class ModelHealthResponse(BaseModel):
    """Response model for model health status."""
    healthy_models: List[str]
    unhealthy_models: List[str]
    circuit_breaker_status: Dict[str, str]
    overall_health_score: float
    reliability_target_met: bool


@router.post("/synthesize", response_model=PolicySynthesisResponse)
async def synthesize_policy(
    request: SynthesisRequestAPI,
    background_tasks: BackgroundTasks
) -> PolicySynthesisResponse:
    """
    Synthesize a policy using the multi-model LangGraph workflow.
    
    This endpoint orchestrates multiple specialized Gemini models to:
    1. Analyze constitutional principles
    2. Generate policy drafts
    3. Validate constitutional fidelity
    4. Resolve conflicts if needed
    5. Ensure quality meets thresholds
    
    Returns a comprehensive response with the generated policy,
    constitutional fidelity scores, and performance metrics.
    """
    try:
        # Generate unique request ID
        request_id = f"synthesis_{uuid.uuid4().hex[:8]}_{int(datetime.utcnow().timestamp())}"
        
        # Convert API request to internal request format
        synthesis_request = PolicySynthesisRequest(
            principle_ids=request.principle_ids,
            context=request.context,
            policy_type=request.policy_type,
            creativity_level=request.creativity_level,
            strictness_level=request.strictness_level,
            bias_mitigation_enabled=request.bias_mitigation_enabled,
            target_fidelity_score=request.target_fidelity_score,
            max_violations=request.max_violations,
            request_id=request_id,
            requester=request.requester or "api_user"
        )
        
        # Get workflow instance and execute synthesis
        workflow = get_policy_synthesis_workflow()
        response = await workflow.synthesize_policy(synthesis_request)
        
        # Log synthesis metrics for monitoring
        background_tasks.add_task(
            _log_synthesis_metrics,
            request_id,
            response.success,
            response.synthesis_duration_ms,
            response.constitutional_fidelity.overall_score if response.constitutional_fidelity else 0.0
        )
        
        logger.info(f"Policy synthesis completed: {request_id}, success: {response.success}")
        return response
        
    except Exception as e:
        logger.error(f"Policy synthesis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Policy synthesis failed: {str(e)}"
        )


@router.get("/performance", response_model=ModelPerformanceResponse)
async def get_model_performance() -> ModelPerformanceResponse:
    """
    Get performance metrics for all models in the multi-model manager.
    
    Returns detailed metrics including:
    - Success rates for each model
    - Average response times
    - Circuit breaker status
    - Overall reliability metrics
    - Model recommendations
    """
    try:
        manager = get_multi_model_manager()
        metrics = manager.get_performance_metrics()
        recommendations = manager.get_model_recommendations()
        
        # Extract overall metrics
        overall_metrics = metrics.pop("overall", {})
        
        return ModelPerformanceResponse(
            model_metrics=metrics,
            overall_metrics=overall_metrics,
            recommendations=recommendations,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Failed to get model performance: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get model performance: {str(e)}"
        )


@router.get("/health", response_model=ModelHealthResponse)
async def get_model_health() -> ModelHealthResponse:
    """
    Get health status for all models in the multi-model manager.
    
    Returns health information including:
    - List of healthy/unhealthy models
    - Circuit breaker status for each model
    - Overall health score
    - Whether reliability targets are being met
    """
    try:
        manager = get_multi_model_manager()
        metrics = manager.get_performance_metrics()
        
        healthy_models = []
        unhealthy_models = []
        circuit_breaker_status = {}
        
        for model_name, model_metrics in metrics.items():
            if model_name == "overall":
                continue
                
            success_rate = model_metrics.get("success_rate", 0.0)
            circuit_breaker_open = model_metrics.get("circuit_breaker_open", False)
            
            circuit_breaker_status[model_name] = "open" if circuit_breaker_open else "closed"
            
            if success_rate >= 0.8 and not circuit_breaker_open:
                healthy_models.append(model_name)
            else:
                unhealthy_models.append(model_name)
        
        # Calculate overall health score
        total_models = len(healthy_models) + len(unhealthy_models)
        overall_health_score = len(healthy_models) / total_models if total_models > 0 else 0.0
        
        # Check if reliability targets are met
        overall_metrics = metrics.get("overall", {})
        reliability_target_met = overall_metrics.get("reliability_target_met", False)
        
        return ModelHealthResponse(
            healthy_models=healthy_models,
            unhealthy_models=unhealthy_models,
            circuit_breaker_status=circuit_breaker_status,
            overall_health_score=overall_health_score,
            reliability_target_met=reliability_target_met
        )
        
    except Exception as e:
        logger.error(f"Failed to get model health: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get model health: {str(e)}"
        )


@router.get("/models/config", response_model=ModelSpecializationConfig)
async def get_model_configuration() -> ModelSpecializationConfig:
    """
    Get the current model specialization configuration.
    
    Returns the configuration for:
    - Model assignments for different roles
    - Temperature settings for each model type
    - Fallback chains for reliability
    - Circuit breaker settings
    """
    try:
        workflow = get_policy_synthesis_workflow()
        return workflow.config
        
    except Exception as e:
        logger.error(f"Failed to get model configuration: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get model configuration: {str(e)}"
        )


@router.post("/models/reset-circuit-breakers")
async def reset_circuit_breakers() -> JSONResponse:
    """
    Reset all circuit breakers for model failure handling.
    
    This endpoint allows manual recovery from circuit breaker states
    when models have been marked as unhealthy but may have recovered.
    """
    try:
        manager = get_multi_model_manager()
        
        # Reset circuit breakers for all models
        reset_count = 0
        for tracker in manager.performance_trackers.values():
            if tracker.circuit_breaker_open:
                tracker.circuit_breaker_open = False
                reset_count += 1
        
        logger.info(f"Reset {reset_count} circuit breakers")
        
        return JSONResponse(
            content={
                "message": f"Successfully reset {reset_count} circuit breakers",
                "reset_count": reset_count,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to reset circuit breakers: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset circuit breakers: {str(e)}"
        )


async def _log_synthesis_metrics(
    request_id: str,
    success: bool,
    duration_ms: float,
    fidelity_score: float
):
    """Background task to log synthesis metrics for monitoring."""
    try:
        # In a production system, this would send metrics to a monitoring system
        # like Prometheus, DataDog, or CloudWatch
        logger.info(
            f"SYNTHESIS_METRICS: request_id={request_id}, "
            f"success={success}, duration_ms={duration_ms:.2f}, "
            f"fidelity_score={fidelity_score:.3f}"
        )
    except Exception as e:
        logger.error(f"Failed to log synthesis metrics: {e}")


# Health check endpoint for the multi-model synthesis service
@router.get("/status")
async def get_synthesis_status() -> JSONResponse:
    """Get the status of the multi-model synthesis service."""
    try:
        manager = get_multi_model_manager()
        workflow = get_policy_synthesis_workflow()
        
        # Check if core components are available
        langgraph_available = workflow.workflow_graph is not None
        models_initialized = len(manager.model_clients) > 0
        
        status = {
            "service": "multi_model_synthesis",
            "status": "healthy" if (langgraph_available and models_initialized) else "degraded",
            "langgraph_available": langgraph_available,
            "models_initialized": models_initialized,
            "model_count": len(manager.model_clients),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return JSONResponse(content=status)
        
    except Exception as e:
        logger.error(f"Failed to get synthesis status: {e}")
        return JSONResponse(
            content={
                "service": "multi_model_synthesis",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=500
        )
