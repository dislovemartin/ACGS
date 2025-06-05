"""
violation_config.py

Constitutional Violation Configuration Management.
Implements configurable threshold management, environment variable integration,
and dynamic threshold adjustment for violation detection systems.

Classes:
    ViolationConfigManager: Main configuration manager
    ThresholdConfig: Configuration data structure
    ConfigSource: Enumeration of configuration sources
"""

import os
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from shared.models import ViolationThreshold, User
from shared.database import get_async_db

logger = logging.getLogger(__name__)


class ConfigSource(Enum):
    """Sources of configuration data."""
    ENVIRONMENT = "environment"
    DATABASE = "database"
    FILE = "file"
    DEFAULT = "default"


class ThresholdType(Enum):
    """Types of violation thresholds."""
    FIDELITY_SCORE = "fidelity_score"
    VIOLATION_COUNT = "violation_count"
    SEVERITY_BASED = "severity_based"
    TIME_BASED = "time_based"
    CUSTOM = "custom"


@dataclass
class ThresholdConfig:
    """Configuration for violation thresholds."""
    name: str
    threshold_type: ThresholdType
    green_threshold: float
    amber_threshold: float
    red_threshold: float
    enabled: bool = True
    description: str = ""
    configuration: Dict[str, Any] = None
    source: ConfigSource = ConfigSource.DEFAULT
    
    def __post_init__(self):
        if self.configuration is None:
            self.configuration = {}


@dataclass
class ViolationDetectionConfig:
    """Configuration for violation detection."""
    scan_interval_seconds: int = 30
    batch_size: int = 100
    detection_timeout_seconds: int = 60
    enable_real_time_scanning: bool = True
    enable_batch_analysis: bool = True
    enable_historical_analysis: bool = True
    max_violations_per_scan: int = 1000
    cache_threshold_seconds: int = 300


@dataclass
class EscalationConfig:
    """Configuration for violation escalation."""
    enable_automatic_escalation: bool = True
    enable_timeout_escalation: bool = True
    max_escalation_level: str = "emergency_response"
    default_response_time_minutes: int = 30
    notification_retry_attempts: int = 3
    notification_retry_delay_seconds: int = 60


class ViolationConfigManager:
    """
    Constitutional Violation Configuration Manager.
    
    Manages configurable thresholds, environment variable integration,
    and dynamic threshold adjustment for violation detection systems.
    """
    
    def __init__(self, config_file_path: Optional[str] = None):
        """
        Initialize the violation configuration manager.
        
        Args:
            config_file_path: Path to configuration file (optional)
        """
        self.config_file_path = config_file_path
        self.cached_thresholds: Dict[str, ThresholdConfig] = {}
        self.cache_updated_at: Optional[datetime] = None
        self.cache_ttl_seconds = 300  # 5 minutes
        
        # Load initial configuration
        self._load_initial_config()
        
        logger.info("Violation Configuration Manager initialized")
    
    def get_threshold_config(self, threshold_name: str) -> Optional[ThresholdConfig]:
        """
        Get threshold configuration by name.
        
        Args:
            threshold_name: Name of the threshold
            
        Returns:
            ThresholdConfig if found, None otherwise
        """
        try:
            # Check cache first
            if self._is_cache_valid() and threshold_name in self.cached_thresholds:
                return self.cached_thresholds[threshold_name]
            
            # Load from various sources
            config = self._load_threshold_from_sources(threshold_name)
            
            # Cache the result
            if config:
                self.cached_thresholds[threshold_name] = config
                self.cache_updated_at = datetime.now(timezone.utc)
            
            return config
            
        except Exception as e:
            logger.error(f"Error getting threshold config for {threshold_name}: {e}")
            return None
    
    async def get_all_threshold_configs(self, db: Optional[AsyncSession] = None) -> Dict[str, ThresholdConfig]:
        """
        Get all threshold configurations.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary of threshold configurations
        """
        if db is None:
            async for db_session in get_async_db():
                return await self.get_all_threshold_configs(db_session)
        
        try:
            # Check cache first
            if self._is_cache_valid() and self.cached_thresholds:
                return self.cached_thresholds.copy()
            
            # Load from database
            result = await db.execute(
                select(ViolationThreshold).where(ViolationThreshold.enabled == True)
            )
            db_thresholds = result.scalars().all()
            
            # Convert to ThresholdConfig objects
            configs = {}
            for threshold in db_thresholds:
                config = ThresholdConfig(
                    name=threshold.threshold_name,
                    threshold_type=ThresholdType(threshold.threshold_type),
                    green_threshold=float(threshold.green_threshold),
                    amber_threshold=float(threshold.amber_threshold),
                    red_threshold=float(threshold.red_threshold),
                    enabled=threshold.enabled,
                    description=threshold.description or "",
                    configuration=threshold.configuration or {},
                    source=ConfigSource.DATABASE
                )
                configs[threshold.threshold_name] = config
            
            # Merge with environment and default configs
            env_configs = self._load_environment_configs()
            configs.update(env_configs)
            
            default_configs = self._get_default_configs()
            for name, config in default_configs.items():
                if name not in configs:
                    configs[name] = config
            
            # Update cache
            self.cached_thresholds = configs
            self.cache_updated_at = datetime.now(timezone.utc)
            
            return configs.copy()
            
        except Exception as e:
            logger.error(f"Error getting all threshold configs: {e}")
            return {}
    
    async def update_threshold_config(
        self,
        threshold_name: str,
        config: ThresholdConfig,
        user: Optional[User] = None,
        db: Optional[AsyncSession] = None
    ) -> bool:
        """
        Update threshold configuration.
        
        Args:
            threshold_name: Name of the threshold
            config: New threshold configuration
            user: User making the update
            db: Database session
            
        Returns:
            True if update successful, False otherwise
        """
        if db is None:
            async for db_session in get_async_db():
                return await self.update_threshold_config(threshold_name, config, user, db_session)
        
        try:
            # Validate configuration
            if not self._validate_threshold_config(config):
                logger.error(f"Invalid threshold configuration for {threshold_name}")
                return False
            
            # Check if threshold exists
            result = await db.execute(
                select(ViolationThreshold).where(
                    ViolationThreshold.threshold_name == threshold_name
                )
            )
            existing_threshold = result.scalar_one_or_none()
            
            if existing_threshold:
                # Update existing threshold
                existing_threshold.threshold_type = config.threshold_type.value
                existing_threshold.green_threshold = config.green_threshold
                existing_threshold.amber_threshold = config.amber_threshold
                existing_threshold.red_threshold = config.red_threshold
                existing_threshold.enabled = config.enabled
                existing_threshold.description = config.description
                existing_threshold.configuration = config.configuration
                existing_threshold.updated_by = user.id if user else None
            else:
                # Create new threshold
                new_threshold = ViolationThreshold(
                    threshold_name=threshold_name,
                    threshold_type=config.threshold_type.value,
                    green_threshold=config.green_threshold,
                    amber_threshold=config.amber_threshold,
                    red_threshold=config.red_threshold,
                    enabled=config.enabled,
                    description=config.description,
                    configuration=config.configuration,
                    created_by=user.id if user else None
                )
                db.add(new_threshold)
            
            await db.commit()
            
            # Invalidate cache
            self._invalidate_cache()
            
            logger.info(f"Updated threshold configuration: {threshold_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating threshold config {threshold_name}: {e}")
            await db.rollback()
            return False
    
    def get_detection_config(self) -> ViolationDetectionConfig:
        """Get violation detection configuration."""
        return ViolationDetectionConfig(
            scan_interval_seconds=int(os.getenv("VIOLATION_SCAN_INTERVAL_SECONDS", "30")),
            batch_size=int(os.getenv("VIOLATION_BATCH_SIZE", "100")),
            detection_timeout_seconds=int(os.getenv("VIOLATION_DETECTION_TIMEOUT_SECONDS", "60")),
            enable_real_time_scanning=os.getenv("ENABLE_REAL_TIME_VIOLATION_SCANNING", "true").lower() == "true",
            enable_batch_analysis=os.getenv("ENABLE_BATCH_VIOLATION_ANALYSIS", "true").lower() == "true",
            enable_historical_analysis=os.getenv("ENABLE_HISTORICAL_VIOLATION_ANALYSIS", "true").lower() == "true",
            max_violations_per_scan=int(os.getenv("MAX_VIOLATIONS_PER_SCAN", "1000")),
            cache_threshold_seconds=int(os.getenv("VIOLATION_CACHE_THRESHOLD_SECONDS", "300"))
        )
    
    def get_escalation_config(self) -> EscalationConfig:
        """Get violation escalation configuration."""
        return EscalationConfig(
            enable_automatic_escalation=os.getenv("ENABLE_AUTOMATIC_ESCALATION", "true").lower() == "true",
            enable_timeout_escalation=os.getenv("ENABLE_TIMEOUT_ESCALATION", "true").lower() == "true",
            max_escalation_level=os.getenv("MAX_ESCALATION_LEVEL", "emergency_response"),
            default_response_time_minutes=int(os.getenv("DEFAULT_ESCALATION_RESPONSE_TIME_MINUTES", "30")),
            notification_retry_attempts=int(os.getenv("ESCALATION_NOTIFICATION_RETRY_ATTEMPTS", "3")),
            notification_retry_delay_seconds=int(os.getenv("ESCALATION_NOTIFICATION_RETRY_DELAY_SECONDS", "60"))
        )
    
    def _load_initial_config(self):
        """Load initial configuration from all sources."""
        try:
            # Load default configurations
            self.cached_thresholds = self._get_default_configs()
            
            # Override with environment configurations
            env_configs = self._load_environment_configs()
            self.cached_thresholds.update(env_configs)
            
            # Load from file if specified
            if self.config_file_path and Path(self.config_file_path).exists():
                file_configs = self._load_file_configs()
                self.cached_thresholds.update(file_configs)
            
            self.cache_updated_at = datetime.now(timezone.utc)
            
        except Exception as e:
            logger.error(f"Error loading initial configuration: {e}")
    
    def _load_threshold_from_sources(self, threshold_name: str) -> Optional[ThresholdConfig]:
        """Load threshold configuration from various sources."""
        # Try environment first
        env_config = self._load_environment_config(threshold_name)
        if env_config:
            return env_config
        
        # Try file config
        if self.config_file_path:
            file_config = self._load_file_config(threshold_name)
            if file_config:
                return file_config
        
        # Try default config
        default_configs = self._get_default_configs()
        return default_configs.get(threshold_name)
    
    def _load_environment_configs(self) -> Dict[str, ThresholdConfig]:
        """Load threshold configurations from environment variables."""
        configs = {}
        
        # Fidelity score thresholds
        if os.getenv("CONSTITUTIONAL_FIDELITY_GREEN_THRESHOLD"):
            configs["fidelity_score"] = ThresholdConfig(
                name="fidelity_score",
                threshold_type=ThresholdType.FIDELITY_SCORE,
                green_threshold=float(os.getenv("CONSTITUTIONAL_FIDELITY_GREEN_THRESHOLD", "0.85")),
                amber_threshold=float(os.getenv("CONSTITUTIONAL_FIDELITY_AMBER_THRESHOLD", "0.70")),
                red_threshold=float(os.getenv("CONSTITUTIONAL_FIDELITY_RED_THRESHOLD", "0.55")),
                description="Constitutional fidelity score thresholds",
                source=ConfigSource.ENVIRONMENT
            )
        
        # Violation count thresholds
        if os.getenv("VIOLATION_COUNT_GREEN_THRESHOLD"):
            configs["violation_count"] = ThresholdConfig(
                name="violation_count",
                threshold_type=ThresholdType.VIOLATION_COUNT,
                green_threshold=float(os.getenv("VIOLATION_COUNT_GREEN_THRESHOLD", "2")),
                amber_threshold=float(os.getenv("VIOLATION_COUNT_AMBER_THRESHOLD", "5")),
                red_threshold=float(os.getenv("VIOLATION_COUNT_RED_THRESHOLD", "10")),
                description="Violation count thresholds per hour",
                source=ConfigSource.ENVIRONMENT
            )
        
        return configs

    def _load_environment_config(self, threshold_name: str) -> Optional[ThresholdConfig]:
        """Load specific threshold configuration from environment variables."""
        env_configs = self._load_environment_configs()
        return env_configs.get(threshold_name)

    def _load_file_configs(self) -> Dict[str, ThresholdConfig]:
        """Load threshold configurations from file."""
        # This would implement file-based configuration loading
        # For now, return empty dict
        return {}

    def _load_file_config(self, threshold_name: str) -> Optional[ThresholdConfig]:
        """Load specific threshold configuration from file."""
        file_configs = self._load_file_configs()
        return file_configs.get(threshold_name)

    def _get_default_configs(self) -> Dict[str, ThresholdConfig]:
        """Get default threshold configurations."""
        return {
            "fidelity_score": ThresholdConfig(
                name="fidelity_score",
                threshold_type=ThresholdType.FIDELITY_SCORE,
                green_threshold=0.85,
                amber_threshold=0.70,
                red_threshold=0.55,
                description="Default constitutional fidelity score thresholds",
                source=ConfigSource.DEFAULT
            ),
            "violation_count": ThresholdConfig(
                name="violation_count",
                threshold_type=ThresholdType.VIOLATION_COUNT,
                green_threshold=2.0,
                amber_threshold=5.0,
                red_threshold=10.0,
                description="Default violation count thresholds per hour",
                configuration={"time_window_hours": 1},
                source=ConfigSource.DEFAULT
            ),
            "severity_critical": ThresholdConfig(
                name="severity_critical",
                threshold_type=ThresholdType.SEVERITY_BASED,
                green_threshold=0.0,
                amber_threshold=1.0,
                red_threshold=3.0,
                description="Critical severity violation thresholds",
                configuration={"severity_level": "critical", "time_window_hours": 24},
                source=ConfigSource.DEFAULT
            ),
            "resolution_time": ThresholdConfig(
                name="resolution_time",
                threshold_type=ThresholdType.TIME_BASED,
                green_threshold=15.0,  # minutes
                amber_threshold=30.0,
                red_threshold=60.0,
                description="Violation resolution time thresholds",
                configuration={"unit": "minutes"},
                source=ConfigSource.DEFAULT
            )
        }

    def _validate_threshold_config(self, config: ThresholdConfig) -> bool:
        """Validate threshold configuration."""
        try:
            # Check threshold ordering
            if not (config.red_threshold <= config.amber_threshold <= config.green_threshold):
                logger.error(f"Invalid threshold ordering for {config.name}")
                return False

            # Check threshold values are non-negative
            if any(t < 0 for t in [config.green_threshold, config.amber_threshold, config.red_threshold]):
                logger.error(f"Negative threshold values not allowed for {config.name}")
                return False

            # Validate threshold type
            if not isinstance(config.threshold_type, ThresholdType):
                logger.error(f"Invalid threshold type for {config.name}")
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating threshold config: {e}")
            return False

    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        if self.cache_updated_at is None:
            return False

        cache_age = (datetime.now(timezone.utc) - self.cache_updated_at).total_seconds()
        return cache_age < self.cache_ttl_seconds

    def _invalidate_cache(self):
        """Invalidate the configuration cache."""
        self.cache_updated_at = None
        self.cached_thresholds.clear()


# Global configuration manager instance
violation_config_manager = ViolationConfigManager()


def get_violation_config_manager() -> ViolationConfigManager:
    """Get the global violation configuration manager."""
    return violation_config_manager


def get_threshold_config(threshold_name: str) -> Optional[ThresholdConfig]:
    """Get threshold configuration by name."""
    return violation_config_manager.get_threshold_config(threshold_name)


def get_detection_config() -> ViolationDetectionConfig:
    """Get violation detection configuration."""
    return violation_config_manager.get_detection_config()


def get_escalation_config() -> EscalationConfig:
    """Get violation escalation configuration."""
    return violation_config_manager.get_escalation_config()
