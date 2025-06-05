"""
reliability_metrics_dashboard.py

Comprehensive Reliability Metrics Dashboard for LLM Constitutional Governance System.
Provides real-time monitoring, historical analysis, and actionable insights for achieving
>99.9% reliability target in constitutional decision-making.

This dashboard integrates with the existing constitutional fidelity monitor and QEC-inspired
reliability mechanisms to provide comprehensive oversight of system reliability.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import aiohttp
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

# Import existing monitoring components
try:
    from ...alphaevolve_gs_engine.src.alphaevolve_gs_engine.services.qec_enhancement.constitutional_fidelity_monitor import (
        ConstitutionalFidelityMonitor, FidelityComponents, FidelityAlert, FidelityLevel
    )
    from ...alphaevolve_gs_engine.src.alphaevolve_gs_engine.services.qec_enhancement.constitutional_distance_calculator import (
        ConstitutionalDistanceCalculator
    )
except ImportError:
    # Fallback for development/testing
    logger = logging.getLogger(__name__)
    logger.warning("Could not import QEC enhancement modules. Using mock implementations.")
    
    class FidelityLevel(Enum):
        GREEN = "green"
        AMBER = "amber"
        RED = "red"
        CRITICAL = "critical"
    
    @dataclass
    class FidelityComponents:
        principle_coverage: float = 0.0
        synthesis_success: float = 0.0
        enforcement_reliability: float = 0.0
        adaptation_speed: float = 0.0
        stakeholder_satisfaction: float = 0.0
        appeal_frequency: float = 0.0
        composite_score: float = 0.0
        calculation_metadata: Dict[str, Any] = None

logger = logging.getLogger(__name__)


class ReliabilityMetricType(Enum):
    """Types of reliability metrics tracked by the dashboard."""
    LLM_RESPONSE_ACCURACY = "llm_response_accuracy"
    CONSTITUTIONAL_COMPLIANCE = "constitutional_compliance"
    SYNTHESIS_SUCCESS_RATE = "synthesis_success_rate"
    ENFORCEMENT_RELIABILITY = "enforcement_reliability"
    SYSTEM_AVAILABILITY = "system_availability"
    APPEAL_RESOLUTION_TIME = "appeal_resolution_time"
    BIAS_MITIGATION_EFFECTIVENESS = "bias_mitigation_effectiveness"
    VALIDATION_PIPELINE_SUCCESS = "validation_pipeline_success"


@dataclass
class ReliabilityMetric:
    """Individual reliability metric with metadata."""
    metric_type: ReliabilityMetricType
    value: float
    timestamp: datetime
    unit: str
    target_threshold: float
    alert_threshold: float
    metadata: Dict[str, Any]
    
    @property
    def is_healthy(self) -> bool:
        """Check if metric meets target threshold."""
        return self.value >= self.target_threshold
    
    @property
    def needs_alert(self) -> bool:
        """Check if metric requires alerting."""
        return self.value < self.alert_threshold


@dataclass
class ReliabilityTrend:
    """Historical trend analysis for reliability metrics."""
    metric_type: ReliabilityMetricType
    values: List[float]
    timestamps: List[datetime]
    trend_direction: str  # "improving", "declining", "stable"
    trend_strength: float  # 0.0-1.0, strength of trend
    prediction_next_hour: float
    prediction_confidence: float


@dataclass
class DashboardAlert:
    """Dashboard-specific alert configuration."""
    id: str
    severity: str  # "info", "warning", "error", "critical"
    title: str
    description: str
    metric_type: ReliabilityMetricType
    current_value: float
    threshold_value: float
    timestamp: datetime
    acknowledged: bool = False
    resolved: bool = False
    resolution_notes: Optional[str] = None


class ReliabilityMetricsDashboard:
    """
    Comprehensive reliability metrics dashboard for constitutional governance system.
    
    Features:
    - Real-time metric collection and visualization
    - Historical trend analysis with predictions
    - Alert management and escalation
    - Drill-down capabilities for root cause analysis
    - Integration with existing monitoring infrastructure
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the reliability metrics dashboard."""
        self.config = config or self._get_default_config()
        self.app = FastAPI(title="Reliability Metrics Dashboard", version="1.0.0")
        
        # Initialize monitoring components
        self.fidelity_monitor = None
        self.distance_calculator = None
        try:
            self.fidelity_monitor = ConstitutionalFidelityMonitor()
            self.distance_calculator = ConstitutionalDistanceCalculator()
        except Exception as e:
            logger.warning(f"Could not initialize monitoring components: {e}")
        
        # Data storage for metrics and alerts
        self.current_metrics: Dict[ReliabilityMetricType, ReliabilityMetric] = {}
        self.historical_data: Dict[ReliabilityMetricType, List[ReliabilityMetric]] = {}
        self.active_alerts: List[DashboardAlert] = []
        self.alert_history: List[DashboardAlert] = []
        
        # Reliability targets (configurable)
        self.reliability_targets = self.config.get("reliability_targets", {
            ReliabilityMetricType.LLM_RESPONSE_ACCURACY: 0.999,
            ReliabilityMetricType.CONSTITUTIONAL_COMPLIANCE: 0.995,
            ReliabilityMetricType.SYNTHESIS_SUCCESS_RATE: 0.990,
            ReliabilityMetricType.ENFORCEMENT_RELIABILITY: 0.998,
            ReliabilityMetricType.SYSTEM_AVAILABILITY: 0.999,
            ReliabilityMetricType.APPEAL_RESOLUTION_TIME: 300.0,  # seconds
            ReliabilityMetricType.BIAS_MITIGATION_EFFECTIVENESS: 0.985,
            ReliabilityMetricType.VALIDATION_PIPELINE_SUCCESS: 0.992
        })
        
        # Initialize FastAPI routes
        self._setup_routes()
        
        # Start background monitoring tasks
        self.monitoring_task = None
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for the dashboard."""
        return {
            "update_interval_seconds": 30,
            "historical_retention_days": 30,
            "alert_cooldown_minutes": 5,
            "prometheus_url": "http://localhost:9090",
            "grafana_url": "http://localhost:3000",
            "max_metrics_per_type": 1000,
            "trend_analysis_window_hours": 24,
            "prediction_confidence_threshold": 0.7
        }
    
    def _setup_routes(self):
        """Setup FastAPI routes for the dashboard API."""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home():
            """Serve the main dashboard HTML page."""
            return self._generate_dashboard_html()
        
        @self.app.get("/api/metrics/current")
        async def get_current_metrics():
            """Get current reliability metrics."""
            return {
                "timestamp": datetime.now().isoformat(),
                "metrics": {
                    metric_type.value: asdict(metric) 
                    for metric_type, metric in self.current_metrics.items()
                },
                "overall_reliability": self._calculate_overall_reliability(),
                "status": self._get_system_status()
            }
        
        @self.app.get("/api/metrics/historical")
        async def get_historical_metrics(
            metric_type: str = Query(..., description="Metric type to retrieve"),
            hours: int = Query(24, description="Hours of history to retrieve")
        ):
            """Get historical data for a specific metric."""
            try:
                metric_enum = ReliabilityMetricType(metric_type)
                cutoff_time = datetime.now() - timedelta(hours=hours)
                
                historical = self.historical_data.get(metric_enum, [])
                filtered_data = [
                    asdict(metric) for metric in historical 
                    if metric.timestamp >= cutoff_time
                ]
                
                trend = self._calculate_trend(metric_enum, hours)
                
                return {
                    "metric_type": metric_type,
                    "data": filtered_data,
                    "trend": asdict(trend) if trend else None,
                    "summary": self._calculate_metric_summary(filtered_data)
                }
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid metric type: {metric_type}")
        
        @self.app.get("/api/alerts/active")
        async def get_active_alerts():
            """Get currently active alerts."""
            return {
                "alerts": [asdict(alert) for alert in self.active_alerts],
                "count": len(self.active_alerts),
                "severity_breakdown": self._get_alert_severity_breakdown()
            }
        
        @self.app.post("/api/alerts/{alert_id}/acknowledge")
        async def acknowledge_alert(alert_id: str):
            """Acknowledge a specific alert."""
            for alert in self.active_alerts:
                if alert.id == alert_id:
                    alert.acknowledged = True
                    return {"status": "acknowledged", "alert_id": alert_id}
            raise HTTPException(status_code=404, detail="Alert not found")
        
        @self.app.get("/api/dashboard/summary")
        async def get_dashboard_summary():
            """Get high-level dashboard summary."""
            return {
                "overall_reliability": self._calculate_overall_reliability(),
                "system_status": self._get_system_status(),
                "metrics_summary": self._get_metrics_summary(),
                "alerts_summary": {
                    "active_count": len(self.active_alerts),
                    "critical_count": len([a for a in self.active_alerts if a.severity == "critical"]),
                    "unacknowledged_count": len([a for a in self.active_alerts if not a.acknowledged])
                },
                "trends": self._get_trend_summary(),
                "recommendations": self._generate_recommendations()
            }
        
        @self.app.get("/api/metrics/export")
        async def export_metrics():
            """Export metrics data for external analysis."""
            return {
                "export_timestamp": datetime.now().isoformat(),
                "current_metrics": {
                    metric_type.value: asdict(metric) 
                    for metric_type, metric in self.current_metrics.items()
                },
                "historical_summary": {
                    metric_type.value: len(data) 
                    for metric_type, data in self.historical_data.items()
                },
                "configuration": {
                    "targets": {k.value: v for k, v in self.reliability_targets.items()},
                    "update_interval": self.config["update_interval_seconds"]
                }
            }
    
    async def start_monitoring(self):
        """Start the background monitoring tasks."""
        if self.monitoring_task is None:
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            logger.info("Started reliability metrics monitoring")
    
    async def stop_monitoring(self):
        """Stop the background monitoring tasks."""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None
            logger.info("Stopped reliability metrics monitoring")
    
    async def _monitoring_loop(self):
        """Main monitoring loop for collecting metrics."""
        while True:
            try:
                await self._collect_metrics()
                await self._analyze_trends()
                await self._check_alerts()
                await self._cleanup_old_data()
                
                await asyncio.sleep(self.config["update_interval_seconds"])
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Brief pause before retrying
    
    async def _collect_metrics(self):
        """Collect current reliability metrics from various sources."""
        timestamp = datetime.now()
        
        # Collect metrics from constitutional fidelity monitor
        if self.fidelity_monitor:
            try:
                fidelity_components = await self._get_fidelity_components()
                
                # Map fidelity components to reliability metrics
                metrics_to_update = {
                    ReliabilityMetricType.CONSTITUTIONAL_COMPLIANCE: fidelity_components.principle_coverage,
                    ReliabilityMetricType.SYNTHESIS_SUCCESS_RATE: fidelity_components.synthesis_success,
                    ReliabilityMetricType.ENFORCEMENT_RELIABILITY: fidelity_components.enforcement_reliability,
                }
                
                for metric_type, value in metrics_to_update.items():
                    metric = ReliabilityMetric(
                        metric_type=metric_type,
                        value=value,
                        timestamp=timestamp,
                        unit="ratio",
                        target_threshold=self.reliability_targets[metric_type],
                        alert_threshold=self.reliability_targets[metric_type] * 0.95,
                        metadata={"source": "constitutional_fidelity_monitor"}
                    )
                    self._update_metric(metric)
                    
            except Exception as e:
                logger.error(f"Error collecting fidelity metrics: {e}")
        
        # Collect metrics from Prometheus (if available)
        await self._collect_prometheus_metrics(timestamp)
        
        # Collect LLM-specific metrics
        await self._collect_llm_metrics(timestamp)
        
        # Collect system availability metrics
        await self._collect_availability_metrics(timestamp)
    
    async def _collect_prometheus_metrics(self, timestamp: datetime):
        """Collect metrics from Prometheus endpoint."""
        prometheus_url = self.config["prometheus_url"]
        
        try:
            async with aiohttp.ClientSession() as session:
                # Query system availability
                query = "up{job='acgs-service'}"
                async with session.get(f"{prometheus_url}/api/v1/query", 
                                     params={"query": query}) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data["data"]["result"]:
                            availability = float(data["data"]["result"][0]["value"][1])
                            metric = ReliabilityMetric(
                                metric_type=ReliabilityMetricType.SYSTEM_AVAILABILITY,
                                value=availability,
                                timestamp=timestamp,
                                unit="ratio",
                                target_threshold=self.reliability_targets[ReliabilityMetricType.SYSTEM_AVAILABILITY],
                                alert_threshold=self.reliability_targets[ReliabilityMetricType.SYSTEM_AVAILABILITY] * 0.99,
                                metadata={"source": "prometheus", "query": query}
                            )
                            self._update_metric(metric)
        except Exception as e:
            logger.warning(f"Could not collect Prometheus metrics: {e}")
    
    async def _collect_llm_metrics(self, timestamp: datetime):
        """Collect LLM-specific reliability metrics."""
        # Mock implementation - would integrate with actual LLM monitoring
        try:
            # Simulate LLM response accuracy measurement
            llm_accuracy = await self._measure_llm_accuracy()
            metric = ReliabilityMetric(
                metric_type=ReliabilityMetricType.LLM_RESPONSE_ACCURACY,
                value=llm_accuracy,
                timestamp=timestamp,
                unit="ratio",
                target_threshold=self.reliability_targets[ReliabilityMetricType.LLM_RESPONSE_ACCURACY],
                alert_threshold=self.reliability_targets[ReliabilityMetricType.LLM_RESPONSE_ACCURACY] * 0.98,
                metadata={"source": "llm_monitor", "model": "constitutional_ai"}
            )
            self._update_metric(metric)
            
            # Simulate bias mitigation effectiveness
            bias_effectiveness = await self._measure_bias_mitigation()
            metric = ReliabilityMetric(
                metric_type=ReliabilityMetricType.BIAS_MITIGATION_EFFECTIVENESS,
                value=bias_effectiveness,
                timestamp=timestamp,
                unit="ratio",
                target_threshold=self.reliability_targets[ReliabilityMetricType.BIAS_MITIGATION_EFFECTIVENESS],
                alert_threshold=self.reliability_targets[ReliabilityMetricType.BIAS_MITIGATION_EFFECTIVENESS] * 0.95,
                metadata={"source": "bias_monitor"}
            )
            self._update_metric(metric)
            
        except Exception as e:
            logger.error(f"Error collecting LLM metrics: {e}")
    
    async def _collect_availability_metrics(self, timestamp: datetime):
        """Collect system availability and performance metrics."""
        # Mock implementation - would integrate with actual monitoring
        try:
            # Simulate validation pipeline success rate
            validation_success = 0.995  # Would be calculated from actual pipeline data
            metric = ReliabilityMetric(
                metric_type=ReliabilityMetricType.VALIDATION_PIPELINE_SUCCESS,
                value=validation_success,
                timestamp=timestamp,
                unit="ratio",
                target_threshold=self.reliability_targets[ReliabilityMetricType.VALIDATION_PIPELINE_SUCCESS],
                alert_threshold=self.reliability_targets[ReliabilityMetricType.VALIDATION_PIPELINE_SUCCESS] * 0.97,
                metadata={"source": "validation_monitor"}
            )
            self._update_metric(metric)
            
        except Exception as e:
            logger.error(f"Error collecting availability metrics: {e}")
    
    def _update_metric(self, metric: ReliabilityMetric):
        """Update a reliability metric and maintain historical data."""
        # Update current metric
        self.current_metrics[metric.metric_type] = metric
        
        # Add to historical data
        if metric.metric_type not in self.historical_data:
            self.historical_data[metric.metric_type] = []
        
        self.historical_data[metric.metric_type].append(metric)
        
        # Maintain maximum historical data points
        max_points = self.config["max_metrics_per_type"]
        if len(self.historical_data[metric.metric_type]) > max_points:
            self.historical_data[metric.metric_type] = self.historical_data[metric.metric_type][-max_points:]
    
    async def _get_fidelity_components(self) -> FidelityComponents:
        """Get current fidelity components from the monitor."""
        if self.fidelity_monitor:
            try:
                # This would call the actual fidelity monitor
                return await self.fidelity_monitor.calculate_current_fidelity()
            except Exception as e:
                logger.warning(f"Could not get fidelity components: {e}")
        
        # Return mock data for testing
        return FidelityComponents(
            principle_coverage=0.985,
            synthesis_success=0.992,
            enforcement_reliability=0.997,
            adaptation_speed=0.875,
            stakeholder_satisfaction=0.910,
            appeal_frequency=0.150,
            composite_score=0.945,
            calculation_metadata={"mock": True}
        )
    
    async def _measure_llm_accuracy(self) -> float:
        """Measure current LLM response accuracy."""
        # Mock implementation - would integrate with actual LLM testing
        return 0.9985
    
    async def _measure_bias_mitigation(self) -> float:
        """Measure bias mitigation effectiveness."""
        # Mock implementation - would integrate with bias detection systems
        return 0.991
    
    def _calculate_overall_reliability(self) -> float:
        """Calculate overall system reliability score."""
        if not self.current_metrics:
            return 0.0
        
        # Weighted average of all current metrics
        weights = {
            ReliabilityMetricType.LLM_RESPONSE_ACCURACY: 0.25,
            ReliabilityMetricType.CONSTITUTIONAL_COMPLIANCE: 0.20,
            ReliabilityMetricType.SYNTHESIS_SUCCESS_RATE: 0.15,
            ReliabilityMetricType.ENFORCEMENT_RELIABILITY: 0.15,
            ReliabilityMetricType.SYSTEM_AVAILABILITY: 0.10,
            ReliabilityMetricType.BIAS_MITIGATION_EFFECTIVENESS: 0.10,
            ReliabilityMetricType.VALIDATION_PIPELINE_SUCCESS: 0.05
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for metric_type, metric in self.current_metrics.items():
            if metric_type in weights:
                weight = weights[metric_type]
                weighted_sum += metric.value * weight
                total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _get_system_status(self) -> str:
        """Get overall system status based on reliability metrics."""
        overall_reliability = self._calculate_overall_reliability()
        
        if overall_reliability >= 0.995:
            return "healthy"
        elif overall_reliability >= 0.990:
            return "warning"
        elif overall_reliability >= 0.980:
            return "degraded"
        else:
            return "critical"
    
    async def _analyze_trends(self):
        """Analyze trends for all metrics and update predictions."""
        for metric_type in ReliabilityMetricType:
            if metric_type in self.historical_data:
                trend = self._calculate_trend(metric_type, 
                                            self.config["trend_analysis_window_hours"])
                # Store trend data for dashboard display
                # This would be implemented based on storage requirements
    
    def _calculate_trend(self, metric_type: ReliabilityMetricType, hours: int) -> Optional[ReliabilityTrend]:
        """Calculate trend analysis for a specific metric."""
        if metric_type not in self.historical_data:
            return None
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_data = [
            metric for metric in self.historical_data[metric_type]
            if metric.timestamp >= cutoff_time
        ]
        
        if len(recent_data) < 2:
            return None
        
        values = [metric.value for metric in recent_data]
        timestamps = [metric.timestamp for metric in recent_data]
        
        # Simple trend calculation
        if len(values) >= 3:
            recent_avg = statistics.mean(values[-3:])
            earlier_avg = statistics.mean(values[:3])
            
            if recent_avg > earlier_avg * 1.02:
                trend_direction = "improving"
                trend_strength = min((recent_avg - earlier_avg) / earlier_avg, 1.0)
            elif recent_avg < earlier_avg * 0.98:
                trend_direction = "declining"
                trend_strength = min((earlier_avg - recent_avg) / earlier_avg, 1.0)
            else:
                trend_direction = "stable"
                trend_strength = 0.0
        else:
            trend_direction = "stable"
            trend_strength = 0.0
        
        # Simple prediction (would use more sophisticated methods in production)
        prediction_next_hour = values[-1]
        prediction_confidence = 0.7 if len(values) >= 10 else 0.4
        
        return ReliabilityTrend(
            metric_type=metric_type,
            values=values,
            timestamps=timestamps,
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            prediction_next_hour=prediction_next_hour,
            prediction_confidence=prediction_confidence
        )
    
    async def _check_alerts(self):
        """Check for alert conditions and generate alerts."""
        new_alerts = []
        
        for metric_type, metric in self.current_metrics.items():
            if metric.needs_alert:
                # Check if we already have an active alert for this metric
                existing_alert = next(
                    (alert for alert in self.active_alerts 
                     if alert.metric_type == metric_type and not alert.resolved),
                    None
                )
                
                if not existing_alert:
                    # Create new alert
                    alert = DashboardAlert(
                        id=f"{metric_type.value}_{int(metric.timestamp.timestamp())}",
                        severity=self._determine_alert_severity(metric),
                        title=f"Reliability Alert: {metric_type.value}",
                        description=f"Metric {metric_type.value} is below threshold: {metric.value:.4f} < {metric.alert_threshold:.4f}",
                        metric_type=metric_type,
                        current_value=metric.value,
                        threshold_value=metric.alert_threshold,
                        timestamp=metric.timestamp
                    )
                    new_alerts.append(alert)
        
        # Add new alerts to active alerts
        self.active_alerts.extend(new_alerts)
        
        # Check for resolved alerts
        for alert in self.active_alerts:
            if not alert.resolved:
                current_metric = self.current_metrics.get(alert.metric_type)
                if current_metric and current_metric.value >= current_metric.target_threshold:
                    alert.resolved = True
                    alert.resolution_notes = "Metric returned to healthy threshold"
    
    def _determine_alert_severity(self, metric: ReliabilityMetric) -> str:
        """Determine alert severity based on metric value."""
        target = metric.target_threshold
        value = metric.value
        
        if value < target * 0.90:
            return "critical"
        elif value < target * 0.95:
            return "error"
        elif value < target * 0.98:
            return "warning"
        else:
            return "info"
    
    async def _cleanup_old_data(self):
        """Clean up old historical data and resolved alerts."""
        retention_days = self.config["historical_retention_days"]
        cutoff_time = datetime.now() - timedelta(days=retention_days)
        
        # Clean up historical metrics
        for metric_type in list(self.historical_data.keys()):
            self.historical_data[metric_type] = [
                metric for metric in self.historical_data[metric_type]
                if metric.timestamp >= cutoff_time
            ]
        
        # Move resolved alerts to history
        resolved_alerts = [alert for alert in self.active_alerts if alert.resolved]
        self.alert_history.extend(resolved_alerts)
        self.active_alerts = [alert for alert in self.active_alerts if not alert.resolved]
        
        # Clean up old alert history
        self.alert_history = [
            alert for alert in self.alert_history
            if alert.timestamp >= cutoff_time
        ]
    
    def _get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of current metrics."""
        healthy_count = sum(1 for metric in self.current_metrics.values() if metric.is_healthy)
        total_count = len(self.current_metrics)
        
        return {
            "total_metrics": total_count,
            "healthy_metrics": healthy_count,
            "unhealthy_metrics": total_count - healthy_count,
            "health_percentage": (healthy_count / total_count * 100) if total_count > 0 else 0,
            "last_update": max(
                (metric.timestamp for metric in self.current_metrics.values()),
                default=datetime.now()
            ).isoformat()
        }
    
    def _get_alert_severity_breakdown(self) -> Dict[str, int]:
        """Get breakdown of active alerts by severity."""
        severity_counts = {"info": 0, "warning": 0, "error": 0, "critical": 0}
        for alert in self.active_alerts:
            severity_counts[alert.severity] = severity_counts.get(alert.severity, 0) + 1
        return severity_counts
    
    def _get_trend_summary(self) -> Dict[str, str]:
        """Get summary of metric trends."""
        trend_summary = {}
        for metric_type in ReliabilityMetricType:
            trend = self._calculate_trend(metric_type, 24)
            if trend:
                trend_summary[metric_type.value] = trend.trend_direction
        return trend_summary
    
    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations based on current system state."""
        recommendations = []
        
        overall_reliability = self._calculate_overall_reliability()
        if overall_reliability < 0.995:
            recommendations.append("Overall reliability is below target (99.5%). Review critical metrics.")
        
        for metric_type, metric in self.current_metrics.items():
            if not metric.is_healthy:
                recommendations.append(f"Address {metric_type.value}: current {metric.value:.3f} < target {metric.target_threshold:.3f}")
        
        critical_alerts = [alert for alert in self.active_alerts if alert.severity == "critical"]
        if critical_alerts:
            recommendations.append(f"Resolve {len(critical_alerts)} critical alert(s) immediately")
        
        if not recommendations:
            recommendations.append("System is operating within all reliability targets")
        
        return recommendations
    
    def _calculate_metric_summary(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics for metric data."""
        if not data:
            return {}
        
        values = [item["value"] for item in data]
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0.0
        }
    
    def _generate_dashboard_html(self) -> str:
        """Generate the main dashboard HTML page."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Reliability Metrics Dashboard</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
                .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
                .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
                .metric-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0