"""
OPA (Open Policy Agent) Configuration Module

This module provides configuration management for OPA integration within the
governance synthesis service, supporting policy validation, decision caching,
and performance optimization.

Phase 2: Governance Synthesis Hardening with Rego/OPA Integration
"""

import os
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class OPAMode(Enum):
    """OPA operation modes."""
    EMBEDDED = "embedded"  # OPA embedded as library
    SERVER = "server"      # OPA as external server
    HYBRID = "hybrid"      # Both embedded and server


@dataclass
class OPAServerConfig:
    """Configuration for OPA server connection."""
    host: str = "localhost"
    port: int = 8181
    protocol: str = "http"
    timeout_seconds: int = 5
    max_retries: int = 3
    retry_delay_seconds: float = 0.1
    health_check_interval_seconds: int = 30
    
    @property
    def base_url(self) -> str:
        """Get the base URL for OPA server."""
        return f"{self.protocol}://{self.host}:{self.port}"
    
    @property
    def data_api_url(self) -> str:
        """Get the data API URL."""
        return f"{self.base_url}/v1/data"
    
    @property
    def policy_api_url(self) -> str:
        """Get the policy API URL."""
        return f"{self.base_url}/v1/policies"
    
    @property
    def health_url(self) -> str:
        """Get the health check URL."""
        return f"{self.base_url}/health"


@dataclass
class OPAPerformanceConfig:
    """Configuration for OPA performance optimization."""
    max_policy_decision_latency_ms: int = 50
    enable_decision_caching: bool = True
    cache_ttl_seconds: int = 300
    cache_max_size: int = 1000
    enable_batch_evaluation: bool = True
    batch_size: int = 100
    enable_parallel_evaluation: bool = True
    max_parallel_workers: int = 4
    enable_metrics_collection: bool = True
    metrics_export_interval_seconds: int = 60


@dataclass
class OPAPolicyConfig:
    """Configuration for OPA policy management."""
    policy_directory: str = "src/backend/gs_service/policies"
    auto_reload_policies: bool = True
    policy_validation_on_load: bool = True
    enable_policy_versioning: bool = True
    default_policy_package: str = "acgs.governance"
    constitutional_principles_package: str = "acgs.constitutional"
    policy_synthesis_package: str = "acgs.synthesis"
    compliance_package: str = "acgs.compliance"


@dataclass
class OPASecurityConfig:
    """Configuration for OPA security settings."""
    enable_authentication: bool = False
    api_key: Optional[str] = None
    enable_tls: bool = False
    tls_cert_path: Optional[str] = None
    tls_key_path: Optional[str] = None
    enable_authorization: bool = False
    allowed_origins: List[str] = None
    
    def __post_init__(self):
        if self.allowed_origins is None:
            self.allowed_origins = ["localhost", "127.0.0.1"]


class OPAConfig:
    """
    Comprehensive OPA configuration manager for governance synthesis service.
    
    Provides centralized configuration for OPA integration including:
    - Server connection settings
    - Performance optimization parameters
    - Policy management configuration
    - Security settings
    - Environment-specific overrides
    """
    
    def __init__(self):
        self.mode = self._get_opa_mode()
        self.server = self._get_server_config()
        self.performance = self._get_performance_config()
        self.policy = self._get_policy_config()
        self.security = self._get_security_config()
        
        logger.info(f"OPA configuration initialized in {self.mode.value} mode")
    
    def _get_opa_mode(self) -> OPAMode:
        """Get OPA operation mode from environment."""
        mode_str = os.getenv("OPA_MODE", "embedded").lower()
        try:
            return OPAMode(mode_str)
        except ValueError:
            logger.warning(f"Invalid OPA mode '{mode_str}', defaulting to embedded")
            return OPAMode.EMBEDDED
    
    def _get_server_config(self) -> OPAServerConfig:
        """Get OPA server configuration from environment."""
        return OPAServerConfig(
            host=os.getenv("OPA_SERVER_HOST", "localhost"),
            port=int(os.getenv("OPA_SERVER_PORT", "8181")),
            protocol=os.getenv("OPA_SERVER_PROTOCOL", "http"),
            timeout_seconds=int(os.getenv("OPA_TIMEOUT_SECONDS", "5")),
            max_retries=int(os.getenv("OPA_MAX_RETRIES", "3")),
            retry_delay_seconds=float(os.getenv("OPA_RETRY_DELAY_SECONDS", "0.1")),
            health_check_interval_seconds=int(os.getenv("OPA_HEALTH_CHECK_INTERVAL", "30"))
        )
    
    def _get_performance_config(self) -> OPAPerformanceConfig:
        """Get OPA performance configuration from environment."""
        return OPAPerformanceConfig(
            max_policy_decision_latency_ms=int(os.getenv("OPA_MAX_LATENCY_MS", "50")),
            enable_decision_caching=os.getenv("OPA_ENABLE_CACHING", "true").lower() == "true",
            cache_ttl_seconds=int(os.getenv("OPA_CACHE_TTL_SECONDS", "300")),
            cache_max_size=int(os.getenv("OPA_CACHE_MAX_SIZE", "1000")),
            enable_batch_evaluation=os.getenv("OPA_ENABLE_BATCH", "true").lower() == "true",
            batch_size=int(os.getenv("OPA_BATCH_SIZE", "100")),
            enable_parallel_evaluation=os.getenv("OPA_ENABLE_PARALLEL", "true").lower() == "true",
            max_parallel_workers=int(os.getenv("OPA_MAX_WORKERS", "4")),
            enable_metrics_collection=os.getenv("OPA_ENABLE_METRICS", "true").lower() == "true",
            metrics_export_interval_seconds=int(os.getenv("OPA_METRICS_INTERVAL", "60"))
        )
    
    def _get_policy_config(self) -> OPAPolicyConfig:
        """Get OPA policy configuration from environment."""
        return OPAPolicyConfig(
            policy_directory=os.getenv("OPA_POLICY_DIR", "src/backend/gs_service/policies"),
            auto_reload_policies=os.getenv("OPA_AUTO_RELOAD", "true").lower() == "true",
            policy_validation_on_load=os.getenv("OPA_VALIDATE_ON_LOAD", "true").lower() == "true",
            enable_policy_versioning=os.getenv("OPA_ENABLE_VERSIONING", "true").lower() == "true",
            default_policy_package=os.getenv("OPA_DEFAULT_PACKAGE", "acgs.governance"),
            constitutional_principles_package=os.getenv("OPA_CONSTITUTIONAL_PACKAGE", "acgs.constitutional"),
            policy_synthesis_package=os.getenv("OPA_SYNTHESIS_PACKAGE", "acgs.synthesis"),
            compliance_package=os.getenv("OPA_COMPLIANCE_PACKAGE", "acgs.compliance")
        )
    
    def _get_security_config(self) -> OPASecurityConfig:
        """Get OPA security configuration from environment."""
        allowed_origins = os.getenv("OPA_ALLOWED_ORIGINS", "localhost,127.0.0.1").split(",")
        return OPASecurityConfig(
            enable_authentication=os.getenv("OPA_ENABLE_AUTH", "false").lower() == "true",
            api_key=os.getenv("OPA_API_KEY"),
            enable_tls=os.getenv("OPA_ENABLE_TLS", "false").lower() == "true",
            tls_cert_path=os.getenv("OPA_TLS_CERT_PATH"),
            tls_key_path=os.getenv("OPA_TLS_KEY_PATH"),
            enable_authorization=os.getenv("OPA_ENABLE_AUTHZ", "false").lower() == "true",
            allowed_origins=[origin.strip() for origin in allowed_origins]
        )
    
    def get_config_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary for serialization."""
        return {
            "mode": self.mode.value,
            "server": {
                "host": self.server.host,
                "port": self.server.port,
                "protocol": self.server.protocol,
                "timeout_seconds": self.server.timeout_seconds,
                "max_retries": self.server.max_retries,
                "retry_delay_seconds": self.server.retry_delay_seconds,
                "health_check_interval_seconds": self.server.health_check_interval_seconds
            },
            "performance": {
                "max_policy_decision_latency_ms": self.performance.max_policy_decision_latency_ms,
                "enable_decision_caching": self.performance.enable_decision_caching,
                "cache_ttl_seconds": self.performance.cache_ttl_seconds,
                "cache_max_size": self.performance.cache_max_size,
                "enable_batch_evaluation": self.performance.enable_batch_evaluation,
                "batch_size": self.performance.batch_size,
                "enable_parallel_evaluation": self.performance.enable_parallel_evaluation,
                "max_parallel_workers": self.performance.max_parallel_workers,
                "enable_metrics_collection": self.performance.enable_metrics_collection,
                "metrics_export_interval_seconds": self.performance.metrics_export_interval_seconds
            },
            "policy": {
                "policy_directory": self.policy.policy_directory,
                "auto_reload_policies": self.policy.auto_reload_policies,
                "policy_validation_on_load": self.policy.policy_validation_on_load,
                "enable_policy_versioning": self.policy.enable_policy_versioning,
                "default_policy_package": self.policy.default_policy_package,
                "constitutional_principles_package": self.policy.constitutional_principles_package,
                "policy_synthesis_package": self.policy.policy_synthesis_package,
                "compliance_package": self.policy.compliance_package
            },
            "security": {
                "enable_authentication": self.security.enable_authentication,
                "enable_tls": self.security.enable_tls,
                "enable_authorization": self.security.enable_authorization,
                "allowed_origins": self.security.allowed_origins
            }
        }
    
    def validate_config(self) -> bool:
        """Validate the configuration settings."""
        try:
            # Validate performance constraints
            if self.performance.max_policy_decision_latency_ms <= 0:
                logger.error("Max policy decision latency must be positive")
                return False
            
            if self.performance.max_policy_decision_latency_ms > 1000:
                logger.warning("Max policy decision latency > 1000ms may impact performance")
            
            # Validate server configuration
            if self.mode in [OPAMode.SERVER, OPAMode.HYBRID]:
                if not (1 <= self.server.port <= 65535):
                    logger.error(f"Invalid OPA server port: {self.server.port}")
                    return False
            
            # Validate policy directory
            if not os.path.exists(os.path.dirname(self.policy.policy_directory)):
                logger.warning(f"Policy directory parent does not exist: {self.policy.policy_directory}")
            
            logger.info("OPA configuration validation passed")
            return True
            
        except Exception as e:
            logger.error(f"OPA configuration validation failed: {e}")
            return False


# Global configuration instance
_opa_config: Optional[OPAConfig] = None


def get_opa_config() -> OPAConfig:
    """Get or create the global OPA configuration instance."""
    global _opa_config
    if _opa_config is None:
        _opa_config = OPAConfig()
        if not _opa_config.validate_config():
            logger.error("OPA configuration validation failed")
            raise ValueError("Invalid OPA configuration")
    return _opa_config


def reload_opa_config() -> OPAConfig:
    """Reload the OPA configuration from environment variables."""
    global _opa_config
    _opa_config = None
    return get_opa_config()
