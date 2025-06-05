"""
Performance Monitoring Service for ACGS Governance Synthesis

This service provides comprehensive performance monitoring, profiling, and optimization
capabilities for the governance synthesis system, targeting <50ms policy decision latency.

Phase 3: Performance Optimization and Security Compliance
"""

import asyncio
import time
import logging
import psutil
import threading
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
from contextlib import asynccontextmanager, contextmanager
import json
import statistics
from functools import wraps

import redis
from prometheus_client import Counter, Histogram, Gauge, Summary, CollectorRegistry, generate_latest
import structlog

logger = structlog.get_logger(__name__)

# Prometheus metrics
POLICY_DECISION_LATENCY = Histogram(
    'policy_decision_latency_seconds',
    'Time spent on policy decisions',
    ['endpoint', 'policy_type', 'validation_level']
)

CACHE_HIT_RATE = Gauge(
    'cache_hit_rate',
    'Cache hit rate percentage',
    ['cache_type']
)

SYSTEM_RESOURCE_USAGE = Gauge(
    'system_resource_usage',
    'System resource usage metrics',
    ['resource_type']
)

CONCURRENT_REQUESTS = Gauge(
    'concurrent_requests',
    'Number of concurrent requests being processed'
)

ERROR_RATE = Counter(
    'error_rate_total',
    'Total number of errors',
    ['error_type', 'endpoint']
)

THROUGHPUT = Counter(
    'throughput_total',
    'Total number of requests processed',
    ['endpoint', 'status']
)


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure."""
    timestamp: datetime
    latency_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    cache_hit_rate: float
    concurrent_requests: int
    error_count: int
    throughput_rps: float
    endpoint: str
    operation_type: str


@dataclass
class LatencyProfile:
    """Latency profiling data structure."""
    operation: str
    min_latency_ms: float
    max_latency_ms: float
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    sample_count: int
    timestamp: datetime


class PerformanceProfiler:
    """Advanced performance profiler with bottleneck detection."""
    
    def __init__(self, max_samples: int = 10000):
        self.max_samples = max_samples
        self.latency_samples: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_samples))
        self.operation_counts: Dict[str, int] = defaultdict(int)
        self.bottlenecks: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
    
    def record_latency(self, operation: str, latency_ms: float):
        """Record latency measurement for an operation."""
        with self._lock:
            self.latency_samples[operation].append({
                'latency_ms': latency_ms,
                'timestamp': datetime.now()
            })
            self.operation_counts[operation] += 1
            
            # Check for performance threshold violations
            if latency_ms > 50.0:  # 50ms threshold
                self._record_bottleneck(operation, latency_ms)
    
    def _record_bottleneck(self, operation: str, latency_ms: float):
        """Record performance bottleneck."""
        bottleneck = {
            'operation': operation,
            'latency_ms': latency_ms,
            'timestamp': datetime.now(),
            'severity': 'high' if latency_ms > 100 else 'medium'
        }
        self.bottlenecks.append(bottleneck)
        
        # Keep only recent bottlenecks
        cutoff_time = datetime.now() - timedelta(hours=1)
        self.bottlenecks = [b for b in self.bottlenecks if b['timestamp'] > cutoff_time]
        
        logger.warning(
            "Performance bottleneck detected",
            operation=operation,
            latency_ms=latency_ms,
            severity=bottleneck['severity']
        )
    
    def get_latency_profile(self, operation: str) -> Optional[LatencyProfile]:
        """Get latency profile for a specific operation."""
        with self._lock:
            samples = self.latency_samples.get(operation, [])
            if not samples:
                return None
            
            latencies = [s['latency_ms'] for s in samples]
            
            return LatencyProfile(
                operation=operation,
                min_latency_ms=min(latencies),
                max_latency_ms=max(latencies),
                avg_latency_ms=statistics.mean(latencies),
                p95_latency_ms=statistics.quantiles(latencies, n=20)[18] if len(latencies) > 20 else max(latencies),
                p99_latency_ms=statistics.quantiles(latencies, n=100)[98] if len(latencies) > 100 else max(latencies),
                sample_count=len(latencies),
                timestamp=datetime.now()
            )
    
    def get_all_profiles(self) -> List[LatencyProfile]:
        """Get latency profiles for all operations."""
        profiles = []
        for operation in self.latency_samples.keys():
            profile = self.get_latency_profile(operation)
            if profile:
                profiles.append(profile)
        return profiles
    
    def get_bottlenecks(self, hours: int = 1) -> List[Dict[str, Any]]:
        """Get recent performance bottlenecks."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [b for b in self.bottlenecks if b['timestamp'] > cutoff_time]


class SystemResourceMonitor:
    """System resource monitoring with alerting."""
    
    def __init__(self, check_interval: int = 30):
        self.check_interval = check_interval
        self.monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None
        self.thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_percent': 90.0
        }
    
    async def start_monitoring(self):
        """Start system resource monitoring."""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("System resource monitoring started")
    
    async def stop_monitoring(self):
        """Stop system resource monitoring."""
        self.monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("System resource monitoring stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                await self._collect_metrics()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in resource monitoring", error=str(e))
                await asyncio.sleep(self.check_interval)
    
    async def _collect_metrics(self):
        """Collect system resource metrics."""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        SYSTEM_RESOURCE_USAGE.labels(resource_type='cpu_percent').set(cpu_percent)
        
        # Memory usage
        memory = psutil.virtual_memory()
        SYSTEM_RESOURCE_USAGE.labels(resource_type='memory_percent').set(memory.percent)
        SYSTEM_RESOURCE_USAGE.labels(resource_type='memory_available_gb').set(memory.available / (1024**3))
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        SYSTEM_RESOURCE_USAGE.labels(resource_type='disk_percent').set(disk_percent)
        
        # Network I/O
        network = psutil.net_io_counters()
        SYSTEM_RESOURCE_USAGE.labels(resource_type='network_bytes_sent').set(network.bytes_sent)
        SYSTEM_RESOURCE_USAGE.labels(resource_type='network_bytes_recv').set(network.bytes_recv)
        
        # Check thresholds and alert
        await self._check_thresholds(cpu_percent, memory.percent, disk_percent)
    
    async def _check_thresholds(self, cpu_percent: float, memory_percent: float, disk_percent: float):
        """Check resource usage against thresholds."""
        alerts = []
        
        if cpu_percent > self.thresholds['cpu_percent']:
            alerts.append(f"High CPU usage: {cpu_percent:.1f}%")
        
        if memory_percent > self.thresholds['memory_percent']:
            alerts.append(f"High memory usage: {memory_percent:.1f}%")
        
        if disk_percent > self.thresholds['disk_percent']:
            alerts.append(f"High disk usage: {disk_percent:.1f}%")
        
        if alerts:
            logger.warning("Resource usage alerts", alerts=alerts)


class PerformanceMonitor:
    """Main performance monitoring service."""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.profiler = PerformanceProfiler()
        self.resource_monitor = SystemResourceMonitor()
        self.active_requests = 0
        self._lock = threading.Lock()
        
    async def initialize(self):
        """Initialize performance monitoring."""
        await self.resource_monitor.start_monitoring()
        logger.info("Performance monitoring initialized")
    
    async def shutdown(self):
        """Shutdown performance monitoring."""
        await self.resource_monitor.stop_monitoring()
        logger.info("Performance monitoring shutdown")
    
    @asynccontextmanager
    async def monitor_request(self, endpoint: str, operation_type: str = "default"):
        """Context manager for monitoring request performance."""
        start_time = time.time()
        
        with self._lock:
            self.active_requests += 1
            CONCURRENT_REQUESTS.set(self.active_requests)
        
        try:
            yield
            
            # Record successful completion
            latency_ms = (time.time() - start_time) * 1000
            self.profiler.record_latency(f"{endpoint}:{operation_type}", latency_ms)
            
            POLICY_DECISION_LATENCY.labels(
                endpoint=endpoint,
                policy_type=operation_type,
                validation_level="standard"
            ).observe(latency_ms / 1000)
            
            THROUGHPUT.labels(endpoint=endpoint, status="success").inc()
            
        except Exception as e:
            # Record error
            ERROR_RATE.labels(error_type=type(e).__name__, endpoint=endpoint).inc()
            THROUGHPUT.labels(endpoint=endpoint, status="error").inc()
            raise
        
        finally:
            with self._lock:
                self.active_requests -= 1
                CONCURRENT_REQUESTS.set(self.active_requests)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        profiles = self.profiler.get_all_profiles()
        bottlenecks = self.profiler.get_bottlenecks()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'latency_profiles': [asdict(p) for p in profiles],
            'bottlenecks': bottlenecks,
            'active_requests': self.active_requests,
            'system_metrics': self._get_current_system_metrics()
        }
    
    def _get_current_system_metrics(self) -> Dict[str, float]:
        """Get current system metrics."""
        memory = psutil.virtual_memory()
        return {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': memory.percent,
            'memory_available_gb': memory.available / (1024**3),
            'active_requests': self.active_requests
        }


# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def performance_monitor_decorator(endpoint: str, operation_type: str = "default"):
    """Decorator for monitoring function performance."""
    def decorator(func: Callable):
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                monitor = get_performance_monitor()
                async with monitor.monitor_request(endpoint, operation_type):
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                monitor = get_performance_monitor()
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    latency_ms = (time.time() - start_time) * 1000
                    monitor.profiler.record_latency(f"{endpoint}:{operation_type}", latency_ms)
                    return result
                except Exception as e:
                    ERROR_RATE.labels(error_type=type(e).__name__, endpoint=endpoint).inc()
                    raise
            return sync_wrapper
    return decorator
