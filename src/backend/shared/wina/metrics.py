"""
WINA Metrics and Performance Monitoring

Implements comprehensive metrics collection and performance monitoring
for WINA (Weight Informed Neuron Activation) optimization.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timezone
from collections import defaultdict, deque
import json

try:
    from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Prometheus client not available, metrics will be stored locally only")

from .config import WINAConfig
from .exceptions import WINAMetricsError

logger = logging.getLogger(__name__)


@dataclass
class WINAPerformanceSnapshot:
    """
    Snapshot of WINA performance metrics at a point in time.
    
    Attributes:
        timestamp: When the snapshot was taken
        gflops_baseline: Baseline GFLOPs without WINA
        gflops_optimized: GFLOPs with WINA optimization
        gflops_reduction: Percentage reduction in GFLOPs
        accuracy_baseline: Baseline accuracy without WINA
        accuracy_optimized: Accuracy with WINA optimization
        accuracy_retention: Percentage of accuracy retained
        latency_baseline: Baseline inference latency
        latency_optimized: Optimized inference latency
        sparsity_achieved: Average sparsity achieved across layers
        optimization_overhead: Time overhead for WINA optimization
    """
    timestamp: datetime
    gflops_baseline: float
    gflops_optimized: float
    gflops_reduction: float
    accuracy_baseline: float
    accuracy_optimized: float
    accuracy_retention: float
    latency_baseline: float
    latency_optimized: float
    sparsity_achieved: float
    optimization_overhead: float


@dataclass
class WINAMetricsConfig:
    """
    Configuration for WINA metrics collection.
    
    Attributes:
        enable_prometheus: Enable Prometheus metrics export
        enable_detailed_logging: Enable detailed performance logging
        snapshot_interval: Interval for taking performance snapshots (seconds)
        history_retention: Number of snapshots to retain in memory
        alert_thresholds: Thresholds for performance alerts
    """
    enable_prometheus: bool = True
    enable_detailed_logging: bool = True
    snapshot_interval: int = 60
    history_retention: int = 1000
    alert_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "gflops_reduction_min": 0.3,  # Minimum 30% GFLOPs reduction
        "accuracy_retention_min": 0.95,  # Minimum 95% accuracy retention
        "latency_increase_max": 0.1,  # Maximum 10% latency increase
        "optimization_overhead_max": 0.05,  # Maximum 5% optimization overhead
    })


class GFLOPsTracker:
    """
    Tracks GFLOPs (Giga Floating Point Operations) for WINA optimization.
    
    This class provides methods to estimate and track GFLOPs consumption
    before and after WINA optimization.
    """
    
    def __init__(self):
        """Initialize GFLOPs tracker."""
        self.operation_counts: Dict[str, int] = defaultdict(int)
        self.layer_gflops: Dict[str, float] = {}
        
        logger.debug("Initialized GFLOPs tracker")
    
    def estimate_gflops(self, model: Any, input_data: Any) -> float:
        """
        Estimate GFLOPs for model inference without WINA.
        
        Args:
            model: The model to analyze
            input_data: Input data for inference
            
        Returns:
            Estimated GFLOPs for inference
        """
        try:
            # This is a simplified estimation
            # In practice, this would analyze the model architecture
            # and calculate actual FLOPs based on layer dimensions
            
            # Mock implementation for demonstration
            estimated_gflops = 100.0  # Placeholder value
            
            logger.debug(f"Estimated baseline GFLOPs: {estimated_gflops}")
            return estimated_gflops
            
        except Exception as e:
            logger.error(f"GFLOPs estimation failed: {e}")
            raise WINAMetricsError(f"GFLOPs estimation failed: {e}")
    
    def estimate_optimized_gflops(self, model: Any, input_data: Any, 
                                 activation_masks: Dict[str, Any]) -> float:
        """
        Estimate GFLOPs for model inference with WINA optimization.
        
        Args:
            model: The model to analyze
            input_data: Input data for inference
            activation_masks: WINA activation masks
            
        Returns:
            Estimated GFLOPs for optimized inference
        """
        try:
            # Calculate reduction based on sparsity
            baseline_gflops = self.estimate_gflops(model, input_data)
            
            # Calculate average sparsity across layers
            sparsities = [mask.sparsity_ratio for mask in activation_masks.values()]
            average_sparsity = np.mean(sparsities) if sparsities else 0.0
            
            # Estimate GFLOPs reduction (simplified linear model)
            # In practice, this would be more sophisticated
            reduction_factor = 1.0 - average_sparsity
            optimized_gflops = baseline_gflops * reduction_factor
            
            logger.debug(f"Estimated optimized GFLOPs: {optimized_gflops} "
                        f"(reduction: {(1 - reduction_factor) * 100:.1f}%)")
            
            return optimized_gflops
            
        except Exception as e:
            logger.error(f"Optimized GFLOPs estimation failed: {e}")
            raise WINAMetricsError(f"Optimized GFLOPs estimation failed: {e}")
    
    def track_layer_gflops(self, layer_name: str, gflops: float) -> None:
        """
        Track GFLOPs for a specific layer.
        
        Args:
            layer_name: Name of the layer
            gflops: GFLOPs consumed by the layer
        """
        self.layer_gflops[layer_name] = gflops
        logger.debug(f"Tracked {gflops} GFLOPs for layer {layer_name}")
    
    def get_layer_breakdown(self) -> Dict[str, float]:
        """
        Get GFLOPs breakdown by layer.
        
        Returns:
            Dictionary of GFLOPs per layer
        """
        return self.layer_gflops.copy()


class PerformanceMonitor:
    """
    Monitors WINA performance metrics and provides alerting.
    
    This class continuously monitors WINA performance and can trigger
    alerts when performance degrades below configured thresholds.
    """
    
    def __init__(self, config: WINAMetricsConfig):
        """
        Initialize performance monitor.
        
        Args:
            config: Metrics configuration
        """
        self.config = config
        self.snapshots: deque = deque(maxlen=config.history_retention)
        self.alerts_triggered: List[Dict[str, Any]] = []
        self.monitoring_active = False
        
        # Prometheus metrics (if available)
        if PROMETHEUS_AVAILABLE and config.enable_prometheus:
            self.registry = CollectorRegistry()
            self._setup_prometheus_metrics()
        
        logger.info("Initialized WINA performance monitor")
    
    def _setup_prometheus_metrics(self) -> None:
        """Setup Prometheus metrics collectors."""
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.prometheus_metrics = {
            "gflops_reduction": Gauge(
                "wina_gflops_reduction_ratio",
                "WINA GFLOPs reduction ratio",
                registry=self.registry
            ),
            "accuracy_retention": Gauge(
                "wina_accuracy_retention_ratio", 
                "WINA accuracy retention ratio",
                registry=self.registry
            ),
            "sparsity_achieved": Gauge(
                "wina_sparsity_achieved",
                "WINA sparsity achieved",
                registry=self.registry
            ),
            "optimization_time": Histogram(
                "wina_optimization_time_seconds",
                "WINA optimization time in seconds",
                registry=self.registry
            ),
            "optimizations_total": Counter(
                "wina_optimizations_total",
                "Total number of WINA optimizations",
                registry=self.registry
            )
        }
        
        logger.debug("Setup Prometheus metrics for WINA monitoring")
    
    async def start_monitoring(self) -> None:
        """Start continuous performance monitoring."""
        if self.monitoring_active:
            logger.warning("Performance monitoring already active")
            return
        
        self.monitoring_active = True
        logger.info("Started WINA performance monitoring")
        
        # Start monitoring loop
        asyncio.create_task(self._monitoring_loop())
    
    async def stop_monitoring(self) -> None:
        """Stop performance monitoring."""
        self.monitoring_active = False
        logger.info("Stopped WINA performance monitoring")
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                await asyncio.sleep(self.config.snapshot_interval)
                
                # Take performance snapshot would be implemented here
                # This is a placeholder for the monitoring logic
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Brief pause before retrying
    
    def record_performance_snapshot(self, snapshot: WINAPerformanceSnapshot) -> None:
        """
        Record a performance snapshot.
        
        Args:
            snapshot: Performance snapshot to record
        """
        try:
            # Store snapshot
            self.snapshots.append(snapshot)
            
            # Update Prometheus metrics
            if PROMETHEUS_AVAILABLE and hasattr(self, 'prometheus_metrics'):
                self.prometheus_metrics["gflops_reduction"].set(snapshot.gflops_reduction)
                self.prometheus_metrics["accuracy_retention"].set(snapshot.accuracy_retention)
                self.prometheus_metrics["sparsity_achieved"].set(snapshot.sparsity_achieved)
                self.prometheus_metrics["optimization_time"].observe(snapshot.optimization_overhead)
                self.prometheus_metrics["optimizations_total"].inc()
            
            # Check for alerts
            self._check_performance_alerts(snapshot)
            
            # Detailed logging
            if self.config.enable_detailed_logging:
                logger.info(f"WINA Performance Snapshot: "
                           f"GFLOPs reduction: {snapshot.gflops_reduction:.2%}, "
                           f"Accuracy retention: {snapshot.accuracy_retention:.2%}, "
                           f"Sparsity: {snapshot.sparsity_achieved:.2%}")
            
        except Exception as e:
            logger.error(f"Failed to record performance snapshot: {e}")
            raise WINAMetricsError(f"Snapshot recording failed: {e}")
    
    def _check_performance_alerts(self, snapshot: WINAPerformanceSnapshot) -> None:
        """
        Check performance snapshot against alert thresholds.
        
        Args:
            snapshot: Performance snapshot to check
        """
        alerts = []
        thresholds = self.config.alert_thresholds
        
        # Check GFLOPs reduction
        if snapshot.gflops_reduction < thresholds.get("gflops_reduction_min", 0.3):
            alerts.append({
                "type": "gflops_reduction_low",
                "message": f"GFLOPs reduction ({snapshot.gflops_reduction:.2%}) below threshold",
                "threshold": thresholds.get("gflops_reduction_min", 0.3),
                "actual": snapshot.gflops_reduction
            })
        
        # Check accuracy retention
        if snapshot.accuracy_retention < thresholds.get("accuracy_retention_min", 0.95):
            alerts.append({
                "type": "accuracy_retention_low",
                "message": f"Accuracy retention ({snapshot.accuracy_retention:.2%}) below threshold",
                "threshold": thresholds.get("accuracy_retention_min", 0.95),
                "actual": snapshot.accuracy_retention
            })
        
        # Check latency increase
        latency_increase = (snapshot.latency_optimized - snapshot.latency_baseline) / snapshot.latency_baseline
        if latency_increase > thresholds.get("latency_increase_max", 0.1):
            alerts.append({
                "type": "latency_increase_high",
                "message": f"Latency increase ({latency_increase:.2%}) above threshold",
                "threshold": thresholds.get("latency_increase_max", 0.1),
                "actual": latency_increase
            })
        
        # Check optimization overhead
        if snapshot.optimization_overhead > thresholds.get("optimization_overhead_max", 0.05):
            alerts.append({
                "type": "optimization_overhead_high",
                "message": f"Optimization overhead ({snapshot.optimization_overhead:.2%}) above threshold",
                "threshold": thresholds.get("optimization_overhead_max", 0.05),
                "actual": snapshot.optimization_overhead
            })
        
        # Store and log alerts
        for alert in alerts:
            alert["timestamp"] = snapshot.timestamp
            self.alerts_triggered.append(alert)
            logger.warning(f"WINA Performance Alert: {alert['message']}")
    
    def get_performance_summary(self, window_minutes: Optional[int] = None) -> Dict[str, Any]:
        """
        Get performance summary for a time window.
        
        Args:
            window_minutes: Time window in minutes (None for all data)
            
        Returns:
            Dictionary containing performance summary
        """
        if not self.snapshots:
            return {"error": "No performance data available"}
        
        # Filter snapshots by time window if specified
        snapshots = list(self.snapshots)
        if window_minutes:
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
            snapshots = [s for s in snapshots if s.timestamp >= cutoff_time]
        
        if not snapshots:
            return {"error": "No data in specified time window"}
        
        # Calculate summary statistics
        gflops_reductions = [s.gflops_reduction for s in snapshots]
        accuracy_retentions = [s.accuracy_retention for s in snapshots]
        sparsities = [s.sparsity_achieved for s in snapshots]
        
        summary = {
            "time_window_minutes": window_minutes,
            "total_snapshots": len(snapshots),
            "gflops_reduction": {
                "mean": np.mean(gflops_reductions),
                "std": np.std(gflops_reductions),
                "min": np.min(gflops_reductions),
                "max": np.max(gflops_reductions)
            },
            "accuracy_retention": {
                "mean": np.mean(accuracy_retentions),
                "std": np.std(accuracy_retentions),
                "min": np.min(accuracy_retentions),
                "max": np.max(accuracy_retentions)
            },
            "sparsity_achieved": {
                "mean": np.mean(sparsities),
                "std": np.std(sparsities),
                "min": np.min(sparsities),
                "max": np.max(sparsities)
            },
            "alerts_in_window": len([a for a in self.alerts_triggered 
                                   if not window_minutes or 
                                   a["timestamp"] >= datetime.now(timezone.utc) - timedelta(minutes=window_minutes)])
        }
        
        return summary


class WINAMetrics:
    """
    Main WINA metrics collection and management class.
    
    This class coordinates all WINA metrics collection, including
    GFLOPs tracking, performance monitoring, and alerting.
    """
    
    def __init__(self, wina_config: WINAConfig, metrics_config: Optional[WINAMetricsConfig] = None):
        """
        Initialize WINA metrics.
        
        Args:
            wina_config: WINA configuration
            metrics_config: Optional metrics configuration
        """
        self.wina_config = wina_config
        self.metrics_config = metrics_config or WINAMetricsConfig()
        
        self.gflops_tracker = GFLOPsTracker()
        self.performance_monitor = PerformanceMonitor(self.metrics_config)
        
        # Metrics storage
        self.optimization_history: List[Dict[str, Any]] = []
        self.current_metrics: Dict[str, float] = {}
        
        logger.info("Initialized WINA metrics collection system")
    
    async def record_optimization(self, optimization_result: Any) -> None:
        """
        Record an optimization result.
        
        Args:
            optimization_result: Result from WINA optimization
        """
        try:
            # Extract metrics from optimization result
            metrics = optimization_result.performance_metrics
            accuracy_metrics = optimization_result.accuracy_metrics
            
            # Create performance snapshot
            snapshot = WINAPerformanceSnapshot(
                timestamp=datetime.now(timezone.utc),
                gflops_baseline=metrics.get("baseline_gflops", 0.0),
                gflops_optimized=metrics.get("optimized_gflops", 0.0),
                gflops_reduction=metrics.get("gflops_reduction", 0.0),
                accuracy_baseline=1.0,  # Placeholder
                accuracy_optimized=accuracy_metrics.get("estimated_accuracy_retention", 0.95),
                accuracy_retention=accuracy_metrics.get("estimated_accuracy_retention", 0.95),
                latency_baseline=1.0,  # Placeholder
                latency_optimized=1.0,  # Placeholder
                sparsity_achieved=metrics.get("average_sparsity", 0.0),
                optimization_overhead=optimization_result.optimization_time
            )
            
            # Record snapshot
            self.performance_monitor.record_performance_snapshot(snapshot)
            
            # Store in history
            self.optimization_history.append({
                "timestamp": snapshot.timestamp.isoformat(),
                "success": optimization_result.success,
                "metrics": metrics,
                "accuracy_metrics": accuracy_metrics
            })
            
            # Update current metrics
            self.current_metrics.update(metrics)
            
        except Exception as e:
            logger.error(f"Failed to record optimization metrics: {e}")
            raise WINAMetricsError(f"Optimization recording failed: {e}")
    
    async def get_current_metrics(self) -> Dict[str, Any]:
        """
        Get current WINA metrics.
        
        Returns:
            Dictionary of current metrics
        """
        return {
            "current_metrics": self.current_metrics.copy(),
            "performance_summary": self.performance_monitor.get_performance_summary(window_minutes=60),
            "gflops_breakdown": self.gflops_tracker.get_layer_breakdown(),
            "total_optimizations": len(self.optimization_history),
            "monitoring_active": self.performance_monitor.monitoring_active
        }
    
    async def start_monitoring(self) -> None:
        """Start metrics monitoring."""
        await self.performance_monitor.start_monitoring()
    
    async def stop_monitoring(self) -> None:
        """Stop metrics monitoring."""
        await self.performance_monitor.stop_monitoring()
