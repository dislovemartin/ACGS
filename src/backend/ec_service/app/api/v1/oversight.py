"""
WINA EC Layer Oversight API

Provides endpoints for WINA-optimized oversight coordination of evolutionary
computation systems with constitutional compliance verification.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field

from src.backend.ec_service.app.core.wina_oversight_coordinator import (
    WINAECOversightCoordinator,
    ECOversightRequest,
    WINAOversightResult,
    ECOversightContext,
    ECOversightStrategy
)
from src.backend.ec_service.app.services.ac_client import ac_service_client
from src.backend.ec_service.app.services.gs_client import gs_service_client
from src.backend.ec_service.app.services.pgc_client import pgc_service_client

logger = logging.getLogger(__name__)
router = APIRouter()


class OversightRequestModel(BaseModel):
    """Request model for EC oversight operations."""
    target_system: str = Field(..., description="Target EC system identifier")
    context: ECOversightContext = Field(..., description="Oversight context")
    requirements: List[str] = Field(..., description="Oversight requirements")
    optimization_objective: Optional[str] = Field(None, description="Optimization objective")
    constitutional_constraints: List[str] = Field(default_factory=list, description="Constitutional constraints")
    priority_level: str = Field(default="medium", description="Priority level")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class OversightResponseModel(BaseModel):
    """Response model for EC oversight operations."""
    oversight_id: str = Field(..., description="Unique oversight operation ID")
    decision: str = Field(..., description="Oversight decision")
    rationale: str = Field(..., description="Decision rationale")
    confidence_score: float = Field(..., description="Confidence score")
    constitutional_compliance: bool = Field(..., description="Constitutional compliance status")
    wina_optimization_applied: bool = Field(..., description="Whether WINA optimization was applied")
    governance_recommendations: List[str] = Field(..., description="Governance recommendations")
    performance_metrics: Dict[str, Any] = Field(..., description="Performance metrics")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    timestamp: str = Field(..., description="Operation timestamp")


class BatchOversightRequestModel(BaseModel):
    """Request model for batch EC oversight operations."""
    requests: List[OversightRequestModel] = Field(..., description="List of oversight requests")
    batch_context: Optional[str] = Field(None, description="Batch processing context")
    optimization_hints: Optional[Dict[str, Any]] = Field(None, description="WINA optimization hints")


class BatchOversightResponseModel(BaseModel):
    """Response model for batch EC oversight operations."""
    batch_id: str = Field(..., description="Unique batch operation ID")
    results: List[OversightResponseModel] = Field(..., description="Individual oversight results")
    batch_summary: Dict[str, Any] = Field(..., description="Batch processing summary")
    total_processing_time_ms: float = Field(..., description="Total processing time")
    success_rate: float = Field(..., description="Success rate")


def get_wina_coordinator() -> WINAECOversightCoordinator:
    """Dependency to get WINA oversight coordinator."""
    from src.backend.ec_service.app.main import get_wina_coordinator
    return get_wina_coordinator()


@router.post("/coordinate", response_model=OversightResponseModel)
async def coordinate_oversight(
    request: OversightRequestModel,
    background_tasks: BackgroundTasks,
    coordinator: WINAECOversightCoordinator = Depends(get_wina_coordinator)
):
    """
    Coordinate WINA-optimized EC layer oversight operation.
    
    This endpoint provides comprehensive oversight coordination including:
    - Constitutional compliance verification
    - WINA-informed strategy selection
    - Performance optimization
    - Governance recommendations
    """
    start_time = datetime.utcnow()
    oversight_id = str(uuid.uuid4())
    
    try:
        logger.info(f"Starting oversight coordination for {request.target_system}")
        
        # Create oversight request
        oversight_request = ECOversightRequest(
            target_system=request.target_system,
            context=request.context,
            requirements=request.requirements,
            optimization_objective=request.optimization_objective,
            constitutional_constraints=request.constitutional_constraints,
            priority_level=request.priority_level,
            metadata=request.metadata
        )
        
        # Coordinate oversight with WINA optimization
        result = await coordinator.coordinate_oversight(oversight_request)
        
        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Create response
        response = OversightResponseModel(
            oversight_id=oversight_id,
            decision=result.oversight_decision,
            rationale=result.decision_rationale,
            confidence_score=result.confidence_score,
            constitutional_compliance=result.constitutional_compliance,
            wina_optimization_applied=result.wina_optimization_applied,
            governance_recommendations=result.governance_recommendations,
            performance_metrics={
                "governance_efficiency_improvement": result.oversight_metrics.governance_efficiency_improvement,
                "constitutional_compliance_score": result.oversight_metrics.constitutional_compliance_score,
                "wina_optimization_score": result.oversight_metrics.wina_optimization_score,
                "strategy_selection_accuracy": result.oversight_metrics.strategy_selection_accuracy,
                "cache_hit_rate": result.oversight_metrics.cache_hit_rate,
                "learning_adaptation_rate": result.oversight_metrics.learning_adaptation_rate
            },
            processing_time_ms=processing_time,
            timestamp=start_time.isoformat()
        )
        
        # Background task: Report to AC service
        background_tasks.add_task(
            _report_oversight_activity,
            oversight_id,
            request.target_system,
            result
        )
        
        logger.info(f"Oversight coordination completed for {request.target_system} in {processing_time:.2f}ms")
        return response
        
    except Exception as e:
        logger.error(f"Oversight coordination failed: {e}")
        raise HTTPException(status_code=500, detail=f"Oversight coordination failed: {str(e)}")


@router.post("/batch-coordinate", response_model=BatchOversightResponseModel)
async def batch_coordinate_oversight(
    request: BatchOversightRequestModel,
    background_tasks: BackgroundTasks,
    coordinator: WINAECOversightCoordinator = Depends(get_wina_coordinator)
):
    """
    Coordinate batch WINA-optimized EC layer oversight operations.
    
    Efficiently processes multiple oversight requests with shared optimization
    and constitutional compliance verification.
    """
    start_time = datetime.utcnow()
    batch_id = str(uuid.uuid4())
    
    try:
        logger.info(f"Starting batch oversight coordination for {len(request.requests)} requests")
        
        results = []
        successful_operations = 0
        
        for req in request.requests:
            try:
                # Create individual oversight request
                oversight_request = ECOversightRequest(
                    target_system=req.target_system,
                    context=req.context,
                    requirements=req.requirements,
                    optimization_objective=req.optimization_objective,
                    constitutional_constraints=req.constitutional_constraints,
                    priority_level=req.priority_level,
                    metadata=req.metadata
                )
                
                # Coordinate oversight
                result = await coordinator.coordinate_oversight(
                    oversight_request, 
                    request.optimization_hints
                )
                
                # Create individual response
                individual_response = OversightResponseModel(
                    oversight_id=str(uuid.uuid4()),
                    decision=result.oversight_decision,
                    rationale=result.decision_rationale,
                    confidence_score=result.confidence_score,
                    constitutional_compliance=result.constitutional_compliance,
                    wina_optimization_applied=result.wina_optimization_applied,
                    governance_recommendations=result.governance_recommendations,
                    performance_metrics={
                        "governance_efficiency_improvement": result.oversight_metrics.governance_efficiency_improvement,
                        "constitutional_compliance_score": result.oversight_metrics.constitutional_compliance_score,
                        "wina_optimization_score": result.oversight_metrics.wina_optimization_score
                    },
                    processing_time_ms=0.0,  # Will be calculated in batch summary
                    timestamp=datetime.utcnow().isoformat()
                )
                
                results.append(individual_response)
                successful_operations += 1
                
            except Exception as e:
                logger.error(f"Individual oversight failed for {req.target_system}: {e}")
                # Continue with other requests
                
        # Calculate batch metrics
        total_processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        success_rate = successful_operations / len(request.requests) if request.requests else 0.0
        
        batch_summary = {
            "total_requests": len(request.requests),
            "successful_operations": successful_operations,
            "failed_operations": len(request.requests) - successful_operations,
            "average_confidence_score": sum(r.confidence_score for r in results) / len(results) if results else 0.0,
            "constitutional_compliance_rate": sum(1 for r in results if r.constitutional_compliance) / len(results) if results else 0.0,
            "wina_optimization_rate": sum(1 for r in results if r.wina_optimization_applied) / len(results) if results else 0.0
        }
        
        response = BatchOversightResponseModel(
            batch_id=batch_id,
            results=results,
            batch_summary=batch_summary,
            total_processing_time_ms=total_processing_time,
            success_rate=success_rate
        )
        
        logger.info(f"Batch oversight coordination completed: {successful_operations}/{len(request.requests)} successful")
        return response
        
    except Exception as e:
        logger.error(f"Batch oversight coordination failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch oversight coordination failed: {str(e)}")


async def _report_oversight_activity(
    oversight_id: str,
    target_system: str,
    result: WINAOversightResult
):
    """Background task to report oversight activity to AC service."""
    try:
        await ac_service_client.report_oversight_activity(
            activity_type="ec_oversight",
            details={
                "oversight_id": oversight_id,
                "target_system": target_system,
                "decision": result.oversight_decision,
                "constitutional_compliance": result.constitutional_compliance,
                "wina_optimization_applied": result.wina_optimization_applied
            },
            metrics={
                "governance_efficiency_improvement": result.oversight_metrics.governance_efficiency_improvement,
                "constitutional_compliance_score": result.oversight_metrics.constitutional_compliance_score,
                "wina_optimization_score": result.oversight_metrics.wina_optimization_score
            }
        )
        logger.debug(f"Reported oversight activity {oversight_id} to AC service")
    except Exception as e:
        logger.error(f"Failed to report oversight activity: {e}")


@router.get("/strategies")
async def get_oversight_strategies():
    """Get available EC oversight strategies."""
    return {
        "strategies": [
            {
                "name": strategy.value,
                "description": f"EC oversight strategy: {strategy.value.replace('_', ' ').title()}"
            }
            for strategy in ECOversightStrategy
        ]
    }


@router.get("/contexts")
async def get_oversight_contexts():
    """Get available EC oversight contexts."""
    return {
        "contexts": [
            {
                "name": context.value,
                "description": f"EC oversight context: {context.value.replace('_', ' ').title()}"
            }
            for context in ECOversightContext
        ]
    }


@router.get("/health")
async def oversight_health_check(
    coordinator: WINAECOversightCoordinator = Depends(get_wina_coordinator)
):
    """Health check for oversight coordination system."""
    try:
        # Perform basic health check
        health_status = {
            "status": "healthy",
            "wina_enabled": coordinator.enable_wina,
            "timestamp": datetime.utcnow().isoformat()
        }

        return health_status

    except Exception as e:
        logger.error(f"Oversight health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Oversight system unhealthy: {str(e)}")
