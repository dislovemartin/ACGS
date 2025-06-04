"""
Configuration settings for Research Infrastructure Service
"""

import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""
    
    # Service configuration
    SERVICE_NAME: str = "research_infrastructure"
    SERVICE_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # Database configuration
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5434/acgs_research",
        env="RESEARCH_DATABASE_URL"
    )
    
    # Redis configuration for caching and task queues
    REDIS_URL: str = Field(
        default="redis://localhost:6379/2",
        env="RESEARCH_REDIS_URL"
    )
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="ALLOWED_ORIGINS"
    )
    
    # Research automation settings
    EXPERIMENT_TRACKING_ENABLED: bool = Field(default=True, env="EXPERIMENT_TRACKING_ENABLED")
    AUTO_ANALYSIS_ENABLED: bool = Field(default=True, env="AUTO_ANALYSIS_ENABLED")
    REPRODUCIBILITY_CHECKS_ENABLED: bool = Field(default=True, env="REPRODUCIBILITY_CHECKS_ENABLED")
    
    # Data collection settings
    MAX_EXPERIMENT_DURATION_HOURS: int = Field(default=24, env="MAX_EXPERIMENT_DURATION_HOURS")
    DATA_RETENTION_DAYS: int = Field(default=365, env="DATA_RETENTION_DAYS")
    MAX_CONCURRENT_EXPERIMENTS: int = Field(default=10, env="MAX_CONCURRENT_EXPERIMENTS")
    
    # Analysis settings
    STATISTICAL_SIGNIFICANCE_THRESHOLD: float = Field(default=0.05, env="STATISTICAL_SIGNIFICANCE_THRESHOLD")
    EFFECT_SIZE_THRESHOLD: float = Field(default=0.2, env="EFFECT_SIZE_THRESHOLD")
    MIN_SAMPLE_SIZE: int = Field(default=30, env="MIN_SAMPLE_SIZE")
    
    # External service URLs
    AC_SERVICE_URL: str = Field(default="http://localhost:8001", env="AC_SERVICE_URL")
    GS_SERVICE_URL: str = Field(default="http://localhost:8004", env="GS_SERVICE_URL")
    FV_SERVICE_URL: str = Field(default="http://localhost:8003", env="FV_SERVICE_URL")
    INTEGRITY_SERVICE_URL: str = Field(default="http://localhost:8002", env="INTEGRITY_SERVICE_URL")
    PGC_SERVICE_URL: str = Field(default="http://localhost:8005", env="PGC_SERVICE_URL")
    
    # Research data storage
    RESEARCH_DATA_PATH: str = Field(default="./research_data", env="RESEARCH_DATA_PATH")
    EXPERIMENT_ARTIFACTS_PATH: str = Field(default="./experiment_artifacts", env="EXPERIMENT_ARTIFACTS_PATH")
    ANALYSIS_RESULTS_PATH: str = Field(default="./analysis_results", env="ANALYSIS_RESULTS_PATH")
    
    # Notification settings
    SLACK_WEBHOOK_URL: Optional[str] = Field(default=None, env="SLACK_WEBHOOK_URL")
    EMAIL_NOTIFICATIONS_ENABLED: bool = Field(default=False, env="EMAIL_NOTIFICATIONS_ENABLED")
    
    # Security settings
    SECRET_KEY: str = Field(default="research-secret-key-change-in-production", env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Logging configuration
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    # Performance settings
    MAX_WORKERS: int = Field(default=4, env="MAX_WORKERS")
    REQUEST_TIMEOUT_SECONDS: int = Field(default=300, env="REQUEST_TIMEOUT_SECONDS")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
