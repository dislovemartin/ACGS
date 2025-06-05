"""
Phase 2 AlphaEvolve-ACGS Enhanced Synthesis API

This module provides API endpoints for Phase 2 enhanced policy synthesis with
advanced WINA optimization, multi-model coordination, and constitutional fidelity monitoring.

Key Features:
- Multi-model ensemble synthesis
- Advanced WINA optimization
- Real-time performance monitoring
- Constitutional fidelity tracking
- Performance target achievement validation
"""

import logging
import time
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field

from ...services.enhanced_governance_synthesis import (
    EnhancedGovernanceSynthesis,
    EnhancedSynthesisRequest,
    EnhancedSynthesisResponse
)
from ...core.multi_model_coordinator import EnsembleStrategy
from ...core.performance_optimizer import OptimizationStrategy

logger = logging.getLogger(__name__)
router = APIRouter()

# Global enhanced synthesis service instance
enhanced_synthesis_service: Optional[EnhancedGovernanceSynthesis] = None


async def get_enhanced_synthesis_service() -> EnhancedGovernanceSynthesis:
    """Get or create the enhanced synthesis service instance."""
    global enhanced_synthesis_service
    if enhanced_synthesis_service is None:
        enhanced_synthesis_service = EnhancedGovernanceSynthesis()
        await enhanced_synthesis_service.initialize()
    return enhanced_synthesis_service


class Phase2SynthesisRequest(BaseModel):
    """Phase 2 enhanced synthesis request model."""
    synthesis_goal: str = Field(..., description="Goal for policy synthesis")
    constitutional_principles: List[Dict[str, Any]] = Field(default=[], description="Constitutional principles to apply")
    constraints: Optional[List[str]] = Field(default=None, description="Synthesis constraints")
    context_data: Optional[Dict[str, Any]] = Field(default=None, description="Context data for synthesis")
    
    # Phase 2 specific options
    enable_multi_model_ensemble: bool = Field(default=True, description="Enable multi-model ensemble synthesis")
    ensemble_strategy: str = Field(default="weighted_voting", description="Ensemble strategy to use")
    enable_wina_optimization: bool = Field(default=True, description="Enable WINA optimization")
    optimization_strategy: str = Field(default="adaptive", description="WINA optimization strategy")
    enable_constitutional_monitoring: bool = Field(default=True, description="Enable constitutional fidelity monitoring")
    
    # Performance targets
    target_gflops_reduction: Optional[float] = Field(default=0.5, description="Target GFLOPs reduction (0.0-1.0)")
    target_accuracy_retention: Optional[float] = Field(default=0.95, description="Target accuracy retention (0.0-1.0)")
    target_constitutional_compliance: Optional[float] = Field(default=0.85, description="Target constitutional compliance (0.0-1.0)")
    
    # Validation options
    max_synthesis_time_ms: int = Field(default=5000, description="Maximum synthesis time in milliseconds")
    enable_performance_validation: bool = Field(default=True, description="Enable performance target validation")


class Phase2SynthesisResponse(BaseModel):
    """Phase 2 enhanced synthesis response model."""
    synthesis_id: str
    success: bool
    synthesized_policy: str
    
    # Phase 2 performance metrics
    gflops_reduction_achieved: float
    accuracy_retained: float
    constitutional_compliance: float
    synthesis_time_ms: float
    
    # Ensemble information
    contributing_models: List[str]
    ensemble_strategy_used: str
    confidence_score: float
    
    # Optimization details
    wina_optimization_applied: bool
    optimization_strategy_used: str
    performance_targets_met: bool
    
    # Quality metrics
    constitutional_fidelity_score: float
    validation_passed: bool
    
    # Feedback
    recommendations: List[str]
    warnings: List[str]
    
    # Metadata
    phase2_features_used: List[str]
    metadata: Dict[str, Any]


class PerformanceTargetsRequest(BaseModel):
    """Request model for updating performance targets."""
    target_gflops_reduction: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    target_accuracy_retention: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    target_constitutional_compliance: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    optimization_strategy: Optional[str] = Field(default=None)


@router.post("/synthesize", response_model=Phase2SynthesisResponse)
async def synthesize_policy_phase2(
    request: Phase2SynthesisRequest,
    background_tasks: BackgroundTasks,
    service: EnhancedGovernanceSynthesis = Depends(get_enhanced_synthesis_service)
):
    """
    Synthesize governance policy using Phase 2 enhanced capabilities.
    
    This endpoint provides advanced policy synthesis with multi-model ensemble coordination,
    WINA optimization, and real-time constitutional fidelity monitoring.
    """
    start_time = time.time()
    
    try:
        logger.info(f"Starting Phase 2 policy synthesis: {request.synthesis_goal}")
        
        # Convert to internal request format
        enhanced_request = EnhancedSynthesisRequest(
            synthesis_goal=request.synthesis_goal,
            constitutional_principles=request.constitutional_principles,
            constraints=request.constraints,
            context_data=request.context_data or {},
            enable_wina_optimization=request.enable_wina_optimization,
            enable_alphaevolve_synthesis=True,
            enable_langgraph_workflow=True
        )
        
        # Add Phase 2 specific context
        enhanced_request.context_data.update({
            "phase2_enabled": True,
            "ensemble_strategy": request.ensemble_strategy,
            "optimization_strategy": request.optimization_strategy,
            "performance_targets": {
                "gflops_reduction": request.target_gflops_reduction,
                "accuracy_retention": request.target_accuracy_retention,
                "constitutional_compliance": request.target_constitutional_compliance
            }
        })
        
        # Execute synthesis
        synthesis_response = await service.synthesize_policy(enhanced_request)
        
        # Extract Phase 2 specific metrics
        ensemble_result = synthesis_response.alphaevolve_metadata or {}
        optimization_result = getattr(synthesis_response, 'optimization_result', None)
        
        # Calculate performance achievements
        performance_targets_met = (
            synthesis_response.validation_score >= (request.target_constitutional_compliance or 0.85) and
            synthesis_response.is_valid
        )
        
        # Determine Phase 2 features used
        phase2_features = []
        if request.enable_multi_model_ensemble:
            phase2_features.append("multi_model_ensemble")
        if request.enable_wina_optimization:
            phase2_features.append("wina_optimization")
        if request.enable_constitutional_monitoring:
            phase2_features.append("constitutional_monitoring")
        
        # Extract synthesized policy content safely
        policy_content = synthesis_response.synthesized_policy
        if isinstance(policy_content, dict):
            # If it's a dict, extract the actual policy content
            policy_content = policy_content.get("policy_content", str(policy_content))
        elif not isinstance(policy_content, str):
            # Convert to string if it's not already
            policy_content = str(policy_content)

        # Create response
        response = Phase2SynthesisResponse(
            synthesis_id=synthesis_response.synthesis_id,
            success=synthesis_response.is_valid,
            synthesized_policy=policy_content,
            gflops_reduction_achieved=optimization_result.gflops_reduction_achieved if optimization_result else 0.0,
            accuracy_retained=optimization_result.accuracy_retained if optimization_result else 1.0,
            constitutional_compliance=synthesis_response.validation_score,
            synthesis_time_ms=synthesis_response.total_latency_ms,
            contributing_models=ensemble_result.get("contributing_models", ["primary"]),
            ensemble_strategy_used=request.ensemble_strategy,
            confidence_score=synthesis_response.validation_score,
            wina_optimization_applied=request.enable_wina_optimization,
            optimization_strategy_used=request.optimization_strategy,
            performance_targets_met=performance_targets_met,
            constitutional_fidelity_score=synthesis_response.validation_score,
            validation_passed=synthesis_response.is_valid,
            recommendations=synthesis_response.recommendations,
            warnings=synthesis_response.warnings,
            phase2_features_used=phase2_features,
            metadata=synthesis_response.policy_metadata
        )
        
        # Schedule background performance tracking
        background_tasks.add_task(
            _track_synthesis_performance,
            service,
            response,
            time.time() - start_time
        )
        
        logger.info(f"Phase 2 synthesis completed successfully: {synthesis_response.synthesis_id}")
        return response
        
    except Exception as e:
        logger.error(f"Phase 2 synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {str(e)}")


@router.get("/performance-summary")
async def get_performance_summary(
    service: EnhancedGovernanceSynthesis = Depends(get_enhanced_synthesis_service)
):
    """Get comprehensive Phase 2 performance summary."""
    try:
        metrics = service.get_metrics()
        return {
            "status": "success",
            "phase2_performance": metrics,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Failed to get performance summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance summary: {str(e)}")


@router.get("/health")
async def health_check_phase2(
    service: EnhancedGovernanceSynthesis = Depends(get_enhanced_synthesis_service)
):
    """Perform comprehensive Phase 2 health check."""
    try:
        health_status = await service.health_check()
        
        # Add Phase 2 specific health checks
        phase2_health = {
            "multi_model_coordinator": "available" if service.multi_model_coordinator else "unavailable",
            "performance_optimizer": "available" if service.performance_optimizer else "unavailable",
            "constitutional_fidelity_monitor": "available" if service.constitutional_fidelity_monitor else "unavailable",
            "wina_svd_transformer": "available" if service.wina_svd_transformer else "unavailable"
        }
        
        health_status["phase2_components"] = phase2_health
        health_status["phase2_ready"] = all(status == "available" for status in phase2_health.values())
        
        return health_status
        
    except Exception as e:
        logger.error(f"Phase 2 health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.post("/update-performance-targets")
async def update_performance_targets(
    request: PerformanceTargetsRequest,
    service: EnhancedGovernanceSynthesis = Depends(get_enhanced_synthesis_service)
):
    """Update Phase 2 performance targets."""
    try:
        if service.performance_optimizer:
            # Update optimizer configuration
            if request.target_gflops_reduction is not None:
                service.performance_optimizer.target_gflops_reduction = request.target_gflops_reduction
            if request.target_accuracy_retention is not None:
                service.performance_optimizer.accuracy_retention_threshold = request.target_accuracy_retention
            if request.target_constitutional_compliance is not None:
                service.performance_optimizer.constitutional_compliance_threshold = request.target_constitutional_compliance
            if request.optimization_strategy is not None:
                service.performance_optimizer.optimization_strategy = OptimizationStrategy(request.optimization_strategy)
            
            return {
                "status": "success",
                "message": "Performance targets updated successfully",
                "updated_targets": {
                    "gflops_reduction": service.performance_optimizer.target_gflops_reduction,
                    "accuracy_retention": service.performance_optimizer.accuracy_retention_threshold,
                    "constitutional_compliance": service.performance_optimizer.constitutional_compliance_threshold,
                    "optimization_strategy": service.performance_optimizer.optimization_strategy.value
                }
            }
        else:
            raise HTTPException(status_code=503, detail="Performance optimizer not available")
            
    except Exception as e:
        logger.error(f"Failed to update performance targets: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update targets: {str(e)}")


@router.get("/optimization-recommendations")
async def get_optimization_recommendations(
    service: EnhancedGovernanceSynthesis = Depends(get_enhanced_synthesis_service)
):
    """Get optimization strategy recommendations based on current performance."""
    try:
        if service.performance_optimizer:
            recommendations = await service.performance_optimizer.recommend_strategy_adjustment()
            return {
                "status": "success",
                "recommendations": recommendations,
                "timestamp": time.time()
            }
        else:
            raise HTTPException(status_code=503, detail="Performance optimizer not available")
            
    except Exception as e:
        logger.error(f"Failed to get optimization recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")


async def _track_synthesis_performance(
    service: EnhancedGovernanceSynthesis,
    response: Phase2SynthesisResponse,
    total_time: float
):
    """Background task to track synthesis performance."""
    try:
        # Update service metrics with Phase 2 specific data
        service.metrics["wina_optimization_success_rate"] = (
            (service.metrics["wina_optimization_success_rate"] * service.metrics["total_syntheses"] + 
             (1.0 if response.wina_optimization_applied and response.success else 0.0)) /
            (service.metrics["total_syntheses"] + 1)
        )
        
        service.metrics["gflops_reduction_achieved"] = (
            (service.metrics["gflops_reduction_achieved"] * service.metrics["total_syntheses"] + 
             response.gflops_reduction_achieved) /
            (service.metrics["total_syntheses"] + 1)
        )
        
        service.metrics["constitutional_fidelity_score"] = (
            (service.metrics["constitutional_fidelity_score"] * service.metrics["total_syntheses"] + 
             response.constitutional_fidelity_score) /
            (service.metrics["total_syntheses"] + 1)
        )
        
        # Check if Phase 2 targets are being met
        service.metrics["target_performance_achieved"] = (
            response.gflops_reduction_achieved >= 0.4 and  # At least 40% GFLOPs reduction
            response.accuracy_retained >= 0.95 and        # At least 95% accuracy retention
            response.constitutional_compliance >= 0.85     # At least 85% constitutional compliance
        )
        
        logger.debug(f"Performance tracking updated for synthesis {response.synthesis_id}")
        
    except Exception as e:
        logger.error(f"Failed to track synthesis performance: {e}")
