"""
WINA Comprehensive Performance Monitoring System

This module implements the comprehensive performance monitoring and metrics
collection system for WINA (Weight Informed Neuron Activation) integration,
providing real-time insights, analytics, and reporting capabilities.

Key Features:
- Centralized metrics collection from all WINA components
- Real-time performance dashboards and alerting
- Comprehensive analytics and trend analysis
- Integration metrics for Rego Policy Synthesis, EC Layer Oversight, etc.
- Health monitoring and system status tracking
- Export capabilities for metrics data
"""

import asyncio
import logging
import time
import json
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque
from enum import Enum
import numpy as np
import statistics

try:
    from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

from .config import WINAConfig
from .exceptions import WINAMetricsError
from .metrics import WINAMetrics, WINAPerformanceSnapshot, GFLOPsTracker

logger = logging.getLogger(__name__)


class WINAMonitoringLevel(Enum):
    """Monitoring detail levels."""
    BASIC = "basic"
    DETAILED = "detailed"  
    COMPREHENSIVE = "comprehensive"
    DEBUG = "debug"


class WINAComponentType(Enum):
    """WINA component types for metrics tracking."""
    CORE_OPTIMIZATION = "core_optimization"
    REGO_POLICY_SYNTHESIS = "rego_policy_synthesis"
    EC_LAYER_OVERSIGHT = "ec_layer_oversight"
    PGC_ENFORCEMENT = "pgc_enforcement"
    CONSTITUTIONAL_INTEGRATION = "constitutional_integration"
    SVD_TRANSFORMATION = "svd_transformation"
    DYNAMIC_GATING = "dynamic_gating"
    NEURON_ACTIVATION = "neuron_activation"
    LEARNING_FEEDBACK = "learning_feedback"


@dataclass
class WINANeuronActivationMetrics:
    """Metrics for neuron activation tracking."""
    layer_name: str
    total_neurons: int
    active_neurons: int
    deactivated_neurons: int
    activation_ratio: float
    activation_scores_mean: float
    activation_scores_std: float
    performance_impact_ms: float
    energy_savings_ratio: float
    timestamp: datetime


@dataclass
class WINASVDTransformationMetrics:
    """Metrics for SVD transformation operations."""
    layer_name: str
    original_rank: int
    reduced_rank: int
    rank_reduction_ratio: float
    svd_computation_time_ms: float
    reconstruction_error: float
    compression_ratio: float
    memory_savings_mb: float
    timestamp: datetime


@dataclass
class WINADynamicGatingMetrics:
    """Metrics for dynamic gating decisions."""
    gate_id: str
    gating_strategy: str
    threshold_value: float
    gates_activated: int
    gates_total: int
    gating_efficiency: float
    decision_latency_ms: float
    accuracy_impact: float
    resource_savings: float
    timestamp: datetime


@dataclass 
class WINAConstitutionalComplianceMetrics:
    """Metrics for constitutional compliance monitoring."""
    component_type: str
    principles_evaluated: int
    compliance_score: float
    violations_detected: int
    compliance_check_time_ms: float
    constitutional_overhead_ratio: float
    principle_adherence_breakdown: Dict[str, float]
    remediation_actions_taken: int
    timestamp: datetime


@dataclass
class WINALearningFeedbackMetrics:
    """Metrics for learning and adaptation tracking."""
    feedback_source: str
    adaptation_type: str
    learning_accuracy: float
    adaptation_effectiveness: float
    feedback_processing_time_ms: float
    model_update_size_mb: float
    convergence_rate: float
    feedback_quality_score: float
    timestamp: datetime


@dataclass
class WINAIntegrationMetrics:
    """Metrics for component integration performance."""
    integration_type: str
    source_component: str
    target_component: str
    integration_latency_ms: float
    data_transfer_mb: float
    synchronization_overhead_ms: float
    integration_success_rate: float
    error_count: int
    performance_improvement_ratio: float
    timestamp: datetime


@dataclass
class WINASystemHealthMetrics:
    """Overall system health metrics."""
    cpu_utilization_percent: float
    memory_utilization_percent: float
    gpu_utilization_percent: float
    throughput_ops_per_second: float
    error_rate_percent: float
    availability_percent: float
    response_time_p95_ms: float
    concurrent_operations: int
    timestamp: datetime


@dataclass
class WINAPerformanceReport:
    """Comprehensive performance report."""
    report_id: str
    reporting_period: Tuple[datetime, datetime]
    overall_gflops_reduction: float
    overall_accuracy_retention: float
    constitutional_compliance_rate: float
    total_operations: int
    performance_targets_met: bool
    component_metrics: Dict[str, Any]
    integration_metrics: Dict[str, Any]
    health_metrics: Dict[str, Any]
    alerts_triggered: List[Dict[str, Any]]
    recommendations: List[str]
    trends: Dict[str, Any]
    timestamp: datetime


class WINAPerformanceCollector:
    """
    Centralized performance metrics collector for all WINA components.
    
    Aggregates metrics from all WINA components and provides unified
    access to performance data with real-time monitoring capabilities.
    """
    
    def __init__(self, monitoring_level: WINAMonitoringLevel = WINAMonitoringLevel.DETAILED):
        """
        Initialize WINA performance collector.
        
        Args:
            monitoring_level: Level of monitoring detail
        """
        self.monitoring_level = monitoring_level
        
        # Metrics storage by component type
        self.neuron_activation_metrics: deque = deque(maxlen=10000)
        self.svd_transformation_metrics: deque = deque(maxlen=5000)
        self.dynamic_gating_metrics: deque = deque(maxlen=10000)
        self.constitutional_compliance_metrics: deque = deque(maxlen=5000)
        self.learning_feedback_metrics: deque = deque(maxlen=5000)
        self.integration_metrics: deque = deque(maxlen=10000)
        self.system_health_metrics: deque = deque(maxlen=1000)
        
        # Component-specific metrics storage
        self.component_metrics: Dict[WINAComponentType, deque] = {
            component_type: deque(maxlen=5000) for component_type in WINAComponentType
        }
        
        # Performance tracking
        self.performance_snapshots: deque = deque(maxlen=1000)
        self.alerts_history: deque = deque(maxlen=1000)
        
        # Real-time monitoring
        self.real_time_metrics: Dict[str, Any] = {}
        self.monitoring_active = False
        self.collection_interval = 30  # seconds
        
        # Prometheus metrics
        if PROMETHEUS_AVAILABLE:
            self.registry = CollectorRegistry()
            self._setup_prometheus_metrics()
        
        logger.info(f"WINA Performance Collector initialized with {monitoring_level.value} monitoring")
    
    def _setup_prometheus_metrics(self) -> None:
        """Setup Prometheus metrics collectors."""
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.prometheus_metrics = {
            # Core performance metrics
            "gflops_reduction": Gauge(
                "wina_gflops_reduction_ratio",
                "WINA GFLOPs reduction ratio",
                ["component"],
                registry=self.registry
            ),
            "accuracy_retention": Gauge(
                "wina_accuracy_retention_ratio",
                "WINA accuracy retention ratio", 
                ["component"],
                registry=self.registry
            ),
            "constitutional_compliance": Gauge(
                "wina_constitutional_compliance_score",
                "WINA constitutional compliance score",
                ["component"],
                registry=self.registry
            ),
            
            # Component-specific metrics
            "neuron_activation_ratio": Gauge(
                "wina_neuron_activation_ratio",
                "WINA neuron activation ratio",
                ["layer"],
                registry=self.registry
            ),
            "svd_compression_ratio": Gauge(
                "wina_svd_compression_ratio", 
                "WINA SVD compression ratio",
                ["layer"],
                registry=self.registry
            ),
            "gating_efficiency": Gauge(
                "wina_gating_efficiency",
                "WINA dynamic gating efficiency",
                ["gate_id"],
                registry=self.registry
            ),
            
            # Performance counters
            "operations_total": Counter(
                "wina_operations_total",
                "Total WINA operations",
                ["component", "operation_type"],
                registry=self.registry
            ),
            "operation_duration": Histogram(
                "wina_operation_duration_seconds",
                "WINA operation duration",
                ["component", "operation_type"],
                registry=self.registry
            ),
            "integration_latency": Histogram(
                "wina_integration_latency_seconds",
                "WINA component integration latency",
                ["source", "target"],
                registry=self.registry
            ),
            
            # System health metrics
            "system_cpu_utilization": Gauge(
                "wina_system_cpu_utilization_percent",
                "WINA system CPU utilization",
                registry=self.registry
            ),
            "system_memory_utilization": Gauge(
                "wina_system_memory_utilization_percent", 
                "WINA system memory utilization",
                registry=self.registry
            ),
            "system_error_rate": Gauge(
                "wina_system_error_rate_percent",
                "WINA system error rate",
                registry=self.registry
            )
        }
        
        logger.debug("Prometheus metrics setup completed")
    
    async def start_monitoring(self) -> None:
        """Start real-time performance monitoring."""
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
        """Main monitoring loop for real-time metrics collection."""
        while self.monitoring_active:
            try:
                await asyncio.sleep(self.collection_interval)
                await self._collect_real_time_metrics()
                await self._check_performance_alerts()
                await self._update_prometheus_metrics()
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)
    
    async def record_neuron_activation_metrics(self, metrics: WINANeuronActivationMetrics) -> None:
        """Record neuron activation metrics."""
        try:
            self.neuron_activation_metrics.append(metrics)
            
            # Update Prometheus metrics
            if PROMETHEUS_AVAILABLE and hasattr(self, 'prometheus_metrics'):
                self.prometheus_metrics["neuron_activation_ratio"].labels(
                    layer=metrics.layer_name
                ).set(metrics.activation_ratio)
            
            logger.debug(f"Recorded neuron activation metrics for layer {metrics.layer_name}")
            
        except Exception as e:
            logger.error(f"Failed to record neuron activation metrics: {e}")
            raise WINAMetricsError(f"Neuron activation metrics recording failed: {e}")
    
    async def record_svd_transformation_metrics(self, metrics: WINASVDTransformationMetrics) -> None:
        """Record SVD transformation metrics."""
        try:
            self.svd_transformation_metrics.append(metrics)
            
            # Update Prometheus metrics
            if PROMETHEUS_AVAILABLE and hasattr(self, 'prometheus_metrics'):
                self.prometheus_metrics["svd_compression_ratio"].labels(
                    layer=metrics.layer_name
                ).set(metrics.compression_ratio)
            
            logger.debug(f"Recorded SVD transformation metrics for layer {metrics.layer_name}")
            
        except Exception as e:
            logger.error(f"Failed to record SVD transformation metrics: {e}")
            raise WINAMetricsError(f"SVD transformation metrics recording failed: {e}")
    
    async def record_dynamic_gating_metrics(self, metrics: WINADynamicGatingMetrics) -> None:
        """Record dynamic gating metrics."""
        try:
            self.dynamic_gating_metrics.append(metrics)
            
            # Update Prometheus metrics
            if PROMETHEUS_AVAILABLE and hasattr(self, 'prometheus_metrics'):
                self.prometheus_metrics["gating_efficiency"].labels(
                    gate_id=metrics.gate_id
                ).set(metrics.gating_efficiency)
            
            logger.debug(f"Recorded dynamic gating metrics for gate {metrics.gate_id}")
            
        except Exception as e:
            logger.error(f"Failed to record dynamic gating metrics: {e}")
            raise WINAMetricsError(f"Dynamic gating metrics recording failed: {e}")
    
    async def record_constitutional_compliance_metrics(self, metrics: WINAConstitutionalComplianceMetrics) -> None:
        """Record constitutional compliance metrics."""
        try:
            self.constitutional_compliance_metrics.append(metrics)
            
            # Update Prometheus metrics
            if PROMETHEUS_AVAILABLE and hasattr(self, 'prometheus_metrics'):
                self.prometheus_metrics["constitutional_compliance"].labels(
                    component=metrics.component_type
                ).set(metrics.compliance_score)
            
            logger.debug(f"Recorded constitutional compliance metrics for {metrics.component_type}")
            
        except Exception as e:
            logger.error(f"Failed to record constitutional compliance metrics: {e}")
            raise WINAMetricsError(f"Constitutional compliance metrics recording failed: {e}")
    
    async def record_learning_feedback_metrics(self, metrics: WINALearningFeedbackMetrics) -> None:
        """Record learning feedback metrics."""
        try:
            self.learning_feedback_metrics.append(metrics)
            
            logger.debug(f"Recorded learning feedback metrics from {metrics.feedback_source}")
            
        except Exception as e:
            logger.error(f"Failed to record learning feedback metrics: {e}")
            raise WINAMetricsError(f"Learning feedback metrics recording failed: {e}")
    
    async def record_integration_metrics(self, metrics: WINAIntegrationMetrics) -> None:
        """Record component integration metrics."""
        try:
            self.integration_metrics.append(metrics)
            
            # Update Prometheus metrics
            if PROMETHEUS_AVAILABLE and hasattr(self, 'prometheus_metrics'):
                self.prometheus_metrics["integration_latency"].labels(
                    source=metrics.source_component,
                    target=metrics.target_component
                ).observe(metrics.integration_latency_ms / 1000.0)
            
            logger.debug(f"Recorded integration metrics: {metrics.source_component} -> {metrics.target_component}")
            
        except Exception as e:
            logger.error(f"Failed to record integration metrics: {e}")
            raise WINAMetricsError(f"Integration metrics recording failed: {e}")
    
    async def record_system_health_metrics(self, metrics: WINASystemHealthMetrics) -> None:
        """Record system health metrics."""
        try:
            self.system_health_metrics.append(metrics)
            
            # Update Prometheus metrics
            if PROMETHEUS_AVAILABLE and hasattr(self, 'prometheus_metrics'):
                self.prometheus_metrics["system_cpu_utilization"].set(metrics.cpu_utilization_percent)
                self.prometheus_metrics["system_memory_utilization"].set(metrics.memory_utilization_percent)
                self.prometheus_metrics["system_error_rate"].set(metrics.error_rate_percent)
            
            logger.debug("Recorded system health metrics")
            
        except Exception as e:
            logger.error(f"Failed to record system health metrics: {e}")
            raise WINAMetricsError(f"System health metrics recording failed: {e}")
    
    async def record_component_operation(self, component: WINAComponentType, operation_type: str, 
                                       duration_ms: float, success: bool = True) -> None:
        """Record a component operation for tracking."""
        try:
            # Update Prometheus counters
            if PROMETHEUS_AVAILABLE and hasattr(self, 'prometheus_metrics'):
                self.prometheus_metrics["operations_total"].labels(
                    component=component.value,
                    operation_type=operation_type
                ).inc()
                
                self.prometheus_metrics["operation_duration"].labels(
                    component=component.value,
                    operation_type=operation_type
                ).observe(duration_ms / 1000.0)
            
            # Store in component metrics
            operation_data = {
                "operation_type": operation_type,
                "duration_ms": duration_ms,
                "success": success,
                "timestamp": datetime.now(timezone.utc)
            }
            self.component_metrics[component].append(operation_data)
            
            logger.debug(f"Recorded {component.value} operation: {operation_type}")
            
        except Exception as e:
            logger.error(f"Failed to record component operation: {e}")
    
    async def _collect_real_time_metrics(self) -> None:
        """Collect real-time metrics for monitoring."""
        try:
            current_time = datetime.now(timezone.utc)
            
            # Calculate real-time performance metrics
            self.real_time_metrics = {
                "timestamp": current_time.isoformat(),
                "neuron_activation": await self._calculate_neuron_activation_summary(),
                "svd_transformation": await self._calculate_svd_transformation_summary(),
                "dynamic_gating": await self._calculate_dynamic_gating_summary(),
                "constitutional_compliance": await self._calculate_constitutional_compliance_summary(),
                "learning_feedback": await self._calculate_learning_feedback_summary(),
                "integration_performance": await self._calculate_integration_performance_summary(),
                "system_health": await self._calculate_system_health_summary(),
                "overall_performance": await self._calculate_overall_performance_summary()
            }
            
        except Exception as e:
            logger.error(f"Real-time metrics collection failed: {e}")
    
    async def _calculate_neuron_activation_summary(self) -> Dict[str, Any]:
        """Calculate neuron activation summary metrics."""
        if not self.neuron_activation_metrics:
            return {"total_layers": 0, "avg_activation_ratio": 0.0}
        
        recent_metrics = [m for m in self.neuron_activation_metrics 
                         if datetime.now(timezone.utc) - m.timestamp < timedelta(minutes=10)]
        
        if not recent_metrics:
            return {"total_layers": 0, "avg_activation_ratio": 0.0}
        
        return {
            "total_layers": len(set(m.layer_name for m in recent_metrics)),
            "avg_activation_ratio": statistics.mean(m.activation_ratio for m in recent_metrics),
            "avg_performance_impact_ms": statistics.mean(m.performance_impact_ms for m in recent_metrics),
            "avg_energy_savings": statistics.mean(m.energy_savings_ratio for m in recent_metrics),
            "total_neurons_managed": sum(m.total_neurons for m in recent_metrics),
            "total_neurons_active": sum(m.active_neurons for m in recent_metrics)
        }
    
    async def _calculate_svd_transformation_summary(self) -> Dict[str, Any]:
        """Calculate SVD transformation summary metrics."""
        if not self.svd_transformation_metrics:
            return {"total_transformations": 0, "avg_compression_ratio": 0.0}
        
        recent_metrics = [m for m in self.svd_transformation_metrics
                         if datetime.now(timezone.utc) - m.timestamp < timedelta(minutes=10)]
        
        if not recent_metrics:
            return {"total_transformations": 0, "avg_compression_ratio": 0.0}
        
        return {
            "total_transformations": len(recent_metrics),
            "avg_compression_ratio": statistics.mean(m.compression_ratio for m in recent_metrics),
            "avg_rank_reduction": statistics.mean(m.rank_reduction_ratio for m in recent_metrics),
            "avg_computation_time_ms": statistics.mean(m.svd_computation_time_ms for m in recent_metrics),
            "total_memory_savings_mb": sum(m.memory_savings_mb for m in recent_metrics),
            "avg_reconstruction_error": statistics.mean(m.reconstruction_error for m in recent_metrics)
        }
    
    async def _calculate_dynamic_gating_summary(self) -> Dict[str, Any]:
        """Calculate dynamic gating summary metrics."""
        if not self.dynamic_gating_metrics:
            return {"total_gates": 0, "avg_gating_efficiency": 0.0}
        
        recent_metrics = [m for m in self.dynamic_gating_metrics
                         if datetime.now(timezone.utc) - m.timestamp < timedelta(minutes=10)]
        
        if not recent_metrics:
            return {"total_gates": 0, "avg_gating_efficiency": 0.0}
        
        return {
            "total_gates": len(set(m.gate_id for m in recent_metrics)),
            "avg_gating_efficiency": statistics.mean(m.gating_efficiency for m in recent_metrics),
            "avg_decision_latency_ms": statistics.mean(m.decision_latency_ms for m in recent_metrics),
            "avg_resource_savings": statistics.mean(m.resource_savings for m in recent_metrics),
            "total_gates_activated": sum(m.gates_activated for m in recent_metrics),
            "gating_strategies": list(set(m.gating_strategy for m in recent_metrics))
        }
    
    async def _calculate_constitutional_compliance_summary(self) -> Dict[str, Any]:
        """Calculate constitutional compliance summary metrics."""
        if not self.constitutional_compliance_metrics:
            return {"avg_compliance_score": 1.0, "total_violations": 0}
        
        recent_metrics = [m for m in self.constitutional_compliance_metrics
                         if datetime.now(timezone.utc) - m.timestamp < timedelta(minutes=10)]
        
        if not recent_metrics:
            return {"avg_compliance_score": 1.0, "total_violations": 0}
        
        return {
            "avg_compliance_score": statistics.mean(m.compliance_score for m in recent_metrics),
            "total_violations": sum(m.violations_detected for m in recent_metrics),
            "total_principles_evaluated": sum(m.principles_evaluated for m in recent_metrics),
            "avg_check_time_ms": statistics.mean(m.compliance_check_time_ms for m in recent_metrics),
            "components_monitored": len(set(m.component_type for m in recent_metrics)),
            "remediation_actions": sum(m.remediation_actions_taken for m in recent_metrics)
        }
    
    async def _calculate_learning_feedback_summary(self) -> Dict[str, Any]:
        """Calculate learning feedback summary metrics."""
        if not self.learning_feedback_metrics:
            return {"total_adaptations": 0, "avg_effectiveness": 0.0}
        
        recent_metrics = [m for m in self.learning_feedback_metrics
                         if datetime.now(timezone.utc) - m.timestamp < timedelta(minutes=10)]
        
        if not recent_metrics:
            return {"total_adaptations": 0, "avg_effectiveness": 0.0}
        
        return {
            "total_adaptations": len(recent_metrics),
            "avg_effectiveness": statistics.mean(m.adaptation_effectiveness for m in recent_metrics),
            "avg_learning_accuracy": statistics.mean(m.learning_accuracy for m in recent_metrics),
            "avg_convergence_rate": statistics.mean(m.convergence_rate for m in recent_metrics),
            "feedback_sources": list(set(m.feedback_source for m in recent_metrics)),
            "adaptation_types": list(set(m.adaptation_type for m in recent_metrics))
        }
    
    async def _calculate_integration_performance_summary(self) -> Dict[str, Any]:
        """Calculate integration performance summary metrics."""
        if not self.integration_metrics:
            return {"total_integrations": 0, "avg_latency_ms": 0.0}
        
        recent_metrics = [m for m in self.integration_metrics
                         if datetime.now(timezone.utc) - m.timestamp < timedelta(minutes=10)]
        
        if not recent_metrics:
            return {"total_integrations": 0, "avg_latency_ms": 0.0}
        
        return {
            "total_integrations": len(recent_metrics),
            "avg_latency_ms": statistics.mean(m.integration_latency_ms for m in recent_metrics),
            "avg_success_rate": statistics.mean(m.integration_success_rate for m in recent_metrics),
            "total_data_transferred_mb": sum(m.data_transfer_mb for m in recent_metrics),
            "avg_performance_improvement": statistics.mean(m.performance_improvement_ratio for m in recent_metrics),
            "integration_pairs": len(set(f"{m.source_component}->{m.target_component}" for m in recent_metrics))
        }
    
    async def _calculate_system_health_summary(self) -> Dict[str, Any]:
        """Calculate system health summary metrics."""
        if not self.system_health_metrics:
            return {"status": "unknown", "availability": 0.0}
        
        recent_metrics = [m for m in self.system_health_metrics
                         if datetime.now(timezone.utc) - m.timestamp < timedelta(minutes=5)]
        
        if not recent_metrics:
            return {"status": "unknown", "availability": 0.0}
        
        latest_metric = recent_metrics[-1]
        avg_error_rate = statistics.mean(m.error_rate_percent for m in recent_metrics)
        
        status = "healthy"
        if avg_error_rate > 5.0 or latest_metric.cpu_utilization_percent > 90:
            status = "degraded"
        if avg_error_rate > 10.0 or latest_metric.availability_percent < 95:
            status = "critical"
        
        return {
            "status": status,
            "availability": latest_metric.availability_percent,
            "cpu_utilization": latest_metric.cpu_utilization_percent,
            "memory_utilization": latest_metric.memory_utilization_percent,
            "error_rate": avg_error_rate,
            "throughput": latest_metric.throughput_ops_per_second,
            "response_time_p95": latest_metric.response_time_p95_ms
        }
    
    async def _calculate_overall_performance_summary(self) -> Dict[str, Any]:
        """Calculate overall WINA performance summary."""
        try:
            # Calculate overall GFLOPs reduction
            gflops_reduction = 0.0
            if self.neuron_activation_metrics and self.svd_transformation_metrics:
                neuron_savings = statistics.mean(m.energy_savings_ratio for m in self.neuron_activation_metrics[-10:]) if self.neuron_activation_metrics else 0.0
                svd_savings = statistics.mean(m.compression_ratio for m in self.svd_transformation_metrics[-10:]) if self.svd_transformation_metrics else 0.0
                gflops_reduction = min((neuron_savings + svd_savings) / 2, 0.7)  # Cap at 70%
            
            # Calculate overall accuracy retention
            accuracy_retention = 0.95  # Default target
            if self.constitutional_compliance_metrics:
                accuracy_retention = min(
                    statistics.mean(m.compliance_score for m in self.constitutional_compliance_metrics[-10:]),
                    1.0
                )
            
            # Check performance targets
            targets_met = (
                gflops_reduction >= 0.4 and  # 40% minimum
                gflops_reduction <= 0.7 and  # 70% maximum
                accuracy_retention >= 0.95   # 95% minimum
            )
            
            return {
                "gflops_reduction_achieved": gflops_reduction,
                "accuracy_retention": accuracy_retention,
                "constitutional_compliance_rate": accuracy_retention,
                "performance_targets_met": targets_met,
                "efficiency_score": (gflops_reduction + accuracy_retention) / 2,
                "optimization_status": "optimal" if targets_met else "needs_tuning"
            }
            
        except Exception as e:
            logger.error(f"Overall performance summary calculation failed: {e}")
            return {
                "gflops_reduction_achieved": 0.0,
                "accuracy_retention": 0.95,
                "constitutional_compliance_rate": 0.95,
                "performance_targets_met": False,
                "efficiency_score": 0.0,
                "optimization_status": "error"
            }
    
    async def _check_performance_alerts(self) -> None:
        """Check for performance alerts and trigger notifications."""
        try:
            alerts = []
            current_time = datetime.now(timezone.utc)
            
            # Check GFLOPs reduction target
            overall_perf = self.real_time_metrics.get("overall_performance", {})
            gflops_reduction = overall_perf.get("gflops_reduction_achieved", 0.0)
            
            if gflops_reduction < 0.4:
                alerts.append({
                    "type": "performance_degradation",
                    "severity": "warning",
                    "message": f"GFLOPs reduction ({gflops_reduction:.1%}) below 40% target",
                    "timestamp": current_time,
                    "metric": "gflops_reduction",
                    "threshold": 0.4,
                    "actual": gflops_reduction
                })
            
            # Check accuracy retention
            accuracy_retention = overall_perf.get("accuracy_retention", 0.95)
            if accuracy_retention < 0.95:
                alerts.append({
                    "type": "accuracy_degradation",
                    "severity": "critical",
                    "message": f"Accuracy retention ({accuracy_retention:.1%}) below 95% target",
                    "timestamp": current_time,
                    "metric": "accuracy_retention",
                    "threshold": 0.95,
                    "actual": accuracy_retention
                })
            
            # Check system health
            system_health = self.real_time_metrics.get("system_health", {})
            if system_health.get("status") == "critical":
                alerts.append({
                    "type": "system_health_critical",
                    "severity": "critical",
                    "message": "System health status is critical",
                    "timestamp": current_time,
                    "metric": "system_health",
                    "details": system_health
                })
            
            # Store alerts
            for alert in alerts:
                self.alerts_history.append(alert)
                logger.warning(f"WINA Performance Alert: {alert['message']}")
            
        except Exception as e:
            logger.error(f"Performance alert checking failed: {e}")
    
    async def _update_prometheus_metrics(self) -> None:
        """Update Prometheus metrics with current values."""
        if not PROMETHEUS_AVAILABLE or not hasattr(self, 'prometheus_metrics'):
            return
        
        try:
            overall_perf = self.real_time_metrics.get("overall_performance", {})
            
            # Update core performance metrics
            for component in WINAComponentType:
                self.prometheus_metrics["gflops_reduction"].labels(
                    component=component.value
                ).set(overall_perf.get("gflops_reduction_achieved", 0.0))
                
                self.prometheus_metrics["accuracy_retention"].labels(
                    component=component.value
                ).set(overall_perf.get("accuracy_retention", 0.95))
            
        except Exception as e:
            logger.error(f"Prometheus metrics update failed: {e}")
    
    async def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get current real-time metrics."""
        return self.real_time_metrics.copy()
    
    async def get_performance_report(self, 
                                   start_time: Optional[datetime] = None,
                                   end_time: Optional[datetime] = None) -> WINAPerformanceReport:
        """
        Generate comprehensive performance report.
        
        Args:
            start_time: Report start time (default: 24 hours ago)
            end_time: Report end time (default: now)
            
        Returns:
            WINAPerformanceReport with comprehensive analytics
        """
        if end_time is None:
            end_time = datetime.now(timezone.utc)
        if start_time is None:
            start_time = end_time - timedelta(hours=24)
        
        try:
            # Filter metrics by time range
            filtered_metrics = await self._filter_metrics_by_time_range(start_time, end_time)
            
            # Calculate overall performance
            overall_metrics = await self._calculate_report_overall_metrics(filtered_metrics)
            
            # Calculate component metrics
            component_metrics = await self._calculate_report_component_metrics(filtered_metrics)
            
            # Calculate integration metrics
            integration_metrics = await self._calculate_report_integration_metrics(filtered_metrics)
            
            # Calculate health metrics
            health_metrics = await self._calculate_report_health_metrics(filtered_metrics)
            
            # Get alerts for period
            period_alerts = [
                alert for alert in self.alerts_history
                if start_time <= alert["timestamp"] <= end_time
            ]
            
            # Generate recommendations
            recommendations = await self._generate_performance_recommendations(
                overall_metrics, component_metrics, health_metrics
            )
            
            # Calculate trends
            trends = await self._calculate_performance_trends(filtered_metrics, start_time, end_time)
            
            report = WINAPerformanceReport(
                report_id=f"WINA_PERF_REPORT_{int(end_time.timestamp())}",
                reporting_period=(start_time, end_time),
                overall_gflops_reduction=overall_metrics.get("gflops_reduction", 0.0),
                overall_accuracy_retention=overall_metrics.get("accuracy_retention", 0.95),
                constitutional_compliance_rate=overall_metrics.get("compliance_rate", 0.95),
                total_operations=overall_metrics.get("total_operations", 0),
                performance_targets_met=overall_metrics.get("targets_met", False),
                component_metrics=component_metrics,
                integration_metrics=integration_metrics,
                health_metrics=health_metrics,
                alerts_triggered=period_alerts,
                recommendations=recommendations,
                trends=trends,
                timestamp=datetime.now(timezone.utc)
            )
            
            logger.info(f"Generated WINA performance report: {report.report_id}")
            return report
            
        except Exception as e:
            logger.error(f"Performance report generation failed: {e}")
            raise WINAMetricsError(f"Performance report generation failed: {e}")
    
    async def _filter_metrics_by_time_range(self, start_time: datetime, end_time: datetime) -> Dict[str, List]:
        """Filter all metrics by time range."""
        return {
            "neuron_activation": [m for m in self.neuron_activation_metrics if start_time <= m.timestamp <= end_time],
            "svd_transformation": [m for m in self.svd_transformation_metrics if start_time <= m.timestamp <= end_time],
            "dynamic_gating": [m for m in self.dynamic_gating_metrics if start_time <= m.timestamp <= end_time],
            "constitutional_compliance": [m for m in self.constitutional_compliance_metrics if start_time <= m.timestamp <= end_time],
            "learning_feedback": [m for m in self.learning_feedback_metrics if start_time <= m.timestamp <= end_time],
            "integration": [m for m in self.integration_metrics if start_time <= m.timestamp <= end_time],
            "system_health": [m for m in self.system_health_metrics if start_time <= m.timestamp <= end_time]
        }
    
    async def _calculate_report_overall_metrics(self, filtered_metrics: Dict[str, List]) -> Dict[str, Any]:
        """Calculate overall metrics for performance report."""
        try:
            # Calculate GFLOPs reduction from neuron activation and SVD
            gflops_reduction = 0.0
            if filtered_metrics["neuron_activation"] and filtered_metrics["svd_transformation"]:
                neuron_savings = statistics.mean(m.energy_savings_ratio for m in filtered_metrics["neuron_activation"])
                svd_compression = statistics.mean(m.compression_ratio for m in filtered_metrics["svd_transformation"])
                gflops_reduction = min((neuron_savings + svd_compression) / 2, 0.7)
            
            # Calculate accuracy retention from constitutional compliance
            accuracy_retention = 0.95
            if filtered_metrics["constitutional_compliance"]:
                accuracy_retention = statistics.mean(m.compliance_score for m in filtered_metrics["constitutional_compliance"])
            
            # Calculate total operations
            total_operations = sum(
                len(metrics) for metrics in filtered_metrics.values()
            )
            
            # Check if targets are met
            targets_met = (
                gflops_reduction >= 0.4 and
                gflops_reduction <= 0.7 and
                accuracy_retention >= 0.95
            )
            
            return {
                "gflops_reduction": gflops_reduction,
                "accuracy_retention": accuracy_retention,
                "compliance_rate": accuracy_retention,
                "total_operations": total_operations,
                "targets_met": targets_met
            }
            
        except Exception as e:
            logger.error(f"Overall metrics calculation failed: {e}")
            return {
                "gflops_reduction": 0.0,
                "accuracy_retention": 0.95,
                "compliance_rate": 0.95,
                "total_operations": 0,
                "targets_met": False
            }
    
    async def _calculate_report_component_metrics(self, filtered_metrics: Dict[str, List]) -> Dict[str, Any]:
        """Calculate component-specific metrics for performance report."""
        component_metrics = {}
        
        try:
            # Neuron activation metrics
            if filtered_metrics["neuron_activation"]:
                component_metrics["neuron_activation"] = {
                    "total_layers": len(set(m.layer_name for m in filtered_metrics["neuron_activation"])),
                    "avg_activation_ratio": statistics.mean(m.activation_ratio for m in filtered_metrics["neuron_activation"]),
                    "avg_energy_savings": statistics.mean(m.energy_savings_ratio for m in filtered_metrics["neuron_activation"]),
                    "total_neurons_managed": sum(m.total_neurons for m in filtered_metrics["neuron_activation"])
                }
            
            # SVD transformation metrics
            if filtered_metrics["svd_transformation"]:
                component_metrics["svd_transformation"] = {
                    "total_transformations": len(filtered_metrics["svd_transformation"]),
                    "avg_compression_ratio": statistics.mean(m.compression_ratio for m in filtered_metrics["svd_transformation"]),
                    "total_memory_savings_mb": sum(m.memory_savings_mb for m in filtered_metrics["svd_transformation"]),
                    "avg_computation_time_ms": statistics.mean(m.svd_computation_time_ms for m in filtered_metrics["svd_transformation"])
                }
            
            # Dynamic gating metrics
            if filtered_metrics["dynamic_gating"]:
                component_metrics["dynamic_gating"] = {
                    "total_gates": len(set(m.gate_id for m in filtered_metrics["dynamic_gating"])),
                    "avg_gating_efficiency": statistics.mean(m.gating_efficiency for m in filtered_metrics["dynamic_gating"]),
                    "avg_resource_savings": statistics.mean(m.resource_savings for m in filtered_metrics["dynamic_gating"]),
                    "total_gates_activated": sum(m.gates_activated for m in filtered_metrics["dynamic_gating"])
                }
            
        except Exception as e:
            logger.error(f"Component metrics calculation failed: {e}")
        
        return component_metrics
    
    async def _calculate_report_integration_metrics(self, filtered_metrics: Dict[str, List]) -> Dict[str, Any]:
        """Calculate integration metrics for performance report."""
        try:
            if not filtered_metrics["integration"]:
                return {}
            
            return {
                "total_integrations": len(filtered_metrics["integration"]),
                "avg_latency_ms": statistics.mean(m.integration_latency_ms for m in filtered_metrics["integration"]),
                "avg_success_rate": statistics.mean(m.integration_success_rate for m in filtered_metrics["integration"]),
                "total_data_transferred_mb": sum(m.data_transfer_mb for m in filtered_metrics["integration"]),
                "avg_performance_improvement": statistics.mean(m.performance_improvement_ratio for m in filtered_metrics["integration"]),
                "unique_integration_pairs": len(set(f"{m.source_component}->{m.target_component}" for m in filtered_metrics["integration"]))
            }
            
        except Exception as e:
            logger.error(f"Integration metrics calculation failed: {e}")
            return {}
    
    async def _calculate_report_health_metrics(self, filtered_metrics: Dict[str, List]) -> Dict[str, Any]:
        """Calculate health metrics for performance report."""
        try:
            if not filtered_metrics["system_health"]:
                return {}
            
            latest_health = filtered_metrics["system_health"][-1] if filtered_metrics["system_health"] else None
            
            return {
                "avg_cpu_utilization": statistics.mean(m.cpu_utilization_percent for m in filtered_metrics["system_health"]),
                "avg_memory_utilization": statistics.mean(m.memory_utilization_percent for m in filtered_metrics["system_health"]),
                "avg_error_rate": statistics.mean(m.error_rate_percent for m in filtered_metrics["system_health"]),
                "avg_availability": statistics.mean(m.availability_percent for m in filtered_metrics["system_health"]),
                "current_status": "healthy" if latest_health and latest_health.error_rate_percent < 5.0 else "degraded"
            }
            
        except Exception as e:
            logger.error(f"Health metrics calculation failed: {e}")
            return {}
    
    async def _generate_performance_recommendations(self, overall_metrics: Dict[str, Any],
                                                  component_metrics: Dict[str, Any],
                                                  health_metrics: Dict[str, Any]) -> List[str]:
        """Generate performance recommendations based on metrics."""
        recommendations = []
        
        try:
            # GFLOPs reduction recommendations
            gflops_reduction = overall_metrics.get("gflops_reduction", 0.0)
            if gflops_reduction < 0.4:
                recommendations.append("GFLOPs reduction below target - consider more aggressive neuron pruning")
            elif gflops_reduction > 0.7:
                recommendations.append("GFLOPs reduction very high - monitor accuracy retention carefully")
            
            # Accuracy recommendations
            accuracy = overall_metrics.get("accuracy_retention", 0.95)
            if accuracy < 0.95:
                recommendations.append("Accuracy retention below target - review constitutional compliance settings")
            
            # Component-specific recommendations
            if "neuron_activation" in component_metrics:
                activation_ratio = component_metrics["neuron_activation"].get("avg_activation_ratio", 0.0)
                if activation_ratio > 0.8:
                    recommendations.append("High neuron activation ratio - consider increasing sparsity targets")
            
            # Health recommendations
            if health_metrics.get("avg_error_rate", 0.0) > 5.0:
                recommendations.append("Elevated error rate detected - review system configuration")
            
            if not recommendations:
                recommendations.append("System performing within optimal parameters")
            
        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}")
            recommendations.append("Unable to generate recommendations due to analysis error")
        
        return recommendations
    
    async def _calculate_performance_trends(self, filtered_metrics: Dict[str, List],
                                          start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Calculate performance trends over the reporting period."""
        try:
            trends = {}
            
            # Calculate GFLOPs reduction trend
            if filtered_metrics["neuron_activation"]:
                energy_savings = [m.energy_savings_ratio for m in filtered_metrics["neuron_activation"]]
                if len(energy_savings) > 1:
                    trends["gflops_reduction_trend"] = {
                        "direction": "improving" if energy_savings[-1] > energy_savings[0] else "declining",
                        "change_percent": ((energy_savings[-1] - energy_savings[0]) / energy_savings[0]) * 100 if energy_savings[0] != 0 else 0
                    }
            
            # Calculate accuracy trend
            if filtered_metrics["constitutional_compliance"]:
                compliance_scores = [m.compliance_score for m in filtered_metrics["constitutional_compliance"]]
                if len(compliance_scores) > 1:
                    trends["accuracy_trend"] = {
                        "direction": "improving" if compliance_scores[-1] > compliance_scores[0] else "declining",
                        "change_percent": ((compliance_scores[-1] - compliance_scores[0]) / compliance_scores[0]) * 100 if compliance_scores[0] != 0 else 0
                    }
            
            return trends
            
        except Exception as e:
            logger.error(f"Trend calculation failed: {e}")
            return {}
    
    def get_prometheus_metrics(self) -> str:
        """Get Prometheus metrics in exposition format."""
        if not PROMETHEUS_AVAILABLE or not hasattr(self, 'registry'):
            return "# Prometheus not available\n"
        
        return generate_latest(self.registry).decode('utf-8')


# Global performance collector instance
_wina_performance_collector: Optional[WINAPerformanceCollector] = None


async def get_wina_performance_collector() -> WINAPerformanceCollector:
    """Get or create the global WINA performance collector instance."""
    global _wina_performance_collector
    
    if _wina_performance_collector is None:
        _wina_performance_collector = WINAPerformanceCollector()
        await _wina_performance_collector.start_monitoring()
        logger.info("WINA Performance Collector instance created")
    
    return _wina_performance_collector


async def close_wina_performance_collector() -> None:
    """Close the global WINA performance collector."""
    global _wina_performance_collector
    if _wina_performance_collector:
        await _wina_performance_collector.stop_monitoring()
        _wina_performance_collector = None
        logger.info("WINA Performance Collector instance closed")