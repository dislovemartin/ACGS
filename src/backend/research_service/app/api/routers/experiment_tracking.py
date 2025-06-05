"""
Experiment Tracking API Router

Provides endpoints for experiment management, tracking, and analysis.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from ...core.database import get_db_session
from ...services.experiment_tracker import (
    ExperimentTracker, ExperimentConfig, ExperimentStatus, MetricType
)
from ...models.experiment import Experiment, ExperimentRun, ExperimentMetric

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic models for API
class ExperimentCreateRequest(BaseModel):
    """Request model for creating experiments."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    hypothesis: str = Field(..., min_length=1)
    methodology: str = Field(..., min_length=1)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    expected_duration_hours: float = Field(..., gt=0, le=168)  # Max 1 week
    success_criteria: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExperimentResponse(BaseModel):
    """Response model for experiments."""
    id: str
    name: str
    description: Optional[str]
    hypothesis: str
    methodology: str
    parameters: Dict[str, Any]
    expected_duration_hours: float
    success_criteria: Dict[str, Any]
    tags: List[str]
    metadata: Dict[str, Any]
    status: str
    created_at: datetime
    updated_at: Optional[datetime]


class ExperimentRunCreateRequest(BaseModel):
    """Request model for creating experiment runs."""
    config: Dict[str, Any] = Field(default_factory=dict)


class ExperimentRunResponse(BaseModel):
    """Response model for experiment runs."""
    id: str
    experiment_id: str
    run_number: int
    config: Dict[str, Any]
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    summary: Optional[str]
    conclusions: List[str]
    recommendations: List[str]


class MetricLogRequest(BaseModel):
    """Request model for logging metrics."""
    metric_name: str = Field(..., min_length=1, max_length=255)
    value: float
    step: Optional[int] = None
    timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MetricResponse(BaseModel):
    """Response model for metrics."""
    id: str
    run_id: str
    metric_name: str
    value: float
    step: Optional[int]
    timestamp: datetime
    metadata: Dict[str, Any]


class ArtifactSaveRequest(BaseModel):
    """Request model for saving artifacts."""
    artifact_name: str = Field(..., min_length=1, max_length=255)
    artifact_data: Any
    artifact_type: str = Field(default="json")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExperimentCompleteRequest(BaseModel):
    """Request model for completing experiments."""
    status: str = Field(default="completed")
    summary: Optional[str] = None
    conclusions: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


# Initialize experiment tracker
experiment_tracker = ExperimentTracker()


@router.post("/", response_model=ExperimentResponse)
async def create_experiment(
    request: ExperimentCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    user_id: Optional[int] = None
):
    """Create a new experiment."""
    try:
        config = ExperimentConfig(
            name=request.name,
            description=request.description or "",
            hypothesis=request.hypothesis,
            methodology=request.methodology,
            parameters=request.parameters,
            expected_duration_hours=request.expected_duration_hours,
            success_criteria=request.success_criteria,
            tags=request.tags,
            metadata=request.metadata
        )
        
        experiment = await experiment_tracker.create_experiment(db, config, user_id)
        
        return ExperimentResponse(
            id=experiment.id,
            name=experiment.name,
            description=experiment.description,
            hypothesis=experiment.hypothesis,
            methodology=experiment.methodology,
            parameters=experiment.parameters,
            expected_duration_hours=experiment.expected_duration_hours,
            success_criteria=experiment.success_criteria,
            tags=experiment.tags,
            metadata=experiment.metadata,
            status=experiment.status,
            created_at=experiment.created_at,
            updated_at=experiment.updated_at
        )
        
    except Exception as e:
        logger.error(f"Error creating experiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[ExperimentResponse])
async def list_experiments(
    db: AsyncSession = Depends(get_db_session),
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0)
):
    """List experiments with optional filtering."""
    try:
        # This would be implemented with proper database queries
        # For now, return empty list as placeholder
        return []
        
    except Exception as e:
        logger.error(f"Error listing experiments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment(
    experiment_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get experiment by ID."""
    try:
        # This would be implemented with proper database queries
        # For now, raise not found as placeholder
        raise HTTPException(status_code=404, detail="Experiment not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting experiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{experiment_id}/runs", response_model=ExperimentRunResponse)
async def start_experiment_run(
    experiment_id: str,
    request: ExperimentRunCreateRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Start a new experiment run."""
    try:
        experiment_run = await experiment_tracker.start_experiment_run(
            db, experiment_id, request.config
        )
        
        return ExperimentRunResponse(
            id=experiment_run.id,
            experiment_id=experiment_run.experiment_id,
            run_number=experiment_run.run_number,
            config=experiment_run.config,
            status=experiment_run.status,
            started_at=experiment_run.started_at,
            completed_at=experiment_run.completed_at,
            duration_seconds=experiment_run.duration_seconds,
            summary=experiment_run.summary,
            conclusions=experiment_run.conclusions or [],
            recommendations=experiment_run.recommendations or []
        )
        
    except Exception as e:
        logger.error(f"Error starting experiment run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{experiment_id}/runs/{run_id}/metrics", response_model=MetricResponse)
async def log_metric(
    experiment_id: str,
    run_id: str,
    request: MetricLogRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Log a metric for an experiment run."""
    try:
        metric = await experiment_tracker.log_metric(
            db=db,
            run_id=run_id,
            metric_name=request.metric_name,
            value=request.value,
            step=request.step,
            timestamp=request.timestamp,
            metadata=request.metadata
        )
        
        return MetricResponse(
            id=metric.id,
            run_id=metric.run_id,
            metric_name=metric.metric_name,
            value=metric.value,
            step=metric.step,
            timestamp=metric.timestamp,
            metadata=metric.metadata
        )
        
    except Exception as e:
        logger.error(f"Error logging metric: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{experiment_id}/runs/{run_id}/artifacts")
async def save_artifact(
    experiment_id: str,
    run_id: str,
    request: ArtifactSaveRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Save an artifact for an experiment run."""
    try:
        artifact = await experiment_tracker.save_artifact(
            db=db,
            run_id=run_id,
            artifact_name=request.artifact_name,
            artifact_data=request.artifact_data,
            artifact_type=request.artifact_type,
            metadata=request.metadata
        )
        
        return {
            "id": artifact.id,
            "name": artifact.name,
            "type": artifact.type,
            "size_bytes": artifact.size_bytes,
            "checksum": artifact.checksum,
            "created_at": artifact.created_at
        }
        
    except Exception as e:
        logger.error(f"Error saving artifact: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{experiment_id}/runs/{run_id}/complete", response_model=ExperimentRunResponse)
async def complete_experiment_run(
    experiment_id: str,
    run_id: str,
    request: ExperimentCompleteRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Complete an experiment run."""
    try:
        status = ExperimentStatus(request.status)
        
        experiment_run = await experiment_tracker.complete_experiment_run(
            db=db,
            run_id=run_id,
            status=status,
            summary=request.summary,
            conclusions=request.conclusions,
            recommendations=request.recommendations
        )
        
        return ExperimentRunResponse(
            id=experiment_run.id,
            experiment_id=experiment_run.experiment_id,
            run_number=experiment_run.run_number,
            config=experiment_run.config,
            status=experiment_run.status,
            started_at=experiment_run.started_at,
            completed_at=experiment_run.completed_at,
            duration_seconds=experiment_run.duration_seconds,
            summary=experiment_run.summary,
            conclusions=experiment_run.conclusions or [],
            recommendations=experiment_run.recommendations or []
        )
        
    except Exception as e:
        logger.error(f"Error completing experiment run: {e}")
        raise HTTPException(status_code=500, detail=str(e))
