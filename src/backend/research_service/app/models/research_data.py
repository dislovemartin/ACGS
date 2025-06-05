"""
Database models for research data management
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()


class ResearchDataset(Base):
    """Research dataset model for organizing research data."""
    
    __tablename__ = "research_datasets"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    version = Column(String(50), nullable=False, default="1.0.0")
    
    # Dataset metadata
    domain = Column(String(100), index=True)
    data_type = Column(String(50), nullable=False)  # experimental, observational, synthetic
    size_bytes = Column(Integer)
    record_count = Column(Integer)
    
    # Schema information
    schema_definition = Column(JSON, default=dict)
    data_format = Column(String(50))  # json, csv, parquet, etc.
    
    # Quality metrics
    completeness_score = Column(Float)  # 0.0 to 1.0
    consistency_score = Column(Float)  # 0.0 to 1.0
    validity_score = Column(Float)  # 0.0 to 1.0
    
    # Access control
    access_level = Column(String(50), default="private")  # public, private, restricted
    allowed_users = Column(JSON, default=list)
    
    # Storage information
    storage_path = Column(String(500))
    checksum = Column(String(64))  # SHA-256 hash
    
    # Metadata
    tags = Column(JSON, default=list)
    model_metadata = Column(JSON, default=dict)
    
    # Audit fields
    created_by = Column(Integer)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    data_points = relationship("DataPoint", back_populates="dataset", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ResearchDataset(id='{self.id}', name='{self.name}', version='{self.version}')>"


class DataPoint(Base):
    """Individual data point within a research dataset."""
    
    __tablename__ = "data_points"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String, ForeignKey("research_datasets.id"), nullable=False, index=True)
    
    # Data content
    data = Column(JSON, nullable=False)
    
    # Metadata
    source = Column(String(255))
    timestamp = Column(DateTime, index=True)
    quality_score = Column(Float)  # 0.0 to 1.0
    
    # Annotations
    labels = Column(JSON, default=dict)
    annotations = Column(JSON, default=dict)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    dataset = relationship("ResearchDataset", back_populates="data_points")
    
    def __repr__(self):
        return f"<DataPoint(id='{self.id}', dataset_id='{self.dataset_id}')>"


class AnalysisResult(Base):
    """Analysis result model for storing statistical analysis results."""
    
    __tablename__ = "analysis_results"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    
    # Analysis metadata
    analysis_type = Column(String(100), nullable=False, index=True)
    methodology = Column(Text)
    
    # Input data
    input_datasets = Column(JSON, default=list)  # List of dataset IDs
    input_parameters = Column(JSON, default=dict)
    
    # Results
    results = Column(JSON, nullable=False)
    summary = Column(Text)
    conclusions = Column(JSON, default=list)
    recommendations = Column(JSON, default=list)
    
    # Statistical measures
    p_value = Column(Float)
    effect_size = Column(Float)
    confidence_interval = Column(JSON)
    sample_size = Column(Integer)
    
    # Quality metrics
    reliability_score = Column(Float)  # 0.0 to 1.0
    validity_score = Column(Float)  # 0.0 to 1.0
    
    # Reproducibility
    reproducible = Column(Boolean, default=False)
    reproduction_instructions = Column(Text)
    
    # Metadata
    tags = Column(JSON, default=list)
    model_metadata = Column(JSON, default=dict)
    
    # Audit fields
    created_by = Column(Integer)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<AnalysisResult(id='{self.id}', name='{self.name}', analysis_type='{self.analysis_type}')>"


class Benchmark(Base):
    """Benchmark model for tracking performance benchmarks."""
    
    __tablename__ = "benchmarks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    
    # Benchmark metadata
    category = Column(String(100), nullable=False, index=True)
    version = Column(String(50), nullable=False, default="1.0.0")
    
    # Benchmark configuration
    test_cases = Column(JSON, default=list)
    evaluation_metrics = Column(JSON, default=list)
    baseline_scores = Column(JSON, default=dict)
    
    # Execution settings
    timeout_seconds = Column(Integer, default=300)
    max_retries = Column(Integer, default=3)
    
    # Metadata
    tags = Column(JSON, default=list)
    model_metadata = Column(JSON, default=dict)
    
    # Audit fields
    created_by = Column(Integer)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    results = relationship("BenchmarkResult", back_populates="benchmark", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Benchmark(id='{self.id}', name='{self.name}', category='{self.category}')>"


class BenchmarkResult(Base):
    """Benchmark result model for storing benchmark execution results."""
    
    __tablename__ = "benchmark_results"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    benchmark_id = Column(String, ForeignKey("benchmarks.id"), nullable=False, index=True)
    
    # Execution metadata
    system_under_test = Column(String(255), nullable=False)
    test_configuration = Column(JSON, default=dict)
    
    # Results
    scores = Column(JSON, nullable=False)
    detailed_results = Column(JSON, default=dict)
    
    # Performance metrics
    execution_time_seconds = Column(Float)
    memory_usage_mb = Column(Float)
    cpu_usage_percent = Column(Float)
    
    # Status
    status = Column(String(50), nullable=False, default="completed", index=True)
    error_message = Column(Text)
    
    # Comparison with baseline
    improvement_over_baseline = Column(JSON, default=dict)
    regression_detected = Column(Boolean, default=False)
    
    # Metadata
    environment_info = Column(JSON, default=dict)
    model_metadata = Column(JSON, default=dict)
    
    # Audit fields
    executed_by = Column(Integer)
    executed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    benchmark = relationship("Benchmark", back_populates="results")
    
    def __repr__(self):
        return f"<BenchmarkResult(id='{self.id}', benchmark_id='{self.benchmark_id}', status='{self.status}')>"


class ReproducibilityRecord(Base):
    """Reproducibility record for tracking experiment reproducibility."""
    
    __tablename__ = "reproducibility_records"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    original_experiment_id = Column(String, nullable=False, index=True)
    reproduction_experiment_id = Column(String, nullable=False, index=True)
    
    # Reproducibility assessment
    reproducibility_score = Column(Float, nullable=False)  # 0.0 to 1.0
    reproducible = Column(Boolean, nullable=False)
    
    # Comparison results
    metric_comparisons = Column(JSON, default=dict)
    statistical_tests = Column(JSON, default=dict)
    
    # Differences identified
    differences = Column(JSON, default=list)
    potential_causes = Column(JSON, default=list)
    
    # Environment comparison
    environment_differences = Column(JSON, default=dict)
    dependency_differences = Column(JSON, default=dict)
    
    # Metadata
    reproduction_notes = Column(Text)
    model_metadata = Column(JSON, default=dict)
    
    # Audit fields
    created_by = Column(Integer)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ReproducibilityRecord(id='{self.id}', reproducible={self.reproducible}, score={self.reproducibility_score})>"
