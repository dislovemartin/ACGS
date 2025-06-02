"""
WINA Performance Dashboard

This module provides real-time dashboard functionality for WINA performance
monitoring, including data visualization, alert management, and system overview.

Key Features:
- Real-time performance dashboard
- Interactive charts and visualizations
- Alert and notification management
- Historical trend analysis
- Component health monitoring
- Export and reporting capabilities
"""

import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone, timedelta
from dataclasses import asdict
import asyncio

from .performance_monitoring import (
    WINAPerformanceCollector,
    WINAComponentType,
    get_wina_performance_collector
)

logger = logging.getLogger(__name__)


class WINADashboard:
    """
    Real-time dashboard for WINA performance monitoring.
    
    Provides data aggregation and visualization support for the WINA
    performance monitoring system with real-time updates and alerting.
    """
    
    def __init__(self):
        """Initialize WINA dashboard."""
        self.performance_collector: Optional[WINAPerformanceCollector] = None
        self.dashboard_cache: Dict[str, Any] = {}
        self.cache_ttl = timedelta(seconds=30)  # 30-second cache
        self.last_cache_update = datetime.min.replace(tzinfo=timezone.utc)
        
        # Dashboard configuration
        self.refresh_interval = 5  # seconds
        self.chart_data_points = 100
        self.alert_display_limit = 50
        
        logger.info("WINA Dashboard initialized")
    
    async def initialize(self) -> None:
        """Initialize dashboard with performance collector."""
        try:
            self.performance_collector = await get_wina_performance_collector()
            logger.info("WINA Dashboard connected to performance collector")
        except Exception as e:
            logger.error(f"Failed to initialize dashboard: {e}")
            raise
    
    async def get_dashboard_data(self, refresh_cache: bool = False) -> Dict[str, Any]:
        """
        Get comprehensive dashboard data.
        
        Args:
            refresh_cache: Force cache refresh
            
        Returns:
            Dashboard data with all visualizations and metrics
        """
        try:
            current_time = datetime.now(timezone.utc)
            
            # Check cache validity
            if (not refresh_cache and 
                self.dashboard_cache and 
                current_time - self.last_cache_update < self.cache_ttl):
                return self.dashboard_cache
            
            if not self.performance_collector:
                await self.initialize()
            
            # Gather all dashboard data
            dashboard_data = {
                "timestamp": current_time.isoformat(),
                "overview": await self._get_system_overview(),
                "performance_metrics": await self._get_performance_metrics(),
                "component_status": await self._get_component_status(),
                "alerts": await self._get_alerts_summary(),
                "charts": await self._get_chart_data(),
                "health_indicators": await self._get_health_indicators(),
                "trends": await self._get_trends_data(),
                "recommendations": await self._get_recommendations()
            }
            
            # Update cache
            self.dashboard_cache = dashboard_data
            self.last_cache_update = current_time
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Dashboard data retrieval failed: {e}")
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": f"Dashboard data unavailable: {str(e)}",
                "status": "error"
            }
    
    async def _get_system_overview(self) -> Dict[str, Any]:
        """Get high-level system overview."""
        try:
            real_time_metrics = await self.performance_collector.get_real_time_metrics()
            overall_performance = real_time_metrics.get("overall_performance", {})
            system_health = real_time_metrics.get("system_health", {})
            
            return {
                "wina_optimization_status": overall_performance.get("optimization_status", "unknown"),
                "performance_targets_met": overall_performance.get("performance_targets_met", False),
                "gflops_reduction": {
                    "current": overall_performance.get("gflops_reduction_achieved", 0.0),
                    "target_min": 0.4,
                    "target_max": 0.7,
                    "status": "optimal" if 0.4 <= overall_performance.get("gflops_reduction_achieved", 0.0) <= 0.7 else "needs_attention"
                },
                "accuracy_retention": {
                    "current": overall_performance.get("accuracy_retention", 0.95),
                    "target": 0.95,
                    "status": "optimal" if overall_performance.get("accuracy_retention", 0.95) >= 0.95 else "degraded"
                },
                "constitutional_compliance": {
                    "current": overall_performance.get("constitutional_compliance_rate", 0.95),
                    "target": 0.90,
                    "status": "compliant" if overall_performance.get("constitutional_compliance_rate", 0.95) >= 0.90 else "non_compliant"
                },
                "system_health": {
                    "status": system_health.get("status", "unknown"),
                    "availability": system_health.get("availability", 0.0),
                    "error_rate": system_health.get("error_rate", 0.0),
                    "throughput": system_health.get("throughput", 0.0)
                },
                "monitoring_active": self.performance_collector.monitoring_active,
                "last_update": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"System overview generation failed: {e}")
            return {"error": str(e)}
    
    async def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics."""
        try:
            real_time_metrics = await self.performance_collector.get_real_time_metrics()
            
            return {
                "neuron_activation": real_time_metrics.get("neuron_activation", {}),
                "svd_transformation": real_time_metrics.get("svd_transformation", {}),
                "dynamic_gating": real_time_metrics.get("dynamic_gating", {}),
                "constitutional_compliance": real_time_metrics.get("constitutional_compliance", {}),
                "learning_feedback": real_time_metrics.get("learning_feedback", {}),
                "integration_performance": real_time_metrics.get("integration_performance", {}),
                "efficiency_score": real_time_metrics.get("overall_performance", {}).get("efficiency_score", 0.0)
            }
            
        except Exception as e:
            logger.error(f"Performance metrics generation failed: {e}")
            return {"error": str(e)}
    
    async def _get_component_status(self) -> Dict[str, Any]:
        """Get status of all WINA components."""
        try:
            component_status = {}
            
            for component in WINAComponentType:
                # Get recent component metrics
                component_metrics = self.performance_collector.component_metrics.get(component, [])
                recent_metrics = [
                    m for m in component_metrics
                    if datetime.now(timezone.utc) - m.get("timestamp", datetime.min.replace(tzinfo=timezone.utc)) < timedelta(minutes=5)
                ]
                
                if recent_metrics:
                    success_rate = sum(1 for m in recent_metrics if m.get("success", True)) / len(recent_metrics)
                    avg_duration = sum(m.get("duration_ms", 0) for m in recent_metrics) / len(recent_metrics)
                    
                    status = "healthy"
                    if success_rate < 0.95:
                        status = "degraded"
                    if success_rate < 0.8:
                        status = "critical"
                    
                    component_status[component.value] = {
                        "status": status,
                        "success_rate": success_rate,
                        "avg_duration_ms": avg_duration,
                        "recent_operations": len(recent_metrics),
                        "last_activity": max(m.get("timestamp", datetime.min.replace(tzinfo=timezone.utc)) for m in recent_metrics).isoformat() if recent_metrics else None
                    }
                else:
                    component_status[component.value] = {
                        "status": "inactive",
                        "success_rate": 0.0,
                        "avg_duration_ms": 0.0,
                        "recent_operations": 0,
                        "last_activity": None
                    }
            
            return component_status
            
        except Exception as e:
            logger.error(f"Component status generation failed: {e}")
            return {"error": str(e)}
    
    async def _get_alerts_summary(self) -> Dict[str, Any]:
        """Get alerts summary for dashboard."""
        try:
            current_time = datetime.now(timezone.utc)
            
            # Get recent alerts
            recent_alerts = [
                alert for alert in self.performance_collector.alerts_history
                if current_time - alert["timestamp"] < timedelta(hours=24)
            ]
            
            # Categorize alerts by severity
            critical_alerts = [a for a in recent_alerts if a.get("severity") == "critical"]
            warning_alerts = [a for a in recent_alerts if a.get("severity") == "warning"]
            
            # Get active alerts (last 1 hour)
            active_alerts = [
                alert for alert in recent_alerts
                if current_time - alert["timestamp"] < timedelta(hours=1)
            ]
            
            # Convert timestamps to ISO strings
            for alert in active_alerts[-self.alert_display_limit:]:
                alert["timestamp"] = alert["timestamp"].isoformat()
            
            return {
                "total_alerts_24h": len(recent_alerts),
                "critical_alerts_24h": len(critical_alerts),
                "warning_alerts_24h": len(warning_alerts),
                "active_alerts": len(active_alerts),
                "recent_alerts": active_alerts[-self.alert_display_limit:],
                "alert_trend": "increasing" if len(active_alerts) > len(recent_alerts) / 24 else "stable"
            }
            
        except Exception as e:
            logger.error(f"Alerts summary generation failed: {e}")
            return {"error": str(e)}
    
    async def _get_chart_data(self) -> Dict[str, Any]:
        """Get data for dashboard charts."""
        try:
            chart_data = {}
            
            # GFLOPs reduction over time
            chart_data["gflops_reduction_chart"] = await self._get_gflops_chart_data()
            
            # Accuracy retention over time
            chart_data["accuracy_retention_chart"] = await self._get_accuracy_chart_data()
            
            # Component performance distribution
            chart_data["component_performance_chart"] = await self._get_component_performance_chart()
            
            # System health metrics
            chart_data["system_health_chart"] = await self._get_system_health_chart()
            
            # Integration latency trends
            chart_data["integration_latency_chart"] = await self._get_integration_latency_chart()
            
            return chart_data
            
        except Exception as e:
            logger.error(f"Chart data generation failed: {e}")
            return {"error": str(e)}
    
    async def _get_gflops_chart_data(self) -> Dict[str, Any]:
        """Get GFLOPs reduction chart data."""
        try:
            current_time = datetime.now(timezone.utc)
            time_range = timedelta(hours=2)
            
            # Get neuron activation metrics for GFLOPs calculation
            relevant_metrics = [
                m for m in self.performance_collector.neuron_activation_metrics
                if current_time - m.timestamp < time_range
            ]
            
            if not relevant_metrics:
                return {"labels": [], "data": [], "target_min": 0.4, "target_max": 0.7}
            
            # Sample data points
            step = max(1, len(relevant_metrics) // self.chart_data_points)
            sampled_metrics = relevant_metrics[::step]
            
            labels = [m.timestamp.strftime("%H:%M") for m in sampled_metrics]
            data = [m.energy_savings_ratio for m in sampled_metrics]
            
            return {
                "labels": labels,
                "data": data,
                "target_min": 0.4,
                "target_max": 0.7,
                "current": data[-1] if data else 0.0,
                "trend": "improving" if len(data) > 1 and data[-1] > data[0] else "stable"
            }
            
        except Exception as e:
            logger.error(f"GFLOPs chart data generation failed: {e}")
            return {"labels": [], "data": [], "error": str(e)}
    
    async def _get_accuracy_chart_data(self) -> Dict[str, Any]:
        """Get accuracy retention chart data."""
        try:
            current_time = datetime.now(timezone.utc)
            time_range = timedelta(hours=2)
            
            # Get constitutional compliance metrics for accuracy
            relevant_metrics = [
                m for m in self.performance_collector.constitutional_compliance_metrics
                if current_time - m.timestamp < time_range
            ]
            
            if not relevant_metrics:
                return {"labels": [], "data": [], "target": 0.95}
            
            # Sample data points
            step = max(1, len(relevant_metrics) // self.chart_data_points)
            sampled_metrics = relevant_metrics[::step]
            
            labels = [m.timestamp.strftime("%H:%M") for m in sampled_metrics]
            data = [m.compliance_score for m in sampled_metrics]
            
            return {
                "labels": labels,
                "data": data,
                "target": 0.95,
                "current": data[-1] if data else 0.95,
                "trend": "improving" if len(data) > 1 and data[-1] > data[0] else "stable"
            }
            
        except Exception as e:
            logger.error(f"Accuracy chart data generation failed: {e}")
            return {"labels": [], "data": [], "error": str(e)}
    
    async def _get_component_performance_chart(self) -> Dict[str, Any]:
        """Get component performance distribution chart."""
        try:
            component_data = []
            
            for component in WINAComponentType:
                component_metrics = self.performance_collector.component_metrics.get(component, [])
                recent_metrics = [
                    m for m in component_metrics
                    if datetime.now(timezone.utc) - m.get("timestamp", datetime.min.replace(tzinfo=timezone.utc)) < timedelta(minutes=30)
                ]
                
                if recent_metrics:
                    avg_duration = sum(m.get("duration_ms", 0) for m in recent_metrics) / len(recent_metrics)
                    success_rate = sum(1 for m in recent_metrics if m.get("success", True)) / len(recent_metrics)
                    
                    component_data.append({
                        "component": component.value.replace("_", " ").title(),
                        "avg_duration_ms": avg_duration,
                        "success_rate": success_rate,
                        "operations_count": len(recent_metrics)
                    })
            
            return {
                "components": component_data,
                "chart_type": "bar"
            }
            
        except Exception as e:
            logger.error(f"Component performance chart generation failed: {e}")
            return {"components": [], "error": str(e)}
    
    async def _get_system_health_chart(self) -> Dict[str, Any]:
        """Get system health metrics chart."""
        try:
            current_time = datetime.now(timezone.utc)
            time_range = timedelta(hours=1)
            
            relevant_metrics = [
                m for m in self.performance_collector.system_health_metrics
                if current_time - m.timestamp < time_range
            ]
            
            if not relevant_metrics:
                return {"labels": [], "cpu": [], "memory": [], "error_rate": []}
            
            # Sample data points
            step = max(1, len(relevant_metrics) // self.chart_data_points)
            sampled_metrics = relevant_metrics[::step]
            
            labels = [m.timestamp.strftime("%H:%M") for m in sampled_metrics]
            cpu_data = [m.cpu_utilization_percent for m in sampled_metrics]
            memory_data = [m.memory_utilization_percent for m in sampled_metrics]
            error_rate_data = [m.error_rate_percent for m in sampled_metrics]
            
            return {
                "labels": labels,
                "cpu": cpu_data,
                "memory": memory_data,
                "error_rate": error_rate_data,
                "current_cpu": cpu_data[-1] if cpu_data else 0.0,
                "current_memory": memory_data[-1] if memory_data else 0.0,
                "current_error_rate": error_rate_data[-1] if error_rate_data else 0.0
            }
            
        except Exception as e:
            logger.error(f"System health chart generation failed: {e}")
            return {"labels": [], "cpu": [], "memory": [], "error_rate": [], "error": str(e)}
    
    async def _get_integration_latency_chart(self) -> Dict[str, Any]:
        """Get integration latency trends chart."""
        try:
            current_time = datetime.now(timezone.utc)
            time_range = timedelta(hours=2)
            
            relevant_metrics = [
                m for m in self.performance_collector.integration_metrics
                if current_time - m.timestamp < time_range
            ]
            
            if not relevant_metrics:
                return {"integration_pairs": [], "latency_trends": []}
            
            # Group by integration pair
            integration_pairs = {}
            for metric in relevant_metrics:
                pair_key = f"{metric.source_component} -> {metric.target_component}"
                if pair_key not in integration_pairs:
                    integration_pairs[pair_key] = []
                integration_pairs[pair_key].append(metric)
            
            # Calculate trends for each pair
            latency_trends = []
            for pair_key, metrics in integration_pairs.items():
                if len(metrics) >= 2:
                    avg_latency = sum(m.integration_latency_ms for m in metrics) / len(metrics)
                    latest_latency = metrics[-1].integration_latency_ms
                    earliest_latency = metrics[0].integration_latency_ms
                    
                    trend = "stable"
                    if latest_latency > earliest_latency * 1.1:
                        trend = "increasing"
                    elif latest_latency < earliest_latency * 0.9:
                        trend = "decreasing"
                    
                    latency_trends.append({
                        "integration_pair": pair_key,
                        "avg_latency_ms": avg_latency,
                        "latest_latency_ms": latest_latency,
                        "trend": trend,
                        "data_points": len(metrics)
                    })
            
            return {
                "integration_pairs": list(integration_pairs.keys()),
                "latency_trends": latency_trends
            }
            
        except Exception as e:
            logger.error(f"Integration latency chart generation failed: {e}")
            return {"integration_pairs": [], "latency_trends": [], "error": str(e)}
    
    async def _get_health_indicators(self) -> Dict[str, Any]:
        """Get system health indicators."""
        try:
            real_time_metrics = await self.performance_collector.get_real_time_metrics()
            system_health = real_time_metrics.get("system_health", {})
            overall_performance = real_time_metrics.get("overall_performance", {})
            
            # Calculate health scores
            performance_health = 100.0
            if not overall_performance.get("performance_targets_met", False):
                performance_health -= 30.0
            
            gflops_reduction = overall_performance.get("gflops_reduction_achieved", 0.0)
            if gflops_reduction < 0.4:
                performance_health -= 20.0
            if gflops_reduction > 0.7:
                performance_health -= 15.0
            
            accuracy_retention = overall_performance.get("accuracy_retention", 0.95)
            if accuracy_retention < 0.95:
                performance_health -= 25.0
            
            system_health_score = 100.0
            error_rate = system_health.get("error_rate", 0.0)
            if error_rate > 5.0:
                system_health_score -= 30.0
            if error_rate > 10.0:
                system_health_score -= 20.0
            
            cpu_util = system_health.get("cpu_utilization", 0.0)
            if cpu_util > 80.0:
                system_health_score -= 15.0
            if cpu_util > 95.0:
                system_health_score -= 15.0
            
            overall_health = (performance_health + system_health_score) / 2
            
            health_status = "excellent"
            if overall_health < 90:
                health_status = "good"
            if overall_health < 70:
                health_status = "fair" 
            if overall_health < 50:
                health_status = "poor"
            
            return {
                "overall_health_score": overall_health,
                "health_status": health_status,
                "performance_health_score": performance_health,
                "system_health_score": system_health_score,
                "indicators": {
                    "wina_optimization": {
                        "status": overall_performance.get("optimization_status", "unknown"),
                        "score": performance_health
                    },
                    "system_stability": {
                        "status": system_health.get("status", "unknown"),
                        "score": system_health_score
                    },
                    "error_rate": {
                        "status": "good" if error_rate < 5.0 else "degraded",
                        "value": error_rate
                    },
                    "resource_utilization": {
                        "status": "good" if cpu_util < 80.0 else "high",
                        "cpu": cpu_util,
                        "memory": system_health.get("memory_utilization", 0.0)
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Health indicators generation failed: {e}")
            return {"overall_health_score": 0.0, "health_status": "unknown", "error": str(e)}
    
    async def _get_trends_data(self) -> Dict[str, Any]:
        """Get trend analysis data."""
        try:
            # Get 24-hour performance report for trends
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=24)
            
            report = await self.performance_collector.get_performance_report(start_time, end_time)
            
            return {
                "performance_trends": report.trends,
                "gflops_reduction_trend": {
                    "current": report.overall_gflops_reduction,
                    "target_range": "40-70%",
                    "status": "on_target" if 0.4 <= report.overall_gflops_reduction <= 0.7 else "off_target"
                },
                "accuracy_trend": {
                    "current": report.overall_accuracy_retention,
                    "target": "≥95%",
                    "status": "on_target" if report.overall_accuracy_retention >= 0.95 else "below_target"
                },
                "operations_trend": {
                    "total_24h": report.total_operations,
                    "hourly_average": report.total_operations / 24,
                    "growth_rate": "stable"  # Could calculate based on historical data
                }
            }
            
        except Exception as e:
            logger.error(f"Trends data generation failed: {e}")
            return {"error": str(e)}
    
    async def _get_recommendations(self) -> List[str]:
        """Get system recommendations based on current performance."""
        try:
            recommendations = []
            real_time_metrics = await self.performance_collector.get_real_time_metrics()
            overall_performance = real_time_metrics.get("overall_performance", {})
            system_health = real_time_metrics.get("system_health", {})
            
            # GFLOPs reduction recommendations
            gflops_reduction = overall_performance.get("gflops_reduction_achieved", 0.0)
            if gflops_reduction < 0.4:
                recommendations.append("GFLOPs reduction below target (40%). Consider increasing neuron pruning aggressiveness.")
            elif gflops_reduction > 0.7:
                recommendations.append("GFLOPs reduction above safe threshold (70%). Monitor accuracy retention closely.")
            
            # Accuracy recommendations
            accuracy_retention = overall_performance.get("accuracy_retention", 0.95)
            if accuracy_retention < 0.95:
                recommendations.append("Accuracy retention below 95% target. Review constitutional compliance settings.")
            
            # System health recommendations
            error_rate = system_health.get("error_rate", 0.0)
            if error_rate > 5.0:
                recommendations.append("Elevated error rate detected. Review system logs and configuration.")
            
            cpu_util = system_health.get("cpu_utilization", 0.0)
            if cpu_util > 90.0:
                recommendations.append("High CPU utilization. Consider scaling resources or optimizing workload.")
            
            # Alert-based recommendations
            recent_alerts = [
                alert for alert in self.performance_collector.alerts_history
                if datetime.now(timezone.utc) - alert["timestamp"] < timedelta(hours=1)
            ]
            
            if len(recent_alerts) > 5:
                recommendations.append("Multiple recent alerts detected. Review system stability.")
            
            # Component-specific recommendations
            neuron_activation = real_time_metrics.get("neuron_activation", {})
            if neuron_activation.get("avg_activation_ratio", 0.0) > 0.8:
                recommendations.append("High neuron activation ratio. Consider more aggressive sparsity targets.")
            
            if not recommendations:
                recommendations.append("System operating within optimal parameters. No immediate action required.")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Recommendations generation failed: {e}")
            return [f"Unable to generate recommendations: {str(e)}"]
    
    async def export_dashboard_data(self, format_type: str = "json") -> str:
        """
        Export dashboard data in specified format.
        
        Args:
            format_type: Export format (json, csv)
            
        Returns:
            Exported data as string
        """
        try:
            dashboard_data = await self.get_dashboard_data(refresh_cache=True)
            
            if format_type.lower() == "json":
                return json.dumps(dashboard_data, indent=2, default=str)
            elif format_type.lower() == "csv":
                # Simple CSV export of key metrics
                lines = ["metric,value,timestamp"]
                timestamp = dashboard_data.get("timestamp", "")
                
                overview = dashboard_data.get("overview", {})
                lines.append(f"gflops_reduction,{overview.get('gflops_reduction', {}).get('current', 0.0)},{timestamp}")
                lines.append(f"accuracy_retention,{overview.get('accuracy_retention', {}).get('current', 0.95)},{timestamp}")
                lines.append(f"constitutional_compliance,{overview.get('constitutional_compliance', {}).get('current', 0.95)},{timestamp}")
                
                return "\n".join(lines)
            else:
                raise ValueError(f"Unsupported export format: {format_type}")
                
        except Exception as e:
            logger.error(f"Dashboard data export failed: {e}")
            raise
    
    async def get_component_details(self, component_type: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific component.
        
        Args:
            component_type: Component type to get details for
            
        Returns:
            Detailed component information
        """
        try:
            # Validate component type
            try:
                component_enum = WINAComponentType(component_type)
            except ValueError:
                raise ValueError(f"Invalid component type: {component_type}")
            
            component_metrics = self.performance_collector.component_metrics.get(component_enum, [])
            
            # Get recent metrics (last hour)
            current_time = datetime.now(timezone.utc)
            recent_metrics = [
                m for m in component_metrics
                if current_time - m.get("timestamp", datetime.min.replace(tzinfo=timezone.utc)) < timedelta(hours=1)
            ]
            
            if not recent_metrics:
                return {
                    "component_type": component_type,
                    "status": "inactive",
                    "message": "No recent activity"
                }
            
            # Calculate statistics
            success_rate = sum(1 for m in recent_metrics if m.get("success", True)) / len(recent_metrics)
            avg_duration = sum(m.get("duration_ms", 0) for m in recent_metrics) / len(recent_metrics)
            total_operations = len(recent_metrics)
            
            # Get operation type breakdown
            operation_types = {}
            for metric in recent_metrics:
                op_type = metric.get("operation_type", "unknown")
                if op_type not in operation_types:
                    operation_types[op_type] = {"count": 0, "avg_duration": 0, "success_rate": 0}
                
                operation_types[op_type]["count"] += 1
                operation_types[op_type]["avg_duration"] += metric.get("duration_ms", 0)
                if metric.get("success", True):
                    operation_types[op_type]["success_rate"] += 1
            
            # Finalize operation type statistics
            for op_type in operation_types:
                count = operation_types[op_type]["count"]
                operation_types[op_type]["avg_duration"] /= count
                operation_types[op_type]["success_rate"] /= count
            
            return {
                "component_type": component_type,
                "status": "healthy" if success_rate > 0.95 else "degraded",
                "summary": {
                    "total_operations": total_operations,
                    "success_rate": success_rate,
                    "avg_duration_ms": avg_duration,
                    "last_activity": max(m.get("timestamp", datetime.min.replace(tzinfo=timezone.utc)) for m in recent_metrics).isoformat()
                },
                "operation_breakdown": operation_types,
                "recent_trends": {
                    "operations_per_minute": total_operations / 60,
                    "performance_trend": "stable"  # Could calculate based on duration trends
                }
            }
            
        except Exception as e:
            logger.error(f"Component details retrieval failed: {e}")
            return {
                "component_type": component_type,
                "error": str(e),
                "status": "error"
            }


# Global dashboard instance
_wina_dashboard: Optional[WINADashboard] = None


async def get_wina_dashboard() -> WINADashboard:
    """Get or create the global WINA dashboard instance."""
    global _wina_dashboard
    
    if _wina_dashboard is None:
        _wina_dashboard = WINADashboard()
        await _wina_dashboard.initialize()
        logger.info("WINA Dashboard instance created")
    
    return _wina_dashboard