#!/usr/bin/env python3
"""
Memory Optimization Service for ACGS-master Phase 3
Addresses memory usage optimization to stay below 85% target under load.
"""

import asyncio
import gc
import logging
import time
import weakref
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from contextlib import asynccontextmanager
import sys
import tracemalloc

# Graceful psutil import with fallback
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    # Create mock psutil for basic functionality
    class MockPsutil:
        @staticmethod
        def virtual_memory():
            # Fallback using /proc/meminfo on Linux
            try:
                with open('/proc/meminfo', 'r') as f:
                    meminfo = {}
                    for line in f:
                        key, value = line.split(':')
                        meminfo[key.strip()] = int(value.split()[0]) * 1024  # Convert KB to bytes

                    total = meminfo.get('MemTotal', 8 * 1024**3)  # Default 8GB
                    available = meminfo.get('MemAvailable', meminfo.get('MemFree', total // 2))
                    used = total - available
                    percent = (used / total) * 100

                    class MemoryInfo:
                        def __init__(self, total, used, available, percent):
                            self.total = total
                            self.used = used
                            self.available = available
                            self.percent = percent

                    return MemoryInfo(total, used, available, percent)
            except Exception:
                # Ultimate fallback
                class MemoryInfo:
                    def __init__(self):
                        self.total = 8 * 1024**3  # 8GB default
                        self.used = 4 * 1024**3   # 4GB default
                        self.available = 4 * 1024**3  # 4GB default
                        self.percent = 50.0
                return MemoryInfo()

        @staticmethod
        def Process():
            class MockProcess:
                def memory_info(self):
                    class MemInfo:
                        def __init__(self):
                            self.rss = 100 * 1024 * 1024  # 100MB default
                    return MemInfo()

                def nice(self, value=None):
                    return 0  # Normal priority

            return MockProcess()

        @staticmethod
        def cpu_percent(interval=None):
            return 25.0  # Default 25% CPU usage

        @staticmethod
        def disk_usage(path):
            class DiskInfo:
                def __init__(self):
                    self.total = 100 * 1024**3  # 100GB default
                    self.used = 50 * 1024**3    # 50GB default
                    self.free = 50 * 1024**3    # 50GB default
            return DiskInfo()

    psutil = MockPsutil()

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class MemoryMetrics:
    """Memory usage metrics."""
    total_memory_gb: float
    used_memory_gb: float
    available_memory_gb: float
    memory_percent: float
    process_memory_mb: float
    gc_collections: Dict[int, int]
    memory_leaks_detected: int
    timestamp: datetime

@dataclass
class MemoryThresholds:
    """Memory usage thresholds for optimization."""
    warning_threshold: float = 80.0  # 80% memory usage warning
    critical_threshold: float = 85.0  # 85% memory usage critical
    restart_threshold: float = 90.0  # 90% memory usage restart
    gc_trigger_threshold: float = 75.0  # 75% memory usage triggers GC
    leak_detection_threshold: int = 100  # MB growth for leak detection

class MemoryOptimizer:
    """
    Memory optimization service for ACGS services.
    
    Features:
    - Real-time memory monitoring
    - Automatic garbage collection
    - Memory leak detection
    - Request payload size limits
    - Connection pooling optimization
    - Process restart recommendations
    """
    
    def __init__(self, service_name: str, thresholds: Optional[MemoryThresholds] = None):
        self.service_name = service_name
        self.thresholds = thresholds or MemoryThresholds()
        self.process = psutil.Process()
        self.monitoring_active = False
        self.monitoring_task: Optional[asyncio.Task] = None
        self.psutil_available = PSUTIL_AVAILABLE
        
        # Memory tracking
        self.memory_history: List[MemoryMetrics] = []
        self.max_history_size = 100
        self.last_gc_time = time.time()
        self.gc_interval = 30  # seconds
        
        # Leak detection
        self.baseline_memory = None
        self.leak_detection_enabled = False
        self.memory_snapshots = []
        
        # Request tracking
        self.active_requests = weakref.WeakSet()
        self.request_memory_tracking = {}
        
        # Optimization callbacks
        self.optimization_callbacks: List[Callable] = []
        
    async def initialize(self):
        """Initialize memory optimizer."""
        try:
            # Log psutil availability
            if not self.psutil_available:
                logger.warning("psutil not available - using fallback memory monitoring")
            else:
                logger.info("psutil available - using full memory monitoring")

            # Enable tracemalloc for memory leak detection
            if not tracemalloc.is_tracing():
                tracemalloc.start()
                self.leak_detection_enabled = True
                logger.info("Memory leak detection enabled")

            # Get baseline memory usage
            self.baseline_memory = self.get_current_memory_usage()
            logger.info(f"Memory optimizer initialized for {self.service_name}")
            logger.info(f"Baseline memory: {self.baseline_memory.process_memory_mb:.1f} MB")

        except Exception as e:
            logger.error(f"Failed to initialize memory optimizer: {e}")
            raise
    
    def get_current_memory_usage(self) -> MemoryMetrics:
        """Get current memory usage metrics."""
        # System memory
        memory = psutil.virtual_memory()
        
        # Process memory
        process_memory = self.process.memory_info()
        
        # Garbage collection stats
        gc_stats = {}
        for i in range(3):
            gc_stats[i] = gc.get_count()[i]
        
        return MemoryMetrics(
            total_memory_gb=memory.total / (1024**3),
            used_memory_gb=memory.used / (1024**3),
            available_memory_gb=memory.available / (1024**3),
            memory_percent=memory.percent,
            process_memory_mb=process_memory.rss / (1024**2),
            gc_collections=gc_stats,
            memory_leaks_detected=len(self.memory_snapshots),
            timestamp=datetime.now()
        )
    
    async def start_monitoring(self, interval: float = 10.0):
        """Start continuous memory monitoring."""
        if self.monitoring_active:
            logger.warning("Memory monitoring already active")
            return
        
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop(interval))
        logger.info(f"Started memory monitoring with {interval}s interval")
    
    async def stop_monitoring(self):
        """Stop memory monitoring."""
        self.monitoring_active = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped memory monitoring")
    
    async def _monitoring_loop(self, interval: float):
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                # Get current metrics
                metrics = self.get_current_memory_usage()
                self.memory_history.append(metrics)
                
                # Trim history
                if len(self.memory_history) > self.max_history_size:
                    self.memory_history.pop(0)
                
                # Check thresholds and optimize
                await self._check_thresholds_and_optimize(metrics)
                
                # Detect memory leaks
                if self.leak_detection_enabled:
                    await self._detect_memory_leaks()
                
                # Log metrics periodically
                if len(self.memory_history) % 6 == 0:  # Every minute with 10s interval
                    logger.info(
                        f"Memory usage: {metrics.memory_percent:.1f}% "
                        f"({metrics.process_memory_mb:.1f} MB process)"
                    )
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in memory monitoring loop: {e}")
                await asyncio.sleep(interval)
    
    async def _check_thresholds_and_optimize(self, metrics: MemoryMetrics):
        """Check memory thresholds and trigger optimizations."""
        memory_percent = metrics.memory_percent
        
        if memory_percent >= self.thresholds.restart_threshold:
            logger.critical(
                f"CRITICAL: Memory usage {memory_percent:.1f}% >= {self.thresholds.restart_threshold}% "
                f"- Process restart recommended!"
            )
            await self._trigger_optimization_callbacks("restart_recommended", metrics)
            
        elif memory_percent >= self.thresholds.critical_threshold:
            logger.error(
                f"CRITICAL: Memory usage {memory_percent:.1f}% >= {self.thresholds.critical_threshold}% "
                f"- Triggering aggressive optimization"
            )
            await self._aggressive_memory_cleanup()
            await self._trigger_optimization_callbacks("critical_threshold", metrics)
            
        elif memory_percent >= self.thresholds.warning_threshold:
            logger.warning(
                f"WARNING: Memory usage {memory_percent:.1f}% >= {self.thresholds.warning_threshold}% "
                f"- Triggering memory optimization"
            )
            await self._standard_memory_cleanup()
            await self._trigger_optimization_callbacks("warning_threshold", metrics)
            
        elif memory_percent >= self.thresholds.gc_trigger_threshold:
            # Trigger garbage collection if enough time has passed
            current_time = time.time()
            if current_time - self.last_gc_time >= self.gc_interval:
                await self._trigger_garbage_collection()
                self.last_gc_time = current_time
    
    async def _standard_memory_cleanup(self):
        """Standard memory cleanup procedures."""
        logger.info("Performing standard memory cleanup")
        
        # Trigger garbage collection
        await self._trigger_garbage_collection()
        
        # Clear request tracking for completed requests
        self._cleanup_request_tracking()
        
        # Trigger optimization callbacks
        await self._trigger_optimization_callbacks("standard_cleanup", None)
    
    async def _aggressive_memory_cleanup(self):
        """Aggressive memory cleanup procedures."""
        logger.info("Performing aggressive memory cleanup")
        
        # Multiple garbage collection passes
        for i in range(3):
            await self._trigger_garbage_collection()
            await asyncio.sleep(0.1)
        
        # Clear all request tracking
        self.request_memory_tracking.clear()
        
        # Clear memory history (keep only recent entries)
        if len(self.memory_history) > 10:
            self.memory_history = self.memory_history[-10:]
        
        # Trigger optimization callbacks
        await self._trigger_optimization_callbacks("aggressive_cleanup", None)
    
    async def _trigger_garbage_collection(self):
        """Trigger garbage collection."""
        collected = gc.collect()
        logger.debug(f"Garbage collection freed {collected} objects")
    
    def _cleanup_request_tracking(self):
        """Clean up completed request tracking."""
        current_time = time.time()
        expired_requests = [
            req_id for req_id, data in self.request_memory_tracking.items()
            if current_time - data.get('start_time', 0) > 300  # 5 minutes
        ]
        
        for req_id in expired_requests:
            del self.request_memory_tracking[req_id]
    
    async def _detect_memory_leaks(self):
        """Detect potential memory leaks."""
        if not self.leak_detection_enabled:
            return
        
        try:
            current_snapshot = tracemalloc.take_snapshot()
            
            if len(self.memory_snapshots) > 0:
                # Compare with previous snapshot
                previous_snapshot = self.memory_snapshots[-1]
                top_stats = current_snapshot.compare_to(previous_snapshot, 'lineno')
                
                # Check for significant memory growth
                for stat in top_stats[:5]:  # Top 5 memory growth areas
                    if stat.size_diff > self.thresholds.leak_detection_threshold * 1024 * 1024:  # Convert MB to bytes
                        logger.warning(
                            f"Potential memory leak detected: {stat.traceback.format()[-1]} "
                            f"grew by {stat.size_diff / (1024*1024):.1f} MB"
                        )
            
            # Keep only recent snapshots
            self.memory_snapshots.append(current_snapshot)
            if len(self.memory_snapshots) > 5:
                self.memory_snapshots.pop(0)
                
        except Exception as e:
            logger.error(f"Memory leak detection failed: {e}")
    
    def add_optimization_callback(self, callback: Callable):
        """Add callback for optimization events."""
        self.optimization_callbacks.append(callback)
    
    async def _trigger_optimization_callbacks(self, event_type: str, metrics: Optional[MemoryMetrics]):
        """Trigger optimization callbacks."""
        for callback in self.optimization_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event_type, metrics)
                else:
                    callback(event_type, metrics)
            except Exception as e:
                logger.error(f"Optimization callback failed: {e}")
    
    @asynccontextmanager
    async def track_request_memory(self, request_id: str):
        """Context manager to track memory usage for a request."""
        start_time = time.time()
        start_memory = self.process.memory_info().rss
        
        self.request_memory_tracking[request_id] = {
            'start_time': start_time,
            'start_memory': start_memory
        }
        
        try:
            yield
        finally:
            end_time = time.time()
            end_memory = self.process.memory_info().rss
            
            if request_id in self.request_memory_tracking:
                self.request_memory_tracking[request_id].update({
                    'end_time': end_time,
                    'end_memory': end_memory,
                    'duration': end_time - start_time,
                    'memory_delta': end_memory - start_memory
                })
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics."""
        # Get current memory usage even if no history
        current = self.get_current_memory_usage()

        # Add to history if not already there
        if not self.memory_history or self.memory_history[-1].timestamp != current.timestamp:
            self.memory_history.append(current)
            # Trim history
            if len(self.memory_history) > self.max_history_size:
                self.memory_history.pop(0)

        # Calculate trends
        if len(self.memory_history) >= 2:
            previous = self.memory_history[-2]
            memory_trend = current.memory_percent - previous.memory_percent
            process_trend = current.process_memory_mb - previous.process_memory_mb
        else:
            memory_trend = 0.0
            process_trend = 0.0

        return {
            "current_metrics": {
                "memory_percent": current.memory_percent,
                "process_memory_mb": current.process_memory_mb,
                "available_memory_gb": current.available_memory_gb,
                "timestamp": current.timestamp.isoformat()
            },
            "trends": {
                "memory_trend_percent": memory_trend,
                "process_trend_mb": process_trend
            },
            "thresholds": {
                "warning": self.thresholds.warning_threshold,
                "critical": self.thresholds.critical_threshold,
                "restart": self.thresholds.restart_threshold
            },
            "optimization_status": {
                "monitoring_active": self.monitoring_active,
                "leak_detection_enabled": self.leak_detection_enabled,
                "active_requests": len(self.request_memory_tracking),
                "memory_snapshots": len(self.memory_snapshots)
            },
            "compliance": {
                "within_critical_threshold": current.memory_percent < self.thresholds.critical_threshold,
                "within_warning_threshold": current.memory_percent < self.thresholds.warning_threshold,
                "production_ready": current.memory_percent < self.thresholds.critical_threshold
            }
        }

# Global memory optimizer instance
_memory_optimizer: Optional[MemoryOptimizer] = None

def get_memory_optimizer(service_name: str) -> MemoryOptimizer:
    """Get or create memory optimizer instance."""
    global _memory_optimizer
    if _memory_optimizer is None:
        _memory_optimizer = MemoryOptimizer(service_name)
    return _memory_optimizer

async def initialize_memory_optimization(service_name: str) -> MemoryOptimizer:
    """Initialize memory optimization for a service."""
    optimizer = get_memory_optimizer(service_name)
    await optimizer.initialize()
    await optimizer.start_monitoring()
    return optimizer
