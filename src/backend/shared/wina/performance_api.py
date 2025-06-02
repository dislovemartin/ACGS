"""
WINA Performance Monitoring API

This module provides REST API endpoints for WINA performance monitoring,
metrics retrieval, health checks, and system configuration.

Key Features:
- Real-time metrics API endpoints
- Performance report generation
- Health check and status endpoints
- Prometheus metrics export
- Configuration management API
- Alert and notification endpoints
"""

import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
from dataclasses import asdict
from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from fastapi.responses import PlainTextResponse, JSONResponse
from pydantic import BaseModel, Field

from .performance_monitoring import (
    WINAPerformanceCollector,
    WINAMonitoringLevel,
    WINAComponentType,
    WINANeuronActivationMetrics,
    WINASVDTransformationMetrics,
    WINADynamicGatingMetrics,
    WINAConstitutionalComplianceMetrics,
    WINALearningFeedbackMetrics,
    WINAIntegrationMetrics,
    WINASystemHealthMetrics,
    get_wina_performance_collector
)
from .exceptions import WINAMetricsError

logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses

class MetricsTimeRangeRequest(BaseModel):
    """Request model for time-range based metrics queries."""
    start_time: Optional[datetime] = Field(None, description="Start time for metrics query")
    end_time: Optional[datetime] = Field(None, description="End time for metrics query")
    component_types: Optional[List[str]] = Field(None, description="Filter by component types")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PerformanceReportRequest(BaseModel):
    """Request model for performance report generation."""
    start_time: Optional[datetime] = Field(None, description="Report start time")
    end_time: Optional[datetime] = Field(None, description="Report end time")
    include_trends: bool = Field(True, description="Include trend analysis")
    include_recommendations: bool = Field(True, description="Include recommendations")


class NeuronActivationMetricsRequest(BaseModel):
    """Request model for recording neuron activation metrics."""
    layer_name: str
    total_neurons: int
    active_neurons: int
    deactivated_neurons: int
    activation_ratio: float = Field(..., ge=0.0, le=1.0)
    activation_scores_mean: float
    activation_scores_std: float
    performance_impact_ms: float
    energy_savings_ratio: float = Field(..., ge=0.0, le=1.0)


class SVDTransformationMetricsRequest(BaseModel):
    """Request model for recording SVD transformation metrics."""
    layer_name: str
    original_rank: int = Field(..., gt=0)
    reduced_rank: int = Field(..., gt=0)
    rank_reduction_ratio: float = Field(..., ge=0.0, le=1.0)
    svd_computation_time_ms: float = Field(..., ge=0.0)
    reconstruction_error: float = Field(..., ge=0.0)
    compression_ratio: float = Field(..., ge=0.0, le=1.0)
    memory_savings_mb: float = Field(..., ge=0.0)


class DynamicGatingMetricsRequest(BaseModel):
    """Request model for recording dynamic gating metrics."""
    gate_id: str
    gating_strategy: str
    threshold_value: float
    gates_activated: int = Field(..., ge=0)
    gates_total: int = Field(..., gt=0)
    gating_efficiency: float = Field(..., ge=0.0, le=1.0)
    decision_latency_ms: float = Field(..., ge=0.0)
    accuracy_impact: float
    resource_savings: float = Field(..., ge=0.0)


class ConstitutionalComplianceMetricsRequest(BaseModel):
    """Request model for recording constitutional compliance metrics."""
    component_type: str
    principles_evaluated: int = Field(..., ge=0)
    compliance_score: float = Field(..., ge=0.0, le=1.0)
    violations_detected: int = Field(..., ge=0)
    compliance_check_time_ms: float = Field(..., ge=0.0)
    constitutional_overhead_ratio: float = Field(..., ge=0.0)
    principle_adherence_breakdown: Dict[str, float]
    remediation_actions_taken: int = Field(..., ge=0)


class LearningFeedbackMetricsRequest(BaseModel):
    """Request model for recording learning feedback metrics."""
    feedback_source: str
    adaptation_type: str
    learning_accuracy: float = Field(..., ge=0.0, le=1.0)
    adaptation_effectiveness: float = Field(..., ge=0.0, le=1.0)
    feedback_processing_time_ms: float = Field(..., ge=0.0)
    model_update_size_mb: float = Field(..., ge=0.0)
    convergence_rate: float = Field(..., ge=0.0)
    feedback_quality_score: float = Field(..., ge=0.0, le=1.0)


class IntegrationMetricsRequest(BaseModel):
    """Request model for recording integration metrics."""
    integration_type: str
    source_component: str
    target_component: str
    integration_latency_ms: float = Field(..., ge=0.0)
    data_transfer_mb: float = Field(..., ge=0.0)
    synchronization_overhead_ms: float = Field(..., ge=0.0)
    integration_success_rate: float = Field(..., ge=0.0, le=1.0)
    error_count: int = Field(..., ge=0)
    performance_improvement_ratio: float


class SystemHealthMetricsRequest(BaseModel):
    """Request model for recording system health metrics."""
    cpu_utilization_percent: float = Field(..., ge=0.0, le=100.0)
    memory_utilization_percent: float = Field(..., ge=0.0, le=100.0)
    gpu_utilization_percent: float = Field(..., ge=0.0, le=100.0)
    throughput_ops_per_second: float = Field(..., ge=0.0)
    error_rate_percent: float = Field(..., ge=0.0, le=100.0)
    availability_percent: float = Field(..., ge=0.0, le=100.0)
    response_time_p95_ms: float = Field(..., ge=0.0)
    concurrent_operations: int = Field(..., ge=0)


class MonitoringConfigurationRequest(BaseModel):
    """Request model for monitoring configuration updates."""
    monitoring_level: str = Field(..., description="Monitoring level: basic, detailed, comprehensive, debug")
    collection_interval_seconds: Optional[int] = Field(None, ge=1, le=3600)
    enable_prometheus: Optional[bool] = None
    enable_real_time_alerts: Optional[bool] = None
    alert_thresholds: Optional[Dict[str, float]] = None


# Router for WINA performance monitoring API
router = APIRouter(prefix="/wina/performance", tags=["WINA Performance Monitoring"])


# Global reference to performance collector getter function
_collector_getter = None

def set_collector_getter(getter_func):
    """Set the function to get the performance collector."""
    global _collector_getter
    _collector_getter = getter_func

async def get_performance_collector() -> WINAPerformanceCollector:
    """Dependency to get the performance collector instance."""
    try:
        if _collector_getter is None:
            raise HTTPException(
                status_code=503,
                detail="Performance monitoring not initialized"
            )
        
        collector = _collector_getter()
        if collector is None:
            raise HTTPException(
                status_code=503,
                detail="Performance collector not available"
            )
        
        return collector
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get performance collector: {e}")
        raise HTTPException(status_code=500, detail="Performance monitoring service unavailable")


@router.get("/health")
async def get_health_status(collector: WINAPerformanceCollector = Depends(get_performance_collector)) -> Dict[str, Any]:
    """
    Get WINA performance monitoring system health status.
    
    Returns current system health, monitoring status, and key performance indicators.
    """
    try:
        real_time_metrics = await collector.get_real_time_metrics()
        
        system_health = real_time_metrics.get("system_health", {})
        overall_performance = real_time_metrics.get("overall_performance", {})
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "monitoring_active": collector.monitoring_active,
            "monitoring_level": collector.monitoring_level.value,
            "system_health": system_health,
            "performance_summary": {
                "gflops_reduction_achieved": overall_performance.get("gflops_reduction_achieved", 0.0),
                "accuracy_retention": overall_performance.get("accuracy_retention", 0.95),
                "constitutional_compliance_rate": overall_performance.get("constitutional_compliance_rate", 0.95),
                "performance_targets_met": overall_performance.get("performance_targets_met", False),
                "optimization_status": overall_performance.get("optimization_status", "unknown")
            },
            "components_monitored": len([comp for comp in WINAComponentType]),
            "recent_alerts": len([alert for alert in collector.alerts_history if 
                                datetime.now(timezone.utc) - alert["timestamp"] < timedelta(hours=1)])
        }
        
        # Determine overall status
        if system_health.get("status") == "critical":
            health_status["status"] = "critical"
        elif system_health.get("status") == "degraded" or not overall_performance.get("performance_targets_met", False):
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health status check failed: {str(e)}")


@router.get("/metrics/realtime")
async def get_realtime_metrics(collector: WINAPerformanceCollector = Depends(get_performance_collector)) -> Dict[str, Any]:
    """
    Get real-time WINA performance metrics.
    
    Returns current performance metrics across all WINA components.
    """
    try:
        return await collector.get_real_time_metrics()
        
    except Exception as e:
        logger.error(f"Real-time metrics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Real-time metrics retrieval failed: {str(e)}")


@router.get("/metrics/summary")
async def get_metrics_summary(
    time_range_hours: int = Query(24, ge=1, le=168, description="Time range in hours for metrics summary"),
    component_type: Optional[str] = Query(None, description="Filter by component type"),
    collector: WINAPerformanceCollector = Depends(get_performance_collector)
) -> Dict[str, Any]:
    """
    Get summarized WINA performance metrics for a specified time range.
    
    Args:
        time_range_hours: Time range in hours (default: 24, max: 168)
        component_type: Optional component type filter
        
    Returns:
        Summarized performance metrics
    """
    try:
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=time_range_hours)
        
        # Get performance report for the time range
        report = await collector.get_performance_report(start_time, end_time)
        
        summary = {
            "time_range": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_hours": time_range_hours
            },
            "overall_performance": {
                "gflops_reduction": report.overall_gflops_reduction,
                "accuracy_retention": report.overall_accuracy_retention,
                "constitutional_compliance_rate": report.constitutional_compliance_rate,
                "total_operations": report.total_operations,
                "performance_targets_met": report.performance_targets_met
            },
            "component_metrics": report.component_metrics if not component_type else 
                                {component_type: report.component_metrics.get(component_type, {})},
            "integration_metrics": report.integration_metrics,
            "health_metrics": report.health_metrics,
            "alerts_count": len(report.alerts_triggered),
            "trends": report.trends
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"Metrics summary retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics summary retrieval failed: {str(e)}")


@router.post("/report/generate")
async def generate_performance_report(
    request: PerformanceReportRequest,
    background_tasks: BackgroundTasks,
    collector: WINAPerformanceCollector = Depends(get_performance_collector)
) -> Dict[str, Any]:
    """
    Generate comprehensive WINA performance report.
    
    Args:
        request: Performance report configuration
        
    Returns:
        Comprehensive performance report
    """
    try:
        report = await collector.get_performance_report(
            start_time=request.start_time,
            end_time=request.end_time
        )
        
        # Convert report to dictionary for JSON serialization
        report_dict = asdict(report)
        
        # Convert datetime objects to ISO strings
        def convert_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: convert_datetime(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_datetime(item) for item in obj]
            elif isinstance(obj, tuple):
                return tuple(convert_datetime(item) for item in obj)
            return obj
        
        report_dict = convert_datetime(report_dict)
        
        return {
            "report": report_dict,
            "generation_timestamp": datetime.now(timezone.utc).isoformat(),
            "report_size": len(json.dumps(report_dict)),
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Performance report generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Performance report generation failed: {str(e)}")


@router.get("/prometheus")
async def get_prometheus_metrics(collector: WINAPerformanceCollector = Depends(get_performance_collector)) -> PlainTextResponse:
    """
    Get Prometheus metrics in exposition format.
    
    Returns:
        Prometheus metrics in text format
    """
    try:
        metrics_text = collector.get_prometheus_metrics()
        return PlainTextResponse(content=metrics_text, media_type="text/plain")
        
    except Exception as e:
        logger.error(f"Prometheus metrics export failed: {e}")
        raise HTTPException(status_code=500, detail=f"Prometheus metrics export failed: {str(e)}")


@router.get("/alerts")
async def get_recent_alerts(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back for alerts"),
    severity: Optional[str] = Query(None, description="Filter by alert severity"),
    collector: WINAPerformanceCollector = Depends(get_performance_collector)
) -> Dict[str, Any]:
    """
    Get recent performance alerts.
    
    Args:
        hours: Hours to look back for alerts
        severity: Optional severity filter (warning, critical)
        
    Returns:
        Recent performance alerts
    """
    try:
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        recent_alerts = [
            alert for alert in collector.alerts_history
            if alert["timestamp"] >= cutoff_time
        ]
        
        if severity:
            recent_alerts = [
                alert for alert in recent_alerts
                if alert.get("severity") == severity
            ]
        
        # Convert datetime objects to ISO strings
        for alert in recent_alerts:
            alert["timestamp"] = alert["timestamp"].isoformat()
        
        return {
            "alerts": recent_alerts,
            "total_count": len(recent_alerts),
            "time_range": {
                "start_time": cutoff_time.isoformat(),
                "end_time": datetime.now(timezone.utc).isoformat(),
                "duration_hours": hours
            },
            "severity_filter": severity
        }
        
    except Exception as e:
        logger.error(f"Alerts retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Alerts retrieval failed: {str(e)}")


# Metrics recording endpoints

@router.post("/metrics/neuron-activation")
async def record_neuron_activation_metrics(
    request: NeuronActivationMetricsRequest,
    collector: WINAPerformanceCollector = Depends(get_performance_collector)
) -> Dict[str, str]:
    """Record neuron activation metrics."""
    try:
        metrics = WINANeuronActivationMetrics(
            layer_name=request.layer_name,
            total_neurons=request.total_neurons,
            active_neurons=request.active_neurons,
            deactivated_neurons=request.deactivated_neurons,
            activation_ratio=request.activation_ratio,
            activation_scores_mean=request.activation_scores_mean,
            activation_scores_std=request.activation_scores_std,
            performance_impact_ms=request.performance_impact_ms,
            energy_savings_ratio=request.energy_savings_ratio,
            timestamp=datetime.now(timezone.utc)
        )
        
        await collector.record_neuron_activation_metrics(metrics)
        
        return {"status": "success", "message": f"Neuron activation metrics recorded for layer {request.layer_name}"}
        
    except Exception as e:
        logger.error(f"Neuron activation metrics recording failed: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics recording failed: {str(e)}")


@router.post("/metrics/svd-transformation")
async def record_svd_transformation_metrics(
    request: SVDTransformationMetricsRequest,
    collector: WINAPerformanceCollector = Depends(get_performance_collector)
) -> Dict[str, str]:
    """Record SVD transformation metrics."""
    try:
        metrics = WINASVDTransformationMetrics(
            layer_name=request.layer_name,
            original_rank=request.original_rank,
            reduced_rank=request.reduced_rank,
            rank_reduction_ratio=request.rank_reduction_ratio,
            svd_computation_time_ms=request.svd_computation_time_ms,
            reconstruction_error=request.reconstruction_error,
            compression_ratio=request.compression_ratio,
            memory_savings_mb=request.memory_savings_mb,
            timestamp=datetime.now(timezone.utc)
        )
        
        await collector.record_svd_transformation_metrics(metrics)
        
        return {"status": "success", "message": f"SVD transformation metrics recorded for layer {request.layer_name}"}
        
    except Exception as e:
        logger.error(f"SVD transformation metrics recording failed: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics recording failed: {str(e)}")


@router.post("/metrics/dynamic-gating")
async def record_dynamic_gating_metrics(
    request: DynamicGatingMetricsRequest,
    collector: WINAPerformanceCollector = Depends(get_performance_collector)
) -> Dict[str, str]:
    """Record dynamic gating metrics."""
    try:
        metrics = WINADynamicGatingMetrics(
            gate_id=request.gate_id,
            gating_strategy=request.gating_strategy,
            threshold_value=request.threshold_value,
            gates_activated=request.gates_activated,
            gates_total=request.gates_total,
            gating_efficiency=request.gating_efficiency,
            decision_latency_ms=request.decision_latency_ms,
            accuracy_impact=request.accuracy_impact,
            resource_savings=request.resource_savings,
            timestamp=datetime.now(timezone.utc)
        )
        
        await collector.record_dynamic_gating_metrics(metrics)
        
        return {"status": "success", "message": f"Dynamic gating metrics recorded for gate {request.gate_id}"}
        
    except Exception as e:
        logger.error(f"Dynamic gating metrics recording failed: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics recording failed: {str(e)}")


@router.post("/metrics/constitutional-compliance")
async def record_constitutional_compliance_metrics(
    request: ConstitutionalComplianceMetricsRequest,
    collector: WINAPerformanceCollector = Depends(get_performance_collector)
) -> Dict[str, str]:
    """Record constitutional compliance metrics."""
    try:
        metrics = WINAConstitutionalComplianceMetrics(
            component_type=request.component_type,
            principles_evaluated=request.principles_evaluated,
            compliance_score=request.compliance_score,
            violations_detected=request.violations_detected,
            compliance_check_time_ms=request.compliance_check_time_ms,
            constitutional_overhead_ratio=request.constitutional_overhead_ratio,
            principle_adherence_breakdown=request.principle_adherence_breakdown,
            remediation_actions_taken=request.remediation_actions_taken,
            timestamp=datetime.now(timezone.utc)
        )
        
        await collector.record_constitutional_compliance_metrics(metrics)
        
        return {"status": "success", "message": f"Constitutional compliance metrics recorded for {request.component_type}"}
        
    except Exception as e:
        logger.error(f"Constitutional compliance metrics recording failed: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics recording failed: {str(e)}")


@router.post("/metrics/learning-feedback")
async def record_learning_feedback_metrics(
    request: LearningFeedbackMetricsRequest,
    collector: WINAPerformanceCollector = Depends(get_performance_collector)
) -> Dict[str, str]:
    """Record learning feedback metrics."""
    try:
        metrics = WINALearningFeedbackMetrics(
            feedback_source=request.feedback_source,
            adaptation_type=request.adaptation_type,
            learning_accuracy=request.learning_accuracy,
            adaptation_effectiveness=request.adaptation_effectiveness,
            feedback_processing_time_ms=request.feedback_processing_time_ms,
            model_update_size_mb=request.model_update_size_mb,
            convergence_rate=request.convergence_rate,
            feedback_quality_score=request.feedback_quality_score,
            timestamp=datetime.now(timezone.utc)
        )
        
        await collector.record_learning_feedback_metrics(metrics)
        
        return {"status": "success", "message": f"Learning feedback metrics recorded from {request.feedback_source}"}
        
    except Exception as e:
        logger.error(f"Learning feedback metrics recording failed: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics recording failed: {str(e)}")


@router.post("/metrics/integration")
async def record_integration_metrics(
    request: IntegrationMetricsRequest,
    collector: WINAPerformanceCollector = Depends(get_performance_collector)
) -> Dict[str, str]:
    """Record component integration metrics."""
    try:
        metrics = WINAIntegrationMetrics(
            integration_type=request.integration_type,
            source_component=request.source_component,
            target_component=request.target_component,
            integration_latency_ms=request.integration_latency_ms,
            data_transfer_mb=request.data_transfer_mb,
            synchronization_overhead_ms=request.synchronization_overhead_ms,
            integration_success_rate=request.integration_success_rate,
            error_count=request.error_count,
            performance_improvement_ratio=request.performance_improvement_ratio,
            timestamp=datetime.now(timezone.utc)
        )
        
        await collector.record_integration_metrics(metrics)
        
        return {"status": "success", "message": f"Integration metrics recorded: {request.source_component} -> {request.target_component}"}
        
    except Exception as e:
        logger.error(f"Integration metrics recording failed: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics recording failed: {str(e)}")


@router.post("/metrics/system-health")
async def record_system_health_metrics(
    request: SystemHealthMetricsRequest,
    collector: WINAPerformanceCollector = Depends(get_performance_collector)
) -> Dict[str, str]:
    """Record system health metrics."""
    try:
        metrics = WINASystemHealthMetrics(
            cpu_utilization_percent=request.cpu_utilization_percent,
            memory_utilization_percent=request.memory_utilization_percent,
            gpu_utilization_percent=request.gpu_utilization_percent,
            throughput_ops_per_second=request.throughput_ops_per_second,
            error_rate_percent=request.error_rate_percent,
            availability_percent=request.availability_percent,
            response_time_p95_ms=request.response_time_p95_ms,
            concurrent_operations=request.concurrent_operations,
            timestamp=datetime.now(timezone.utc)
        )
        
        await collector.record_system_health_metrics(metrics)
        
        return {"status": "success", "message": "System health metrics recorded"}
        
    except Exception as e:
        logger.error(f"System health metrics recording failed: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics recording failed: {str(e)}")


# Configuration endpoints

@router.get("/config")
async def get_monitoring_configuration(collector: WINAPerformanceCollector = Depends(get_performance_collector)) -> Dict[str, Any]:
    """Get current monitoring configuration."""
    try:
        return {
            "monitoring_level": collector.monitoring_level.value,
            "monitoring_active": collector.monitoring_active,
            "collection_interval_seconds": collector.collection_interval,
            "prometheus_available": hasattr(collector, 'prometheus_metrics'),
            "components_monitored": [comp.value for comp in WINAComponentType],
            "metrics_storage_limits": {
                "neuron_activation_metrics": collector.neuron_activation_metrics.maxlen,
                "svd_transformation_metrics": collector.svd_transformation_metrics.maxlen,
                "dynamic_gating_metrics": collector.dynamic_gating_metrics.maxlen,
                "constitutional_compliance_metrics": collector.constitutional_compliance_metrics.maxlen,
                "learning_feedback_metrics": collector.learning_feedback_metrics.maxlen,
                "integration_metrics": collector.integration_metrics.maxlen,
                "system_health_metrics": collector.system_health_metrics.maxlen
            }
        }
        
    except Exception as e:
        logger.error(f"Configuration retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration retrieval failed: {str(e)}")


@router.post("/config")
async def update_monitoring_configuration(
    request: MonitoringConfigurationRequest,
    collector: WINAPerformanceCollector = Depends(get_performance_collector)
) -> Dict[str, str]:
    """Update monitoring configuration."""
    try:
        # Validate monitoring level
        try:
            new_level = WINAMonitoringLevel(request.monitoring_level)
            collector.monitoring_level = new_level
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid monitoring level: {request.monitoring_level}")
        
        # Update collection interval if provided
        if request.collection_interval_seconds is not None:
            collector.collection_interval = request.collection_interval_seconds
        
        logger.info(f"Monitoring configuration updated: level={new_level.value}, interval={collector.collection_interval}s")
        
        return {
            "status": "success",
            "message": f"Monitoring configuration updated to {new_level.value} level"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Configuration update failed: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration update failed: {str(e)}")


@router.post("/monitoring/start")
async def start_monitoring(collector: WINAPerformanceCollector = Depends(get_performance_collector)) -> Dict[str, str]:
    """Start performance monitoring."""
    try:
        await collector.start_monitoring()
        return {"status": "success", "message": "Performance monitoring started"}
        
    except Exception as e:
        logger.error(f"Monitoring start failed: {e}")
        raise HTTPException(status_code=500, detail=f"Monitoring start failed: {str(e)}")


@router.post("/monitoring/stop")
async def stop_monitoring(collector: WINAPerformanceCollector = Depends(get_performance_collector)) -> Dict[str, str]:
    """Stop performance monitoring."""
    try:
        await collector.stop_monitoring()
        return {"status": "success", "message": "Performance monitoring stopped"}
        
    except Exception as e:
        logger.error(f"Monitoring stop failed: {e}")
        raise HTTPException(status_code=500, detail=f"Monitoring stop failed: {str(e)}")


# Add the router to the main API
def get_wina_performance_router() -> APIRouter:
    """Get the WINA performance monitoring API router."""
    return router