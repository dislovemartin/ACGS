"""
Scalability Dashboard Integration

This module provides dashboard integration for the scalability metrics system,
offering real-time monitoring dashboards, alerting integration, and visualization
capabilities for system scalability and performance metrics.

Key Features:
- Real-time scalability metrics dashboard
- Interactive performance visualizations
- Alert management interface
- Component health monitoring
- Trend analysis and predictive insights
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import plotly.graph_objects as go
from fastapi import WebSocket, WebSocketDisconnect
from plotly.utils import PlotlyJSONEncoder

from .scalability_metrics import (
    ScalabilityMetricsCollector,
    get_scalability_metrics_collector,
)

logger = logging.getLogger(__name__)


class ScalabilityDashboard:
    """
    Real-time scalability metrics dashboard.

    Provides web-based dashboard interface for monitoring system scalability
    and performance metrics with real-time updates and interactive visualizations.
    """

    def __init__(self, metrics_collector: ScalabilityMetricsCollector):
        """Initialize scalability dashboard."""
        self.metrics_collector = metrics_collector
        self.websocket_connections: List[WebSocket] = []
        self.dashboard_active = False

        # Dashboard configuration
        self.update_interval = 5  # seconds
        self.chart_history_minutes = 60

        logger.info("Scalability Dashboard initialized")

    async def start_dashboard(self) -> None:
        """Start the dashboard real-time updates."""
        if self.dashboard_active:
            logger.warning("Dashboard already active")
            return

        self.dashboard_active = True
        logger.info("Started scalability dashboard")

        # Start dashboard update loop
        asyncio.create_task(self._dashboard_update_loop())

    async def stop_dashboard(self) -> None:
        """Stop the dashboard."""
        self.dashboard_active = False

        # Close all websocket connections
        for websocket in self.websocket_connections:
            try:
                await websocket.close()
            except Exception as e:
                logger.error(f"Error closing websocket: {e}")

        self.websocket_connections.clear()
        logger.info("Stopped scalability dashboard")

    async def _dashboard_update_loop(self) -> None:
        """Main dashboard update loop."""
        while self.dashboard_active:
            try:
                if self.websocket_connections:
                    # Get current metrics
                    metrics_data = await self.get_dashboard_data()

                    # Broadcast to all connected clients
                    await self._broadcast_to_websockets(metrics_data)

                await asyncio.sleep(self.update_interval)

            except Exception as e:
                logger.error(f"Error in dashboard update loop: {e}")
                await asyncio.sleep(5)

    async def _broadcast_to_websockets(self, data: Dict[str, Any]) -> None:
        """Broadcast data to all connected websockets."""
        if not self.websocket_connections:
            return

        message = json.dumps(data, cls=PlotlyJSONEncoder)
        disconnected_clients = []

        for websocket in self.websocket_connections:
            try:
                await websocket.send_text(message)
            except WebSocketDisconnect:
                disconnected_clients.append(websocket)
            except Exception as e:
                logger.error(f"Error sending websocket message: {e}")
                disconnected_clients.append(websocket)

        # Remove disconnected clients
        for websocket in disconnected_clients:
            self.websocket_connections.remove(websocket)

    async def add_websocket_connection(self, websocket: WebSocket) -> None:
        """Add a new websocket connection."""
        await websocket.accept()
        self.websocket_connections.append(websocket)
        logger.info(
            f"Added websocket connection, total: {len(self.websocket_connections)}"
        )

        # Send initial data
        try:
            initial_data = await self.get_dashboard_data()
            await websocket.send_text(json.dumps(initial_data, cls=PlotlyJSONEncoder))
        except Exception as e:
            logger.error(f"Error sending initial websocket data: {e}")

    async def remove_websocket_connection(self, websocket: WebSocket) -> None:
        """Remove a websocket connection."""
        if websocket in self.websocket_connections:
            self.websocket_connections.remove(websocket)
            logger.info(
                f"Removed websocket connection, total: {len(self.websocket_connections)}"
            )

    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data."""
        try:
            # Get metrics summary
            metrics_summary = await self.metrics_collector.get_metrics_summary()

            # Generate charts
            charts = await self._generate_dashboard_charts()

            # Get alert summary
            alert_summary = await self._get_alert_summary()

            # Get component health overview
            component_health = await self._get_component_health_overview()

            # Get performance trends
            performance_trends = await self._get_performance_trends()

            dashboard_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "metrics_summary": metrics_summary,
                "charts": charts,
                "alerts": alert_summary,
                "component_health": component_health,
                "performance_trends": performance_trends,
                "system_status": await self._get_system_status(),
            }

            return dashboard_data

        except Exception as e:
            logger.error(f"Failed to generate dashboard data: {e}")
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}

    async def _generate_dashboard_charts(self) -> Dict[str, Any]:
        """Generate interactive charts for the dashboard."""
        charts = {}

        try:
            # Latency chart
            charts["latency_chart"] = await self._create_latency_chart()

            # Throughput chart
            charts["throughput_chart"] = await self._create_throughput_chart()

            # Resource utilization chart
            charts["resource_chart"] = await self._create_resource_utilization_chart()

            # Concurrent operations chart
            charts["concurrent_ops_chart"] = (
                await self._create_concurrent_operations_chart()
            )

            # Scalability scores chart
            charts["scalability_scores_chart"] = (
                await self._create_scalability_scores_chart()
            )

            # Alert trend chart
            charts["alert_trend_chart"] = await self._create_alert_trend_chart()

        except Exception as e:
            logger.error(f"Failed to generate dashboard charts: {e}")
            charts["error"] = str(e)

        return charts

    async def _create_latency_chart(self) -> Dict[str, Any]:
        """Create latency metrics chart."""
        fig = go.Figure()

        # Add traces for each component
        for (
            component_name,
            metrics_queue,
        ) in self.metrics_collector.latency_metrics.items():
            if not metrics_queue:
                continue

            recent_metrics = list(metrics_queue)[-20:]  # Last 20 samples
            timestamps = [m.timestamp for m in recent_metrics]
            p95_latencies = [m.p95_latency_ms for m in recent_metrics]

            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=p95_latencies,
                    mode="lines+markers",
                    name=f"{component_name} P95",
                    line=dict(width=2),
                )
            )

        fig.update_layout(
            title="P95 Latency by Component",
            xaxis_title="Time",
            yaxis_title="Latency (ms)",
            hovermode="x unified",
            template="plotly_white",
        )

        return json.loads(fig.to_json())

    async def _create_throughput_chart(self) -> Dict[str, Any]:
        """Create throughput metrics chart."""
        fig = go.Figure()

        # Add traces for each component
        for (
            component_name,
            metrics_queue,
        ) in self.metrics_collector.throughput_metrics.items():
            if not metrics_queue:
                continue

            recent_metrics = list(metrics_queue)[-20:]  # Last 20 samples
            timestamps = [m.timestamp for m in recent_metrics]
            ops_per_second = [m.operations_per_second for m in recent_metrics]

            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=ops_per_second,
                    mode="lines+markers",
                    name=f"{component_name} Ops/sec",
                    line=dict(width=2),
                )
            )

        fig.update_layout(
            title="Throughput by Component",
            xaxis_title="Time",
            yaxis_title="Operations per Second",
            hovermode="x unified",
            template="plotly_white",
        )

        return json.loads(fig.to_json())

    async def _create_resource_utilization_chart(self) -> Dict[str, Any]:
        """Create resource utilization chart."""
        fig = go.Figure()

        # Add traces for system resources
        if "system" in self.metrics_collector.resource_metrics:
            metrics_queue = self.metrics_collector.resource_metrics["system"]
            recent_metrics = list(metrics_queue)[-20:]  # Last 20 samples

            timestamps = [m.timestamp for m in recent_metrics]
            cpu_percents = [m.cpu_percent for m in recent_metrics]
            memory_percents = [m.memory_percent for m in recent_metrics]

            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=cpu_percents,
                    mode="lines+markers",
                    name="CPU %",
                    line=dict(color="red", width=2),
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=memory_percents,
                    mode="lines+markers",
                    name="Memory %",
                    line=dict(color="blue", width=2),
                )
            )

        fig.update_layout(
            title="System Resource Utilization",
            xaxis_title="Time",
            yaxis_title="Utilization (%)",
            yaxis=dict(range=[0, 100]),
            hovermode="x unified",
            template="plotly_white",
        )

        return json.loads(fig.to_json())

    async def _create_concurrent_operations_chart(self) -> Dict[str, Any]:
        """Create concurrent operations chart."""
        fig = go.Figure()

        # Add traces for each component
        for (
            component_name,
            metrics_queue,
        ) in self.metrics_collector.concurrent_ops_metrics.items():
            if not metrics_queue:
                continue

            recent_metrics = list(metrics_queue)[-20:]  # Last 20 samples
            timestamps = [m.timestamp for m in recent_metrics]
            active_ops = [m.active_operations for m in recent_metrics]
            queue_sizes = [m.operation_queue_size for m in recent_metrics]

            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=active_ops,
                    mode="lines+markers",
                    name=f"{component_name} Active Ops",
                    line=dict(width=2),
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=queue_sizes,
                    mode="lines+markers",
                    name=f"{component_name} Queue Size",
                    line=dict(dash="dash", width=2),
                )
            )

        fig.update_layout(
            title="Concurrent Operations and Queue Sizes",
            xaxis_title="Time",
            yaxis_title="Count",
            hovermode="x unified",
            template="plotly_white",
        )

        return json.loads(fig.to_json())

    async def _create_scalability_scores_chart(self) -> Dict[str, Any]:
        """Create scalability scores chart."""
        scalability_scores = (
            await self.metrics_collector._calculate_scalability_scores()
        )

        if not scalability_scores:
            return {"data": [], "layout": {"title": "No scalability data available"}}

        fig = go.Figure(
            data=[
                go.Bar(
                    x=list(scalability_scores.keys()),
                    y=list(scalability_scores.values()),
                    marker_color=[
                        "green" if score >= 0.8 else "yellow" if score >= 0.6 else "red"
                        for score in scalability_scores.values()
                    ],
                )
            ]
        )

        fig.update_layout(
            title="Component Scalability Scores",
            xaxis_title="Component",
            yaxis_title="Scalability Score",
            yaxis=dict(range=[0, 1]),
            template="plotly_white",
        )

        return json.loads(fig.to_json())

    async def _create_alert_trend_chart(self) -> Dict[str, Any]:
        """Create alert trend chart."""
        # Group alerts by hour for the last 24 hours
        now = datetime.utcnow()
        hours = [
            (now - timedelta(hours=i)).replace(minute=0, second=0, microsecond=0)
            for i in range(24, 0, -1)
        ]

        alert_counts = {hour: {"WARNING": 0, "CRITICAL": 0} for hour in hours}

        for alert in self.metrics_collector.alert_history:
            alert_hour = alert.timestamp.replace(minute=0, second=0, microsecond=0)
            if alert_hour in alert_counts:
                alert_counts[alert_hour][alert.severity] += 1

        fig = go.Figure()

        # Warning alerts
        fig.add_trace(
            go.Scatter(
                x=list(alert_counts.keys()),
                y=[counts["WARNING"] for counts in alert_counts.values()],
                mode="lines+markers",
                name="Warning Alerts",
                line=dict(color="orange", width=2),
            )
        )

        # Critical alerts
        fig.add_trace(
            go.Scatter(
                x=list(alert_counts.keys()),
                y=[counts["CRITICAL"] for counts in alert_counts.values()],
                mode="lines+markers",
                name="Critical Alerts",
                line=dict(color="red", width=2),
            )
        )

        fig.update_layout(
            title="Alert Trend (Last 24 Hours)",
            xaxis_title="Time",
            yaxis_title="Alert Count",
            hovermode="x unified",
            template="plotly_white",
        )

        return json.loads(fig.to_json())

    async def _get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary for the dashboard."""
        active_alerts = [
            alert
            for alert in self.metrics_collector.active_alerts.values()
            if not alert.resolved
        ]

        recent_alerts = list(self.metrics_collector.alert_history)[-10:]

        return {
            "active_count": len(active_alerts),
            "total_count": len(self.metrics_collector.alert_history),
            "by_severity": self.metrics_collector._count_alerts_by_severity(),
            "recent_alerts": [
                {
                    "alert_id": alert.alert_id,
                    "component": alert.component_name,
                    "severity": alert.severity,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "acknowledged": alert.acknowledged,
                    "resolved": alert.resolved,
                }
                for alert in recent_alerts
            ],
        }

    async def _get_component_health_overview(self) -> Dict[str, Any]:
        """Get component health overview."""
        health_overview = {}

        for component_name in self.metrics_collector.monitored_components.keys():
            # Determine overall health status
            status = "healthy"
            issues = []

            # Check latency
            if component_name in self.metrics_collector.latency_metrics:
                latest_latency = self.metrics_collector.latency_metrics[component_name]
                if (
                    latest_latency
                    and latest_latency[-1].p95_latency_ms
                    > self.metrics_collector.thresholds.latency_warning_ms
                ):
                    status = "degraded" if status == "healthy" else status
                    issues.append("High latency")

            # Check throughput
            if component_name in self.metrics_collector.throughput_metrics:
                latest_throughput = self.metrics_collector.throughput_metrics[
                    component_name
                ]
                if (
                    latest_throughput
                    and latest_throughput[-1].operations_per_second
                    < self.metrics_collector.thresholds.throughput_warning_ops_per_second
                ):
                    status = "degraded" if status == "healthy" else status
                    issues.append("Low throughput")

            # Check resource utilization
            if component_name in self.metrics_collector.resource_metrics:
                latest_resource = self.metrics_collector.resource_metrics[
                    component_name
                ]
                if latest_resource:
                    if (
                        latest_resource[-1].cpu_percent
                        > self.metrics_collector.thresholds.cpu_warning_percent
                    ):
                        status = "degraded" if status == "healthy" else status
                        issues.append("High CPU usage")
                    if (
                        latest_resource[-1].memory_percent
                        > self.metrics_collector.thresholds.memory_warning_percent
                    ):
                        status = "degraded" if status == "healthy" else status
                        issues.append("High memory usage")

            health_overview[component_name] = {
                "status": status,
                "issues": issues,
                "last_updated": datetime.utcnow().isoformat(),
            }

        return health_overview

    async def _get_performance_trends(self) -> Dict[str, Any]:
        """Get performance trends analysis."""
        trends = {}

        # Analyze trends for each component
        for component_name in self.metrics_collector.monitored_components.keys():
            component_trends = {}

            # Latency trend
            if component_name in self.metrics_collector.latency_metrics:
                metrics_queue = self.metrics_collector.latency_metrics[component_name]
                if len(metrics_queue) >= 5:
                    recent_latencies = [
                        m.p95_latency_ms for m in list(metrics_queue)[-10:]
                    ]
                    trend_direction = (
                        "increasing"
                        if recent_latencies[-1] > recent_latencies[0]
                        else "decreasing"
                    )
                    component_trends["latency"] = {
                        "direction": trend_direction,
                        "change_percent": (
                            (recent_latencies[-1] - recent_latencies[0])
                            / recent_latencies[0]
                        )
                        * 100,
                    }

            # Throughput trend
            if component_name in self.metrics_collector.throughput_metrics:
                metrics_queue = self.metrics_collector.throughput_metrics[
                    component_name
                ]
                if len(metrics_queue) >= 5:
                    recent_throughputs = [
                        m.operations_per_second for m in list(metrics_queue)[-10:]
                    ]
                    trend_direction = (
                        "increasing"
                        if recent_throughputs[-1] > recent_throughputs[0]
                        else "decreasing"
                    )
                    component_trends["throughput"] = {
                        "direction": trend_direction,
                        "change_percent": (
                            (recent_throughputs[-1] - recent_throughputs[0])
                            / recent_throughputs[0]
                        )
                        * 100,
                    }

            if component_trends:
                trends[component_name] = component_trends

        return trends

    async def _get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        # Count healthy vs unhealthy components
        component_health = await self._get_component_health_overview()

        healthy_count = sum(
            1 for health in component_health.values() if health["status"] == "healthy"
        )
        total_count = len(component_health)

        # Determine overall status
        if total_count == 0:
            overall_status = "unknown"
        elif healthy_count == total_count:
            overall_status = "healthy"
        elif healthy_count >= total_count * 0.8:
            overall_status = "mostly_healthy"
        elif healthy_count >= total_count * 0.5:
            overall_status = "degraded"
        else:
            overall_status = "critical"

        # Get active alert counts
        alert_counts = self.metrics_collector._count_alerts_by_severity()

        return {
            "overall_status": overall_status,
            "healthy_components": healthy_count,
            "total_components": total_count,
            "monitoring_active": self.metrics_collector.monitoring_active,
            "active_alerts": sum(alert_counts.values()),
            "critical_alerts": alert_counts.get("CRITICAL", 0),
            "last_updated": datetime.utcnow().isoformat(),
        }

    def get_dashboard_html(self) -> str:
        """Get HTML for the dashboard interface."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>ACGS Scalability Dashboard</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
                .header { background-color: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
                .dashboard-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
                .metric-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .chart-container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
                .status-healthy { color: #27ae60; }
                .status-degraded { color: #f39c12; }
                .status-critical { color: #e74c3c; }
                .alert-item { padding: 10px; margin: 5px 0; border-left: 4px solid #3498db; background: #ecf0f1; }
                .alert-warning { border-color: #f39c12; }
                .alert-critical { border-color: #e74c3c; }
                #status { font-size: 18px; font-weight: bold; }
                .refresh-indicator { position: fixed; top: 20px; right: 20px; padding: 10px; background: #3498db; color: white; border-radius: 4px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>ACGS Scalability Dashboard</h1>
                <div id="status">Loading...</div>
            </div>
            
            <div class="refresh-indicator" id="refreshIndicator" style="display: none;">
                Updating...
            </div>
            
            <div class="dashboard-grid">
                <div class="metric-card">
                    <h3>System Status</h3>
                    <div id="systemStatus">Loading...</div>
                </div>
                
                <div class="metric-card">
                    <h3>Component Health</h3>
                    <div id="componentHealth">Loading...</div>
                </div>
            </div>
            
            <div class="chart-container">
                <div id="latencyChart"></div>
            </div>
            
            <div class="chart-container">
                <div id="throughputChart"></div>
            </div>
            
            <div class="chart-container">
                <div id="resourceChart"></div>
            </div>
            
            <div class="chart-container">
                <div id="scalabilityScoresChart"></div>
            </div>
            
            <div class="metric-card">
                <h3>Recent Alerts</h3>
                <div id="recentAlerts">Loading...</div>
            </div>
            
            <script>
                let ws = null;
                
                function connectWebSocket() {
                    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                    const wsUrl = protocol + '//' + window.location.host + '/ws/scalability';
                    
                    ws = new WebSocket(wsUrl);
                    
                    ws.onopen = function() {
                        console.log('WebSocket connected');
                        document.getElementById('status').innerHTML = '<span class="status-healthy">Connected</span>';
                    };
                    
                    ws.onmessage = function(event) {
                        const data = JSON.parse(event.data);
                        updateDashboard(data);
                        
                        // Show refresh indicator briefly
                        const indicator = document.getElementById('refreshIndicator');
                        indicator.style.display = 'block';
                        setTimeout(() => { indicator.style.display = 'none'; }, 1000);
                    };
                    
                    ws.onclose = function() {
                        console.log('WebSocket disconnected');
                        document.getElementById('status').innerHTML = '<span class="status-critical">Disconnected</span>';
                        // Reconnect after 5 seconds
                        setTimeout(connectWebSocket, 5000);
                    };
                    
                    ws.onerror = function(error) {
                        console.error('WebSocket error:', error);
                        document.getElementById('status').innerHTML = '<span class="status-critical">Error</span>';
                    };
                }
                
                function updateDashboard(data) {
                    // Update system status
                    updateSystemStatus(data.system_status);
                    
                    // Update component health
                    updateComponentHealth(data.component_health);
                    
                    // Update charts
                    if (data.charts) {
                        updateCharts(data.charts);
                    }
                    
                    // Update alerts
                    updateAlerts(data.alerts);
                }
                
                function updateSystemStatus(status) {
                    const statusEl = document.getElementById('systemStatus');
                    const statusClass = status.overall_status === 'healthy' ? 'status-healthy' : 
                                       status.overall_status === 'degraded' ? 'status-degraded' : 'status-critical';
                    
                    statusEl.innerHTML = `
                        <div class="${statusClass}">Status: ${status.overall_status.toUpperCase()}</div>
                        <div>Healthy Components: ${status.healthy_components}/${status.total_components}</div>
                        <div>Active Alerts: ${status.active_alerts}</div>
                        <div>Critical Alerts: ${status.critical_alerts}</div>
                    `;
                }
                
                function updateComponentHealth(health) {
                    const healthEl = document.getElementById('componentHealth');
                    let html = '';
                    
                    for (const [component, info] of Object.entries(health)) {
                        const statusClass = info.status === 'healthy' ? 'status-healthy' : 
                                           info.status === 'degraded' ? 'status-degraded' : 'status-critical';
                        
                        html += `
                            <div>
                                <strong>${component}</strong>: <span class="${statusClass}">${info.status}</span>
                                ${info.issues.length > 0 ? '<br><small>' + info.issues.join(', ') + '</small>' : ''}
                            </div>
                        `;
                    }
                    
                    healthEl.innerHTML = html || 'No components registered';
                }
                
                function updateCharts(charts) {
                    if (charts.latency_chart) {
                        Plotly.react('latencyChart', charts.latency_chart.data, charts.latency_chart.layout);
                    }
                    
                    if (charts.throughput_chart) {
                        Plotly.react('throughputChart', charts.throughput_chart.data, charts.throughput_chart.layout);
                    }
                    
                    if (charts.resource_chart) {
                        Plotly.react('resourceChart', charts.resource_chart.data, charts.resource_chart.layout);
                    }
                    
                    if (charts.scalability_scores_chart) {
                        Plotly.react('scalabilityScoresChart', charts.scalability_scores_chart.data, charts.scalability_scores_chart.layout);
                    }
                }
                
                function updateAlerts(alerts) {
                    const alertsEl = document.getElementById('recentAlerts');
                    let html = '';
                    
                    if (alerts.recent_alerts && alerts.recent_alerts.length > 0) {
                        for (const alert of alerts.recent_alerts) {
                            const alertClass = alert.severity === 'WARNING' ? 'alert-warning' : 'alert-critical';
                            const timestamp = new Date(alert.timestamp).toLocaleString();
                            
                            html += `
                                <div class="alert-item ${alertClass}">
                                    <strong>${alert.component}</strong> - ${alert.severity}<br>
                                    ${alert.message}<br>
                                    <small>${timestamp}</small>
                                </div>
                            `;
                        }
                    } else {
                        html = '<div>No recent alerts</div>';
                    }
                    
                    alertsEl.innerHTML = html;
                }
                
                // Initialize WebSocket connection
                connectWebSocket();
            </script>
        </body>
        </html>
        """


# Global dashboard instance
_scalability_dashboard: Optional[ScalabilityDashboard] = None


async def get_scalability_dashboard() -> ScalabilityDashboard:
    """Get or create the global scalability dashboard."""
    global _scalability_dashboard
    if _scalability_dashboard is None:
        metrics_collector = await get_scalability_metrics_collector()
        _scalability_dashboard = ScalabilityDashboard(metrics_collector)
    return _scalability_dashboard


async def close_scalability_dashboard() -> None:
    """Close the global scalability dashboard."""
    global _scalability_dashboard
    if _scalability_dashboard is not None:
        await _scalability_dashboard.stop_dashboard()
        _scalability_dashboard = None
