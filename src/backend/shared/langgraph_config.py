"""
LangGraph Configuration Management for ACGS-PGP

This module provides configuration management for LangGraph workflows,
including multi-model LLM configuration, Redis state management, and
workflow-specific settings based on the Gemini-LangGraph patterns.
"""

import os
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class ModelRole(str, Enum):
    """Specialized model roles for different ACGS-PGP tasks."""
    CONSTITUTIONAL_PROMPTING = "constitutional_prompting"
    POLICY_SYNTHESIS = "policy_synthesis"
    CONFLICT_RESOLUTION = "conflict_resolution"
    BIAS_MITIGATION = "bias_mitigation"
    REFLECTION = "reflection"
    AMENDMENT_ANALYSIS = "amendment_analysis"
    STAKEHOLDER_COMMUNICATION = "stakeholder_communication"
    FIDELITY_MONITORING = "fidelity_monitoring"


class LangGraphConfiguration(BaseModel):
    """
    Configuration for LangGraph workflows in ACGS-PGP.
    
    Provides centralized configuration for multi-model LLM management,
    state persistence, and workflow-specific settings.
    """
    
    # Multi-model LLM configuration
    models: Dict[ModelRole, str] = Field(default={
        ModelRole.CONSTITUTIONAL_PROMPTING: "gemini-2.5-pro",
        ModelRole.POLICY_SYNTHESIS: "gemini-2.0-flash",
        ModelRole.CONFLICT_RESOLUTION: "gemini-2.5-flash",
        ModelRole.BIAS_MITIGATION: "gemini-2.5-pro",
        ModelRole.REFLECTION: "gemini-2.5-flash-preview",
        ModelRole.AMENDMENT_ANALYSIS: "gemini-2.5-pro",
        ModelRole.STAKEHOLDER_COMMUNICATION: "gemini-2.0-flash",
        ModelRole.FIDELITY_MONITORING: "gemini-2.5-flash"
    })
    
    fallback_models: Dict[ModelRole, str] = Field(default={
        ModelRole.CONSTITUTIONAL_PROMPTING: "meta-llama/llama-4-maverick-17b-128e-instruct",
        ModelRole.POLICY_SYNTHESIS: "grok-3-mini",
        ModelRole.CONFLICT_RESOLUTION: "gemini-2.0-flash",
        ModelRole.BIAS_MITIGATION: "meta-llama/llama-4-maverick-17b-128e-instruct",
        ModelRole.REFLECTION: "grok-3-mini",
        ModelRole.AMENDMENT_ANALYSIS: "gemini-2.0-flash",
        ModelRole.STAKEHOLDER_COMMUNICATION: "grok-3-mini",
        ModelRole.FIDELITY_MONITORING: "gemini-2.0-flash"
    })
    
    # Model performance settings
    max_retries: int = Field(default=3, description="Maximum retry attempts for model calls")
    timeout_seconds: int = Field(default=30, description="Timeout for model API calls")
    temperature_settings: Dict[ModelRole, float] = Field(default={
        ModelRole.CONSTITUTIONAL_PROMPTING: 0.1,  # Low temperature for consistency
        ModelRole.POLICY_SYNTHESIS: 0.3,  # Moderate creativity
        ModelRole.CONFLICT_RESOLUTION: 0.2,  # Balanced approach
        ModelRole.BIAS_MITIGATION: 0.1,  # High precision required
        ModelRole.REFLECTION: 0.5,  # Higher creativity for analysis
        ModelRole.AMENDMENT_ANALYSIS: 0.1,  # Precise analysis
        ModelRole.STAKEHOLDER_COMMUNICATION: 0.4,  # Natural communication
        ModelRole.FIDELITY_MONITORING: 0.1  # Precise monitoring
    })
    
    # Constitutional governance thresholds
    constitutional_fidelity_threshold: float = Field(default=0.85, ge=0.0, le=1.0)
    policy_quality_threshold: float = Field(default=0.80, ge=0.0, le=1.0)
    bias_detection_threshold: float = Field(default=0.15, ge=0.0, le=1.0)
    
    # Workflow iteration limits
    max_synthesis_loops: int = Field(default=3, ge=1, le=10)
    max_refinement_iterations: int = Field(default=5, ge=1, le=15)
    max_correction_attempts: int = Field(default=3, ge=1, le=10)
    
    # Redis configuration for state management
    redis_url: str = Field(default="redis://localhost:6379")
    redis_key_prefix: str = Field(default="acgs_langgraph")
    redis_ttl_seconds: int = Field(default=86400)  # 24 hours
    
    # PostgreSQL configuration for workflow persistence
    postgres_url: Optional[str] = Field(default=None)
    workflow_table_name: str = Field(default="langgraph_workflows")
    
    # API keys and authentication
    gemini_api_key: Optional[str] = Field(default=None)
    openai_api_key: Optional[str] = Field(default=None)
    groq_api_key: Optional[str] = Field(default=None)
    xai_api_key: Optional[str] = Field(default=None)
    
    # Monitoring and alerting
    enable_performance_monitoring: bool = Field(default=True)
    enable_constitutional_alerts: bool = Field(default=True)
    alert_webhook_url: Optional[str] = Field(default=None)
    
    # Development and debugging
    debug_mode: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    enable_workflow_tracing: bool = Field(default=True)

    @classmethod
    def from_environment(cls) -> "LangGraphConfiguration":
        """
        Create configuration from environment variables.
        
        Returns:
            LangGraphConfiguration instance with values from environment
        """
        # Get API keys from environment
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        groq_api_key = os.getenv("GROQ_API_KEY")
        xai_api_key = os.getenv("XAI_API_KEY")
        
        # Get Redis configuration
        redis_url = os.getenv("LANGGRAPH_REDIS_URL", "redis://localhost:6379")
        
        # Get PostgreSQL configuration
        postgres_url = os.getenv("LANGGRAPH_POSTGRES_URL")
        
        # Get threshold configurations
        constitutional_fidelity_threshold = float(
            os.getenv("CONSTITUTIONAL_FIDELITY_THRESHOLD", "0.85")
        )
        policy_quality_threshold = float(
            os.getenv("POLICY_QUALITY_THRESHOLD", "0.80")
        )
        bias_detection_threshold = float(
            os.getenv("BIAS_DETECTION_THRESHOLD", "0.15")
        )
        
        # Get workflow limits
        max_synthesis_loops = int(os.getenv("MAX_SYNTHESIS_LOOPS", "3"))
        max_refinement_iterations = int(os.getenv("MAX_REFINEMENT_ITERATIONS", "5"))
        max_correction_attempts = int(os.getenv("MAX_CORRECTION_ATTEMPTS", "3"))
        
        # Get monitoring settings
        enable_performance_monitoring = os.getenv("ENABLE_PERFORMANCE_MONITORING", "true").lower() == "true"
        enable_constitutional_alerts = os.getenv("ENABLE_CONSTITUTIONAL_ALERTS", "true").lower() == "true"
        alert_webhook_url = os.getenv("ALERT_WEBHOOK_URL")
        
        # Get debug settings
        debug_mode = os.getenv("LANGGRAPH_DEBUG_MODE", "false").lower() == "true"
        log_level = os.getenv("LANGGRAPH_LOG_LEVEL", "INFO")
        enable_workflow_tracing = os.getenv("ENABLE_WORKFLOW_TRACING", "true").lower() == "true"
        
        return cls(
            gemini_api_key=gemini_api_key,
            openai_api_key=openai_api_key,
            groq_api_key=groq_api_key,
            xai_api_key=xai_api_key,
            redis_url=redis_url,
            postgres_url=postgres_url,
            constitutional_fidelity_threshold=constitutional_fidelity_threshold,
            policy_quality_threshold=policy_quality_threshold,
            bias_detection_threshold=bias_detection_threshold,
            max_synthesis_loops=max_synthesis_loops,
            max_refinement_iterations=max_refinement_iterations,
            max_correction_attempts=max_correction_attempts,
            enable_performance_monitoring=enable_performance_monitoring,
            enable_constitutional_alerts=enable_constitutional_alerts,
            alert_webhook_url=alert_webhook_url,
            debug_mode=debug_mode,
            log_level=log_level,
            enable_workflow_tracing=enable_workflow_tracing
        )

    def get_model_for_role(self, role: ModelRole) -> str:
        """Get the primary model for a specific role."""
        return self.models.get(role, "gemini-2.0-flash")
    
    def get_fallback_model_for_role(self, role: ModelRole) -> str:
        """Get the fallback model for a specific role."""
        return self.fallback_models.get(role, "gpt-4o-mini")
    
    def get_temperature_for_role(self, role: ModelRole) -> float:
        """Get the temperature setting for a specific role."""
        return self.temperature_settings.get(role, 0.3)
    
    def validate_api_keys(self) -> Dict[str, bool]:
        """
        Validate that required API keys are available.
        
        Returns:
            Dictionary mapping provider names to availability status
        """
        return {
            "gemini": self.gemini_api_key is not None,
            "openai": self.openai_api_key is not None,
            "groq": self.groq_api_key is not None,
            "xai": self.xai_api_key is not None
        }
    
    def get_redis_key(self, workflow_type: str, workflow_id: str) -> str:
        """
        Generate Redis key for workflow state storage.
        
        Args:
            workflow_type: Type of workflow (e.g., "constitutional_council")
            workflow_id: Unique workflow identifier
            
        Returns:
            Redis key string
        """
        return f"{self.redis_key_prefix}:{workflow_type}:{workflow_id}"


class ConstitutionalCouncilConfig(BaseModel):
    """Specific configuration for Constitutional Council workflows."""
    
    # Amendment processing settings
    amendment_review_period_hours: int = Field(default=72, description="Hours for amendment review")
    voting_period_hours: int = Field(default=48, description="Hours for voting period")
    quorum_percentage: float = Field(default=0.6, ge=0.0, le=1.0, description="Required quorum for voting")
    
    # Stakeholder engagement
    required_stakeholder_roles: List[str] = Field(default=[
        "constitutional_expert", "policy_administrator", "system_auditor", "public_representative"
    ])
    notification_channels: List[str] = Field(default=["email", "dashboard", "webhook"])
    
    # Analysis thresholds
    constitutional_compliance_threshold: float = Field(default=0.90, ge=0.0, le=1.0)
    conflict_detection_sensitivity: float = Field(default=0.75, ge=0.0, le=1.0)
    
    # Automation settings
    enable_automated_analysis: bool = Field(default=True)
    enable_automated_notifications: bool = Field(default=True)
    require_human_approval: bool = Field(default=True)


class PolicySynthesisConfig(BaseModel):
    """Specific configuration for Policy Synthesis workflows."""
    
    # Synthesis parameters
    target_policy_count: int = Field(default=5, ge=1, le=20)
    policy_complexity_level: str = Field(default="moderate", pattern="^(simple|moderate|complex)$")
    
    # Quality assurance
    enable_multi_model_validation: bool = Field(default=True)
    require_formal_verification: bool = Field(default=True)
    enable_bias_detection: bool = Field(default=True)
    
    # Output formats
    generate_rego_policies: bool = Field(default=True)
    generate_natural_language_summaries: bool = Field(default=True)
    include_implementation_guidance: bool = Field(default=True)


# Global configuration instance
_global_config: Optional[LangGraphConfiguration] = None


def get_langgraph_config() -> LangGraphConfiguration:
    """
    Get the global LangGraph configuration instance.
    
    Returns:
        LangGraphConfiguration instance
    """
    global _global_config
    if _global_config is None:
        _global_config = LangGraphConfiguration.from_environment()
    return _global_config


def set_langgraph_config(config: LangGraphConfiguration) -> None:
    """
    Set the global LangGraph configuration instance.
    
    Args:
        config: LangGraphConfiguration instance to set as global
    """
    global _global_config
    _global_config = config
