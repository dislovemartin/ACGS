"""
WINA Rego Synthesis API Endpoints

This module provides REST API endpoints for WINA-optimized Rego policy synthesis
within the AlphaEvolve-ACGS framework.

Endpoints:
- POST /wina-rego-synthesis/synthesize: Synthesize single Rego policy with WINA
- POST /wina-rego-synthesis/batch: Batch synthesize multiple Rego policies
- GET /wina-rego-synthesis/performance: Get WINA synthesis performance metrics
- DELETE /wina-rego-synthesis/cache: Clear WINA synthesis cache
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field

from ...core.wina_rego_synthesis import (
    synthesize_rego_policy_with_wina,
    batch_synthesize_rego_policies_with_wina,
    get_wina_rego_synthesis_performance_summary,
    clear_wina_rego_synthesis_cache,
    WINARegoSynthesisResult,
    WINARegoSynthesisMetrics
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/wina-rego-synthesis", tags=["WINA Rego Synthesis"])


# Request/Response Models
class ConstitutionalPrincipleModel(BaseModel):
    """Constitutional principle model for API requests."""
    id: Optional[str] = None
    description: str = Field(..., description="Description of the constitutional principle")
    type: Optional[str] = Field(default="governance_rule", description="Type of principle")
    priority: Optional[float] = Field(default=1.0, description="Priority weight")
    scope: Optional[str] = Field(default="general", description="Scope of application")


class WINARegoSynthesisRequest(BaseModel):
    """Request model for WINA Rego policy synthesis."""
    synthesis_goal: str = Field(..., description="Natural language description of policy goal")
    constitutional_principles: List[ConstitutionalPrincipleModel] = Field(
        default=[], description="Constitutional principles to incorporate"
    )
    constraints: Optional[List[str]] = Field(
        default=None, description="Optional constraints for the policy"
    )
    context_data: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional context information"
    )
    apply_wina: Optional[bool] = Field(
        default=None, description="Override WINA application (None uses default)"
    )


class WINARegoSynthesisMetricsResponse(BaseModel):
    """Response model for WINA synthesis metrics."""
    synthesis_time: float
    gflops_reduction: float
    accuracy_preservation: float
    constitutional_compliance: bool
    rego_validation_success: bool
    policy_complexity_score: float
    optimization_applied: bool
    error_count: int


class WINARegoSynthesisResponse(BaseModel):
    """Response model for WINA Rego synthesis results."""
    success: bool
    rego_content: str
    constitutional_compliance: bool
    synthesis_metrics: WINARegoSynthesisMetricsResponse
    validation_result: Optional[Dict[str, Any]]
    warnings: List[str]
    policy_suggestion_confidence: Optional[float] = None
    wina_optimization_applied: bool


class BatchWINARegoSynthesisRequest(BaseModel):
    """Request model for batch WINA Rego synthesis."""
    synthesis_requests: List[WINARegoSynthesisRequest] = Field(
        ..., description="List of synthesis requests"
    )
    enable_wina: bool = Field(default=True, description="Enable WINA optimization for batch")


class PerformanceSummaryResponse(BaseModel):
    """Response model for performance summary."""
    performance_metrics: Dict[str, Any]
    synthesis_history_count: int
    wina_enabled: bool
    recent_syntheses: List[Dict[str, Any]]
    target_performance: Dict[str, str]


@router.post("/synthesize", response_model=WINARegoSynthesisResponse)
async def synthesize_rego_policy(request: WINARegoSynthesisRequest):
    """
    Synthesize a Rego policy with WINA optimization.
    
    This endpoint generates a Rego policy based on the provided synthesis goal
    and constitutional principles, using WINA optimization for improved performance.
    
    Returns:
        WINARegoSynthesisResponse with synthesis results and metrics
    """
    try:
        logger.info(f"Starting WINA Rego synthesis for goal: '{request.synthesis_goal}'")
        
        # Convert Pydantic models to dictionaries
        constitutional_principles = [
            principle.dict() for principle in request.constitutional_principles
        ]
        
        # Perform synthesis
        result = await synthesize_rego_policy_with_wina(
            synthesis_goal=request.synthesis_goal,
            constitutional_principles=constitutional_principles,
            constraints=request.constraints,
            context_data=request.context_data,
            apply_wina=request.apply_wina
        )
        
        # Extract policy suggestion confidence if available
        policy_suggestion_confidence = None
        if result.policy_suggestion and result.policy_suggestion.confidence_score:
            policy_suggestion_confidence = result.policy_suggestion.confidence_score
        
        # Create response
        response = WINARegoSynthesisResponse(
            success=result.success,
            rego_content=result.rego_content,
            constitutional_compliance=result.constitutional_compliance,
            synthesis_metrics=WINARegoSynthesisMetricsResponse(
                synthesis_time=result.synthesis_metrics.synthesis_time,
                gflops_reduction=result.synthesis_metrics.gflops_reduction,
                accuracy_preservation=result.synthesis_metrics.accuracy_preservation,
                constitutional_compliance=result.synthesis_metrics.constitutional_compliance,
                rego_validation_success=result.synthesis_metrics.rego_validation_success,
                policy_complexity_score=result.synthesis_metrics.policy_complexity_score,
                optimization_applied=result.synthesis_metrics.optimization_applied,
                error_count=result.synthesis_metrics.error_count
            ),
            validation_result=result.validation_result,
            warnings=result.warnings,
            policy_suggestion_confidence=policy_suggestion_confidence,
            wina_optimization_applied=result.wina_optimization is not None
        )
        
        logger.info(f"WINA Rego synthesis completed. Success: {result.success}, "
                   f"GFLOPs reduction: {result.synthesis_metrics.gflops_reduction:.3f}")
        
        return response
        
    except Exception as e:
        logger.error(f"WINA Rego synthesis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Synthesis failed: {str(e)}"
        )


@router.post("/batch", response_model=List[WINARegoSynthesisResponse])
async def batch_synthesize_rego_policies(request: BatchWINARegoSynthesisRequest):
    """
    Batch synthesize multiple Rego policies with WINA optimization.
    
    This endpoint processes multiple synthesis requests in batch,
    applying WINA optimization to improve overall performance.
    
    Returns:
        List of WINARegoSynthesisResponse objects
    """
    try:
        logger.info(f"Starting batch WINA Rego synthesis for {len(request.synthesis_requests)} requests")
        
        # Convert requests to dictionaries
        synthesis_requests = []
        for req in request.synthesis_requests:
            constitutional_principles = [
                principle.dict() for principle in req.constitutional_principles
            ]
            synthesis_requests.append({
                'synthesis_goal': req.synthesis_goal,
                'constitutional_principles': constitutional_principles,
                'constraints': req.constraints,
                'context_data': req.context_data,
                'apply_wina': req.apply_wina
            })
        
        # Perform batch synthesis
        results = await batch_synthesize_rego_policies_with_wina(
            synthesis_requests=synthesis_requests,
            enable_wina=request.enable_wina
        )
        
        # Convert results to response format
        responses = []
        for result in results:
            policy_suggestion_confidence = None
            if result.policy_suggestion and result.policy_suggestion.confidence_score:
                policy_suggestion_confidence = result.policy_suggestion.confidence_score
            
            responses.append(WINARegoSynthesisResponse(
                success=result.success,
                rego_content=result.rego_content,
                constitutional_compliance=result.constitutional_compliance,
                synthesis_metrics=WINARegoSynthesisMetricsResponse(
                    synthesis_time=result.synthesis_metrics.synthesis_time,
                    gflops_reduction=result.synthesis_metrics.gflops_reduction,
                    accuracy_preservation=result.synthesis_metrics.accuracy_preservation,
                    constitutional_compliance=result.synthesis_metrics.constitutional_compliance,
                    rego_validation_success=result.synthesis_metrics.rego_validation_success,
                    policy_complexity_score=result.synthesis_metrics.policy_complexity_score,
                    optimization_applied=result.synthesis_metrics.optimization_applied,
                    error_count=result.synthesis_metrics.error_count
                ),
                validation_result=result.validation_result,
                warnings=result.warnings,
                policy_suggestion_confidence=policy_suggestion_confidence,
                wina_optimization_applied=result.wina_optimization is not None
            ))
        
        successful_syntheses = sum(1 for r in results if r.success)
        logger.info(f"Batch WINA Rego synthesis completed. "
                   f"Successful: {successful_syntheses}/{len(results)}")
        
        return responses
        
    except Exception as e:
        logger.error(f"Batch WINA Rego synthesis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch synthesis failed: {str(e)}"
        )


@router.get("/performance", response_model=PerformanceSummaryResponse)
async def get_performance_summary():
    """
    Get WINA Rego synthesis performance metrics and statistics.
    
    Returns comprehensive performance data including GFLOPs reduction,
    synthesis accuracy, constitutional compliance rates, and recent synthesis history.
    
    Returns:
        PerformanceSummaryResponse with detailed performance metrics
    """
    try:
        summary = get_wina_rego_synthesis_performance_summary()
        
        return PerformanceSummaryResponse(
            performance_metrics=summary["performance_metrics"],
            synthesis_history_count=summary["synthesis_history_count"],
            wina_enabled=summary["wina_enabled"],
            recent_syntheses=summary["recent_syntheses"],
            target_performance=summary["target_performance"]
        )
        
    except Exception as e:
        logger.error(f"Failed to get performance summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance summary: {str(e)}"
        )


@router.delete("/cache")
async def clear_synthesis_cache():
    """
    Clear WINA Rego synthesis cache and reset performance tracking.
    
    This endpoint clears all cached WINA optimization data and resets
    performance tracking metrics. Use with caution in production.
    
    Returns:
        Success message
    """
    try:
        clear_wina_rego_synthesis_cache()
        logger.info("WINA Rego synthesis cache cleared successfully")
        
        return {"message": "WINA Rego synthesis cache cleared successfully"}
        
    except Exception as e:
        logger.error(f"Failed to clear synthesis cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint for WINA Rego synthesis service.
    
    Returns:
        Service health status and basic information
    """
    try:
        summary = get_wina_rego_synthesis_performance_summary()
        
        return {
            "status": "healthy",
            "service": "WINA Rego Synthesis",
            "wina_enabled": summary["wina_enabled"],
            "total_syntheses": summary["performance_metrics"]["total_syntheses"],
            "wina_optimized_syntheses": summary["performance_metrics"]["wina_optimized_syntheses"]
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "WINA Rego Synthesis",
            "error": str(e)
        }
