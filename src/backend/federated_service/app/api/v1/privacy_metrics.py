"""
Privacy Metrics API Endpoints

REST API endpoints for managing differential privacy,
privacy budget, and privacy metrics monitoring.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, List, Optional, Any
import logging

from shared.auth import get_current_user_from_token, get_current_active_user
from ...core.privacy_metrics import differential_privacy_manager, PrivacyMechanism
from ...schemas import PrivacyMetricsResponse, ErrorResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/budget")
async def get_privacy_budget(
    current_user: dict = Depends(get_current_active_user)
):
    """Get current privacy budget status."""
    try:
        metrics = await differential_privacy_manager.get_privacy_metrics()
        return metrics["privacy_budget"]
        
    except Exception as e:
        logger.error(f"Failed to get privacy budget: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get privacy budget: {str(e)}"
        )


@router.post("/budget/reset")
async def reset_privacy_budget(
    new_epsilon: Optional[float] = Query(None, ge=0.1, le=10.0),
    new_delta: Optional[float] = Query(None, ge=0.0, le=1.0),
    current_user: dict = Depends(get_current_active_user)
):
    """Reset privacy budget (admin only)."""
    try:
        # Check user permissions (admin only)
        if current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can reset privacy budget"
            )
        
        await differential_privacy_manager.reset_privacy_budget(new_epsilon, new_delta)
        
        return {
            "message": "Privacy budget reset successfully",
            "new_epsilon": new_epsilon or differential_privacy_manager.privacy_budget.epsilon,
            "new_delta": new_delta or differential_privacy_manager.privacy_budget.delta
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset privacy budget: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset privacy budget: {str(e)}"
        )


@router.get("/metrics", response_model=PrivacyMetricsResponse)
async def get_privacy_metrics(
    current_user: dict = Depends(get_current_active_user)
):
    """Get comprehensive privacy metrics."""
    try:
        metrics = await differential_privacy_manager.get_privacy_metrics()
        return PrivacyMetricsResponse(**metrics)
        
    except Exception as e:
        logger.error(f"Failed to get privacy metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get privacy metrics: {str(e)}"
        )


@router.post("/estimate-cost")
async def estimate_privacy_cost(
    query_type: str = Query(..., description="Type of query (aggregation, statistical, ml_training)"),
    data_size: int = Query(..., ge=1, description="Size of data to be processed"),
    current_user: dict = Depends(get_current_active_user)
):
    """Estimate privacy cost for a given query."""
    try:
        estimated_cost = await differential_privacy_manager.estimate_privacy_cost(
            query_type, data_size
        )
        
        remaining_budget = differential_privacy_manager.privacy_budget.remaining_epsilon
        
        return {
            "estimated_epsilon_cost": estimated_cost,
            "remaining_epsilon_budget": remaining_budget,
            "can_afford": estimated_cost <= remaining_budget,
            "query_type": query_type,
            "data_size": data_size,
            "cost_factors": {
                "base_cost": 0.1,
                "query_type_multiplier": {
                    "aggregation": 1.0,
                    "statistical": 1.5,
                    "ml_training": 2.0
                }.get(query_type, 1.0),
                "data_size_factor": min(2.0, 1.0 + (data_size / 1000.0))
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to estimate privacy cost: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to estimate privacy cost: {str(e)}"
        )


@router.post("/validate-requirements")
async def validate_privacy_requirements(
    requirements: Dict[str, Any],
    current_user: dict = Depends(get_current_active_user)
):
    """Validate privacy requirements against current budget."""
    try:
        is_valid = await differential_privacy_manager.validate_privacy_requirements(requirements)
        
        return {
            "is_valid": is_valid,
            "requirements": requirements,
            "current_budget": {
                "epsilon_remaining": differential_privacy_manager.privacy_budget.remaining_epsilon,
                "delta_remaining": differential_privacy_manager.privacy_budget.remaining_delta
            },
            "validation_details": {
                "epsilon_sufficient": requirements.get("epsilon", 0.1) <= differential_privacy_manager.privacy_budget.remaining_epsilon,
                "delta_sufficient": requirements.get("delta", 0.0) <= differential_privacy_manager.privacy_budget.remaining_delta,
                "mechanism_valid": requirements.get("mechanism", "laplace") in [m.value for m in PrivacyMechanism]
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to validate privacy requirements: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate requirements: {str(e)}"
        )


@router.get("/mechanisms")
async def list_privacy_mechanisms():
    """List available privacy mechanisms."""
    return {
        "mechanisms": [
            {
                "name": "laplace",
                "display_name": "Laplace Mechanism",
                "description": "Classic differential privacy with Laplace noise",
                "suitable_for": ["numerical_queries", "counting_queries"],
                "privacy_guarantee": "epsilon-DP"
            },
            {
                "name": "gaussian",
                "display_name": "Gaussian Mechanism",
                "description": "Differential privacy with Gaussian noise",
                "suitable_for": ["numerical_queries", "machine_learning"],
                "privacy_guarantee": "(epsilon, delta)-DP"
            },
            {
                "name": "exponential",
                "display_name": "Exponential Mechanism",
                "description": "Selection mechanism for non-numerical outputs",
                "suitable_for": ["selection_queries", "optimization"],
                "privacy_guarantee": "epsilon-DP"
            },
            {
                "name": "local_dp",
                "display_name": "Local Differential Privacy",
                "description": "Privacy at the individual data level",
                "suitable_for": ["distributed_data", "untrusted_aggregator"],
                "privacy_guarantee": "local epsilon-DP"
            }
        ]
    }


@router.get("/history")
async def get_privacy_history(
    limit: int = Query(10, ge=1, le=100, description="Number of recent entries to return"),
    current_user: dict = Depends(get_current_active_user)
):
    """Get privacy application history."""
    try:
        metrics = await differential_privacy_manager.get_privacy_metrics()
        history = metrics.get("recent_history", [])
        
        # Limit results
        limited_history = history[-limit:] if len(history) > limit else history
        
        return {
            "history": limited_history,
            "total_entries": len(differential_privacy_manager.privacy_history),
            "returned_entries": len(limited_history),
            "summary": {
                "total_queries": metrics["metrics"]["total_queries"],
                "average_noise_added": metrics["metrics"]["average_noise_added"],
                "data_utility_score": metrics["metrics"]["data_utility_score"],
                "privacy_violations": metrics["metrics"]["privacy_violations"]
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get privacy history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get privacy history: {str(e)}"
        )


@router.get("/status")
async def get_privacy_status(
    current_user: dict = Depends(get_current_active_user)
):
    """Get the status of the privacy system."""
    try:
        metrics = await differential_privacy_manager.get_privacy_metrics()
        
        budget = metrics["privacy_budget"]
        system_metrics = metrics["metrics"]
        
        return {
            "status": "operational",
            "privacy_budget_health": {
                "epsilon_utilization": budget["epsilon_used"] / budget["epsilon_total"] if budget["epsilon_total"] > 0 else 0,
                "delta_utilization": budget["delta_used"] / budget["delta_total"] if budget["delta_total"] > 0 else 0,
                "budget_exhausted": budget["epsilon_remaining"] <= 0,
                "budget_critical": budget["epsilon_remaining"] < 0.1
            },
            "system_performance": {
                "total_queries_processed": system_metrics["total_queries"],
                "average_data_utility": system_metrics["data_utility_score"],
                "privacy_violations_detected": system_metrics["privacy_violations"],
                "average_noise_level": system_metrics["average_noise_added"]
            },
            "recommendations": {
                "budget_management": "Monitor epsilon usage carefully" if budget["epsilon_remaining"] < 0.5 else "Budget usage is healthy",
                "mechanism_selection": "Consider using Gaussian mechanism for better utility" if system_metrics["data_utility_score"] < 0.7 else "Current mechanism selection is optimal"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get privacy status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get privacy status: {str(e)}"
        )
