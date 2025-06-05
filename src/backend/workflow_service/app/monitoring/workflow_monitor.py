"""
Enhanced Workflow Monitoring and Alerting System
Provides real-time monitoring, metrics collection, and intelligent alerting
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

@dataclass
class Alert:
    id: str
    severity: AlertSeverity
    title: str
    description: str
    workflow_id: Optional[str]
    service: Optional[str]
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None

@dataclass
class Metric:
    name: str
    type: MetricType
    value: float
    timestamp: datetime
    labels: Dict[str, str] = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = {}

class WorkflowMonitor:
    """
    Enhanced monitoring system for ACGS-PGP workflows
    """
    
    def __init__(self):
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.alerts: Dict[str, Alert] = {}
        self.alert_handlers: List[Callable] = []
        self.thresholds: Dict[str, Dict[str, Any]] = {}
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}
        self._initialize_thresholds()
    
    def _initialize_thresholds(self):
        """Initialize monitoring thresholds"""
        
        self.thresholds = {
            "workflow_execution_time": {
                "warning": 300,  # 5 minutes
                "critical": 900  # 15 minutes
            },
            "step_failure_rate": {
                "warning": 0.1,  # 10%
                "critical": 0.25  # 25%
            },
            "service_response_time": {
                "warning": 5.0,  # 5 seconds
                "critical": 10.0  # 10 seconds
            },
            "constitutional_violations": {
                "warning": 1,
                "critical": 5
            },
            "system_resource_usage": {
                "cpu_warning": 80.0,  # 80%
                "cpu_critical": 95.0,  # 95%
                "memory_warning": 85.0,  # 85%
                "memory_critical": 95.0  # 95%
            }
        }
    
    def record_metric(self, name: str, value: float, metric_type: MetricType, labels: Dict[str, str] = None):
        """Record a metric value"""
        
        metric = Metric(
            name=name,
            type=metric_type,
            value=value,
            timestamp=datetime.utcnow(),
            labels=labels or {}
        )
        
        self.metrics[name].append(metric)
        
        # Check for threshold violations
        self._check_thresholds(name, value, labels)
    
    def _check_thresholds(self, metric_name: str, value: float, labels: Dict[str, str]):
        """Check if metric value violates thresholds"""
        
        if metric_name not in self.thresholds:
            return
        
        thresholds = self.thresholds[metric_name]
        
        # Check critical threshold
        if "critical" in thresholds and value >= thresholds["critical"]:
            self._create_alert(
                severity=AlertSeverity.CRITICAL,
                title=f"Critical threshold exceeded: {metric_name}",
                description=f"Metric {metric_name} value {value} exceeds critical threshold {thresholds['critical']}",
                metadata={"metric": metric_name, "value": value, "threshold": thresholds["critical"], "labels": labels}
            )
        
        # Check warning threshold
        elif "warning" in thresholds and value >= thresholds["warning"]:
            self._create_alert(
                severity=AlertSeverity.HIGH,
                title=f"Warning threshold exceeded: {metric_name}",
                description=f"Metric {metric_name} value {value} exceeds warning threshold {thresholds['warning']}",
                metadata={"metric": metric_name, "value": value, "threshold": thresholds["warning"], "labels": labels}
            )
    
    def _create_alert(self, severity: AlertSeverity, title: str, description: str, 
                     workflow_id: str = None, service: str = None, metadata: Dict[str, Any] = None):
        """Create and dispatch an alert"""
        
        alert_id = f"{int(time.time())}_{hash(title + description) % 10000}"
        
        alert = Alert(
            id=alert_id,
            severity=severity,
            title=title,
            description=description,
            workflow_id=workflow_id,
            service=service,
            timestamp=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        self.alerts[alert_id] = alert
        
        # Dispatch to alert handlers
        for handler in self.alert_handlers:
            try:
                asyncio.create_task(handler(alert))
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")
        
        logger.warning(f"Alert created: {title}")
    
    def register_alert_handler(self, handler: Callable):
        """Register an alert handler"""
        self.alert_handlers.append(handler)
    
    async def monitor_workflow(self, workflow_id: str, workflow_engine):
        """Monitor a specific workflow"""
        
        start_time = time.time()
        
        while True:
            try:
                status = workflow_engine.get_workflow_status(workflow_id)
                
                if not status:
                    break
                
                # Record workflow metrics
                self.record_metric(
                    "workflow_active",
                    1.0,
                    MetricType.GAUGE,
                    {"workflow_id": workflow_id, "type": status["type"]}
                )
                
                # Check execution time
                execution_time = time.time() - start_time
                self.record_metric(
                    "workflow_execution_time",
                    execution_time,
                    MetricType.TIMER,
                    {"workflow_id": workflow_id}
                )
                
                # Check for failed steps
                failed_steps = [s for s in status["steps"] if s["status"] == "failed"]
                if failed_steps:
                    self._create_alert(
                        severity=AlertSeverity.HIGH,
                        title=f"Workflow step failure: {workflow_id}",
                        description=f"Workflow {workflow_id} has {len(failed_steps)} failed steps",
                        workflow_id=workflow_id,
                        metadata={"failed_steps": failed_steps}
                    )
                
                # Break if workflow completed or failed
                if status["status"] in ["completed", "failed", "cancelled"]:
                    break
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring workflow {workflow_id}: {e}")
                break
        
        # Cleanup
        if workflow_id in self.monitoring_tasks:
            del self.monitoring_tasks[workflow_id]
    
    async def monitor_service_health(self, service_name: str, health_endpoint: str):
        """Monitor service health continuously"""
        
        consecutive_failures = 0
        
        while True:
            try:
                start_time = time.time()
                
                # Simulate health check (replace with actual HTTP call)
                # response = await http_client.get(health_endpoint)
                response_time = time.time() - start_time
                
                # Record response time
                self.record_metric(
                    "service_response_time",
                    response_time,
                    MetricType.TIMER,
                    {"service": service_name}
                )
                
                # Record service availability
                self.record_metric(
                    "service_availability",
                    1.0,
                    MetricType.GAUGE,
                    {"service": service_name}
                )
                
                consecutive_failures = 0
                
            except Exception as e:
                consecutive_failures += 1
                
                # Record service unavailability
                self.record_metric(
                    "service_availability",
                    0.0,
                    MetricType.GAUGE,
                    {"service": service_name}
                )
                
                if consecutive_failures >= 3:
                    self._create_alert(
                        severity=AlertSeverity.CRITICAL,
                        title=f"Service {service_name} is down",
                        description=f"Service {service_name} has been unavailable for {consecutive_failures} consecutive checks",
                        service=service_name,
                        metadata={"consecutive_failures": consecutive_failures, "error": str(e)}
                    )
                
                logger.error(f"Health check failed for {service_name}: {e}")
            
            await asyncio.sleep(30)  # Check every 30 seconds
    
    def start_workflow_monitoring(self, workflow_id: str, workflow_engine):
        """Start monitoring a workflow"""
        
        if workflow_id not in self.monitoring_tasks:
            task = asyncio.create_task(self.monitor_workflow(workflow_id, workflow_engine))
            self.monitoring_tasks[workflow_id] = task
    
    def stop_workflow_monitoring(self, workflow_id: str):
        """Stop monitoring a workflow"""
        
        if workflow_id in self.monitoring_tasks:
            self.monitoring_tasks[workflow_id].cancel()
            del self.monitoring_tasks[workflow_id]
    
    def get_metrics(self, metric_name: str, time_range: timedelta = None) -> List[Dict[str, Any]]:
        """Get metrics for a specific name and time range"""
        
        if metric_name not in self.metrics:
            return []
        
        metrics = list(self.metrics[metric_name])
        
        if time_range:
            cutoff_time = datetime.utcnow() - time_range
            metrics = [m for m in metrics if m.timestamp >= cutoff_time]
        
        return [asdict(m) for m in metrics]
    
    def get_alerts(self, severity: AlertSeverity = None, resolved: bool = None) -> List[Dict[str, Any]]:
        """Get alerts with optional filtering"""
        
        alerts = list(self.alerts.values())
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        if resolved is not None:
            alerts = [a for a in alerts if a.resolved == resolved]
        
        return [asdict(a) for a in sorted(alerts, key=lambda x: x.timestamp, reverse=True)]
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Mark an alert as resolved"""
        
        if alert_id in self.alerts:
            self.alerts[alert_id].resolved = True
            self.alerts[alert_id].resolved_at = datetime.utcnow()
            return True
        
        return False
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        
        now = datetime.utcnow()
        last_hour = now - timedelta(hours=1)
        last_day = now - timedelta(days=1)
        
        # Active alerts
        active_alerts = [a for a in self.alerts.values() if not a.resolved]
        
        # Recent metrics summary
        recent_metrics = {}
        for metric_name, metric_list in self.metrics.items():
            recent = [m for m in metric_list if m.timestamp >= last_hour]
            if recent:
                recent_metrics[metric_name] = {
                    "count": len(recent),
                    "avg": sum(m.value for m in recent) / len(recent),
                    "max": max(m.value for m in recent),
                    "min": min(m.value for m in recent)
                }
        
        return {
            "timestamp": now.isoformat(),
            "alerts": {
                "active": len(active_alerts),
                "critical": len([a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]),
                "high": len([a for a in active_alerts if a.severity == AlertSeverity.HIGH]),
                "recent": [asdict(a) for a in sorted(active_alerts, key=lambda x: x.timestamp, reverse=True)[:10]]
            },
            "metrics": recent_metrics,
            "monitoring": {
                "active_workflows": len(self.monitoring_tasks),
                "total_metrics": sum(len(m) for m in self.metrics.values())
            }
        }

# Global monitor instance
workflow_monitor = WorkflowMonitor()

# Example alert handlers
async def email_alert_handler(alert: Alert):
    """Send email alerts for critical issues"""
    if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]:
        # Implement email sending logic
        logger.info(f"Email alert sent: {alert.title}")

async def slack_alert_handler(alert: Alert):
    """Send Slack notifications"""
    # Implement Slack webhook logic
    logger.info(f"Slack alert sent: {alert.title}")

async def constitutional_violation_handler(alert: Alert):
    """Special handler for constitutional violations"""
    if alert.metadata and "constitutional_violation" in alert.metadata:
        # Implement special constitutional violation handling
        logger.critical(f"Constitutional violation detected: {alert.description}")

# Register default alert handlers
workflow_monitor.register_alert_handler(email_alert_handler)
workflow_monitor.register_alert_handler(slack_alert_handler)
workflow_monitor.register_alert_handler(constitutional_violation_handler)
