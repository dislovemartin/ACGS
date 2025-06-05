"""
API endpoints for Enhanced Multi-Model Validation System.

This module provides REST API endpoints for advanced multi-model validation,
boosting-based weighted majority vote, and cluster-based dynamic model selection.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.auth import get_current_user_id
from ...services.enhanced_multi_model_validation import (
    get_enhanced_multi_model_validator,
    ValidationStrategy,
    ModelCluster,
    ValidationContext,
    OptimizationLevel
)

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class ValidationRequest(BaseModel):
    """Request model for multi-model validation."""
    query: str = Field(..., description="Query for validation")
    query_type: str = Field(default="general", description="Type of query")
    complexity_score: float = Field(default=0.5, description="Query complexity (0-1)")
    constitutional_requirements: List[str] = Field(
        default_factory=list, 
        description="Constitutional requirements"
    )
    bias_sensitivity: float = Field(default=0.5, description="Bias sensitivity (0-1)")
    uncertainty_tolerance: float = Field(default=0.3, description="Uncertainty tolerance (0-1)")
    target_cluster: Optional[ModelCluster] = Field(
        default=None, 
        description="Target model cluster"
    )
    strategy: ValidationStrategy = Field(
        default=ValidationStrategy.HYBRID_ENSEMBLE,
        description="Validation strategy"
    )
    max_models: int = Field(default=5, description="Maximum models to use")


class ModelPerformanceUpdate(BaseModel):
    """Request model for updating model performance."""
    model_id: str = Field(..., description="Model identifier")
    performance_score: float = Field(..., description="Performance score (0-1)")
    cluster: ModelCluster = Field(..., description="Model cluster")


class EnsembleValidationResponse(BaseModel):
    """Response model for ensemble validation."""
    final_prediction: str
    confidence: float
    strategy_used: str
    model_contributions: List[Dict[str, Any]]
    uncertainty_quantification: Dict[str, float]
    constitutional_fidelity: float
    validation_time: float
    consensus_level: float
    operation_id: str


class ValidationMetricsResponse(BaseModel):
    """Response model for validation metrics."""
    total_validations: int
    recent_validations: int
    average_confidence: float
    average_constitutional_fidelity: float
    average_consensus_level: float
    average_validation_time: float
    strategy_usage_distribution: Dict[str, int]
    model_usage_statistics: Dict[str, int]
    reliability_target: str
    current_reliability: str
    timestamp: str


@router.post("/validate", response_model=EnsembleValidationResponse)
async def validate_with_ensemble(
    request: ValidationRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Perform multi-model validation using advanced ensemble techniques.
    
    This endpoint applies boosting-based weighted majority vote, cluster-based
    dynamic model selection, or hybrid ensemble validation strategies.
    """
    try:
        validator = get_enhanced_multi_model_validator()
        
        # Create validation context
        context = ValidationContext(
            query_type=request.query_type,
            complexity_score=request.complexity_score,
            constitutional_requirements=request.constitutional_requirements,
            bias_sensitivity=request.bias_sensitivity,
            uncertainty_tolerance=request.uncertainty_tolerance,
            target_cluster=request.target_cluster
        )
        
        # Perform ensemble validation
        result = await validator.validate_with_ensemble(
            query=request.query,
            context=context,
            strategy=request.strategy,
            max_models=request.max_models
        )
        
        # Convert model contributions to serializable format
        model_contributions = []
        for pred in result.model_contributions:
            model_contributions.append({
                "model_id": pred.model_id,
                "prediction": pred.prediction,
                "confidence": pred.confidence,
                "constitutional_compliance": pred.constitutional_compliance,
                "bias_score": pred.bias_score,
                "response_time": pred.response_time,
                "uncertainty_score": pred.uncertainty_score
            })
        
        return EnsembleValidationResponse(
            final_prediction=result.final_prediction,
            confidence=result.confidence,
            strategy_used=result.strategy_used.value,
            model_contributions=model_contributions,
            uncertainty_quantification=result.uncertainty_quantification,
            constitutional_fidelity=result.constitutional_fidelity,
            validation_time=result.validation_time,
            consensus_level=result.consensus_level,
            operation_id=str(hash(request.query))  # Simple operation ID
        )
        
    except Exception as e:
        logger.error(f"Error in ensemble validation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform ensemble validation: {str(e)}"
        )


@router.post("/update-performance")
async def update_model_performance(
    request: ModelPerformanceUpdate,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Update model performance for specific cluster.
    
    This endpoint allows updating the performance metrics for models
    in specific clusters to improve future model selection.
    """
    try:
        validator = get_enhanced_multi_model_validator()
        
        await validator.update_model_performance(
            model_id=request.model_id,
            performance_score=request.performance_score,
            cluster=request.cluster
        )
        
        return {
            "message": f"Updated performance for {request.model_id} in {request.cluster.value}",
            "model_id": request.model_id,
            "performance_score": request.performance_score,
            "cluster": request.cluster.value,
            "timestamp": "2024-01-01T00:00:00Z"  # Would use actual timestamp
        }
        
    except Exception as e:
        logger.error(f"Error updating model performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update model performance: {str(e)}"
        )


@router.get("/metrics", response_model=ValidationMetricsResponse)
async def get_validation_metrics(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive validation metrics.
    
    Returns detailed metrics on validation performance, model usage,
    strategy effectiveness, and reliability achievements.
    """
    try:
        validator = get_enhanced_multi_model_validator()
        
        metrics = validator.get_validation_metrics()
        
        return ValidationMetricsResponse(
            total_validations=metrics.get("total_validations", 0),
            recent_validations=metrics.get("recent_validations", 0),
            average_confidence=metrics.get("average_confidence", 0.0),
            average_constitutional_fidelity=metrics.get("average_constitutional_fidelity", 0.0),
            average_consensus_level=metrics.get("average_consensus_level", 0.0),
            average_validation_time=metrics.get("average_validation_time", 0.0),
            strategy_usage_distribution=metrics.get("strategy_usage_distribution", {}),
            model_usage_statistics=metrics.get("model_usage_statistics", {}),
            reliability_target=metrics.get("reliability_target", ">99.9%"),
            current_reliability=metrics.get("current_reliability", "0.00%"),
            timestamp=metrics.get("timestamp", "")
        )
        
    except Exception as e:
        logger.error(f"Error retrieving validation metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve validation metrics: {str(e)}"
        )


@router.get("/strategies")
async def list_validation_strategies(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """List available validation strategies and their descriptions."""
    try:
        strategies = {
            ValidationStrategy.BOOSTING_MAJORITY_VOTE.value: {
                "name": "Boosting-based Weighted Majority Vote",
                "description": "Dynamic weight assignment through boosting algorithms",
                "use_case": "Improved decision-making accuracy with adaptive weighting",
                "performance": "10-20% accuracy improvement over simple majority vote"
            },
            ValidationStrategy.CLUSTER_BASED_SELECTION.value: {
                "name": "Cluster-based Dynamic Model Selection",
                "description": "Context-aware routing based on query characteristics",
                "use_case": "Optimal model selection for specific query types",
                "performance": "Smaller models can outperform 14x larger models"
            },
            ValidationStrategy.UNCERTAINTY_WEIGHTED.value: {
                "name": "Uncertainty-weighted Validation",
                "description": "Weight predictions by inverse uncertainty scores",
                "use_case": "High-confidence decisions with uncertainty quantification",
                "performance": "Improved reliability through uncertainty awareness"
            },
            ValidationStrategy.CONSTITUTIONAL_PRIORITY.value: {
                "name": "Constitutional Priority Validation",
                "description": "Prioritize constitutional compliance in model selection",
                "use_case": "Governance decisions requiring constitutional adherence",
                "performance": "Enhanced constitutional fidelity scores"
            },
            ValidationStrategy.HYBRID_ENSEMBLE.value: {
                "name": "Hybrid Ensemble Validation",
                "description": "Combines multiple strategies for optimal performance",
                "use_case": "General-purpose validation with balanced performance",
                "performance": "Best overall performance across diverse scenarios"
            }
        }
        
        return {
            "message": "Available validation strategies",
            "strategies": strategies,
            "default_strategy": ValidationStrategy.HYBRID_ENSEMBLE.value,
            "recommendation": "Use HYBRID_ENSEMBLE for general purposes, specialized strategies for specific requirements"
        }
        
    except Exception as e:
        logger.error(f"Error listing validation strategies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list validation strategies: {str(e)}"
        )


@router.get("/clusters")
async def list_model_clusters(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """List available model clusters and their characteristics."""
    try:
        clusters = {
            ModelCluster.REASONING_HEAVY.value: {
                "name": "Reasoning Heavy",
                "description": "Complex logical reasoning and chain-of-thought",
                "optimal_models": ["gpt-4", "claude-3", "gemini-pro"],
                "use_cases": ["Constitutional analysis", "Complex policy decisions", "Legal reasoning"]
            },
            ModelCluster.CREATIVE_SYNTHESIS.value: {
                "name": "Creative Synthesis",
                "description": "Creative policy generation and innovative solutions",
                "optimal_models": ["claude-3", "gemini-pro", "gpt-4"],
                "use_cases": ["Policy drafting", "Creative problem solving", "Novel governance approaches"]
            },
            ModelCluster.FACTUAL_ANALYSIS.value: {
                "name": "Factual Analysis",
                "description": "Factual verification and data analysis",
                "optimal_models": ["gemini-pro", "llama-2", "mistral-7b"],
                "use_cases": ["Fact checking", "Data validation", "Compliance verification"]
            },
            ModelCluster.CONSTITUTIONAL_COMPLIANCE.value: {
                "name": "Constitutional Compliance",
                "description": "Constitutional principle analysis and compliance checking",
                "optimal_models": ["gpt-4", "claude-3"],
                "use_cases": ["Constitutional review", "Principle validation", "Rights assessment"]
            },
            ModelCluster.BIAS_DETECTION.value: {
                "name": "Bias Detection",
                "description": "Bias and fairness analysis across social dimensions",
                "optimal_models": ["claude-3", "gpt-4", "gemini-pro"],
                "use_cases": ["Bias assessment", "Fairness evaluation", "Discrimination detection"]
            }
        }
        
        return {
            "message": "Available model clusters",
            "clusters": clusters,
            "cluster_selection": "Automatic based on query characteristics or manual specification",
            "performance_note": "Cluster-based selection can achieve equivalent performance with smaller models"
        }
        
    except Exception as e:
        logger.error(f"Error listing model clusters: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list model clusters: {str(e)}"
        )
