from fastapi import APIRouter, Depends, HTTPException
from src.backend.gs_service.app.core.llm_reliability_framework import EnhancedLLMReliabilityFramework, ReliabilityMetrics
from typing import Dict, Any

router = APIRouter()

# In a real application, you would likely have a singleton instance
# of the framework or inject it via dependency injection.
# For simplicity, we'll create an instance here.
# This assumes the framework is initialized elsewhere or can be initialized on demand.
llm_reliability_framework_instance = EnhancedLLMReliabilityFramework()

@router.get("/reliability_metrics", response_model=Dict[str, Any])
async def get_reliability_metrics():
    """
    Retrieves the current reliability metrics from the LLM Reliability Framework.
    """
    try:
        summary = llm_reliability_framework_instance.get_performance_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve reliability metrics: {e}")

@router.get("/reliability_metrics/history", response_model=Dict[str, Any])
async def get_reliability_metrics_history():
    """
    Retrieves the historical reliability metrics from the LLM Reliability Framework.
    """
    try:
        # Assuming performance_metrics stores a list of ReliabilityMetrics objects
        # We need to convert these dataclasses to dictionaries for JSON serialization
        history_data = [metric.__dict__ for metric in llm_reliability_framework_instance.performance_metrics]
        return {"history": history_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve historical reliability metrics: {e}")