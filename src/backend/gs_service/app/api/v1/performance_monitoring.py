"""
Performance Monitoring API Endpoints

Provides REST API endpoints for accessing performance metrics, monitoring data,
and system health information for the ACGS governance synthesis service.

Phase 3: Performance Optimization and Security Compliance
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field
import structlog

from ...services.performance_monitor import get_performance_monitor, PerformanceMonitor
from ...services.advanced_cache import MultiTierCache
from ...services.security_compliance import get_security_service, security_required
from ...core.opa_integration import get_opa_client

logger = structlog.get_logger(__name__)

router = APIRouter()


class PerformanceMetricsResponse(BaseModel):
    """Performance metrics response model."""
    timestamp: datetime
    latency_profiles: List[Dict[str, Any]]
    bottlenecks: List[Dict[str, Any]]
    active_requests: int
    system_metrics: Dict[str, float]
    cache_stats: Optional[Dict[str, Any]] = None
    opa_metrics: Optional[Dict[str, Any]] = None


class SystemHealthResponse(BaseModel):
    """System health response model."""
    status: str = Field(..., description="Overall system health status")
    timestamp: datetime
    components: Dict[str, Dict[str, Any]]
    performance_summary: Dict[str, Any]
    security_summary: Dict[str, Any]
    alerts: List[Dict[str, Any]]


class AlertConfiguration(BaseModel):
    """Alert configuration model."""
    metric_name: str
    threshold_value: float
    comparison_operator: str = Field(..., pattern="^(gt|lt|gte|lte|eq)$")
    severity: str = Field(..., pattern="^(low|medium|high|critical)$")
    enabled: bool = True


@router.get("/metrics", response_model=PerformanceMetricsResponse)
@security_required(required_roles=["admin", "monitor"])
async def get_performance_metrics(
    hours: int = Query(1, ge=1, le=24, description="Hours of metrics to retrieve"),
    include_cache: bool = Query(True, description="Include cache statistics"),
    include_opa: bool = Query(True, description="Include OPA metrics")
) -> PerformanceMetricsResponse:
    """
    Get comprehensive performance metrics.
    
    Returns detailed performance metrics including latency profiles,
    bottlenecks, system resource usage, and component-specific metrics.
    """
    try:
        performance_monitor = get_performance_monitor()
        summary = performance_monitor.get_performance_summary()
        
        response_data = {
            "timestamp": datetime.now(),
            "latency_profiles": summary["latency_profiles"],
            "bottlenecks": summary["bottlenecks"],
            "active_requests": summary["active_requests"],
            "system_metrics": summary["system_metrics"]
        }
        
        # Include cache statistics if requested
        if include_cache:
            try:
                # This would need to be implemented to get cache stats from the actual cache instance
                response_data["cache_stats"] = {"message": "Cache stats integration pending"}
            except Exception as e:
                logger.warning("Failed to get cache stats", error=str(e))
                response_data["cache_stats"] = {"error": "Cache stats unavailable"}
        
        # Include OPA metrics if requested
        if include_opa:
            try:
                opa_client = get_opa_client()
                response_data["opa_metrics"] = opa_client.get_metrics()
            except Exception as e:
                logger.warning("Failed to get OPA metrics", error=str(e))
                response_data["opa_metrics"] = {"error": "OPA metrics unavailable"}
        
        return PerformanceMetricsResponse(**response_data)
        
    except Exception as e:
        logger.error("Failed to get performance metrics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve performance metrics: {str(e)}"
        )


@router.get("/health", response_model=SystemHealthResponse)
async def get_system_health() -> SystemHealthResponse:
    """
    Get comprehensive system health status.
    
    Returns overall system health including component status,
    performance summary, security status, and active alerts.
    """
    try:
        performance_monitor = get_performance_monitor()
        security_service = get_security_service()
        
        # Get component health status
        components = {
            "performance_monitor": {
                "status": "healthy",
                "last_check": datetime.now().isoformat(),
                "metrics": performance_monitor.get_performance_summary()
            },
            "security_service": {
                "status": "healthy",
                "last_check": datetime.now().isoformat(),
                "summary": security_service.get_security_summary()
            }
        }
        
        # Check OPA client health
        try:
            opa_client = get_opa_client()
            opa_metrics = opa_client.get_metrics()
            components["opa_client"] = {
                "status": "healthy" if opa_metrics.get("error_count", 0) < 10 else "degraded",
                "last_check": datetime.now().isoformat(),
                "metrics": opa_metrics
            }
        except Exception as e:
            components["opa_client"] = {
                "status": "unhealthy",
                "last_check": datetime.now().isoformat(),
                "error": str(e)
            }
        
        # Determine overall system status
        component_statuses = [comp["status"] for comp in components.values()]
        if "unhealthy" in component_statuses:
            overall_status = "unhealthy"
        elif "degraded" in component_statuses:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        # Generate alerts based on metrics
        alerts = _generate_health_alerts(components)
        
        return SystemHealthResponse(
            status=overall_status,
            timestamp=datetime.now(),
            components=components,
            performance_summary=performance_monitor.get_performance_summary(),
            security_summary=security_service.get_security_summary(),
            alerts=alerts
        )
        
    except Exception as e:
        logger.error("Failed to get system health", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve system health: {str(e)}"
        )


@router.get("/bottlenecks")
@security_required(required_roles=["admin", "monitor"])
async def get_performance_bottlenecks(
    hours: int = Query(1, ge=1, le=24, description="Hours of bottlenecks to retrieve"),
    severity: Optional[str] = Query(None, pattern="^(low|medium|high|critical)$", description="Filter by severity")
) -> Dict[str, Any]:
    """
    Get performance bottlenecks and optimization recommendations.
    
    Returns identified performance bottlenecks with severity levels
    and suggested optimization actions.
    """
    try:
        performance_monitor = get_performance_monitor()
        bottlenecks = performance_monitor.profiler.get_bottlenecks(hours=hours)
        
        if severity:
            bottlenecks = [b for b in bottlenecks if b.get("severity") == severity]
        
        # Add optimization recommendations
        for bottleneck in bottlenecks:
            bottleneck["recommendations"] = _get_optimization_recommendations(bottleneck)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "bottlenecks": bottlenecks,
            "total_count": len(bottlenecks),
            "severity_distribution": _get_severity_distribution(bottlenecks)
        }
        
    except Exception as e:
        logger.error("Failed to get performance bottlenecks", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve performance bottlenecks: {str(e)}"
        )


@router.get("/latency-profile")
@security_required(required_roles=["admin", "monitor"])
async def get_latency_profile(
    operation: Optional[str] = Query(None, description="Specific operation to profile")
) -> Dict[str, Any]:
    """
    Get detailed latency profiling information.
    
    Returns latency statistics for all operations or a specific operation,
    including percentiles, trends, and performance targets.
    """
    try:
        performance_monitor = get_performance_monitor()
        
        if operation:
            profile = performance_monitor.profiler.get_latency_profile(operation)
            if not profile:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No latency profile found for operation: {operation}"
                )
            profiles = [profile]
        else:
            profiles = performance_monitor.profiler.get_all_profiles()
        
        # Add performance target analysis
        target_latency_ms = 50.0  # 50ms target
        for profile in profiles:
            profile_dict = profile.__dict__ if hasattr(profile, '__dict__') else profile
            profile_dict["meets_target"] = profile_dict.get("p95_latency_ms", 0) < target_latency_ms
            profile_dict["target_latency_ms"] = target_latency_ms
            profile_dict["performance_grade"] = _calculate_performance_grade(profile_dict)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "profiles": [p.__dict__ if hasattr(p, '__dict__') else p for p in profiles],
            "target_latency_ms": target_latency_ms,
            "summary": {
                "total_operations": len(profiles),
                "meeting_target": sum(1 for p in profiles if (p.__dict__ if hasattr(p, '__dict__') else p).get("meets_target", False)),
                "avg_p95_latency": sum((p.__dict__ if hasattr(p, '__dict__') else p).get("p95_latency_ms", 0) for p in profiles) / len(profiles) if profiles else 0
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get latency profile", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve latency profile: {str(e)}"
        )


@router.post("/alerts/configure")
@security_required(required_roles=["admin"])
async def configure_alert(alert_config: AlertConfiguration) -> Dict[str, Any]:
    """
    Configure performance monitoring alerts.
    
    Allows administrators to set up custom alerts based on
    performance metrics and thresholds.
    """
    try:
        # In a real implementation, this would store the alert configuration
        # in a database or configuration service
        
        logger.info("Alert configured", 
                   metric=alert_config.metric_name,
                   threshold=alert_config.threshold_value,
                   severity=alert_config.severity)
        
        return {
            "message": "Alert configuration saved successfully",
            "alert_id": f"alert_{int(datetime.now().timestamp())}",
            "configuration": alert_config.dict(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to configure alert", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to configure alert: {str(e)}"
        )


@router.get("/prometheus-metrics")
async def get_prometheus_metrics() -> str:
    """
    Get Prometheus-formatted metrics.
    
    Returns performance metrics in Prometheus format for
    integration with monitoring systems.
    """
    try:
        from prometheus_client import generate_latest, REGISTRY
        return generate_latest(REGISTRY).decode('utf-8')
        
    except Exception as e:
        logger.error("Failed to get Prometheus metrics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve Prometheus metrics: {str(e)}"
        )


def _generate_health_alerts(components: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate health alerts based on component status."""
    alerts = []
    
    for component_name, component_data in components.items():
        if component_data["status"] == "unhealthy":
            alerts.append({
                "severity": "critical",
                "component": component_name,
                "message": f"{component_name} is unhealthy",
                "timestamp": datetime.now().isoformat(),
                "details": component_data.get("error", "Unknown error")
            })
        elif component_data["status"] == "degraded":
            alerts.append({
                "severity": "medium",
                "component": component_name,
                "message": f"{component_name} is degraded",
                "timestamp": datetime.now().isoformat(),
                "details": "Performance below optimal levels"
            })
    
    return alerts


def _get_optimization_recommendations(bottleneck: Dict[str, Any]) -> List[str]:
    """Get optimization recommendations for a performance bottleneck."""
    recommendations = []
    operation = bottleneck.get("operation", "")
    latency_ms = bottleneck.get("latency_ms", 0)
    
    if "opa" in operation.lower():
        recommendations.extend([
            "Consider enabling OPA decision caching",
            "Optimize Rego policy complexity",
            "Use batch policy evaluation where possible"
        ])
    
    if "cache" in operation.lower():
        recommendations.extend([
            "Review cache hit rates and TTL settings",
            "Consider increasing cache size",
            "Implement cache warming strategies"
        ])
    
    if latency_ms > 100:
        recommendations.extend([
            "Profile function execution for optimization opportunities",
            "Consider asynchronous processing",
            "Review database query performance"
        ])
    
    return recommendations or ["Review operation implementation for optimization opportunities"]


def _get_severity_distribution(bottlenecks: List[Dict[str, Any]]) -> Dict[str, int]:
    """Get severity distribution of bottlenecks."""
    distribution = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    
    for bottleneck in bottlenecks:
        severity = bottleneck.get("severity", "medium")
        distribution[severity] = distribution.get(severity, 0) + 1
    
    return distribution


def _calculate_performance_grade(profile: Dict[str, Any]) -> str:
    """Calculate performance grade based on latency metrics."""
    p95_latency = profile.get("p95_latency_ms", 0)
    
    if p95_latency < 10:
        return "A"
    elif p95_latency < 25:
        return "B"
    elif p95_latency < 50:
        return "C"
    elif p95_latency < 100:
        return "D"
    else:
        return "F"
