"""
Experiment Tracking Service for Research Infrastructure

Provides comprehensive experiment tracking, metadata management, and
result analysis for constitutional AI research.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib
import pickle
import numpy as np
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from sqlalchemy.orm import selectinload

from ..core.config import get_settings
from ..models.experiment import Experiment, ExperimentRun, ExperimentMetric, ExperimentArtifact
from ..models.research_data import ResearchDataset, DataPoint

logger = logging.getLogger(__name__)
settings = get_settings()


class ExperimentStatus(Enum):
    """Experiment status enumeration."""
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class MetricType(Enum):
    """Metric type enumeration."""
    ACCURACY = "accuracy"
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    RELIABILITY = "reliability"
    CONSTITUTIONAL_COMPLIANCE = "constitutional_compliance"
    BIAS_SCORE = "bias_score"
    FAIRNESS_SCORE = "fairness_score"
    CUSTOM = "custom"


@dataclass
class ExperimentConfig:
    """Experiment configuration."""
    name: str
    description: str
    hypothesis: str
    methodology: str
    parameters: Dict[str, Any]
    expected_duration_hours: float
    success_criteria: Dict[str, Any]
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExperimentResult:
    """Experiment result container."""
    experiment_id: str
    run_id: str
    status: ExperimentStatus
    metrics: Dict[str, float]
    artifacts: List[str]
    summary: str
    conclusions: List[str]
    recommendations: List[str]
    statistical_significance: Optional[Dict[str, Any]] = None


class ExperimentTracker:
    """Comprehensive experiment tracking service."""
    
    def __init__(self):
        self.active_experiments: Dict[str, Experiment] = {}
        self.data_path = Path(settings.RESEARCH_DATA_PATH)
        self.artifacts_path = Path(settings.EXPERIMENT_ARTIFACTS_PATH)
        
        # Ensure directories exist
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.artifacts_path.mkdir(parents=True, exist_ok=True)
    
    async def create_experiment(
        self,
        db: AsyncSession,
        config: ExperimentConfig,
        user_id: Optional[int] = None
    ) -> Experiment:
        """Create a new experiment."""
        try:
            experiment_id = str(uuid.uuid4())
            
            experiment = Experiment(
                id=experiment_id,
                name=config.name,
                description=config.description,
                hypothesis=config.hypothesis,
                methodology=config.methodology,
                parameters=config.parameters,
                expected_duration_hours=config.expected_duration_hours,
                success_criteria=config.success_criteria,
                tags=config.tags,
                metadata=config.metadata,
                status=ExperimentStatus.CREATED.value,
                created_by=user_id,
                created_at=datetime.now(timezone.utc)
            )
            
            db.add(experiment)
            await db.commit()
            await db.refresh(experiment)
            
            self.active_experiments[experiment_id] = experiment
            
            logger.info(f"Created experiment {experiment_id}: {config.name}")
            return experiment
            
        except Exception as e:
            logger.error(f"Error creating experiment: {e}")
            await db.rollback()
            raise
    
    async def start_experiment_run(
        self,
        db: AsyncSession,
        experiment_id: str,
        run_config: Optional[Dict[str, Any]] = None
    ) -> ExperimentRun:
        """Start a new experiment run."""
        try:
            # Get experiment
            result = await db.execute(
                select(Experiment).where(Experiment.id == experiment_id)
            )
            experiment = result.scalar_one_or_none()
            
            if not experiment:
                raise ValueError(f"Experiment {experiment_id} not found")
            
            run_id = str(uuid.uuid4())
            
            experiment_run = ExperimentRun(
                id=run_id,
                experiment_id=experiment_id,
                run_number=await self._get_next_run_number(db, experiment_id),
                config=run_config or {},
                status=ExperimentStatus.RUNNING.value,
                started_at=datetime.now(timezone.utc)
            )
            
            db.add(experiment_run)
            
            # Update experiment status
            experiment.status = ExperimentStatus.RUNNING.value
            experiment.updated_at = datetime.now(timezone.utc)
            
            await db.commit()
            await db.refresh(experiment_run)
            
            logger.info(f"Started run {run_id} for experiment {experiment_id}")
            return experiment_run
            
        except Exception as e:
            logger.error(f"Error starting experiment run: {e}")
            await db.rollback()
            raise
    
    async def log_metric(
        self,
        db: AsyncSession,
        run_id: str,
        metric_name: str,
        value: float,
        step: Optional[int] = None,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ExperimentMetric:
        """Log a metric for an experiment run."""
        try:
            metric = ExperimentMetric(
                id=str(uuid.uuid4()),
                run_id=run_id,
                metric_name=metric_name,
                value=value,
                step=step,
                timestamp=timestamp or datetime.now(timezone.utc),
                metadata=metadata or {}
            )
            
            db.add(metric)
            await db.commit()
            await db.refresh(metric)
            
            return metric
            
        except Exception as e:
            logger.error(f"Error logging metric: {e}")
            await db.rollback()
            raise
    
    async def save_artifact(
        self,
        db: AsyncSession,
        run_id: str,
        artifact_name: str,
        artifact_data: Union[str, bytes, Dict[str, Any]],
        artifact_type: str = "json",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ExperimentArtifact:
        """Save an experiment artifact."""
        try:
            artifact_id = str(uuid.uuid4())
            
            # Save artifact to filesystem
            artifact_path = self.artifacts_path / run_id / f"{artifact_name}_{artifact_id}"
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            
            if artifact_type == "json":
                with open(artifact_path.with_suffix(".json"), "w") as f:
                    json.dump(artifact_data, f, indent=2)
            elif artifact_type == "pickle":
                with open(artifact_path.with_suffix(".pkl"), "wb") as f:
                    pickle.dump(artifact_data, f)
            elif artifact_type == "text":
                with open(artifact_path.with_suffix(".txt"), "w") as f:
                    f.write(str(artifact_data))
            elif artifact_type == "binary":
                with open(artifact_path, "wb") as f:
                    f.write(artifact_data)
            else:
                raise ValueError(f"Unsupported artifact type: {artifact_type}")
            
            # Create database record
            artifact = ExperimentArtifact(
                id=artifact_id,
                run_id=run_id,
                name=artifact_name,
                type=artifact_type,
                path=str(artifact_path),
                size_bytes=artifact_path.stat().st_size,
                checksum=self._calculate_checksum(artifact_path),
                metadata=metadata or {},
                created_at=datetime.now(timezone.utc)
            )
            
            db.add(artifact)
            await db.commit()
            await db.refresh(artifact)
            
            logger.info(f"Saved artifact {artifact_name} for run {run_id}")
            return artifact
            
        except Exception as e:
            logger.error(f"Error saving artifact: {e}")
            await db.rollback()
            raise
    
    async def complete_experiment_run(
        self,
        db: AsyncSession,
        run_id: str,
        status: ExperimentStatus = ExperimentStatus.COMPLETED,
        summary: Optional[str] = None,
        conclusions: Optional[List[str]] = None,
        recommendations: Optional[List[str]] = None
    ) -> ExperimentRun:
        """Complete an experiment run."""
        try:
            # Get experiment run
            result = await db.execute(
                select(ExperimentRun).where(ExperimentRun.id == run_id)
            )
            experiment_run = result.scalar_one_or_none()
            
            if not experiment_run:
                raise ValueError(f"Experiment run {run_id} not found")
            
            # Update run
            experiment_run.status = status.value
            experiment_run.completed_at = datetime.now(timezone.utc)
            experiment_run.summary = summary
            experiment_run.conclusions = conclusions or []
            experiment_run.recommendations = recommendations or []
            
            # Calculate duration
            if experiment_run.started_at:
                duration = experiment_run.completed_at - experiment_run.started_at
                experiment_run.duration_seconds = duration.total_seconds()
            
            await db.commit()
            await db.refresh(experiment_run)
            
            logger.info(f"Completed experiment run {run_id} with status {status.value}")
            return experiment_run
            
        except Exception as e:
            logger.error(f"Error completing experiment run: {e}")
            await db.rollback()
            raise
    
    async def _get_next_run_number(self, db: AsyncSession, experiment_id: str) -> int:
        """Get the next run number for an experiment."""
        result = await db.execute(
            select(func.max(ExperimentRun.run_number))
            .where(ExperimentRun.experiment_id == experiment_id)
        )
        max_run = result.scalar()
        return (max_run or 0) + 1
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
