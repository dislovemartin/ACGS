"""
Enhanced Monitoring Service for ACGS Phase 3

Provides comprehensive monitoring with Prometheus metrics, Grafana dashboards,
AlertManager integration, and distributed tracing capabilities.
"""

import asyncio
import time
import psutil
import os
import httpx
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json

from prometheus_client import (
    Counter, Histogram, Gauge, Summary, Info,
    CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
)
import structlog

from .cache_manager import get_cache_manager
from .performance_monitor import (
    get_performance_monitor,
    ERROR_RATE,
    THROUGHPUT,
)

logger = structlog.get_logger(__name__)


@dataclass
class AlertThreshold:
    """Alert threshold configuration."""
    metric_name: str
    threshold_value: float
    comparison: str  # 'gt', 'lt', 'eq'
    duration_seconds: int
    severity: str  # 'critical', 'warning', 'info'
    description: str


@dataclass
class PerformanceMetrics:
    """Performance metrics snapshot."""
    timestamp: datetime
    policy_decision_latency_ms: float
    cache_hit_rate: float
    concurrent_requests: int
    memory_usage_mb: float
    cpu_usage_percent: float
    error_rate: float


class PrometheusMetrics:
    """Prometheus metrics collection for ACGS."""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry or CollectorRegistry()
        self._initialize_metrics()
    
    def _initialize_metrics(self):
        """Initialize Prometheus metrics."""
        
        # Policy decision metrics
        self.policy_decision_latency = Histogram(
            'acgs_policy_decision_latency_seconds',
            'Time spent on policy decisions',
            ['endpoint', 'policy_type', 'result'],
            registry=self.registry,
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
        )
        
        self.policy_decisions_total = Counter(
            'acgs_policy_decisions_total',
            'Total number of policy decisions',
            ['endpoint', 'policy_type', 'result'],
            registry=self.registry
        )
        
        # Cache metrics
        self.cache_hit_rate = Gauge(
            'acgs_cache_hit_rate',
            'Cache hit rate percentage',
            ['cache_type'],
            registry=self.registry
        )
        
        self.cache_operations_total = Counter(
            'acgs_cache_operations_total',
            'Total cache operations',
            ['cache_type', 'operation', 'result'],
            registry=self.registry
        )
        
        self.cache_size_bytes = Gauge(
            'acgs_cache_size_bytes',
            'Cache size in bytes',
            ['cache_type'],
            registry=self.registry
        )
        
        # System resource metrics
        self.system_memory_usage = Gauge(
            'acgs_system_memory_usage_bytes',
            'System memory usage',
            registry=self.registry
        )
        
        self.system_cpu_usage = Gauge(
            'acgs_system_cpu_usage_percent',
            'System CPU usage percentage',
            registry=self.registry
        )
        
        self.concurrent_requests = Gauge(
            'acgs_concurrent_requests',
            'Number of concurrent requests',
            registry=self.registry
        )
        
        # Error metrics
        self.errors_total = Counter(
            'acgs_errors_total',
            'Total number of errors',
            ['error_type', 'component'],
            registry=self.registry
        )
        
        # Security metrics
        self.security_events_total = Counter(
            'acgs_security_events_total',
            'Total security events',
            ['event_type', 'severity'],
            registry=self.registry
        )
        
        self.authentication_attempts_total = Counter(
            'acgs_authentication_attempts_total',
            'Total authentication attempts',
            ['result'],
            registry=self.registry
        )
        
        # Governance synthesis metrics
        self.governance_synthesis_latency = Histogram(
            'acgs_governance_synthesis_latency_seconds',
            'Time spent on governance synthesis',
            ['synthesis_type', 'complexity'],
            registry=self.registry
        )
        
        self.governance_rules_active = Gauge(
            'acgs_governance_rules_active',
            'Number of active governance rules',
            ['category'],
            registry=self.registry
        )


class AlertManager:
    """Alert management for ACGS monitoring."""
    
    def __init__(self):
        self.thresholds: List[AlertThreshold] = []
        self.active_alerts: Dict[str, Dict[str, Any]] = {}
        self.alert_history: List[Dict[str, Any]] = []
        self._initialize_default_thresholds()
    
    def _initialize_default_thresholds(self):
        """Initialize default alert thresholds."""
        self.thresholds = [
            AlertThreshold(
                metric_name='policy_decision_latency_ms',
                threshold_value=50.0,
                comparison='gt',
                duration_seconds=60,
                severity='warning',
                description='Policy decision latency exceeds 50ms'
            ),
            AlertThreshold(
                metric_name='cache_hit_rate',
                threshold_value=0.7,
                comparison='lt',
                duration_seconds=300,
                severity='warning',
                description='Cache hit rate below 70%'
            ),
            AlertThreshold(
                metric_name='memory_usage_mb',
                threshold_value=1024,
                comparison='gt',
                duration_seconds=120,
                severity='critical',
                description='Memory usage exceeds 1GB'
            ),
            AlertThreshold(
                metric_name='cpu_usage_percent',
                threshold_value=80.0,
                comparison='gt',
                duration_seconds=180,
                severity='warning',
                description='CPU usage exceeds 80%'
            ),
            AlertThreshold(
                metric_name='error_rate',
                threshold_value=0.05,
                comparison='gt',
                duration_seconds=60,
                severity='critical',
                description='Error rate exceeds 5%'
            )
        ]
    
    def check_thresholds(self, metrics: PerformanceMetrics) -> List[Dict[str, Any]]:
        """Check metrics against alert thresholds."""
        triggered_alerts = []
        
        for threshold in self.thresholds:
            metric_value = getattr(metrics, threshold.metric_name, None)
            if metric_value is None:
                continue
            
            alert_triggered = False
            
            if threshold.comparison == 'gt' and metric_value > threshold.threshold_value:
                alert_triggered = True
            elif threshold.comparison == 'lt' and metric_value < threshold.threshold_value:
                alert_triggered = True
            elif threshold.comparison == 'eq' and metric_value == threshold.threshold_value:
                alert_triggered = True
            
            if alert_triggered:
                alert = {
                    'metric_name': threshold.metric_name,
                    'current_value': metric_value,
                    'threshold_value': threshold.threshold_value,
                    'severity': threshold.severity,
                    'description': threshold.description,
                    'timestamp': datetime.now().isoformat()
                }
                triggered_alerts.append(alert)
                
                # Track active alerts
                alert_key = f"{threshold.metric_name}_{threshold.severity}"
                self.active_alerts[alert_key] = alert
        
        return triggered_alerts


class MonitoringService:
    """Comprehensive monitoring service for ACGS."""
    
    def __init__(self):
        self.metrics = PrometheusMetrics()
        self.alert_manager = AlertManager()
        self.performance_history: List[PerformanceMetrics] = []
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start_monitoring(self, interval_seconds: int = 30):
        """Start continuous monitoring."""
        if self._running:
            return
        
        self._running = True
        self._monitoring_task = asyncio.create_task(
            self._monitoring_loop(interval_seconds)
        )
        logger.info("Monitoring service started", interval=interval_seconds)
    
    async def stop_monitoring(self):
        """Stop continuous monitoring."""
        self._running = False
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Monitoring service stopped")
    
    async def _monitoring_loop(self, interval_seconds: int):
        """Main monitoring loop."""
        while self._running:
            try:
                # Collect performance metrics
                metrics = await self._collect_performance_metrics()
                
                # Update Prometheus metrics
                self._update_prometheus_metrics(metrics)
                
                # Check alert thresholds
                alerts = self.alert_manager.check_thresholds(metrics)
                if alerts:
                    await self._handle_alerts(alerts)
                
                # Store metrics history
                self.performance_history.append(metrics)
                
                # Keep only last 1000 metrics (configurable)
                if len(self.performance_history) > 1000:
                    self.performance_history = self.performance_history[-1000:]
                
                await asyncio.sleep(interval_seconds)
                
            except Exception as e:
                logger.error("Monitoring loop error", error=str(e))
                await asyncio.sleep(interval_seconds)
    
    async def _collect_performance_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics."""
        
        # Get system metrics
        memory_info = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Integrate with cache manager to obtain cache hit rate
        cache_hit_rate = 0.0
        try:
            cache_manager = await get_cache_manager()
            cache_stats = await cache_manager.get_cache_stats()
            hit_rates = []
            for stats in cache_stats.values():
                mt_stats = stats.get("multi_tier")
                if mt_stats:
                    hit_rates.append(mt_stats.hit_rate)
            if hit_rates:
                cache_hit_rate = sum(hit_rates) / len(hit_rates)
        except Exception as e:
            logger.warning("Failed to get cache stats", error=str(e))

        # Integrate with performance monitor for latency and active requests
        policy_latency_ms = 0.0
        concurrent_requests = 0
        error_rate = 0.0
        try:
            monitor = get_performance_monitor()
            profile = monitor.profiler.get_latency_profile(
                "opa_policy_evaluation:policy_decision"
            )
            if profile:
                policy_latency_ms = profile.avg_latency_ms
            concurrent_requests = monitor.active_requests

            errors = sum(
                s.value
                for metric in ERROR_RATE.collect()
                for s in metric.samples
                if s.name.endswith("_total")
            )
            requests = sum(
                s.value
                for metric in THROUGHPUT.collect()
                for s in metric.samples
                if s.name.endswith("_total")
            )
            error_rate = errors / requests if requests > 0 else 0.0
        except Exception as e:
            logger.warning("Failed to get performance metrics", error=str(e))

        return PerformanceMetrics(
            timestamp=datetime.now(),
            policy_decision_latency_ms=policy_latency_ms,
            cache_hit_rate=cache_hit_rate,
            concurrent_requests=concurrent_requests,
            memory_usage_mb=memory_info.used / (1024 * 1024),
            cpu_usage_percent=cpu_percent,
            error_rate=error_rate,
        )
    
    def _update_prometheus_metrics(self, metrics: PerformanceMetrics):
        """Update Prometheus metrics with current values."""
        
        # Update system metrics
        self.metrics.system_memory_usage.set(metrics.memory_usage_mb * 1024 * 1024)
        self.metrics.system_cpu_usage.set(metrics.cpu_usage_percent)
        self.metrics.concurrent_requests.set(metrics.concurrent_requests)
        
        # Update cache metrics (placeholder)
        self.metrics.cache_hit_rate.labels(cache_type='multi_tier').set(metrics.cache_hit_rate)
    
    async def _handle_alerts(self, alerts: List[Dict[str, Any]]):
        """Handle triggered alerts."""
        for alert in alerts:
            logger.warning(
                "Alert triggered",
                metric=alert['metric_name'],
                value=alert['current_value'],
                threshold=alert['threshold_value'],
                severity=alert['severity']
            )
            
            # Forward alerts to external alerting systems
            slack_url = os.getenv("SLACK_WEBHOOK_URL")
            if slack_url:
                try:
                    async with httpx.AsyncClient() as client:
                        await client.post(
                            slack_url,
                            json={"text": f"ACGS Alert: {alert['description']}"},
                        )
                except Exception as e:
                    logger.error("Failed to send Slack alert", error=str(e))
    
    def get_metrics_export(self) -> str:
        """Get Prometheus metrics export."""
        return generate_latest(self.metrics.registry).decode('utf-8')
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        if not self.performance_history:
            return {}
        
        recent_metrics = self.performance_history[-10:]  # Last 10 measurements
        
        return {
            'current_metrics': asdict(self.performance_history[-1]) if self.performance_history else {},
            'average_latency_ms': sum(m.policy_decision_latency_ms for m in recent_metrics) / len(recent_metrics),
            'average_cache_hit_rate': sum(m.cache_hit_rate for m in recent_metrics) / len(recent_metrics),
            'average_memory_usage_mb': sum(m.memory_usage_mb for m in recent_metrics) / len(recent_metrics),
            'average_cpu_usage_percent': sum(m.cpu_usage_percent for m in recent_metrics) / len(recent_metrics),
            'active_alerts': list(self.alert_manager.active_alerts.values()),
            'metrics_count': len(self.performance_history)
        }


# Global monitoring service instance
_monitoring_service: Optional[MonitoringService] = None


async def get_monitoring_service() -> MonitoringService:
    """Get global monitoring service instance."""
    global _monitoring_service
    
    if _monitoring_service is None:
        _monitoring_service = MonitoringService()
        await _monitoring_service.start_monitoring()
    
    return _monitoring_service


async def shutdown_monitoring_service():
    """Shutdown global monitoring service."""
    global _monitoring_service
    
    if _monitoring_service:
        await _monitoring_service.stop_monitoring()
        _monitoring_service = None
