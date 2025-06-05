"""
WINA Configuration Management

Configuration classes for WINA (Weight Informed Neuron Activation) integration
within the ACGS-PGP framework.
"""

import os
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

from .exceptions import WINAConfigurationError


class WINAMode(Enum):
    """WINA operation modes."""
    INFERENCE_ONLY = "inference_only"
    TRAINING_AWARE = "training_aware"
    CONSTITUTIONAL_GUIDED = "constitutional_guided"


class SparsityStrategy(Enum):
    """Sparsity application strategies."""
    GLOBAL_UNIFORM = "global_uniform"
    LAYER_SPECIFIC = "layer_specific"
    ADAPTIVE_DYNAMIC = "adaptive_dynamic"


@dataclass
class WINAConfig:
    """
    Core WINA configuration for optimization parameters.
    
    Attributes:
        target_sparsity: Target sparsity ratio (0.0-1.0)
        gflops_reduction_target: Target GFLOPs reduction ratio (0.0-1.0)
        accuracy_threshold: Minimum acceptable accuracy (0.0-1.0)
        mode: WINA operation mode
        sparsity_strategy: Strategy for applying sparsity
        enable_svd_transformation: Enable SVD-based transformation
        enable_runtime_gating: Enable dynamic runtime gating
        layer_specific_sparsity: Layer-specific sparsity ratios
        performance_monitoring: Enable performance monitoring
        constitutional_compliance: Enable constitutional compliance checking
    """
    
    # Core optimization parameters
    target_sparsity: float = 0.6
    gflops_reduction_target: float = 0.5
    accuracy_threshold: float = 0.95
    
    # Operation configuration
    mode: WINAMode = WINAMode.INFERENCE_ONLY
    sparsity_strategy: SparsityStrategy = SparsityStrategy.LAYER_SPECIFIC
    
    # Feature toggles
    enable_svd_transformation: bool = True
    enable_runtime_gating: bool = True
    enable_performance_monitoring: bool = True
    enable_constitutional_compliance: bool = True
    
    # Advanced configuration
    layer_specific_sparsity: Dict[str, float] = field(default_factory=dict)
    svd_rank_reduction: float = 0.8
    gating_threshold: float = 0.1
    
    # Performance settings
    cache_transformed_weights: bool = True
    parallel_processing: bool = True
    batch_optimization: bool = True

    # Monitoring settings
    history_retention: int = 1000  # Number of optimization results to retain in history
    enable_prometheus: bool = True  # Enable Prometheus metrics collection
    
    def __post_init__(self):
        """Validate configuration parameters."""
        self._validate_config()
    
    def _validate_config(self):
        """Validate configuration parameters."""
        if not 0.0 <= self.target_sparsity <= 1.0:
            raise WINAConfigurationError(f"target_sparsity must be between 0.0 and 1.0, got {self.target_sparsity}")
        
        if not 0.0 <= self.gflops_reduction_target <= 1.0:
            raise WINAConfigurationError(f"gflops_reduction_target must be between 0.0 and 1.0, got {self.gflops_reduction_target}")
        
        if not 0.0 <= self.accuracy_threshold <= 1.0:
            raise WINAConfigurationError(f"accuracy_threshold must be between 0.0 and 1.0, got {self.accuracy_threshold}")
        
        if not 0.0 <= self.svd_rank_reduction <= 1.0:
            raise WINAConfigurationError(f"svd_rank_reduction must be between 0.0 and 1.0, got {self.svd_rank_reduction}")
        
        # Validate layer-specific sparsity
        for layer, sparsity in self.layer_specific_sparsity.items():
            if not 0.0 <= sparsity <= 1.0:
                raise WINAConfigurationError(f"Layer {layer} sparsity must be between 0.0 and 1.0, got {sparsity}")


@dataclass
class WINAIntegrationConfig:
    """
    Configuration for WINA integration with ACGS-PGP components.
    
    Attributes:
        gs_engine_optimization: Enable GS Engine LLM optimization
        ec_layer_oversight: Enable EC Layer oversight optimization
        pgc_enforcement_enhancement: Enable PGC enforcement enhancement
        constitutional_principle_updates: Enable constitutional principle updates
        metrics_collection_interval: Metrics collection interval in seconds
        alert_thresholds: Alert thresholds for performance monitoring
    """
    
    # Integration toggles
    gs_engine_optimization: bool = True
    ec_layer_oversight: bool = True
    pgc_enforcement_enhancement: bool = True
    constitutional_principle_updates: bool = True
    
    # Monitoring configuration
    metrics_collection_interval: int = 60  # seconds
    enable_prometheus_metrics: bool = True
    enable_detailed_logging: bool = True
    
    # Alert thresholds
    alert_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "accuracy_drop": 0.05,  # 5% accuracy drop threshold
        "gflops_increase": 0.1,  # 10% GFLOPs increase threshold
        "latency_increase": 0.2,  # 20% latency increase threshold
        "error_rate": 0.01,  # 1% error rate threshold
    })
    
    # Constitutional compliance
    constitutional_compliance_strict: bool = True
    principle_update_approval_required: bool = True
    
    def __post_init__(self):
        """Validate integration configuration."""
        self._validate_integration_config()
    
    def _validate_integration_config(self):
        """Validate integration configuration parameters."""
        if self.metrics_collection_interval <= 0:
            raise WINAConfigurationError(f"metrics_collection_interval must be positive, got {self.metrics_collection_interval}")
        
        # Validate alert thresholds
        for metric, threshold in self.alert_thresholds.items():
            if threshold < 0:
                raise WINAConfigurationError(f"Alert threshold for {metric} must be non-negative, got {threshold}")


def load_wina_config_from_env() -> tuple[WINAConfig, WINAIntegrationConfig]:
    """
    Load WINA configuration from environment variables.
    
    Returns:
        Tuple of (WINAConfig, WINAIntegrationConfig)
    """
    # Core WINA configuration
    wina_config = WINAConfig(
        target_sparsity=float(os.getenv("WINA_TARGET_SPARSITY", "0.6")),
        gflops_reduction_target=float(os.getenv("WINA_GFLOPS_REDUCTION_TARGET", "0.5")),
        accuracy_threshold=float(os.getenv("WINA_ACCURACY_THRESHOLD", "0.95")),
        mode=WINAMode(os.getenv("WINA_MODE", "inference_only")),
        sparsity_strategy=SparsityStrategy(os.getenv("WINA_SPARSITY_STRATEGY", "layer_specific")),
        enable_svd_transformation=os.getenv("WINA_ENABLE_SVD", "true").lower() == "true",
        enable_runtime_gating=os.getenv("WINA_ENABLE_GATING", "true").lower() == "true",
        enable_performance_monitoring=os.getenv("WINA_ENABLE_MONITORING", "true").lower() == "true",
        enable_constitutional_compliance=os.getenv("WINA_ENABLE_CONSTITUTIONAL", "true").lower() == "true",
    )
    
    # Integration configuration
    integration_config = WINAIntegrationConfig(
        gs_engine_optimization=os.getenv("WINA_GS_ENGINE_OPT", "true").lower() == "true",
        ec_layer_oversight=os.getenv("WINA_EC_LAYER_OPT", "true").lower() == "true",
        pgc_enforcement_enhancement=os.getenv("WINA_PGC_ENHANCEMENT", "true").lower() == "true",
        constitutional_principle_updates=os.getenv("WINA_CONSTITUTIONAL_UPDATES", "true").lower() == "true",
        metrics_collection_interval=int(os.getenv("WINA_METRICS_INTERVAL", "60")),
        enable_prometheus_metrics=os.getenv("WINA_PROMETHEUS_METRICS", "true").lower() == "true",
        enable_detailed_logging=os.getenv("WINA_DETAILED_LOGGING", "true").lower() == "true",
    )
    
    return wina_config, integration_config


def save_wina_config(config: WINAConfig, integration_config: WINAIntegrationConfig, 
                     config_path: Union[str, Path]) -> None:
    """
    Save WINA configuration to JSON file.
    
    Args:
        config: WINA core configuration
        integration_config: WINA integration configuration
        config_path: Path to save configuration file
    """
    config_data = {
        "wina_config": {
            "target_sparsity": config.target_sparsity,
            "gflops_reduction_target": config.gflops_reduction_target,
            "accuracy_threshold": config.accuracy_threshold,
            "mode": config.mode.value,
            "sparsity_strategy": config.sparsity_strategy.value,
            "enable_svd_transformation": config.enable_svd_transformation,
            "enable_runtime_gating": config.enable_runtime_gating,
            "enable_performance_monitoring": config.enable_performance_monitoring,
            "enable_constitutional_compliance": config.enable_constitutional_compliance,
            "layer_specific_sparsity": config.layer_specific_sparsity,
            "svd_rank_reduction": config.svd_rank_reduction,
            "gating_threshold": config.gating_threshold,
        },
        "integration_config": {
            "gs_engine_optimization": integration_config.gs_engine_optimization,
            "ec_layer_oversight": integration_config.ec_layer_oversight,
            "pgc_enforcement_enhancement": integration_config.pgc_enforcement_enhancement,
            "constitutional_principle_updates": integration_config.constitutional_principle_updates,
            "metrics_collection_interval": integration_config.metrics_collection_interval,
            "enable_prometheus_metrics": integration_config.enable_prometheus_metrics,
            "enable_detailed_logging": integration_config.enable_detailed_logging,
            "alert_thresholds": integration_config.alert_thresholds,
        }
    }
    
    with open(config_path, 'w') as f:
        json.dump(config_data, f, indent=2)


def load_wina_config_from_file(config_path: Union[str, Path]) -> tuple[WINAConfig, WINAIntegrationConfig]:
    """
    Load WINA configuration from JSON file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Tuple of (WINAConfig, WINAIntegrationConfig)
    """
    with open(config_path, 'r') as f:
        config_data = json.load(f)
    
    wina_data = config_data.get("wina_config", {})
    integration_data = config_data.get("integration_config", {})
    
    wina_config = WINAConfig(
        target_sparsity=wina_data.get("target_sparsity", 0.6),
        gflops_reduction_target=wina_data.get("gflops_reduction_target", 0.5),
        accuracy_threshold=wina_data.get("accuracy_threshold", 0.95),
        mode=WINAMode(wina_data.get("mode", "inference_only")),
        sparsity_strategy=SparsityStrategy(wina_data.get("sparsity_strategy", "layer_specific")),
        enable_svd_transformation=wina_data.get("enable_svd_transformation", True),
        enable_runtime_gating=wina_data.get("enable_runtime_gating", True),
        enable_performance_monitoring=wina_data.get("enable_performance_monitoring", True),
        enable_constitutional_compliance=wina_data.get("enable_constitutional_compliance", True),
        layer_specific_sparsity=wina_data.get("layer_specific_sparsity", {}),
        svd_rank_reduction=wina_data.get("svd_rank_reduction", 0.8),
        gating_threshold=wina_data.get("gating_threshold", 0.1),
    )
    
    integration_config = WINAIntegrationConfig(
        gs_engine_optimization=integration_data.get("gs_engine_optimization", True),
        ec_layer_oversight=integration_data.get("ec_layer_oversight", True),
        pgc_enforcement_enhancement=integration_data.get("pgc_enforcement_enhancement", True),
        constitutional_principle_updates=integration_data.get("constitutional_principle_updates", True),
        metrics_collection_interval=integration_data.get("metrics_collection_interval", 60),
        enable_prometheus_metrics=integration_data.get("enable_prometheus_metrics", True),
        enable_detailed_logging=integration_data.get("enable_detailed_logging", True),
        alert_thresholds=integration_data.get("alert_thresholds", {
            "accuracy_drop": 0.05,
            "gflops_increase": 0.1,
            "latency_increase": 0.2,
            "error_rate": 0.01,
        }),
    )
    
    return wina_config, integration_config
