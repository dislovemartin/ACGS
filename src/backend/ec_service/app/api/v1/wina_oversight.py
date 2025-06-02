"""
WINA-Optimized EC Layer Oversight API Endpoints

This module provides REST API endpoints for accessing WINA-optimized
Executive Council (EC) Layer oversight functionality, including:
- Oversight request coordination and processing
- Comprehensive oversight reporting and analytics
- Constitutional compliance verification
- WINA optimization metrics and insights
- Learning feedback and adaptive strategy management

Endpoints follow FastAPI patterns and include comprehensive error handling,
request validation, and response formatting.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

# EC service imports
from ...core.wina_oversight_coordinator import (
    WINAECOversightCoordinator,
    ECOversightRequest,
    ECOversightContext,
    ECOversightStrategy,
    WINAOversightResult,
    ECOversightReport,
    get_wina_ec_oversight_coordinator
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/wina-oversight", tags=["WINA EC Oversight"])


# Pydantic models for API requests/responses

class OversightRequestModel(BaseModel):
    """API model for EC oversight requests."""
    request_id: str = Field(..., description="Unique identifier for the oversight request")
    oversight_type: str = Field(..., description="Type of oversight operation")
    target_system: str = Field(..., description="System being overseen")
    governance_requirements: List[str] = Field(default_factory=list, description="Governance requirements to evaluate")
    constitutional_constraints: List[str] = Field(default_factory=list, description="Constitutional constraints to enforce")
    performance_thresholds: Dict[str, float] = Field(default_factory=dict, description="Performance thresholds to meet")
    priority_level: str = Field(default="normal", description="Priority level: normal, high, critical")
    wina_optimization_enabled: bool = Field(default=True, description="Whether to enable WINA optimization")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator('oversight_type')
    @classmethod
    def validate_oversight_type(cls, v):
        valid_types = [context.value for context in ECOversightContext]
        if v not in valid_types:
            raise ValueError(f"Invalid oversight_type. Must be one of: {valid_types}")
        return v

    @field_validator('priority_level')
    @classmethod
    def validate_priority_level(cls, v):
        valid_priorities = ["normal", "high", "critical"]
        if v not in valid_priorities:
            raise ValueError(f"Invalid priority_level. Must be one of: {valid_priorities}")
        return v


class OversightStrategySelection(BaseModel):
    """API model for oversight strategy selection requests."""
    request_data: OversightRequestModel
    optimization_hints: Optional[Dict[str, Any]] = Field(default=None, description="Optional optimization hints")


class ReportingPeriodModel(BaseModel):
    """API model for reporting period specification."""
    start_time: Optional[datetime] = Field(default=None, description="Start time for reporting period")
    end_time: Optional[datetime] = Field(default=None, description="End time for reporting period")
    
    @field_validator('end_time')
    @classmethod
    def validate_end_time(cls, v, info):
        if (v and hasattr(info, 'data') and 'start_time' in info.data and
            info.data['start_time'] and v <= info.data['start_time']):
            raise ValueError("end_time must be after start_time")
        return v


class OversightMetricsResponse(BaseModel):
    """API response model for oversight metrics."""
    oversight_time_ms: float
    strategy_used: str
    wina_optimization_applied: bool
    constitutional_compliance_score: float
    governance_efficiency_improvement: float
    accuracy_retention: float
    gflops_reduction_achieved: float
    cache_hit_rate: float
    total_principles_evaluated: int
    optimization_decisions_made: int
    constitutional_violations_detected: int
    oversight_accuracy: float
    feedback_loop_updates: int
    learning_adaptations_applied: int


class OversightResultResponse(BaseModel):
    """API response model for oversight operation results."""
    oversight_decision: str
    decision_rationale: str
    confidence_score: float
    oversight_metrics: OversightMetricsResponse
    constitutional_compliance: bool
    wina_optimization_applied: bool
    governance_recommendations: List[str]
    constitutional_updates_suggested: List[Dict[str, Any]]
    performance_insights: Dict[str, Any]
    warnings: List[str]
    errors: List[str]
    wina_insights: Dict[str, Any]
    feedback_data: Dict[str, Any]


# API Dependencies

async def get_oversight_coordinator() -> WINAECOversightCoordinator:
    """Dependency to get the WINA EC oversight coordinator."""
    try:
        return await get_wina_ec_oversight_coordinator()
    except Exception as e:
        logger.error(f"Failed to get oversight coordinator: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Oversight coordinator not available: {str(e)}"
        )


# API Endpoints

@router.post("/coordinate", response_model=OversightResultResponse)
async def coordinate_oversight(
    request_data: OversightRequestModel,
    optimization_hints: Optional[Dict[str, Any]] = Body(default=None),
    coordinator: WINAECOversightCoordinator = Depends(get_oversight_coordinator)
) -> OversightResultResponse:
    """
    Coordinate a WINA-optimized EC Layer oversight operation.
    
    This endpoint processes oversight requests with constitutional compliance
    verification, WINA optimization, and comprehensive performance tracking.
    """
    try:
        logger.info(f"Processing oversight request: {request_data.request_id}")
        
        # Convert API model to internal request format
        oversight_request = ECOversightRequest(
            request_id=request_data.request_id,
            oversight_type=ECOversightContext(request_data.oversight_type),
            target_system=request_data.target_system,
            governance_requirements=request_data.governance_requirements,
            constitutional_constraints=request_data.constitutional_constraints,
            performance_thresholds=request_data.performance_thresholds,
            priority_level=request_data.priority_level,
            wina_optimization_enabled=request_data.wina_optimization_enabled,
            metadata=request_data.metadata
        )
        
        # Execute oversight coordination
        result = await coordinator.coordinate_oversight(oversight_request, optimization_hints)
        
        # Convert result to API response format
        response = OversightResultResponse(
            oversight_decision=result.oversight_decision,
            decision_rationale=result.decision_rationale,
            confidence_score=result.confidence_score,
            oversight_metrics=OversightMetricsResponse(
                oversight_time_ms=result.oversight_metrics.oversight_time_ms,
                strategy_used=result.oversight_metrics.strategy_used.value,
                wina_optimization_applied=result.oversight_metrics.wina_optimization_applied,
                constitutional_compliance_score=result.oversight_metrics.constitutional_compliance_score,
                governance_efficiency_improvement=result.oversight_metrics.governance_efficiency_improvement,
                accuracy_retention=result.oversight_metrics.accuracy_retention,
                gflops_reduction_achieved=result.oversight_metrics.gflops_reduction_achieved,
                cache_hit_rate=result.oversight_metrics.cache_hit_rate,
                total_principles_evaluated=result.oversight_metrics.total_principles_evaluated,
                optimization_decisions_made=result.oversight_metrics.optimization_decisions_made,
                constitutional_violations_detected=result.oversight_metrics.constitutional_violations_detected,
                oversight_accuracy=result.oversight_metrics.oversight_accuracy,
                feedback_loop_updates=result.oversight_metrics.feedback_loop_updates,
                learning_adaptations_applied=result.oversight_metrics.learning_adaptations_applied
            ),
            constitutional_compliance=result.constitutional_compliance,
            wina_optimization_applied=result.wina_optimization_applied,
            governance_recommendations=result.governance_recommendations,
            constitutional_updates_suggested=result.constitutional_updates_suggested,
            performance_insights=result.performance_insights,
            warnings=result.warnings,
            errors=result.errors,
            wina_insights=result.wina_insights,
            feedback_data=result.feedback_data
        )
        
        logger.info(f"Oversight coordination completed: {result.oversight_decision}")
        return response
        
    except ValueError as e:
        logger.warning(f"Invalid oversight request: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")
    except Exception as e:
        logger.error(f"Oversight coordination failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Oversight coordination failed: {str(e)}"
        )


@router.post("/select-strategy")
async def select_oversight_strategy(
    strategy_request: OversightStrategySelection,
    coordinator: WINAECOversightCoordinator = Depends(get_oversight_coordinator)
) -> Dict[str, Any]:
    """
    Select optimal oversight strategy based on WINA insights and request context.
    
    This endpoint analyzes oversight requests and recommends the most appropriate
    strategy based on WINA optimization potential and constitutional requirements.
    """
    try:
        logger.info(f"Selecting strategy for request: {strategy_request.request_data.request_id}")
        
        # Convert API model to internal format
        oversight_request = ECOversightRequest(
            request_id=strategy_request.request_data.request_id,
            oversight_type=ECOversightContext(strategy_request.request_data.oversight_type),
            target_system=strategy_request.request_data.target_system,
            governance_requirements=strategy_request.request_data.governance_requirements,
            constitutional_constraints=strategy_request.request_data.constitutional_constraints,
            performance_thresholds=strategy_request.request_data.performance_thresholds,
            priority_level=strategy_request.request_data.priority_level,
            wina_optimization_enabled=strategy_request.request_data.wina_optimization_enabled,
            metadata=strategy_request.request_data.metadata
        )
        
        # Select strategy using coordinator's internal method
        strategy = await coordinator._select_oversight_strategy(
            oversight_request, 
            strategy_request.optimization_hints
        )
        
        # Get WINA insights for the selected strategy
        wina_insights = await coordinator._get_wina_strategy_insights(oversight_request)
        
        return {
            "selected_strategy": strategy.value,
            "strategy_rationale": f"Selected based on context: {oversight_request.oversight_type.value}",
            "wina_insights": wina_insights,
            "optimization_potential": wina_insights.get("optimization_potential", 0.0),
            "constitutional_risk": wina_insights.get("constitutional_risk", 0.0),
            "efficiency_benefit": wina_insights.get("efficiency_benefit", 0.0),
            "learning_adaptation_recommended": wina_insights.get("learning_adaptation_recommended", False)
        }
        
    except ValueError as e:
        logger.warning(f"Invalid strategy selection request: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")
    except Exception as e:
        logger.error(f"Strategy selection failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Strategy selection failed: {str(e)}"
        )


@router.post("/generate-report")
async def generate_comprehensive_report(
    reporting_period: Optional[ReportingPeriodModel] = Body(default=None),
    coordinator: WINAECOversightCoordinator = Depends(get_oversight_coordinator)
) -> Dict[str, Any]:
    """
    Generate a comprehensive EC Layer oversight report.
    
    This endpoint creates detailed reports including WINA optimization analytics,
    constitutional compliance summaries, performance improvements, and recommendations.
    """
    try:
        logger.info("Generating comprehensive oversight report")
        
        # Convert reporting period if provided
        period_tuple = None
        if reporting_period and reporting_period.start_time and reporting_period.end_time:
            period_tuple = (reporting_period.start_time, reporting_period.end_time)
        
        # Generate report
        report = await coordinator.generate_comprehensive_report(period_tuple)
        
        # Convert report to API response format
        return {
            "report_id": report.report_id,
            "reporting_period": {
                "start_time": report.reporting_period[0].isoformat(),
                "end_time": report.reporting_period[1].isoformat()
            },
            "oversight_operations_count": report.oversight_operations_count,
            "wina_optimization_summary": report.wina_optimization_summary,
            "constitutional_compliance_summary": report.constitutional_compliance_summary,
            "performance_improvements": report.performance_improvements,
            "governance_decisions": report.governance_decisions,
            "constitutional_updates_proposed": [
                {
                    "principle": getattr(update, 'principle', 'unknown'),
                    "rationale": getattr(update, 'rationale', 'no rationale provided'),
                    "priority": getattr(update, 'priority', 'medium')
                } 
                for update in report.constitutional_updates_proposed
            ],
            "learning_adaptations": report.learning_adaptations,
            "system_health_indicators": report.system_health_indicators,
            "recommendations": report.recommendations,
            "issues_identified": report.issues_identified,
            "timestamp": report.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Report generation failed: {str(e)}"
        )


@router.get("/strategies")
async def get_available_strategies() -> Dict[str, Any]:
    """
    Get available oversight strategies and their descriptions.
    
    This endpoint returns information about all available oversight strategies
    and their appropriate use cases.
    """
    try:
        strategies = {}
        
        for strategy in ECOversightStrategy:
            strategy_info = {
                "name": strategy.value,
                "description": _get_strategy_description(strategy),
                "use_cases": _get_strategy_use_cases(strategy),
                "wina_optimization": strategy != ECOversightStrategy.STANDARD
            }
            strategies[strategy.value] = strategy_info
        
        return {
            "available_strategies": strategies,
            "default_strategy": ECOversightStrategy.WINA_OPTIMIZED.value,
            "total_strategies": len(ECOversightStrategy)
        }
        
    except Exception as e:
        logger.error(f"Strategy information retrieval failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Strategy information retrieval failed: {str(e)}"
        )


@router.get("/contexts")
async def get_oversight_contexts() -> Dict[str, Any]:
    """
    Get available oversight contexts and their descriptions.
    
    This endpoint returns information about all available oversight contexts
    and their characteristics.
    """
    try:
        contexts = {}
        
        for context in ECOversightContext:
            context_info = {
                "name": context.value,
                "description": _get_context_description(context),
                "typical_strategies": _get_context_typical_strategies(context),
                "optimization_potential": _get_context_optimization_potential(context)
            }
            contexts[context.value] = context_info
        
        return {
            "available_contexts": contexts,
            "total_contexts": len(ECOversightContext)
        }
        
    except Exception as e:
        logger.error(f"Context information retrieval failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Context information retrieval failed: {str(e)}"
        )


@router.get("/health")
async def get_oversight_health(
    coordinator: WINAECOversightCoordinator = Depends(get_oversight_coordinator)
) -> Dict[str, Any]:
    """
    Get oversight system health status and performance metrics.
    
    This endpoint provides real-time health information about the WINA EC
    oversight system including performance metrics and system status.
    """
    try:
        # Get recent operations for health analysis
        recent_operations = coordinator._oversight_history[-100:] if coordinator._oversight_history else []
        
        # Calculate health metrics
        health_metrics = {
            "system_status": "healthy",
            "wina_enabled": coordinator.enable_wina,
            "recent_operations_count": len(recent_operations),
            "cache_size": {
                "oversight_cache": len(coordinator._oversight_cache),
                "compliance_cache": len(coordinator._constitutional_compliance_cache)
            },
            "learning_feedback_contexts": len(coordinator._learning_feedback),
            "governance_decisions_logged": len(coordinator._governance_decisions_log),
            "reports_generated": len(coordinator._oversight_reports)
        }
        
        # Calculate performance metrics from recent operations
        if recent_operations:
            avg_time = sum(op.oversight_metrics.oversight_time_ms for op in recent_operations) / len(recent_operations)
            avg_confidence = sum(op.confidence_score for op in recent_operations) / len(recent_operations)
            compliance_rate = sum(1 for op in recent_operations if op.constitutional_compliance) / len(recent_operations)
            wina_adoption = sum(1 for op in recent_operations if op.wina_optimization_applied) / len(recent_operations)
            
            health_metrics.update({
                "performance_metrics": {
                    "avg_oversight_time_ms": avg_time,
                    "avg_confidence_score": avg_confidence,
                    "constitutional_compliance_rate": compliance_rate,
                    "wina_adoption_rate": wina_adoption
                }
            })
        
        # Determine overall health status
        if coordinator.enable_wina and len(recent_operations) > 0:
            if health_metrics.get("performance_metrics", {}).get("constitutional_compliance_rate", 0) > 0.9:
                health_metrics["system_status"] = "excellent"
            elif health_metrics.get("performance_metrics", {}).get("avg_confidence_score", 0) > 0.7:
                health_metrics["system_status"] = "good"
            else:
                health_metrics["system_status"] = "degraded"
        
        return health_metrics
        
    except Exception as e:
        logger.error(f"Health status retrieval failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Health status retrieval failed: {str(e)}"
        )


# Helper functions for endpoint responses

def _get_strategy_description(strategy: ECOversightStrategy) -> str:
    """Get description for an oversight strategy."""
    descriptions = {
        ECOversightStrategy.STANDARD: "Standard oversight procedures without WINA optimization",
        ECOversightStrategy.WINA_OPTIMIZED: "WINA-optimized oversight with efficiency improvements",
        ECOversightStrategy.CONSTITUTIONAL_PRIORITY: "Constitutional compliance prioritized oversight",
        ECOversightStrategy.EFFICIENCY_FOCUSED: "Efficiency-focused oversight with performance optimization",
        ECOversightStrategy.ADAPTIVE_LEARNING: "Learning-based adaptive oversight strategy",
        ECOversightStrategy.EMERGENCY_PROTOCOL: "Emergency response protocol for critical situations"
    }
    return descriptions.get(strategy, "Unknown strategy")


def _get_strategy_use_cases(strategy: ECOversightStrategy) -> List[str]:
    """Get use cases for an oversight strategy."""
    use_cases = {
        ECOversightStrategy.STANDARD: ["Fallback operations", "WINA unavailable"],
        ECOversightStrategy.WINA_OPTIMIZED: ["General oversight", "Performance improvement"],
        ECOversightStrategy.CONSTITUTIONAL_PRIORITY: ["High compliance risk", "Constitutional review"],
        ECOversightStrategy.EFFICIENCY_FOCUSED: ["Performance optimization", "Resource constraints"],
        ECOversightStrategy.ADAPTIVE_LEARNING: ["Continuous improvement", "Pattern recognition"],
        ECOversightStrategy.EMERGENCY_PROTOCOL: ["Incident response", "Critical situations"]
    }
    return use_cases.get(strategy, [])


def _get_context_description(context: ECOversightContext) -> str:
    """Get description for an oversight context."""
    descriptions = {
        ECOversightContext.ROUTINE_MONITORING: "Regular system monitoring and oversight",
        ECOversightContext.CONSTITUTIONAL_REVIEW: "Constitutional compliance review and verification",
        ECOversightContext.PERFORMANCE_OPTIMIZATION: "System performance optimization oversight",
        ECOversightContext.INCIDENT_RESPONSE: "Emergency incident response oversight",
        ECOversightContext.COMPLIANCE_AUDIT: "Compliance audit and verification",
        ECOversightContext.SYSTEM_ADAPTATION: "System adaptation and learning oversight"
    }
    return descriptions.get(context, "Unknown context")


def _get_context_typical_strategies(context: ECOversightContext) -> List[str]:
    """Get typical strategies for an oversight context."""
    typical_strategies = {
        ECOversightContext.ROUTINE_MONITORING: ["wina_optimized", "standard"],
        ECOversightContext.CONSTITUTIONAL_REVIEW: ["constitutional_priority", "wina_optimized"],
        ECOversightContext.PERFORMANCE_OPTIMIZATION: ["efficiency_focused", "wina_optimized"],
        ECOversightContext.INCIDENT_RESPONSE: ["emergency_protocol", "constitutional_priority"],
        ECOversightContext.COMPLIANCE_AUDIT: ["constitutional_priority", "wina_optimized"],
        ECOversightContext.SYSTEM_ADAPTATION: ["adaptive_learning", "wina_optimized"]
    }
    return typical_strategies.get(context, [])


def _get_context_optimization_potential(context: ECOversightContext) -> float:
    """Get optimization potential for an oversight context."""
    optimization_potential = {
        ECOversightContext.ROUTINE_MONITORING: 0.4,
        ECOversightContext.CONSTITUTIONAL_REVIEW: 0.8,
        ECOversightContext.PERFORMANCE_OPTIMIZATION: 0.9,
        ECOversightContext.INCIDENT_RESPONSE: 0.3,
        ECOversightContext.COMPLIANCE_AUDIT: 0.7,
        ECOversightContext.SYSTEM_ADAPTATION: 0.8
    }
    return optimization_potential.get(context, 0.5)