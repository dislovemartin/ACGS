from pydantic import BaseModel, Field
from typing import Optional, List
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

# Amendment schemas
class ACAmendmentBase(BaseModel):
    principle_id: int = Field(..., description="ID of the principle being amended")
    amendment_type: str = Field(..., description="Type of amendment (modify, add, remove, status_change)")
    proposed_changes: str = Field(..., description="Description of proposed changes")
    justification: Optional[str] = Field(None, description="Rationale for the amendment")
    proposed_content: Optional[str] = Field(None, description="New content if modifying/adding")
    proposed_status: Optional[str] = Field(None, description="New status if changing status")

class ACAmendmentCreate(ACAmendmentBase):
    consultation_period_days: Optional[int] = Field(30, description="Days for public consultation")
    public_comment_enabled: bool = Field(True, description="Enable public comments")
    stakeholder_groups: Optional[List[str]] = Field(None, description="Stakeholder groups to invite")

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
