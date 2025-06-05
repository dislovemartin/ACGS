from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# --- Feedback Schemas ---
class FeedbackType(str, Enum):
    accuracy = "accuracy"
    relevance = "relevance"
    completeness = "completeness"
    bias = "bias"
    safety = "safety"
    custom = "custom"


class FeedbackInput(BaseModel):
    feedback_type: FeedbackType = Field(
        ..., description="Type of feedback being provided"
    )
    feedback_value: Any = Field(
        ..., description="Value of the feedback (e.g., score, boolean, text)"
    )
    context: Optional[Dict[str, Any]] = Field(
        None, description="Contextual information related to the feedback"
    )

    @field_validator("feedback_value")
    def validate_feedback_value(cls, v, info):
        if info.data["feedback_type"] == FeedbackType.accuracy:
            if not isinstance(v, (int, float)) or not (0 <= v <= 1):
                raise ValueError("Accuracy feedback must be a float between 0 and 1")
        return v


class FeedbackResponse(BaseModel):
    message: str
    feedback_id: Optional[str] = None
    status: str
    timestamp: datetime


# --- Learning Data Schemas ---
class LearningDataInput(BaseModel):
    data_type: str = Field(
        ...,
        description=(
            "Type of learning data (e.g., 'constitutional_amendment', " "'policy_log')"
        ),
    )
    content: Dict[str, Any] = Field(..., description="The actual data content")
    source: Optional[str] = Field(
        None,
        description=(
            "Source of the data (e.g., 'constitutional_council', " "'user_feedback')"
        ),
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class LearningDataResponse(BaseModel):
    message: str
    data_id: Optional[str] = None
    status: str
    timestamp: datetime


# --- Continuous Learning System Control Schemas ---
class LearningPhase(str, Enum):
    data_collection = "data_collection"
    model_training = "model_training"
    evaluation = "evaluation"
    deployment = "deployment"


class LearningStrategy(str, Enum):
    reinforcement = "reinforcement"
    supervised = "supervised"
    active_learning = "active_learning"


class WINAContinuousLearningSystemConfig(BaseModel):
    enabled: bool = Field(
        True, description="Enable/disable the continuous learning system"
    )
    learning_interval_seconds: int = Field(
        3600, ge=60, description="How often the system checks for new data (in seconds)"
    )
    min_data_points_for_retrain: int = Field(
        100,
        ge=10,
        description=("Minimum new data points to trigger a retraining cycle"),
    )
    learning_strategy: LearningStrategy = Field(
        LearningStrategy.reinforcement,
        description="Overall strategy for continuous learning",
    )
    model_selection_criteria: Optional[List[str]] = Field(
        None, description="Criteria for selecting models post-training"
    )


class WINAContinuousLearningSystemStatus(BaseModel):
    status: str = Field(
        ...,
        description=("Current operational status (e.g., 'running', 'paused', 'error')"),
    )
    last_run_timestamp: Optional[datetime] = None
    next_run_timestamp: Optional[datetime] = None
    current_phase: Optional[LearningPhase] = None
    data_points_collected_since_last_retrain: int = 0
    models_trained_count: int = 0
    errors_count: int = 0
    message: Optional[str] = None
