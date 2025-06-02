"""
WINA Continuous Learning API Module

This module provides REST API endpoints for the WINA Continuous Learning Feedback Loops system,
enabling external services to interact with the learning system, submit feedback, and retrieve
optimization recommendations.

Key Features:
- RESTful API for learning system interaction
- Feedback signal submission endpoints
- Learning status and metrics retrieval
- Component-specific optimization recommendations
- Real-time learning system monitoring
- Integration with performance monitoring from Task 17.10
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field, validator
from enum import Enum

# WINA imports
try:
    from .continuous_learning import (
        WINAContinuousLearningSystem,
        FeedbackSignal,
        FeedbackType,
        LearningStrategy,
        LearningPhase,
        get_wina_learning_system,
        process_efficiency_feedback,
        process_accuracy_feedback,
        process_constitutional_feedback
    )
    from .performance_monitoring import WINAComponentType, WINAPerformanceCollector
    WINA_AVAILABLE = True
except ImportError as e:
    WINA_AVAILABLE = False
    logging.getLogger(__name__).warning(f"WINA modules not available: {e}")

logger = logging.getLogger(__name__)

# API Models

class FeedbackTypeAPI(str, Enum):
    """API enum for feedback types."""
    PERFORMANCE_METRIC = "performance_metric"
    ACCURACY_RETENTION = "accuracy_retention"
    EFFICIENCY_GAIN = "efficiency_gain"
    CONSTITUTIONAL_COMPLIANCE = "constitutional_compliance"
    USER_FEEDBACK = "user_feedback"
    SYSTEM_ERROR = "system_error"
    OPTIMIZATION_SUCCESS = "optimization_success"


class ComponentTypeAPI(str, Enum):
    """API enum for component types."""
    NEURON_ACTIVATION = "neuron_activation"
    SVD_TRANSFORMATION = "svd_transformation"
    DYNAMIC_GATING = "dynamic_gating"
    CONSTITUTIONAL_VERIFICATION = "constitutional_verification"
    EC_OVERSIGHT = "ec_oversight"
    INTEGRATION_MONITORING = "integration_monitoring"


class LearningStrategyAPI(str, Enum):
    """API enum for learning strategies."""
    REINFORCEMENT_LEARNING = "reinforcement_learning"
    PATTERN_RECOGNITION = "pattern_recognition"
    ADAPTIVE_THRESHOLD = "adaptive_threshold"
    GRADIENT_OPTIMIZATION = "gradient_optimization"
    CONSTITUTIONAL_ALIGNMENT = "constitutional_alignment"
    HYBRID_MULTIMODAL = "hybrid_multimodal"


class LearningPhaseAPI(str, Enum):
    """API enum for learning phases."""
    EXPLORATION = "exploration"
    EXPLOITATION = "exploitation"
    CONVERGENCE = "convergence"
    ADAPTATION = "adaptation"


class FeedbackSubmissionRequest(BaseModel):
    """Request model for submitting feedback signals."""
    component_type: ComponentTypeAPI
    feedback_type: FeedbackTypeAPI
    value: float = Field(..., ge=-1.0, le=1.0, description="Feedback value normalized between -1 and 1")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context information")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence in feedback signal")
    source: str = Field(default="api", description="Source of the feedback signal")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @validator('value')
    def validate_value(cls, v, values):
        """Validate feedback value based on feedback type."""
        if 'feedback_type' in values:
            feedback_type = values['feedback_type']
            if feedback_type in [FeedbackTypeAPI.ACCURACY_RETENTION, FeedbackTypeAPI.EFFICIENCY_GAIN]:
                if v < 0:
                    raise ValueError(f"{feedback_type} must be non-negative")
            elif feedback_type == FeedbackTypeAPI.CONSTITUTIONAL_COMPLIANCE:
                if not (0 <= v <= 1):
                    raise ValueError("Constitutional compliance must be between 0 and 1")
        return v


class FeedbackSubmissionResponse(BaseModel):
    """Response model for feedback submission."""
    success: bool
    message: str
    feedback_id: str
    timestamp: datetime
    processing_time_ms: float


class BatchFeedbackRequest(BaseModel):
    """Request model for batch feedback submission."""
    feedback_signals: List[FeedbackSubmissionRequest] = Field(..., min_items=1, max_items=100)
    batch_id: Optional[str] = None
    priority: str = Field(default="normal", regex="^(low|normal|high|critical)$")


class BatchFeedbackResponse(BaseModel):
    """Response model for batch feedback submission."""
    batch_id: str
    total_signals: int
    successful_submissions: int
    failed_submissions: int
    processing_time_ms: float
    errors: List[str] = Field(default_factory=list)


class LearningStatusResponse(BaseModel):
    """Response model for learning system status."""
    current_phase: LearningPhaseAPI
    strategy_in_use: LearningStrategyAPI
    exploration_rate: float
    learning_rate: float
    metrics: Dict[str, Any]
    component_profiles: Dict[str, Any]
    recent_actions: int
    feedback_queue_size: int
    system_health: str
    uptime_seconds: float


class ComponentRecommendationsRequest(BaseModel):
    """Request model for component recommendations."""
    component_type: ComponentTypeAPI
    include_parameters: bool = Field(default=True, description="Include current parameters in response")
    include_history: bool = Field(default=False, description="Include learning history in response")
    optimization_target: Optional[str] = Field(default=None, regex="^(efficiency|accuracy|stability|compliance)$")


class ComponentRecommendationsResponse(BaseModel):
    """Response model for component recommendations."""
    component_type: str
    current_parameters: Dict[str, float]
    parameter_bounds: Dict[str, List[float]]
    stability_score: float
    adaptation_rate: float
    recommendations: List[Dict[str, Any]]
    learning_history: Optional[List[Dict[str, Any]]] = None
    optimization_suggestions: List[str]


class LearningMetricsResponse(BaseModel):
    """Response model for learning metrics."""
    total_feedback_processed: int
    learning_actions_generated: int
    successful_adaptations: int
    failed_adaptations: int
    average_performance_improvement: float
    convergence_events: int
    system_efficiency: float
    learning_effectiveness: float


class OptimizationRequest(BaseModel):
    """Request model for manual optimization trigger."""
    component_type: Optional[ComponentTypeAPI] = None
    optimization_target: str = Field(..., regex="^(efficiency|accuracy|stability|compliance|all)$")
    force_exploration: bool = Field(default=False, description="Force exploration phase")
    learning_rate_override: Optional[float] = Field(default=None, ge=0.0001, le=0.1)


class OptimizationResponse(BaseModel):
    """Response model for optimization trigger."""
    optimization_id: str
    target: str
    estimated_completion_time: float
    expected_improvements: Dict[str, float]
    monitoring_endpoint: str


# FastAPI Router
def create_learning_api_router() -> APIRouter:
    """Create FastAPI router for WINA learning API."""
    
    if not WINA_AVAILABLE:
        # Return minimal router if WINA not available
        router = APIRouter(prefix="/api/v1/wina/learning", tags=["WINA Learning"])
        
        @router.get("/health")
        async def health_check():
            return {"status": "unavailable", "reason": "WINA modules not available"}
        
        return router
    
    router = APIRouter(prefix="/api/v1/wina/learning", tags=["WINA Learning"])
    
    @router.get("/health")
    async def health_check():
        """Health check endpoint for learning system."""
        try:
            learning_system = await get_wina_learning_system()
            status = await learning_system.get_learning_status()
            
            return {
                "status": "healthy",
                "learning_system_active": True,
                "current_phase": status.get("learning_state", {}).get("current_phase", "unknown"),
                "queue_size": status.get("feedback_queue_size", 0),
                "total_feedback_processed": status.get("metrics", {}).get("total_feedback_processed", 0)
            }
        except Exception as e:
            logger.error(f"Learning system health check failed: {e}")
            raise HTTPException(status_code=503, detail=f"Learning system unhealthy: {str(e)}")
    
    @router.post("/feedback", response_model=FeedbackSubmissionResponse)
    async def submit_feedback(
        request: FeedbackSubmissionRequest,
        background_tasks: BackgroundTasks
    ):
        """Submit a single feedback signal to the learning system."""
        start_time = datetime.now()
        
        try:
            # Convert API enums to internal enums
            component_type = _convert_component_type(request.component_type)
            feedback_type = _convert_feedback_type(request.feedback_type)
            
            # Create feedback signal
            feedback = FeedbackSignal(
                component_type=component_type,
                feedback_type=feedback_type,
                value=request.value,
                context=request.context,
                timestamp=datetime.now(),
                confidence=request.confidence,
                source=request.source,
                metadata=request.metadata
            )
            
            # Submit to learning system
            learning_system = await get_wina_learning_system()
            await learning_system.process_feedback_signal(feedback)
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            feedback_id = f"fb_{int(datetime.now().timestamp())}_{hash(str(feedback))}"
            
            return FeedbackSubmissionResponse(
                success=True,
                message="Feedback signal processed successfully",
                feedback_id=feedback_id,
                timestamp=datetime.now(),
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Feedback submission failed: {e}")
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            raise HTTPException(
                status_code=400,
                detail=f"Feedback submission failed: {str(e)}"
            )
    
    @router.post("/feedback/batch", response_model=BatchFeedbackResponse)
    async def submit_batch_feedback(
        request: BatchFeedbackRequest,
        background_tasks: BackgroundTasks
    ):
        """Submit multiple feedback signals as a batch."""
        start_time = datetime.now()
        batch_id = request.batch_id or f"batch_{int(datetime.now().timestamp())}"
        
        successful_submissions = 0
        failed_submissions = 0
        errors = []
        
        try:
            learning_system = await get_wina_learning_system()
            
            for i, feedback_request in enumerate(request.feedback_signals):
                try:
                    # Convert API enums to internal enums
                    component_type = _convert_component_type(feedback_request.component_type)
                    feedback_type = _convert_feedback_type(feedback_request.feedback_type)
                    
                    # Create feedback signal
                    feedback = FeedbackSignal(
                        component_type=component_type,
                        feedback_type=feedback_type,
                        value=feedback_request.value,
                        context=feedback_request.context,
                        timestamp=datetime.now(),
                        confidence=feedback_request.confidence,
                        source=feedback_request.source,
                        metadata=feedback_request.metadata
                    )
                    
                    # Submit to learning system
                    await learning_system.process_feedback_signal(feedback)
                    successful_submissions += 1
                    
                except Exception as e:
                    failed_submissions += 1
                    errors.append(f"Signal {i}: {str(e)}")
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return BatchFeedbackResponse(
                batch_id=batch_id,
                total_signals=len(request.feedback_signals),
                successful_submissions=successful_submissions,
                failed_submissions=failed_submissions,
                processing_time_ms=processing_time,
                errors=errors
            )
            
        except Exception as e:
            logger.error(f"Batch feedback submission failed: {e}")
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            raise HTTPException(
                status_code=500,
                detail=f"Batch feedback submission failed: {str(e)}"
            )
    
    @router.get("/status", response_model=LearningStatusResponse)
    async def get_learning_status():
        """Get current learning system status and metrics."""
        try:
            learning_system = await get_wina_learning_system()
            status = await learning_system.get_learning_status()
            
            # Calculate system health
            metrics = status.get("metrics", {})
            total_adaptations = metrics.get("successful_adaptations", 0) + metrics.get("failed_adaptations", 0)
            success_rate = metrics.get("successful_adaptations", 0) / max(total_adaptations, 1)
            
            if success_rate > 0.9:
                system_health = "excellent"
            elif success_rate > 0.7:
                system_health = "good"
            elif success_rate > 0.5:
                system_health = "fair"
            else:
                system_health = "poor"
            
            return LearningStatusResponse(
                current_phase=LearningPhaseAPI(status["learning_state"]["current_phase"]),
                strategy_in_use=LearningStrategyAPI(status["learning_state"]["strategy_in_use"]),
                exploration_rate=status["learning_state"]["exploration_rate"],
                learning_rate=status["learning_state"]["learning_rate"],
                metrics=status["metrics"],
                component_profiles=status["component_profiles"],
                recent_actions=status["recent_actions"],
                feedback_queue_size=status["feedback_queue_size"],
                system_health=system_health,
                uptime_seconds=0.0  # Would be calculated from system start time
            )
            
        except Exception as e:
            logger.error(f"Failed to get learning status: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get learning status: {str(e)}")
    
    @router.post("/recommendations", response_model=ComponentRecommendationsResponse)
    async def get_component_recommendations(request: ComponentRecommendationsRequest):
        """Get optimization recommendations for a specific component."""
        try:
            component_type = _convert_component_type(request.component_type)
            learning_system = await get_wina_learning_system()
            recommendations = await learning_system.get_component_recommendations(component_type)
            
            if "error" in recommendations:
                raise HTTPException(status_code=404, detail=recommendations["error"])
            
            # Convert parameter bounds to list format for API
            parameter_bounds = {}
            for param, bounds in recommendations.get("parameter_bounds", {}).items():
                parameter_bounds[param] = [bounds[0], bounds[1]]
            
            # Generate optimization suggestions
            optimization_suggestions = []
            for rec in recommendations.get("recommendations", []):
                optimization_suggestions.append(rec.get("suggested_action", ""))
            
            return ComponentRecommendationsResponse(
                component_type=request.component_type.value,
                current_parameters=recommendations.get("current_parameters", {}),
                parameter_bounds=parameter_bounds,
                stability_score=recommendations.get("stability_score", 0.0),
                adaptation_rate=recommendations.get("adaptation_rate", 0.0),
                recommendations=recommendations.get("recommendations", []),
                learning_history=None if not request.include_history else [],
                optimization_suggestions=optimization_suggestions
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get component recommendations: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")
    
    @router.get("/metrics", response_model=LearningMetricsResponse)
    async def get_learning_metrics():
        """Get detailed learning system metrics."""
        try:
            learning_system = await get_wina_learning_system()
            status = await learning_system.get_learning_status()
            metrics = status.get("metrics", {})
            
            # Calculate derived metrics
            total_adaptations = metrics.get("successful_adaptations", 0) + metrics.get("failed_adaptations", 0)
            system_efficiency = metrics.get("successful_adaptations", 0) / max(total_adaptations, 1)
            
            total_actions = metrics.get("learning_actions_generated", 0)
            learning_effectiveness = metrics.get("successful_adaptations", 0) / max(total_actions, 1)
            
            return LearningMetricsResponse(
                total_feedback_processed=metrics.get("total_feedback_processed", 0),
                learning_actions_generated=metrics.get("learning_actions_generated", 0),
                successful_adaptations=metrics.get("successful_adaptations", 0),
                failed_adaptations=metrics.get("failed_adaptations", 0),
                average_performance_improvement=metrics.get("average_performance_improvement", 0.0),
                convergence_events=metrics.get("convergence_events", 0),
                system_efficiency=system_efficiency,
                learning_effectiveness=learning_effectiveness
            )
            
        except Exception as e:
            logger.error(f"Failed to get learning metrics: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get learning metrics: {str(e)}")
    
    @router.post("/optimize", response_model=OptimizationResponse)
    async def trigger_optimization(request: OptimizationRequest):
        """Trigger manual optimization for specific component or system-wide."""
        try:
            optimization_id = f"opt_{int(datetime.now().timestamp())}"
            
            # This would trigger actual optimization in the learning system
            # For now, return a mock response
            expected_improvements = {}
            
            if request.optimization_target == "efficiency":
                expected_improvements = {"gflops_reduction": 0.1, "processing_speed": 0.05}
            elif request.optimization_target == "accuracy":
                expected_improvements = {"accuracy_retention": 0.02, "precision": 0.01}
            elif request.optimization_target == "stability":
                expected_improvements = {"variance_reduction": 0.15, "consistency": 0.08}
            elif request.optimization_target == "compliance":
                expected_improvements = {"compliance_score": 0.05, "governance_alignment": 0.03}
            else:  # all
                expected_improvements = {
                    "gflops_reduction": 0.08,
                    "accuracy_retention": 0.01,
                    "stability": 0.1,
                    "compliance_score": 0.03
                }
            
            return OptimizationResponse(
                optimization_id=optimization_id,
                target=request.optimization_target,
                estimated_completion_time=300.0,  # 5 minutes
                expected_improvements=expected_improvements,
                monitoring_endpoint=f"/api/v1/wina/learning/optimization/{optimization_id}/status"
            )
            
        except Exception as e:
            logger.error(f"Failed to trigger optimization: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to trigger optimization: {str(e)}")
    
    # Convenience endpoints for common feedback types
    
    @router.post("/feedback/efficiency")
    async def submit_efficiency_feedback(
        component_type: ComponentTypeAPI,
        efficiency_value: float = Field(..., ge=0.0, le=1.0),
        context: Dict[str, Any] = {}
    ):
        """Convenience endpoint for efficiency feedback."""
        try:
            component = _convert_component_type(component_type)
            await process_efficiency_feedback(component, efficiency_value, context)
            
            return {
                "success": True,
                "message": f"Efficiency feedback processed for {component_type.value}",
                "value": efficiency_value
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @router.post("/feedback/accuracy")
    async def submit_accuracy_feedback(
        component_type: ComponentTypeAPI,
        accuracy_value: float = Field(..., ge=0.0, le=1.0),
        context: Dict[str, Any] = {}
    ):
        """Convenience endpoint for accuracy feedback."""
        try:
            component = _convert_component_type(component_type)
            await process_accuracy_feedback(component, accuracy_value, context)
            
            return {
                "success": True,
                "message": f"Accuracy feedback processed for {component_type.value}",
                "value": accuracy_value
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @router.post("/feedback/constitutional")
    async def submit_constitutional_feedback(
        compliance_score: float = Field(..., ge=0.0, le=1.0),
        context: Dict[str, Any] = {}
    ):
        """Convenience endpoint for constitutional compliance feedback."""
        try:
            await process_constitutional_feedback(compliance_score, context)
            
            return {
                "success": True,
                "message": "Constitutional compliance feedback processed",
                "compliance_score": compliance_score
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    return router


# Helper functions

def _convert_component_type(api_type: ComponentTypeAPI) -> WINAComponentType:
    """Convert API component type to internal enum."""
    conversion_map = {
        ComponentTypeAPI.NEURON_ACTIVATION: WINAComponentType.NEURON_ACTIVATION,
        ComponentTypeAPI.SVD_TRANSFORMATION: WINAComponentType.SVD_TRANSFORMATION,
        ComponentTypeAPI.DYNAMIC_GATING: WINAComponentType.DYNAMIC_GATING,
        ComponentTypeAPI.CONSTITUTIONAL_VERIFICATION: WINAComponentType.CONSTITUTIONAL_VERIFICATION,
        ComponentTypeAPI.EC_OVERSIGHT: WINAComponentType.EC_OVERSIGHT,
        ComponentTypeAPI.INTEGRATION_MONITORING: WINAComponentType.INTEGRATION_MONITORING
    }
    return conversion_map[api_type]


def _convert_feedback_type(api_type: FeedbackTypeAPI) -> FeedbackType:
    """Convert API feedback type to internal enum."""
    conversion_map = {
        FeedbackTypeAPI.PERFORMANCE_METRIC: FeedbackType.PERFORMANCE_METRIC,
        FeedbackTypeAPI.ACCURACY_RETENTION: FeedbackType.ACCURACY_RETENTION,
        FeedbackTypeAPI.EFFICIENCY_GAIN: FeedbackType.EFFICIENCY_GAIN,
        FeedbackTypeAPI.CONSTITUTIONAL_COMPLIANCE: FeedbackType.CONSTITUTIONAL_COMPLIANCE,
        FeedbackTypeAPI.USER_FEEDBACK: FeedbackType.USER_FEEDBACK,
        FeedbackTypeAPI.SYSTEM_ERROR: FeedbackType.SYSTEM_ERROR,
        FeedbackTypeAPI.OPTIMIZATION_SUCCESS: FeedbackType.OPTIMIZATION_SUCCESS
    }
    return conversion_map[api_type]


# Integration function for external services
async def integrate_with_performance_monitoring(performance_collector: WINAPerformanceCollector):
    """Integrate learning system with performance monitoring."""
    try:
        learning_system = await get_wina_learning_system()
        learning_system.set_performance_collector(performance_collector)
        logger.info("Learning system integrated with performance monitoring")
    except Exception as e:
        logger.error(f"Failed to integrate with performance monitoring: {e}")
        raise