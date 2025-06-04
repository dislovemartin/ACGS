"""
Database models for Multi-Armed Bandit Prompt Optimization System

SQLAlchemy models for storing prompt templates, performance metrics,
and optimization history in the ACGS-PGP database.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid

# Fix the import to use the full package path
from src.backend.shared.database import Base


class PromptTemplateModel(Base):
    """Database model for prompt templates."""
    __tablename__ = "prompt_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    template_content = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, index=True)
    version = Column(String(50), default="1.0")
    
    # Metadata
    metadata_json = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_by_user_id = Column(Integer, nullable=True)  # Reference to user who created template
    
    # Performance tracking
    total_uses = Column(Integer, default=0)
    total_rewards = Column(Float, default=0.0)
    success_count = Column(Integer, default=0)
    average_reward = Column(Float, default=0.0)
    confidence_lower = Column(Float, default=0.0)
    confidence_upper = Column(Float, default=1.0)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Relationships
    performance_records = relationship("PromptPerformanceModel", back_populates="template", cascade="all, delete-orphan")
    optimization_history = relationship("OptimizationHistoryModel", back_populates="template", cascade="all, delete-orphan")


class PromptPerformanceModel(Base):
    """Database model for tracking prompt performance metrics."""
    __tablename__ = "prompt_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(String(255), ForeignKey("prompt_templates.template_id"), nullable=False, index=True)
    
    # Performance metrics
    semantic_similarity = Column(Float, nullable=False)
    policy_quality = Column(Float, nullable=False)
    constitutional_compliance = Column(Float, nullable=False)
    bias_mitigation = Column(Float, nullable=False)
    composite_score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    
    # Context information
    context_json = Column(JSON, default={})
    category = Column(String(100), nullable=True, index=True)
    
    # LLM output metadata
    llm_response_length = Column(Integer, nullable=True)
    llm_response_hash = Column(String(64), nullable=True)  # SHA-256 hash for deduplication
    
    # Timing
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    response_time_ms = Column(Integer, nullable=True)
    
    # Relationships
    template = relationship("PromptTemplateModel", back_populates="performance_records")


class OptimizationHistoryModel(Base):
    """Database model for MAB optimization history."""
    __tablename__ = "optimization_history"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(String(255), ForeignKey("prompt_templates.template_id"), nullable=False, index=True)
    
    # MAB algorithm details
    algorithm_type = Column(String(50), nullable=False)  # thompson_sampling, ucb, epsilon_greedy
    selection_reason = Column(String(255), nullable=True)  # Why this template was selected
    
    # Performance at time of selection
    composite_score = Column(Float, nullable=False)
    reward_components = Column(JSON, default={})  # Detailed reward breakdown
    
    # Template state at time of selection
    total_uses_at_selection = Column(Integer, nullable=False)
    average_reward_at_selection = Column(Float, nullable=False)
    
    # Context
    context_json = Column(JSON, default={})
    category = Column(String(100), nullable=True, index=True)
    
    # Timing
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    
    # Relationships
    template = relationship("PromptTemplateModel", back_populates="optimization_history")


class MABConfigurationModel(Base):
    """Database model for storing MAB configuration."""
    __tablename__ = "mab_configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    config_name = Column(String(255), unique=True, nullable=False)
    
    # Algorithm configuration
    algorithm_type = Column(String(50), nullable=False)
    exploration_rate = Column(Float, default=0.1)
    confidence_level = Column(Float, default=0.95)
    alpha_prior = Column(Float, default=1.0)
    beta_prior = Column(Float, default=1.0)
    
    # Reward function weights
    semantic_similarity_weight = Column(Float, default=0.4)
    policy_quality_weight = Column(Float, default=0.3)
    constitutional_compliance_weight = Column(Float, default=0.2)
    bias_mitigation_weight = Column(Float, default=0.1)
    
    # Performance thresholds
    min_uses_for_confidence = Column(Integer, default=10)
    reward_threshold = Column(Float, default=0.8)
    update_frequency = Column(Integer, default=100)
    
    # Status and metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_by_user_id = Column(Integer, nullable=True)
    
    # Additional configuration as JSON
    additional_config = Column(JSON, default={})


class MABSessionModel(Base):
    """Database model for tracking MAB optimization sessions."""
    __tablename__ = "mab_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Session metadata
    config_name = Column(String(255), ForeignKey("mab_configurations.config_name"), nullable=False)
    start_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    end_time = Column(DateTime(timezone=True), nullable=True)
    
    # Session statistics
    total_selections = Column(Integer, default=0)
    total_rewards = Column(Float, default=0.0)
    average_reward = Column(Float, default=0.0)
    best_template_id = Column(String(255), nullable=True)
    best_template_reward = Column(Float, default=0.0)
    
    # Performance metrics
    exploration_rate_actual = Column(Float, nullable=True)
    convergence_achieved = Column(Boolean, default=False)
    convergence_iteration = Column(Integer, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    status = Column(String(50), default="running")  # running, completed, failed
    
    # Additional session data
    session_metadata = Column(JSON, default={})


class PromptTemplateVersionModel(Base):
    """Database model for prompt template versioning."""
    __tablename__ = "prompt_template_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(String(255), nullable=False, index=True)
    version = Column(String(50), nullable=False)
    
    # Version details
    template_content = Column(Text, nullable=False)
    change_description = Column(Text, nullable=True)
    parent_version = Column(String(50), nullable=True)
    
    # Performance comparison
    performance_improvement = Column(Float, nullable=True)  # Compared to parent version
    a_b_test_results = Column(JSON, default={})
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_by_user_id = Column(Integer, nullable=True)
    is_current = Column(Boolean, default=False)
    
    # Unique constraint on template_id + version
    __table_args__ = (
        {"schema": None}  # Use default schema
    )


class RewardFunctionModel(Base):
    """Database model for custom reward functions."""
    __tablename__ = "reward_functions"
    
    id = Column(Integer, primary_key=True, index=True)
    function_name = Column(String(255), unique=True, nullable=False)
    
    # Function definition
    function_code = Column(Text, nullable=False)  # Python code for custom reward function
    function_type = Column(String(50), default="composite")  # composite, semantic, quality, etc.
    
    # Configuration
    weight_config = Column(JSON, default={})
    threshold_config = Column(JSON, default={})
    
    # Status
    is_active = Column(Boolean, default=True)
    is_validated = Column(Boolean, default=False)
    validation_results = Column(JSON, default={})
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_by_user_id = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
