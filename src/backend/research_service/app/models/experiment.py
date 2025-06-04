"""
Database models for experiment tracking
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()


class Experiment(Base):
    """Experiment model for tracking research experiments."""
    
    __tablename__ = "experiments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    hypothesis = Column(Text)
    methodology = Column(Text)
    parameters = Column(JSON, default=dict)
    expected_duration_hours = Column(Float)
    success_criteria = Column(JSON, default=dict)
    tags = Column(JSON, default=list)
    metadata = Column(JSON, default=dict)
    status = Column(String(50), nullable=False, default="created", index=True)
    
    # Audit fields
    created_by = Column(Integer)  # User ID
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    runs = relationship("ExperimentRun", back_populates="experiment", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Experiment(id='{self.id}', name='{self.name}', status='{self.status}')>"


class ExperimentRun(Base):
    """Experiment run model for tracking individual experiment executions."""
    
    __tablename__ = "experiment_runs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    experiment_id = Column(String, ForeignKey("experiments.id"), nullable=False, index=True)
    run_number = Column(Integer, nullable=False)
    config = Column(JSON, default=dict)
    status = Column(String(50), nullable=False, default="created", index=True)
    
    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)
    
    # Results
    summary = Column(Text)
    conclusions = Column(JSON, default=list)
    recommendations = Column(JSON, default=list)
    
    # Metadata
    metadata = Column(JSON, default=dict)
    
    # Relationships
    experiment = relationship("Experiment", back_populates="runs")
    metrics = relationship("ExperimentMetric", back_populates="run", cascade="all, delete-orphan")
    artifacts = relationship("ExperimentArtifact", back_populates="run", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ExperimentRun(id='{self.id}', experiment_id='{self.experiment_id}', run_number={self.run_number})>"


class ExperimentMetric(Base):
    """Experiment metric model for tracking experiment measurements."""
    
    __tablename__ = "experiment_metrics"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String, ForeignKey("experiment_runs.id"), nullable=False, index=True)
    metric_name = Column(String(255), nullable=False, index=True)
    value = Column(Float, nullable=False)
    step = Column(Integer)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    metadata = Column(JSON, default=dict)
    
    # Relationships
    run = relationship("ExperimentRun", back_populates="metrics")
    
    def __repr__(self):
        return f"<ExperimentMetric(id='{self.id}', metric_name='{self.metric_name}', value={self.value})>"


class ExperimentArtifact(Base):
    """Experiment artifact model for tracking experiment outputs."""
    
    __tablename__ = "experiment_artifacts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String, ForeignKey("experiment_runs.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # json, pickle, text, binary, etc.
    path = Column(String(500), nullable=False)
    size_bytes = Column(Integer)
    checksum = Column(String(64))  # SHA-256 hash
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    run = relationship("ExperimentRun", back_populates="artifacts")
    
    def __repr__(self):
        return f"<ExperimentArtifact(id='{self.id}', name='{self.name}', type='{self.type}')>"


class ResearchProject(Base):
    """Research project model for organizing related experiments."""
    
    __tablename__ = "research_projects"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    objectives = Column(JSON, default=list)
    status = Column(String(50), nullable=False, default="active", index=True)
    
    # Timeline
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    
    # Team
    principal_investigator = Column(Integer)  # User ID
    team_members = Column(JSON, default=list)  # List of user IDs
    
    # Metadata
    tags = Column(JSON, default=list)
    metadata = Column(JSON, default=dict)
    
    # Audit fields
    created_by = Column(Integer)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ResearchProject(id='{self.id}', name='{self.name}', status='{self.status}')>"


class AutomationRule(Base):
    """Automation rule model for research automation."""
    
    __tablename__ = "automation_rules"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    trigger_type = Column(String(50), nullable=False)  # scheduled, event_driven, threshold_based, manual
    conditions = Column(JSON, default=dict)
    actions = Column(JSON, default=list)
    enabled = Column(Boolean, default=True, index=True)
    
    # Execution tracking
    last_executed = Column(DateTime)
    execution_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    
    # Metadata
    metadata = Column(JSON, default=dict)
    
    # Audit fields
    created_by = Column(Integer)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<AutomationRule(id='{self.id}', name='{self.name}', enabled={self.enabled})>"


class ResearchPipeline(Base):
    """Research pipeline model for automated research workflows."""
    
    __tablename__ = "research_pipelines"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    stages = Column(JSON, default=list)
    dependencies = Column(JSON, default=list)
    schedule = Column(String(100))  # Cron expression
    enabled = Column(Boolean, default=True, index=True)
    
    # Execution tracking
    last_executed = Column(DateTime)
    execution_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    average_duration_seconds = Column(Float)
    
    # Metadata
    metadata = Column(JSON, default=dict)
    
    # Audit fields
    created_by = Column(Integer)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ResearchPipeline(id='{self.id}', name='{self.name}', enabled={self.enabled})>"


class PipelineExecution(Base):
    """Pipeline execution model for tracking pipeline runs."""
    
    __tablename__ = "pipeline_executions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    pipeline_id = Column(String, ForeignKey("research_pipelines.id"), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="running", index=True)
    
    # Timing
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)
    
    # Configuration
    parameters = Column(JSON, default=dict)
    
    # Results
    results = Column(JSON, default=dict)
    logs = Column(Text)
    error_message = Column(Text)
    
    # Metadata
    metadata = Column(JSON, default=dict)
    
    def __repr__(self):
        return f"<PipelineExecution(id='{self.id}', pipeline_id='{self.pipeline_id}', status='{self.status}')>"
