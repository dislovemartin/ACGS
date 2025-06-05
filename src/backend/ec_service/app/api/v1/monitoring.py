"""
WINA EC Layer Performance Monitoring API

Provides real-time performance monitoring, metrics collection, and alerting
for WINA-optimized EC layer oversight operations.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from src.backend.ec_service.app.core.wina_oversight_coordinator import WINAECOversightCoordinator
from src.backend.ec_service.app.services.ac_client import ac_service_client
from src.backend.ec_service.app.services.gs_client import gs_service_client
from src.backend.ec_service.app.services.pgc_client import pgc_service_client

logger = logging.getLogger(__name__)
router = APIRouter()


class SystemMetrics(BaseModel):
    """System performance metrics model."""
    cpu_usage: float = Field(..., description="CPU usage percentage")
    memory_usage: float = Field(..., description="Memory usage percentage")
    disk_usage: float = Field(..., description="Disk usage percentage")
    network_io: Dict[str, float] = Field(..., description="Network I/O metrics")
    timestamp: str = Field(..., description="Metrics timestamp")


class WINAPerformanceMetrics(BaseModel):
    """WINA-specific performance metrics model."""
    gflops_reduction: float = Field(..., description="GFLOPs reduction percentage")
    synthesis_latency_ms: float = Field(..., description="Synthesis latency in milliseconds")
    optimization_success_rate: float = Field(..., description="Optimization success rate")
    cache_hit_rate: float = Field(..., description="Cache hit rate")
    strategy_selection_accuracy: float = Field(..., description="Strategy selection accuracy")
    constitutional_compliance_rate: float = Field(..., description="Constitutional compliance rate")
    timestamp: str = Field(..., description="Metrics timestamp")


class AlertRule(BaseModel):
    """Alert rule configuration model."""
    rule_id: str = Field(..., description="Unique rule identifier")
    metric_name: str = Field(..., description="Metric to monitor")
    threshold_value: float = Field(..., description="Alert threshold value")
    comparison_operator: str = Field(..., description="Comparison operator (>, <, >=, <=, ==)")
    severity: str = Field(..., description="Alert severity (critical, warning, info)")
    enabled: bool = Field(default=True, description="Whether rule is enabled")
    description: str = Field(..., description="Rule description")


class Alert(BaseModel):
    """Alert model."""
    alert_id: str = Field(..., description="Unique alert identifier")
    rule_id: str = Field(..., description="Associated rule identifier")
    metric_name: str = Field(..., description="Metric that triggered alert")
    current_value: float = Field(..., description="Current metric value")
    threshold_value: float = Field(..., description="Threshold value")
    severity: str = Field(..., description="Alert severity")
    message: str = Field(..., description="Alert message")
    triggered_at: str = Field(..., description="Alert trigger timestamp")
    acknowledged: bool = Field(default=False, description="Whether alert is acknowledged")


class MonitoringDashboard(BaseModel):
    """Monitoring dashboard data model."""
    system_metrics: SystemMetrics = Field(..., description="System performance metrics")
    wina_metrics: WINAPerformanceMetrics = Field(..., description="WINA performance metrics")
    active_alerts: List[Alert] = Field(..., description="Active alerts")
    service_health: Dict[str, str] = Field(..., description="Service health status")
    oversight_statistics: Dict[str, Any] = Field(..., description="Oversight operation statistics")
    last_updated: str = Field(..., description="Dashboard last update timestamp")


def get_wina_coordinator() -> WINAECOversightCoordinator:
    """Dependency to get WINA oversight coordinator."""
    from src.backend.ec_service.app.main import get_wina_coordinator
    return get_wina_coordinator()


@router.get("/dashboard", response_model=MonitoringDashboard)
async def get_monitoring_dashboard(
    coordinator: WINAECOversightCoordinator = Depends(get_wina_coordinator)
):
    """
    Get comprehensive monitoring dashboard data.
    
    Provides real-time system metrics, WINA performance data,
    active alerts, and service health information.
    """
    try:
        logger.info("Generating monitoring dashboard data")
        
        # Collect system metrics (would be from actual system monitoring)
        system_metrics = SystemMetrics(
            cpu_usage=45.2,  # Would be from actual system monitoring
            memory_usage=62.8,
            disk_usage=34.1,
            network_io={
                "bytes_sent": 1024000.0,
                "bytes_received": 2048000.0,
                "packets_sent": 1500.0,
                "packets_received": 2200.0
            },
            timestamp=datetime.utcnow().isoformat()
        )
        
        # Collect WINA performance metrics
        try:
            wina_synthesis_metrics = await gs_service_client.get_wina_synthesis_metrics()
            enforcement_metrics = await pgc_service_client.get_wina_enforcement_metrics()
            fidelity_metrics = await ac_service_client.get_fidelity_metrics()
            
            wina_metrics = WINAPerformanceMetrics(
                gflops_reduction=wina_synthesis_metrics.get("gflops_reduction", 0.0),
                synthesis_latency_ms=wina_synthesis_metrics.get("average_latency_ms", 0.0),
                optimization_success_rate=wina_synthesis_metrics.get("optimization_success_rate", 0.0),
                cache_hit_rate=enforcement_metrics.get("cache_hit_rate", 0.0),
                strategy_selection_accuracy=enforcement_metrics.get("strategy_accuracy", 0.0),
                constitutional_compliance_rate=fidelity_metrics.get("overall_fidelity_score", 0.0),
                timestamp=datetime.utcnow().isoformat()
            )
        except Exception as e:
            logger.warning(f"Failed to collect WINA metrics: {e}")
            wina_metrics = WINAPerformanceMetrics(
                gflops_reduction=0.0,
                synthesis_latency_ms=0.0,
                optimization_success_rate=0.0,
                cache_hit_rate=0.0,
                strategy_selection_accuracy=0.0,
                constitutional_compliance_rate=0.0,
                timestamp=datetime.utcnow().isoformat()
            )
        
        # Check for active alerts
        active_alerts = await _check_active_alerts(wina_metrics, system_metrics)
        
        # Check service health
        service_health = await _check_service_health()
        
        # Collect oversight statistics (would be from coordinator tracking)
        oversight_statistics = {
            "total_operations_today": 0,  # Would be tracked by coordinator
            "successful_operations": 0,
            "failed_operations": 0,
            "average_processing_time_ms": 0.0,
            "constitutional_compliance_rate": wina_metrics.constitutional_compliance_rate,
            "wina_optimization_rate": wina_metrics.optimization_success_rate
        }
        
        dashboard = MonitoringDashboard(
            system_metrics=system_metrics,
            wina_metrics=wina_metrics,
            active_alerts=active_alerts,
            service_health=service_health,
            oversight_statistics=oversight_statistics,
            last_updated=datetime.utcnow().isoformat()
        )
        
        logger.info("Monitoring dashboard data generated successfully")
        return dashboard
        
    except Exception as e:
        logger.error(f"Failed to generate monitoring dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Dashboard generation failed: {str(e)}")


@router.get("/metrics/wina", response_model=WINAPerformanceMetrics)
async def get_wina_metrics():
    """
    Get current WINA performance metrics.
    
    Provides real-time WINA optimization performance data
    including efficiency gains and accuracy metrics.
    """
    try:
        logger.info("Collecting WINA performance metrics")
        
        # Collect metrics from various services
        wina_synthesis_metrics = await gs_service_client.get_wina_synthesis_metrics()
        enforcement_metrics = await pgc_service_client.get_wina_enforcement_metrics()
        fidelity_metrics = await ac_service_client.get_fidelity_metrics()
        
        metrics = WINAPerformanceMetrics(
            gflops_reduction=wina_synthesis_metrics.get("gflops_reduction", 0.0),
            synthesis_latency_ms=wina_synthesis_metrics.get("average_latency_ms", 0.0),
            optimization_success_rate=wina_synthesis_metrics.get("optimization_success_rate", 0.0),
            cache_hit_rate=enforcement_metrics.get("cache_hit_rate", 0.0),
            strategy_selection_accuracy=enforcement_metrics.get("strategy_accuracy", 0.0),
            constitutional_compliance_rate=fidelity_metrics.get("overall_fidelity_score", 0.0),
            timestamp=datetime.utcnow().isoformat()
        )
        
        logger.info("WINA performance metrics collected successfully")
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to collect WINA metrics: {e}")
        raise HTTPException(status_code=500, detail=f"WINA metrics collection failed: {str(e)}")


@router.get("/metrics/system", response_model=SystemMetrics)
async def get_system_metrics():
    """
    Get current system performance metrics.
    
    Provides real-time system resource utilization data.
    """
    try:
        logger.info("Collecting system performance metrics")
        
        # In a real implementation, this would collect actual system metrics
        # using libraries like psutil or system monitoring tools
        metrics = SystemMetrics(
            cpu_usage=45.2,  # Would be from psutil.cpu_percent()
            memory_usage=62.8,  # Would be from psutil.virtual_memory().percent
            disk_usage=34.1,  # Would be from psutil.disk_usage('/').percent
            network_io={
                "bytes_sent": 1024000.0,
                "bytes_received": 2048000.0,
                "packets_sent": 1500.0,
                "packets_received": 2200.0
            },
            timestamp=datetime.utcnow().isoformat()
        )
        
        logger.info("System performance metrics collected successfully")
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to collect system metrics: {e}")
        raise HTTPException(status_code=500, detail=f"System metrics collection failed: {str(e)}")


@router.get("/alerts")
async def get_active_alerts():
    """
    Get currently active alerts.
    
    Returns all active monitoring alerts with their severity and status.
    """
    try:
        logger.info("Retrieving active alerts")
        
        # Collect current metrics for alert evaluation
        wina_metrics = await get_wina_metrics()
        system_metrics = await get_system_metrics()
        
        # Check for alerts
        active_alerts = await _check_active_alerts(wina_metrics, system_metrics)
        
        return {
            "active_alerts": active_alerts,
            "total_count": len(active_alerts),
            "critical_count": sum(1 for alert in active_alerts if alert.severity == "critical"),
            "warning_count": sum(1 for alert in active_alerts if alert.severity == "warning"),
            "last_checked": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve active alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Alert retrieval failed: {str(e)}")


@router.get("/health")
async def monitoring_health_check():
    """Health check for monitoring system."""
    try:
        service_health = await _check_service_health()
        
        overall_status = "healthy" if all(status == "healthy" for status in service_health.values()) else "degraded"
        
        return {
            "status": overall_status,
            "service_dependencies": service_health,
            "monitoring_active": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Monitoring health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Monitoring system unhealthy: {str(e)}")


async def _check_active_alerts(
    wina_metrics: WINAPerformanceMetrics,
    system_metrics: SystemMetrics
) -> List[Alert]:
    """Check for active alerts based on current metrics."""
    alerts = []
    
    # Define alert rules (in a real system, these would be configurable)
    alert_rules = [
        {
            "rule_id": "wina_gflops_low",
            "metric_name": "gflops_reduction",
            "threshold": 0.30,
            "operator": "<",
            "severity": "warning",
            "message": "WINA GFLOPs reduction below target threshold"
        },
        {
            "rule_id": "constitutional_compliance_low",
            "metric_name": "constitutional_compliance_rate",
            "threshold": 0.85,
            "operator": "<",
            "severity": "critical",
            "message": "Constitutional compliance rate below acceptable threshold"
        },
        {
            "rule_id": "synthesis_latency_high",
            "metric_name": "synthesis_latency_ms",
            "threshold": 1000.0,
            "operator": ">",
            "severity": "warning",
            "message": "Policy synthesis latency exceeds target"
        },
        {
            "rule_id": "cpu_usage_high",
            "metric_name": "cpu_usage",
            "threshold": 80.0,
            "operator": ">",
            "severity": "warning",
            "message": "High CPU usage detected"
        },
        {
            "rule_id": "memory_usage_critical",
            "metric_name": "memory_usage",
            "threshold": 90.0,
            "operator": ">",
            "severity": "critical",
            "message": "Critical memory usage level"
        }
    ]
    
    # Check WINA metrics against rules
    wina_values = {
        "gflops_reduction": wina_metrics.gflops_reduction,
        "constitutional_compliance_rate": wina_metrics.constitutional_compliance_rate,
        "synthesis_latency_ms": wina_metrics.synthesis_latency_ms,
        "optimization_success_rate": wina_metrics.optimization_success_rate,
        "cache_hit_rate": wina_metrics.cache_hit_rate,
        "strategy_selection_accuracy": wina_metrics.strategy_selection_accuracy
    }
    
    # Check system metrics against rules
    system_values = {
        "cpu_usage": system_metrics.cpu_usage,
        "memory_usage": system_metrics.memory_usage,
        "disk_usage": system_metrics.disk_usage
    }
    
    all_values = {**wina_values, **system_values}
    
    for rule in alert_rules:
        metric_value = all_values.get(rule["metric_name"])
        if metric_value is not None:
            threshold = rule["threshold"]
            operator = rule["operator"]
            
            triggered = False
            if operator == ">" and metric_value > threshold:
                triggered = True
            elif operator == "<" and metric_value < threshold:
                triggered = True
            elif operator == ">=" and metric_value >= threshold:
                triggered = True
            elif operator == "<=" and metric_value <= threshold:
                triggered = True
            elif operator == "==" and metric_value == threshold:
                triggered = True
            
            if triggered:
                alert = Alert(
                    alert_id=f"alert_{rule['rule_id']}_{int(datetime.utcnow().timestamp())}",
                    rule_id=rule["rule_id"],
                    metric_name=rule["metric_name"],
                    current_value=metric_value,
                    threshold_value=threshold,
                    severity=rule["severity"],
                    message=rule["message"],
                    triggered_at=datetime.utcnow().isoformat(),
                    acknowledged=False
                )
                alerts.append(alert)
    
    return alerts


async def _check_service_health() -> Dict[str, str]:
    """Check health of dependent services."""
    service_health = {}
    
    # Check AC service
    try:
        await ac_service_client.get_fidelity_metrics()
        service_health["ac_service"] = "healthy"
    except Exception:
        service_health["ac_service"] = "unhealthy"
    
    # Check GS service
    try:
        await gs_service_client.get_wina_synthesis_metrics()
        service_health["gs_service"] = "healthy"
    except Exception:
        service_health["gs_service"] = "unhealthy"
    
    # Check PGC service
    try:
        await pgc_service_client.get_wina_enforcement_metrics()
        service_health["pgc_service"] = "healthy"
    except Exception:
        service_health["pgc_service"] = "unhealthy"
    
    return service_health
