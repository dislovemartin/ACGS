from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime

# Base schema for Principle attributes
class PrincipleBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100, description="Unique name of the principle")
    description: Optional[str] = Field(None, max_length=500, description="Detailed description of the principle")
    content: str = Field(..., description="The full content of the principle (e.g., text, JSON string)")

    # Enhanced Phase 1 Constitutional Fields
    priority_weight: Optional[float] = Field(None, ge=0.0, le=1.0, description="Priority weight for principle prioritization (0.0 to 1.0)")
    scope: Optional[List[str]] = Field(None, description="List of contexts where principle applies")
    normative_statement: Optional[str] = Field(None, description="Structured normative statement for constitutional interpretation")
    constraints: Optional[dict] = Field(None, description="Formal constraints and requirements")
    rationale: Optional[str] = Field(None, description="Detailed rationale and justification for the principle")
    keywords: Optional[List[str]] = Field(None, description="Keywords for principle categorization")
    category: Optional[str] = Field(None, max_length=100, description="Category classification (e.g., Safety, Privacy, Fairness)")
    validation_criteria_nl: Optional[str] = Field(None, description="Natural language validation criteria for testing")
    constitutional_metadata: Optional[dict] = Field(None, description="Metadata for constitutional compliance tracking")

# Schema for creating a new principle
class PrincipleCreate(PrincipleBase):
    # version and status will have default values in the model
    # created_by_user_id will be passed from the request context (e.g., authenticated user)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Data Privacy Protection",
                "description": "Ensure user data privacy and protection",
                "content": "All user data must be encrypted and access logged",
                "priority_weight": 0.8,
                "scope": ["data_processing", "user_management"],
                "category": "Privacy"
            }
        }

# Schema for updating an existing principle
# All fields are optional for updates
class PrincipleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = None
    status: Optional[str] = Field(None, description="e.g., 'draft', 'approved', 'deprecated'")

    # Enhanced Phase 1 Constitutional Fields (all optional for updates)
    priority_weight: Optional[float] = Field(None, ge=0.0, le=1.0, description="Priority weight for principle prioritization")
    scope: Optional[List[str]] = Field(None, description="List of contexts where principle applies")
    normative_statement: Optional[str] = Field(None, description="Structured normative statement")
    constraints: Optional[dict] = Field(None, description="Formal constraints and requirements")
    rationale: Optional[str] = Field(None, description="Detailed rationale and justification")
    keywords: Optional[List[str]] = Field(None, description="Keywords for categorization")
    category: Optional[str] = Field(None, max_length=100, description="Category classification")
    validation_criteria_nl: Optional[str] = Field(None, description="Natural language validation criteria")
    constitutional_metadata: Optional[dict] = Field(None, description="Constitutional compliance metadata")
    # version might be handled automatically or via a specific versioning endpoint
    # version: Optional[int] = Field(None, gt=0)

# Schema for representing a Principle in API responses
class Principle(PrincipleBase):
    id: int
    version: int
    status: str
    created_at: datetime
    updated_at: datetime
    created_by_user_id: Optional[int] = None # Made optional if user can be anonymous or system-created

    class Config:
        from_attributes = True # For SQLAlchemy model compatibility (Pydantic v2)

# Optional: Schema for a list of principles for responses
class PrincipleList(BaseModel):
    principles: List[Principle]
    total: int

# Placeholder for user information, to be refined with actual auth integration
class User(BaseModel):
    id: int
    username: str
    roles: List[str] = [] # e.g., ["user", "ac_admin"]

# Constitutional Council and AC Enhancement Schemas

# Meta-Rules (R) component schemas
class ACMetaRuleBase(BaseModel):
    rule_type: str = Field(..., description="Type of meta-rule (e.g., amendment_procedure, voting_threshold)")
    name: str = Field(..., min_length=3, max_length=255, description="Name of the meta-rule")
    description: Optional[str] = Field(None, description="Description of the meta-rule")
    rule_definition: dict = Field(..., description="JSON structure defining the meta-governance rule")
    threshold: Optional[str] = Field(None, description="Voting threshold (e.g., 0.67, simple_majority)")
    stakeholder_roles: Optional[List[str]] = Field(None, description="Roles that can participate")
    decision_mechanism: Optional[str] = Field(None, description="Decision mechanism (e.g., supermajority_vote)")

class ACMetaRuleCreate(ACMetaRuleBase):

    class Config:
        json_schema_extra = {
            "example": {
                "rule_type": "voting_threshold",
                "name": "Constitutional Amendment Threshold",
                "description": "Defines voting threshold for constitutional amendments",
                "threshold": "0.67",
                "stakeholder_roles": ["admin", "policy_manager"],
                "decision_mechanism": "supermajority_vote"
            }
        }

class ACMetaRuleUpdate(BaseModel):
    rule_type: Optional[str] = None
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    rule_definition: Optional[dict] = None
    threshold: Optional[str] = None
    stakeholder_roles: Optional[List[str]] = None
    decision_mechanism: Optional[str] = None
    status: Optional[str] = Field(None, description="Status (active, deprecated, proposed)")

class ACMetaRule(ACMetaRuleBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    created_by_user_id: Optional[int] = None

    class Config:
        from_attributes = True

# Amendment schemas with enhanced Pydantic v2.0+ validation
class ACAmendmentBase(BaseModel):
    principle_id: int = Field(..., description="ID of the principle being amended", gt=0)
    amendment_type: str = Field(
        ...,
        description="Type of amendment (modify, add, remove, status_change)",
        pattern="^(modify|add|remove|status_change)$"
    )
    proposed_changes: str = Field(
        ...,
        description="Description of proposed changes",
        min_length=10,
        max_length=5000
    )
    justification: Optional[str] = Field(
        None,
        description="Rationale for the amendment",
        max_length=2000
    )
    proposed_content: Optional[str] = Field(
        None,
        description="New content if modifying/adding",
        max_length=10000
    )
    proposed_status: Optional[str] = Field(
        None,
        description="New status if changing status",
        pattern="^(active|inactive|deprecated|under_review)$"
    )

    # Co-evolution metadata fields
    urgency_level: Optional[str] = Field(
        "normal",
        description="Amendment urgency level for co-evolution handling",
        pattern="^(normal|rapid|emergency)$"
    )
    co_evolution_context: Optional[Dict[str, Any]] = Field(
        None,
        description="Context for rapid co-evolution scenarios"
    )
    expected_impact: Optional[str] = Field(
        None,
        description="Expected impact assessment",
        pattern="^(low|medium|high|critical)$"
    )

class ACAmendmentCreate(ACAmendmentBase):
    consultation_period_days: Optional[int] = Field(
        30,
        description="Days for public consultation",
        ge=1,
        le=365
    )
    public_comment_enabled: bool = Field(True, description="Enable public comments")
    stakeholder_groups: Optional[List[str]] = Field(
        None,
        description="Stakeholder groups to invite",
        max_items=20
    )

    # Enhanced validation for co-evolution
    rapid_processing_requested: bool = Field(
        False,
        description="Request rapid processing for urgent amendments"
    )
    constitutional_significance: Optional[str] = Field(
        "normal",
        description="Constitutional significance level",
        pattern="^(normal|significant|fundamental)$"
    )

    @field_validator('stakeholder_groups')
    @classmethod
    def validate_stakeholder_groups(cls, v):
        if v is not None:
            valid_groups = {
                "citizens", "experts", "affected_parties", "regulatory_bodies",
                "constitutional_council", "policy_managers", "auditors",
                "privacy_advocates", "security_experts", "legal_experts"
            }
            for group in v:
                if group not in valid_groups:
                    raise ValueError(f"Invalid stakeholder group: {group}")
        return v

    @field_validator('co_evolution_context')
    @classmethod
    def validate_co_evolution_context(cls, v):
        if v is not None:
            required_fields = {"trigger_event", "timeline", "stakeholders"}
            if not all(field in v for field in required_fields):
                raise ValueError(f"Co-evolution context must include: {required_fields}")
        return v

class ACAmendmentUpdate(BaseModel):
    amendment_type: Optional[str] = None
    proposed_changes: Optional[str] = None
    justification: Optional[str] = None
    proposed_content: Optional[str] = None
    proposed_status: Optional[str] = None
    status: Optional[str] = Field(None, description="Workflow status")
    consultation_period_days: Optional[int] = None
    public_comment_enabled: Optional[bool] = None
    stakeholder_groups: Optional[List[str]] = None

class ACAmendment(ACAmendmentBase):
    id: int
    status: str
    voting_started_at: Optional[datetime] = None
    voting_ends_at: Optional[datetime] = None
    votes_for: int = 0
    votes_against: int = 0
    votes_abstain: int = 0
    required_threshold: Optional[str] = None
    consultation_period_days: Optional[int] = None
    public_comment_enabled: bool = True
    stakeholder_groups: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime
    proposed_by_user_id: int

    # Co-evolution and versioning fields
    version: int = Field(1, description="Amendment version for optimistic locking")
    rapid_processing_requested: bool = False
    constitutional_significance: Optional[str] = "normal"
    processing_metrics: Optional[Dict[str, Any]] = Field(
        None,
        description="Performance metrics for co-evolution tracking"
    )

    # Workflow state tracking
    workflow_state: Optional[str] = Field(
        "proposed",
        description="Current workflow state",
        pattern="^(proposed|under_review|voting|approved|rejected|implemented)$"
    )
    state_transitions: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="History of state transitions"
    )

    class Config:
        from_attributes = True

# Amendment vote schemas
class ACAmendmentVoteBase(BaseModel):
    vote: str = Field(..., description="Vote choice (for, against, abstain)")
    reasoning: Optional[str] = Field(None, description="Optional explanation of vote")

class ACAmendmentVoteCreate(ACAmendmentVoteBase):
    amendment_id: int = Field(..., description="ID of the amendment being voted on")

class ACAmendmentVote(ACAmendmentVoteBase):
    id: int
    amendment_id: int
    voter_id: int
    voted_at: datetime

    class Config:
        from_attributes = True

# Amendment comment schemas
class ACAmendmentCommentBase(BaseModel):
    comment_text: str = Field(..., description="Comment content")
    sentiment: Optional[str] = Field(None, description="Comment sentiment (support, oppose, neutral)")
    stakeholder_group: Optional[str] = Field(None, description="Stakeholder group of commenter")

class ACAmendmentCommentCreate(ACAmendmentCommentBase):
    amendment_id: int = Field(..., description="ID of the amendment being commented on")
    commenter_name: Optional[str] = Field(None, description="Name for anonymous commenters")
    commenter_email: Optional[str] = Field(None, description="Email for anonymous commenters")

class ACAmendmentComment(ACAmendmentCommentBase):
    id: int
    amendment_id: int
    commenter_id: Optional[int] = None
    commenter_name: Optional[str] = None
    commenter_email: Optional[str] = None
    is_public: bool = True
    is_moderated: bool = False
    created_at: datetime

    class Config:
        from_attributes = True

# Conflict resolution schemas
class ACConflictResolutionBase(BaseModel):
    conflict_type: str = Field(..., description="Type of conflict (principle_contradiction, practical_incompatibility)")
    principle_ids: List[int] = Field(..., description="IDs of principles involved in conflict")
    context: Optional[str] = Field(None, description="Context of the conflict")
    conflict_description: str = Field(..., description="Description of the conflict")
    severity: str = Field(..., description="Severity level (low, medium, high, critical)")
    resolution_strategy: str = Field(..., description="Strategy for resolution")
    resolution_details: Optional[dict] = Field(None, description="Structured resolution information")
    precedence_order: Optional[List[int]] = Field(None, description="Priority order of principles")

class ACConflictResolutionCreate(ACConflictResolutionBase):

    class Config:
        json_schema_extra = {
            "example": {
                "conflict_type": "priority_conflict",
                "principle_ids": [1, 2],
                "context": "Privacy vs Security conflict in user authentication",
                "resolution_strategy": "weighted_priority",
                "resolution_details": {"weights": {"privacy": 0.6, "security": 0.4}},
                "precedence_order": [1, 2]
            }
        }

class ACConflictResolutionUpdate(BaseModel):
    conflict_type: Optional[str] = None
    principle_ids: Optional[List[int]] = None
    context: Optional[str] = None
    conflict_description: Optional[str] = None
    severity: Optional[str] = None
    resolution_strategy: Optional[str] = None
    resolution_details: Optional[dict] = None
    precedence_order: Optional[List[int]] = None
    status: Optional[str] = Field(None, description="Status (identified, analyzed, resolved, monitoring)")

class ACConflictResolution(ACConflictResolutionBase):
    id: int
    status: str
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    identified_by_user_id: Optional[int] = None

    class Config:
        from_attributes = True


# Human-in-the-Loop Sampling Schemas

class UncertaintyMetrics(BaseModel):
    """Schema for uncertainty metrics in different dimensions."""
    constitutional: float = Field(..., ge=0.0, le=1.0, description="Constitutional interpretation uncertainty")
    technical: float = Field(..., ge=0.0, le=1.0, description="Technical implementation uncertainty")
    stakeholder: float = Field(..., ge=0.0, le=1.0, description="Stakeholder consensus uncertainty")
    precedent: float = Field(..., ge=0.0, le=1.0, description="Historical precedent uncertainty")
    complexity: float = Field(..., ge=0.0, le=1.0, description="Overall complexity uncertainty")


class HITLSamplingRequest(BaseModel):
    """Schema for requesting human-in-the-loop sampling assessment."""
    decision_id: str = Field(..., description="Unique identifier for the decision")
    decision_context: Dict[str, Any] = Field(..., description="Context information for the decision")
    ai_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="AI confidence score if available")
    principle_ids: Optional[List[int]] = Field(None, description="Related constitutional principle IDs")

    # Decision characteristics
    decision_scope: Optional[str] = Field("local", description="Scope of decision (local, service, system, global)")
    time_pressure: Optional[str] = Field("normal", description="Time pressure level (low, normal, high, critical)")
    reversibility: Optional[str] = Field("reversible", description="Reversibility (reversible, difficult, irreversible)")
    impact_magnitude: Optional[str] = Field("low", description="Impact magnitude (low, medium, high, critical)")
    safety_critical: bool = Field(False, description="Whether decision is safety-critical")

    # Stakeholder information
    stakeholder_count: Optional[int] = Field(1, ge=1, description="Number of stakeholders involved")
    stakeholder_diversity: Optional[float] = Field(0.5, ge=0.0, le=1.0, description="Stakeholder diversity score")
    stakeholder_conflicts: bool = Field(False, description="Whether stakeholder conflicts exist")
    requires_public_consultation: bool = Field(False, description="Whether public consultation is required")

    # Technical factors
    multi_service: bool = Field(False, description="Decision affects multiple services")
    database_changes: bool = Field(False, description="Requires database modifications")
    external_apis: bool = Field(False, description="Involves external API calls")
    real_time_processing: bool = Field(False, description="Requires real-time processing")
    security_implications: bool = Field(False, description="Has security implications")
    performance_critical: bool = Field(False, description="Performance-critical operation")
    novel_technology: bool = Field(False, description="Uses novel or experimental technology")

    # Context flags
    novel_scenario: bool = Field(False, description="Novel scenario without precedent")
    has_training_data: bool = Field(True, description="AI has relevant training data")
    domain_expertise_available: bool = Field(True, description="Domain expertise is available")
    clear_requirements: bool = Field(True, description="Requirements are clear and well-defined")
    has_implementation_precedent: bool = Field(True, description="Implementation precedent exists")
    has_stakeholder_feedback: bool = Field(False, description="Previous stakeholder feedback available")
    escalation_required: bool = Field(False, description="Escalation from conflict resolution")

    class Config:
        json_schema_extra = {
            "example": {
                "decision_id": "policy_update_2024_001",
                "decision_context": {
                    "policy_type": "privacy_protection",
                    "affected_users": 10000,
                    "regulatory_compliance": True
                },
                "ai_confidence": 0.72,
                "principle_ids": [1, 3, 7],
                "decision_scope": "system",
                "safety_critical": True,
                "stakeholder_count": 5,
                "stakeholder_conflicts": True
            }
        }


class HITLSamplingResult(BaseModel):
    """Schema for human-in-the-loop sampling assessment result."""
    decision_id: str = Field(..., description="Decision identifier")
    overall_uncertainty: float = Field(..., ge=0.0, le=1.0, description="Overall uncertainty score")
    dimensional_uncertainties: UncertaintyMetrics = Field(..., description="Uncertainty by dimension")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="AI confidence in decision")

    # Sampling decision
    requires_human_oversight: bool = Field(..., description="Whether human oversight is required")
    recommended_oversight_level: str = Field(..., description="Recommended level of oversight")
    triggers_activated: List[str] = Field(..., description="List of activated sampling triggers")

    # Assessment metadata
    assessment_timestamp: datetime = Field(..., description="When assessment was performed")
    assessment_metadata: Dict[str, Any] = Field(..., description="Additional assessment metadata")

    # Performance tracking
    processing_time_ms: Optional[float] = Field(None, description="Assessment processing time in milliseconds")

    class Config:
        json_schema_extra = {
            "example": {
                "decision_id": "policy_update_2024_001",
                "overall_uncertainty": 0.78,
                "dimensional_uncertainties": {
                    "constitutional": 0.65,
                    "technical": 0.45,
                    "stakeholder": 0.85,
                    "precedent": 0.70,
                    "complexity": 0.75
                },
                "confidence_score": 0.72,
                "requires_human_oversight": True,
                "recommended_oversight_level": "constitutional_council",
                "triggers_activated": ["high_uncertainty", "stakeholder_conflict", "safety_critical"],
                "assessment_timestamp": "2024-01-15T10:30:00Z"
            }
        }


class HITLFeedbackRequest(BaseModel):
    """Schema for submitting human feedback on HITL sampling decisions."""
    assessment_id: str = Field(..., description="ID of the original assessment")
    human_decision: Dict[str, Any] = Field(..., description="Human decision and reasoning")
    agreed_with_assessment: bool = Field(..., description="Whether human agreed with AI assessment")
    reasoning: Optional[str] = Field(None, description="Human reasoning for the decision")
    quality_score: Optional[float] = Field(0.8, ge=0.0, le=1.0, description="Quality score for the decision")
    feedback_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional feedback metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "assessment_id": "policy_update_2024_001",
                "human_decision": {
                    "oversight_needed": True,
                    "final_decision": "approved_with_conditions",
                    "conditions": ["additional_stakeholder_review", "security_audit"]
                },
                "agreed_with_assessment": True,
                "reasoning": "Assessment correctly identified stakeholder conflicts requiring Constitutional Council review",
                "quality_score": 0.9
            }
        }


class HITLPerformanceMetrics(BaseModel):
    """Schema for HITL sampling performance metrics."""
    total_assessments: int = Field(..., description="Total number of assessments performed")
    human_oversight_triggered: int = Field(..., description="Number of times human oversight was triggered")
    oversight_rate: float = Field(..., ge=0.0, le=1.0, description="Rate of human oversight triggers")
    accuracy_rate: float = Field(..., ge=0.0, le=1.0, description="Accuracy rate of oversight predictions")
    false_positive_rate: float = Field(..., ge=0.0, le=1.0, description="False positive rate")
    recent_accuracy: float = Field(..., ge=0.0, le=1.0, description="Recent accuracy (last 50 assessments)")
    recent_quality: float = Field(..., ge=0.0, le=1.0, description="Recent decision quality score")

    # Configuration
    current_thresholds: Dict[str, float] = Field(..., description="Current uncertainty and confidence thresholds")
    learning_enabled: bool = Field(..., description="Whether adaptive learning is enabled")
    feedback_samples: int = Field(..., description="Number of feedback samples collected")
    threshold_adjustments_count: int = Field(..., description="Number of threshold adjustments made")

    class Config:
        json_schema_extra = {
            "example": {
                "total_assessments": 1250,
                "human_oversight_triggered": 187,
                "oversight_rate": 0.15,
                "accuracy_rate": 0.94,
                "false_positive_rate": 0.04,
                "recent_accuracy": 0.96,
                "recent_quality": 0.88,
                "current_thresholds": {
                    "uncertainty_threshold": 0.75,
                    "confidence_threshold": 0.75
                },
                "learning_enabled": True,
                "feedback_samples": 89,
                "threshold_adjustments_count": 3
            }
        }
