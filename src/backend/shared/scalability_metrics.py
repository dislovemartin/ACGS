"""
Comprehensive Scalability Metrics System

This module implements the scalability metrics collection framework to monitor
system scalability and performance across all ACGS components, providing
real-time insights, dashboards, and alerting capabilities.

Key Features:
- Centralized scalability metrics collection
- Latency, throughput, and resource utilization monitoring
- Real-time monitoring dashboards integration
- Automated alerting system for performance degradation
- Trend analysis and predictive scaling recommendations
"""

import asyncio
import json
import logging
import statistics
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import psutil

try:
    from prometheus_client import (
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        generate_latest,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class ScalabilityMetricType(Enum):
    """Types of scalability metrics."""

    LATENCY = "latency"
    THROUGHPUT = "throughput"
    RESOURCE_UTILIZATION = "resource_utilization"
    CONCURRENT_OPERATIONS = "concurrent_operations"
    ERROR_RATE = "error_rate"
    AVAILABILITY = "availability"


class ComponentScalabilityLevel(Enum):
    """Component scalability performance levels."""

    OPTIMAL = "optimal"
    GOOD = "good"
    DEGRADED = "degraded"
    CRITICAL = "critical"


@dataclass
class LatencyMetrics:
    """Latency measurement metrics."""

    component_name: str
    operation_type: str
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    max_latency_ms: float
    min_latency_ms: float
    average_latency_ms: float
    sample_count: int
    timestamp: datetime


@dataclass
class ThroughputMetrics:
    """Throughput measurement metrics."""

    component_name: str
    operations_per_second: float
    requests_per_minute: float
    data_processed_mb_per_second: float
    peak_throughput: float
    sustained_throughput: float
    capacity_utilization_percent: float
    bottleneck_indicators: List[str]
    timestamp: datetime


@dataclass
class ResourceUtilizationMetrics:
    """Resource utilization metrics."""

    component_name: str
    cpu_percent: float
    memory_percent: float
    disk_io_mb_per_second: float
    network_io_mb_per_second: float
    gpu_utilization_percent: Optional[float]
    connection_pool_utilization_percent: float
    queue_depth: int
    active_threads: int
    timestamp: datetime


@dataclass
class ConcurrentOperationsMetrics:
    """Concurrent operations tracking."""

    component_name: str
    active_operations: int
    max_concurrent_operations: int
    operation_queue_size: int
    wait_time_ms: float
    context_switches_per_second: float
    lock_contention_ms: float
    deadlock_count: int
    timestamp: datetime


@dataclass
class ScalabilityAlert:
    """Scalability performance alert."""

    alert_id: str
    component_name: str
    metric_type: ScalabilityMetricType
    severity: str  # INFO, WARNING, CRITICAL
    threshold_breached: str
    current_value: float
    threshold_value: float
    message: str
    timestamp: datetime
    acknowledged: bool = False
    resolved: bool = False


@dataclass
class ScalabilityThresholds:
    """Configurable thresholds for scalability metrics."""

    latency_warning_ms: float = 1000.0
    latency_critical_ms: float = 5000.0
    throughput_warning_ops_per_second: float = 10.0
    throughput_critical_ops_per_second: float = 5.0
    cpu_warning_percent: float = 80.0
    cpu_critical_percent: float = 95.0
    memory_warning_percent: float = 85.0
    memory_critical_percent: float = 95.0
    error_rate_warning_percent: float = 5.0
    error_rate_critical_percent: float = 15.0
    queue_depth_warning: int = 100
    queue_depth_critical: int = 500


class ScalabilityMetricsCollector:
    """
    Comprehensive scalability metrics collector for all ACGS components.

    Instruments key components to capture latency, throughput, and resource
    utilization metrics; integrates with monitoring dashboards and alerting systems.
    """

    def __init__(
        self,
        thresholds: Optional[ScalabilityThresholds] = None,
        enable_prometheus: bool = True,
        enable_redis_cache: bool = True,
    ):
        """
        Initialize scalability metrics collector.

        Args:
            thresholds: Performance thresholds for alerting
            enable_prometheus: Enable Prometheus metrics export
            enable_redis_cache: Enable Redis for metrics caching
        """
        self.thresholds = thresholds or ScalabilityThresholds()
        self.enable_prometheus = enable_prometheus and PROMETHEUS_AVAILABLE
        self.enable_redis = enable_redis_cache and REDIS_AVAILABLE

        # Metrics storage
        self.latency_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.throughput_metrics: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=1000)
        )
        self.resource_metrics: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=1000)
        )
        self.concurrent_ops_metrics: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=1000)
        )

        # Alerting system
        self.active_alerts: Dict[str, ScalabilityAlert] = {}
        self.alert_history: deque = deque(maxlen=5000)
        self.alert_handlers: List[Callable] = []

        # Monitoring state
        self.monitoring_active = False
        self.collection_interval = 30  # seconds
        self.last_collection_time = datetime.utcnow()

        # Component registration
        self.monitored_components: Dict[str, Dict[str, Any]] = {}

        # Initialize external systems
        self._setup_prometheus_metrics()
        self._setup_redis_connection()

        logger.info("Scalability Metrics Collector initialized")

    def _setup_prometheus_metrics(self) -> None:
        """Setup Prometheus metrics collectors."""
        if not self.enable_prometheus:
            return

        self.registry = CollectorRegistry()
        self.prometheus_metrics = {
            # Latency metrics
            "operation_latency": Histogram(
                "acgs_operation_latency_seconds",
                "Operation latency in seconds",
                ["component", "operation", "percentile"],
                registry=self.registry,
            ),
            # Throughput metrics
            "throughput_ops_per_second": Gauge(
                "acgs_throughput_operations_per_second",
                "Operations per second throughput",
                ["component"],
                registry=self.registry,
            ),
            "throughput_data_mb_per_second": Gauge(
                "acgs_throughput_data_mb_per_second",
                "Data throughput in MB per second",
                ["component"],
                registry=self.registry,
            ),
            # Resource utilization metrics
            "cpu_utilization_percent": Gauge(
                "acgs_cpu_utilization_percent",
                "CPU utilization percentage",
                ["component"],
                registry=self.registry,
            ),
            "memory_utilization_percent": Gauge(
                "acgs_memory_utilization_percent",
                "Memory utilization percentage",
                ["component"],
                registry=self.registry,
            ),
            "disk_io_mb_per_second": Gauge(
                "acgs_disk_io_mb_per_second",
                "Disk I/O in MB per second",
                ["component"],
                registry=self.registry,
            ),
            "network_io_mb_per_second": Gauge(
                "acgs_network_io_mb_per_second",
                "Network I/O in MB per second",
                ["component"],
                registry=self.registry,
            ),
            # Concurrent operations metrics
            "concurrent_operations": Gauge(
                "acgs_concurrent_operations",
                "Number of concurrent operations",
                ["component"],
                registry=self.registry,
            ),
            "operation_queue_size": Gauge(
                "acgs_operation_queue_size",
                "Operation queue size",
                ["component"],
                registry=self.registry,
            ),
            # Alert metrics
            "active_alerts": Gauge(
                "acgs_active_alerts_total",
                "Total number of active alerts",
                ["severity"],
                registry=self.registry,
            ),
            # Scalability score metrics
            "scalability_score": Gauge(
                "acgs_scalability_score",
                "Overall component scalability score",
                ["component"],
                registry=self.registry,
            ),
        }

        logger.debug("Prometheus metrics setup completed")

    def _setup_redis_connection(self) -> None:
        """Setup Redis connection for metrics caching."""
        if not self.enable_redis:
            self.redis_client = None
            return

        try:
            self.redis_client = redis.Redis(
                host="localhost",
                port=6379,
                db=0,
                decode_responses=True,
                socket_timeout=5,
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established for metrics caching")
        except Exception as e:
            logger.warning(f"Redis connection failed, disabling caching: {e}")
            self.redis_client = None
            self.enable_redis = False

    async def start_monitoring(self) -> None:
        """Start continuous scalability monitoring."""
        if self.monitoring_active:
            logger.warning("Scalability monitoring already active")
            return

        self.monitoring_active = True
        logger.info("Started scalability metrics monitoring")

        # Start monitoring loop
        asyncio.create_task(self._monitoring_loop())

    async def stop_monitoring(self) -> None:
        """Stop scalability monitoring."""
        self.monitoring_active = False
        logger.info("Stopped scalability metrics monitoring")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop for real-time metrics collection."""
        while self.monitoring_active:
            try:
                await self._collect_system_metrics()
                await self._update_prometheus_metrics()
                await self._check_scalability_alerts()
                await self._cache_metrics_to_redis()

                self.last_collection_time = datetime.utcnow()
                await asyncio.sleep(self.collection_interval)

            except Exception as e:
                logger.error(f"Error in scalability monitoring loop: {e}")
                await asyncio.sleep(5)  # Brief pause before retrying

    async def register_component(
        self,
        component_name: str,
        component_type: str,
        expected_throughput_ops_per_second: float = None,
        max_latency_ms: float = None,
    ) -> None:
        """
        Register a component for scalability monitoring.

        Args:
            component_name: Unique component identifier
            component_type: Type of component (service, database, etc.)
            expected_throughput_ops_per_second: Expected baseline throughput
            max_latency_ms: Maximum acceptable latency
        """
        self.monitored_components[component_name] = {
            "type": component_type,
            "expected_throughput": expected_throughput_ops_per_second,
            "max_latency": max_latency_ms,
            "registration_time": datetime.utcnow(),
            "status": "active",
        }

        logger.info(f"Registered component for monitoring: {component_name}")

    async def record_latency_metrics(self, metrics: LatencyMetrics) -> None:
        """Record latency metrics for a component."""
        try:
            self.latency_metrics[metrics.component_name].append(metrics)

            # Update Prometheus metrics
            if self.enable_prometheus:
                self.prometheus_metrics["operation_latency"].labels(
                    component=metrics.component_name,
                    operation=metrics.operation_type,
                    percentile="p95",
                ).observe(metrics.p95_latency_ms / 1000.0)

            logger.debug(f"Recorded latency metrics for {metrics.component_name}")

        except Exception as e:
            logger.error(f"Failed to record latency metrics: {e}")

    async def record_throughput_metrics(self, metrics: ThroughputMetrics) -> None:
        """Record throughput metrics for a component."""
        try:
            self.throughput_metrics[metrics.component_name].append(metrics)

            # Update Prometheus metrics
            if self.enable_prometheus:
                self.prometheus_metrics["throughput_ops_per_second"].labels(
                    component=metrics.component_name
                ).set(metrics.operations_per_second)

                self.prometheus_metrics["throughput_data_mb_per_second"].labels(
                    component=metrics.component_name
                ).set(metrics.data_processed_mb_per_second)

            logger.debug(f"Recorded throughput metrics for {metrics.component_name}")

        except Exception as e:
            logger.error(f"Failed to record throughput metrics: {e}")

    async def record_resource_utilization_metrics(
        self, metrics: ResourceUtilizationMetrics
    ) -> None:
        """Record resource utilization metrics for a component."""
        try:
            self.resource_metrics[metrics.component_name].append(metrics)

            # Update Prometheus metrics
            if self.enable_prometheus:
                self.prometheus_metrics["cpu_utilization_percent"].labels(
                    component=metrics.component_name
                ).set(metrics.cpu_percent)

                self.prometheus_metrics["memory_utilization_percent"].labels(
                    component=metrics.component_name
                ).set(metrics.memory_percent)

                self.prometheus_metrics["disk_io_mb_per_second"].labels(
                    component=metrics.component_name
                ).set(metrics.disk_io_mb_per_second)

                self.prometheus_metrics["network_io_mb_per_second"].labels(
                    component=metrics.component_name
                ).set(metrics.network_io_mb_per_second)

            logger.debug(
                f"Recorded resource utilization metrics for {metrics.component_name}"
            )

        except Exception as e:
            logger.error(f"Failed to record resource utilization metrics: {e}")

    async def record_concurrent_operations_metrics(
        self, metrics: ConcurrentOperationsMetrics
    ) -> None:
        """Record concurrent operations metrics for a component."""
        try:
            self.concurrent_ops_metrics[metrics.component_name].append(metrics)

            # Update Prometheus metrics
            if self.enable_prometheus:
                self.prometheus_metrics["concurrent_operations"].labels(
                    component=metrics.component_name
                ).set(metrics.active_operations)

                self.prometheus_metrics["operation_queue_size"].labels(
                    component=metrics.component_name
                ).set(metrics.operation_queue_size)

            logger.debug(
                f"Recorded concurrent operations metrics for {metrics.component_name}"
            )

        except Exception as e:
            logger.error(f"Failed to record concurrent operations metrics: {e}")

    async def _collect_system_metrics(self) -> None:
        """Collect system-wide metrics using psutil."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Disk I/O metrics
            disk_io = psutil.disk_io_counters()
            disk_io_mb_per_sec = 0.0
            if hasattr(self, "_last_disk_io") and disk_io:
                time_delta = time.time() - self._last_disk_io_time
                bytes_delta = (
                    disk_io.read_bytes + disk_io.write_bytes
                ) - self._last_disk_io
                if time_delta > 0:
                    disk_io_mb_per_sec = (bytes_delta / time_delta) / (1024 * 1024)

            if disk_io:
                self._last_disk_io = disk_io.read_bytes + disk_io.write_bytes
                self._last_disk_io_time = time.time()

            # Network I/O metrics
            network_io = psutil.net_io_counters()
            network_io_mb_per_sec = 0.0
            if hasattr(self, "_last_network_io") and network_io:
                time_delta = time.time() - self._last_network_io_time
                bytes_delta = (
                    network_io.bytes_sent + network_io.bytes_recv
                ) - self._last_network_io
                if time_delta > 0:
                    network_io_mb_per_sec = (bytes_delta / time_delta) / (1024 * 1024)

            if network_io:
                self._last_network_io = network_io.bytes_sent + network_io.bytes_recv
                self._last_network_io_time = time.time()

            # Record system metrics
            system_metrics = ResourceUtilizationMetrics(
                component_name="system",
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_io_mb_per_second=disk_io_mb_per_sec,
                network_io_mb_per_second=network_io_mb_per_sec,
                gpu_utilization_percent=None,  # Would require additional libraries
                connection_pool_utilization_percent=0.0,  # Would be component-specific
                queue_depth=0,  # Would be component-specific
                active_threads=psutil.cpu_count(),
                timestamp=datetime.utcnow(),
            )

            await self.record_resource_utilization_metrics(system_metrics)

        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")

    async def _update_prometheus_metrics(self) -> None:
        """Update Prometheus metrics with current data."""
        if not self.enable_prometheus:
            return

        try:
            # Update alert counts
            alert_counts = {"INFO": 0, "WARNING": 0, "CRITICAL": 0}
            for alert in self.active_alerts.values():
                if not alert.resolved:
                    alert_counts[alert.severity] += 1

            for severity, count in alert_counts.items():
                self.prometheus_metrics["active_alerts"].labels(severity=severity).set(
                    count
                )

        except Exception as e:
            logger.error(f"Failed to update Prometheus metrics: {e}")

    async def _check_scalability_alerts(self) -> None:
        """Check for scalability threshold violations and generate alerts."""
        try:
            current_time = datetime.utcnow()

            # Check latency thresholds
            for component_name, metrics_queue in self.latency_metrics.items():
                if not metrics_queue:
                    continue

                latest_metrics = metrics_queue[-1]

                if latest_metrics.p95_latency_ms > self.thresholds.latency_critical_ms:
                    await self._create_alert(
                        component_name,
                        ScalabilityMetricType.LATENCY,
                        "CRITICAL",
                        f"P95 latency exceeded critical threshold",
                        latest_metrics.p95_latency_ms,
                        self.thresholds.latency_critical_ms,
                    )
                elif latest_metrics.p95_latency_ms > self.thresholds.latency_warning_ms:
                    await self._create_alert(
                        component_name,
                        ScalabilityMetricType.LATENCY,
                        "WARNING",
                        f"P95 latency exceeded warning threshold",
                        latest_metrics.p95_latency_ms,
                        self.thresholds.latency_warning_ms,
                    )

            # Check throughput thresholds
            for component_name, metrics_queue in self.throughput_metrics.items():
                if not metrics_queue:
                    continue

                latest_metrics = metrics_queue[-1]

                if (
                    latest_metrics.operations_per_second
                    < self.thresholds.throughput_critical_ops_per_second
                ):
                    await self._create_alert(
                        component_name,
                        ScalabilityMetricType.THROUGHPUT,
                        "CRITICAL",
                        f"Throughput below critical threshold",
                        latest_metrics.operations_per_second,
                        self.thresholds.throughput_critical_ops_per_second,
                    )
                elif (
                    latest_metrics.operations_per_second
                    < self.thresholds.throughput_warning_ops_per_second
                ):
                    await self._create_alert(
                        component_name,
                        ScalabilityMetricType.THROUGHPUT,
                        "WARNING",
                        f"Throughput below warning threshold",
                        latest_metrics.operations_per_second,
                        self.thresholds.throughput_warning_ops_per_second,
                    )

            # Check resource utilization thresholds
            for component_name, metrics_queue in self.resource_metrics.items():
                if not metrics_queue:
                    continue

                latest_metrics = metrics_queue[-1]

                # CPU checks
                if latest_metrics.cpu_percent > self.thresholds.cpu_critical_percent:
                    await self._create_alert(
                        component_name,
                        ScalabilityMetricType.RESOURCE_UTILIZATION,
                        "CRITICAL",
                        f"CPU utilization exceeded critical threshold",
                        latest_metrics.cpu_percent,
                        self.thresholds.cpu_critical_percent,
                    )
                elif latest_metrics.cpu_percent > self.thresholds.cpu_warning_percent:
                    await self._create_alert(
                        component_name,
                        ScalabilityMetricType.RESOURCE_UTILIZATION,
                        "WARNING",
                        f"CPU utilization exceeded warning threshold",
                        latest_metrics.cpu_percent,
                        self.thresholds.cpu_warning_percent,
                    )

                # Memory checks
                if (
                    latest_metrics.memory_percent
                    > self.thresholds.memory_critical_percent
                ):
                    await self._create_alert(
                        component_name,
                        ScalabilityMetricType.RESOURCE_UTILIZATION,
                        "CRITICAL",
                        f"Memory utilization exceeded critical threshold",
                        latest_metrics.memory_percent,
                        self.thresholds.memory_critical_percent,
                    )
                elif (
                    latest_metrics.memory_percent
                    > self.thresholds.memory_warning_percent
                ):
                    await self._create_alert(
                        component_name,
                        ScalabilityMetricType.RESOURCE_UTILIZATION,
                        "WARNING",
                        f"Memory utilization exceeded warning threshold",
                        latest_metrics.memory_percent,
                        self.thresholds.memory_warning_percent,
                    )

        except Exception as e:
            logger.error(f"Failed to check scalability alerts: {e}")

    async def _create_alert(
        self,
        component_name: str,
        metric_type: ScalabilityMetricType,
        severity: str,
        message: str,
        current_value: float,
        threshold_value: float,
    ) -> None:
        """Create and manage scalability alerts."""
        alert_key = f"{component_name}_{metric_type.value}_{severity}"

        # Check if alert already exists and is recent
        if alert_key in self.active_alerts:
            existing_alert = self.active_alerts[alert_key]
            time_diff = datetime.utcnow() - existing_alert.timestamp
            if time_diff.total_seconds() < 300:  # 5 minutes cooldown
                return

        alert = ScalabilityAlert(
            alert_id=f"scalability_{alert_key}_{int(time.time())}",
            component_name=component_name,
            metric_type=metric_type,
            severity=severity,
            threshold_breached=f"{metric_type.value}_{severity.lower()}",
            current_value=current_value,
            threshold_value=threshold_value,
            message=message,
            timestamp=datetime.utcnow(),
        )

        self.active_alerts[alert_key] = alert
        self.alert_history.append(alert)

        # Trigger alert handlers
        for handler in self.alert_handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")

        logger.warning(
            f"Scalability alert created: {alert.message} "
            f"(Current: {current_value}, Threshold: {threshold_value})"
        )

    async def _cache_metrics_to_redis(self) -> None:
        """Cache current metrics to Redis for dashboard access."""
        if not self.enable_redis or not self.redis_client:
            return

        try:
            metrics_summary = await self.get_metrics_summary()

            # Cache with expiration
            cache_key = "acgs:scalability:metrics:current"
            self.redis_client.setex(
                cache_key,
                300,  # 5 minute expiration
                json.dumps(metrics_summary, default=str),
            )

        except Exception as e:
            logger.error(f"Failed to cache metrics to Redis: {e}")

    def add_alert_handler(self, handler: Callable) -> None:
        """Add an alert handler function."""
        self.alert_handlers.append(handler)
        logger.info("Added scalability alert handler")

    async def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an active alert."""
        for alert_key, alert in self.active_alerts.items():
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                logger.info(f"Alert acknowledged: {alert_id}")
                return True
        return False

    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an active alert."""
        for alert_key, alert in self.active_alerts.items():
            if alert.alert_id == alert_id:
                alert.resolved = True
                logger.info(f"Alert resolved: {alert_id}")
                return True
        return False

    async def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary for dashboards."""
        try:
            summary = {
                "timestamp": datetime.utcnow().isoformat(),
                "monitoring_active": self.monitoring_active,
                "collection_interval": self.collection_interval,
                "monitored_components": list(self.monitored_components.keys()),
                "metrics": {
                    "latency": await self._summarize_latency_metrics(),
                    "throughput": await self._summarize_throughput_metrics(),
                    "resource_utilization": await self._summarize_resource_metrics(),
                    "concurrent_operations": await self._summarize_concurrent_ops_metrics(),
                },
                "alerts": {
                    "active_count": len(
                        [a for a in self.active_alerts.values() if not a.resolved]
                    ),
                    "total_count": len(self.alert_history),
                    "by_severity": self._count_alerts_by_severity(),
                    "recent_alerts": [
                        asdict(alert) for alert in list(self.alert_history)[-10:]
                    ],
                },
                "scalability_scores": await self._calculate_scalability_scores(),
            }

            return summary

        except Exception as e:
            logger.error(f"Failed to generate metrics summary: {e}")
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}

    async def _summarize_latency_metrics(self) -> Dict[str, Any]:
        """Summarize latency metrics across all components."""
        summary = {}
        for component_name, metrics_queue in self.latency_metrics.items():
            if not metrics_queue:
                continue

            recent_metrics = list(metrics_queue)[-10:]  # Last 10 samples
            avg_p95_latency = statistics.mean(
                [m.p95_latency_ms for m in recent_metrics]
            )
            max_latency = max([m.max_latency_ms for m in recent_metrics])

            summary[component_name] = {
                "avg_p95_latency_ms": round(avg_p95_latency, 2),
                "max_latency_ms": round(max_latency, 2),
                "sample_count": len(recent_metrics),
                "status": (
                    "healthy"
                    if avg_p95_latency < self.thresholds.latency_warning_ms
                    else "degraded"
                ),
            }

        return summary

    async def _summarize_throughput_metrics(self) -> Dict[str, Any]:
        """Summarize throughput metrics across all components."""
        summary = {}
        for component_name, metrics_queue in self.throughput_metrics.items():
            if not metrics_queue:
                continue

            recent_metrics = list(metrics_queue)[-10:]  # Last 10 samples
            avg_ops_per_sec = statistics.mean(
                [m.operations_per_second for m in recent_metrics]
            )
            avg_capacity_util = statistics.mean(
                [m.capacity_utilization_percent for m in recent_metrics]
            )

            summary[component_name] = {
                "avg_operations_per_second": round(avg_ops_per_sec, 2),
                "avg_capacity_utilization_percent": round(avg_capacity_util, 2),
                "sample_count": len(recent_metrics),
                "status": (
                    "healthy"
                    if avg_ops_per_sec
                    >= self.thresholds.throughput_warning_ops_per_second
                    else "degraded"
                ),
            }

        return summary

    async def _summarize_resource_metrics(self) -> Dict[str, Any]:
        """Summarize resource utilization metrics across all components."""
        summary = {}
        for component_name, metrics_queue in self.resource_metrics.items():
            if not metrics_queue:
                continue

            recent_metrics = list(metrics_queue)[-10:]  # Last 10 samples
            avg_cpu = statistics.mean([m.cpu_percent for m in recent_metrics])
            avg_memory = statistics.mean([m.memory_percent for m in recent_metrics])

            summary[component_name] = {
                "avg_cpu_percent": round(avg_cpu, 2),
                "avg_memory_percent": round(avg_memory, 2),
                "sample_count": len(recent_metrics),
                "status": self._determine_resource_status(avg_cpu, avg_memory),
            }

        return summary

    async def _summarize_concurrent_ops_metrics(self) -> Dict[str, Any]:
        """Summarize concurrent operations metrics across all components."""
        summary = {}
        for component_name, metrics_queue in self.concurrent_ops_metrics.items():
            if not metrics_queue:
                continue

            recent_metrics = list(metrics_queue)[-10:]  # Last 10 samples
            avg_concurrent_ops = statistics.mean(
                [m.active_operations for m in recent_metrics]
            )
            avg_queue_size = statistics.mean(
                [m.operation_queue_size for m in recent_metrics]
            )

            summary[component_name] = {
                "avg_concurrent_operations": round(avg_concurrent_ops, 2),
                "avg_queue_size": round(avg_queue_size, 2),
                "sample_count": len(recent_metrics),
                "status": (
                    "healthy"
                    if avg_queue_size < self.thresholds.queue_depth_warning
                    else "degraded"
                ),
            }

        return summary

    def _determine_resource_status(
        self, cpu_percent: float, memory_percent: float
    ) -> str:
        """Determine resource utilization status."""
        if (
            cpu_percent >= self.thresholds.cpu_critical_percent
            or memory_percent >= self.thresholds.memory_critical_percent
        ):
            return "critical"
        elif (
            cpu_percent >= self.thresholds.cpu_warning_percent
            or memory_percent >= self.thresholds.memory_warning_percent
        ):
            return "degraded"
        else:
            return "healthy"

    def _count_alerts_by_severity(self) -> Dict[str, int]:
        """Count active alerts by severity."""
        counts = {"INFO": 0, "WARNING": 0, "CRITICAL": 0}
        for alert in self.active_alerts.values():
            if not alert.resolved:
                counts[alert.severity] += 1
        return counts

    async def _calculate_scalability_scores(self) -> Dict[str, float]:
        """Calculate overall scalability scores for each component."""
        scores = {}

        for component_name in self.monitored_components.keys():
            # Initialize score components
            latency_score = 1.0
            throughput_score = 1.0
            resource_score = 1.0

            # Calculate latency score
            if (
                component_name in self.latency_metrics
                and self.latency_metrics[component_name]
            ):
                latest_latency = self.latency_metrics[component_name][-1]
                if latest_latency.p95_latency_ms <= self.thresholds.latency_warning_ms:
                    latency_score = 1.0
                elif (
                    latest_latency.p95_latency_ms <= self.thresholds.latency_critical_ms
                ):
                    latency_score = 0.7
                else:
                    latency_score = 0.3

            # Calculate throughput score
            if (
                component_name in self.throughput_metrics
                and self.throughput_metrics[component_name]
            ):
                latest_throughput = self.throughput_metrics[component_name][-1]
                if (
                    latest_throughput.operations_per_second
                    >= self.thresholds.throughput_warning_ops_per_second
                ):
                    throughput_score = 1.0
                elif (
                    latest_throughput.operations_per_second
                    >= self.thresholds.throughput_critical_ops_per_second
                ):
                    throughput_score = 0.7
                else:
                    throughput_score = 0.3

            # Calculate resource score
            if (
                component_name in self.resource_metrics
                and self.resource_metrics[component_name]
            ):
                latest_resource = self.resource_metrics[component_name][-1]
                cpu_score = 1.0 - (latest_resource.cpu_percent / 100.0)
                memory_score = 1.0 - (latest_resource.memory_percent / 100.0)
                resource_score = (cpu_score + memory_score) / 2.0

            # Overall score (weighted average)
            overall_score = (
                latency_score * 0.4 + throughput_score * 0.4 + resource_score * 0.2
            )
            scores[component_name] = round(max(0.0, min(1.0, overall_score)), 3)

        return scores

    def get_prometheus_metrics(self) -> str:
        """Export Prometheus metrics."""
        if not self.enable_prometheus:
            return "# Prometheus metrics not enabled"

        try:
            return generate_latest(self.registry).decode("utf-8")
        except Exception as e:
            logger.error(f"Failed to generate Prometheus metrics: {e}")
            return f"# Error generating metrics: {e}"


# Global scalability metrics collector instance
_scalability_collector: Optional[ScalabilityMetricsCollector] = None


async def get_scalability_metrics_collector() -> ScalabilityMetricsCollector:
    """Get or create the global scalability metrics collector."""
    global _scalability_collector
    if _scalability_collector is None:
        _scalability_collector = ScalabilityMetricsCollector()
    return _scalability_collector


async def close_scalability_metrics_collector() -> None:
    """Close the global scalability metrics collector."""
    global _scalability_collector
    if _scalability_collector is not None:
        await _scalability_collector.stop_monitoring()
        _scalability_collector = None
