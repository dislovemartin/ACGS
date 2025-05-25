# ACGS/shared/schemas.py
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timezone
import uuid # For generating unique IDs for certain fields if needed

# --- Timestamp and Base Models ---

class TimestampMixin(BaseModel):
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @validator("created_at", "updated_at", pre=True, always=True)
    def default_datetime(cls, v):
        return v or datetime.now(timezone.utc)

class BaseSchema(BaseModel):
    class Config:
        from_attributes = True # Replaces orm_mode = True in Pydantic v2
        populate_by_name = True # Allows using alias for field names (e.g. for MongoDB "_id")
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
        }

# --- User Schemas (for Auth Service) ---

class UserBase(BaseSchema):
    username: str = Field(..., min_length=3, max_length=100, description="Unique username")
    email: EmailStr = Field(..., description="Unique email address")
    full_name: Optional[str] = Field(None, max_length=255, description="User's full name")
    role: str = Field("user", description="User role, e.g., 'user', 'admin'")
    is_active: bool = True
    is_superuser: bool = False

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="User password")

class UserUpdate(BaseSchema):
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=255)
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8) # For password updates

class User(UserBase, TimestampMixin):
    id: int = Field(..., description="User ID")

    class Config:
        from_attributes = True

class UserInDB(User):
    hashed_password: str

# --- Token Schemas (for Auth Service) ---

class Token(BaseSchema):
    access_token: str
    token_type: str = "bearer"
    expires_in: int # Expiry duration in seconds
    refresh_token: Optional[str] = None
    refresh_token_jti: Optional[str] = None
    refresh_token_expires_in: Optional[int] = None # Expiry duration for refresh token in seconds

class TokenData(BaseSchema):
    username: Optional[str] = None
    user_id: Optional[int] = None
    scopes: List[str] = []
    jti: Optional[str] = None # JWT ID for access token
    refresh_jti: Optional[str] = None # JWT ID for refresh token, if applicable

class RefreshTokenCreate(BaseSchema):
    user_id: int
    jti: str
    expires_at: datetime

class RefreshTokenUpdate(BaseSchema):
    is_revoked: Optional[bool] = None

class RefreshToken(RefreshTokenCreate, TimestampMixin):
    id: int

    class Config:
        from_attributes = True

# --- Principle Schemas (for AC Service) ---

class PrincipleBase(BaseSchema):
    name: str = Field(..., min_length=3, max_length=255, description="Name of the AC principle")
    description: Optional[str] = Field(None, description="Detailed description of the principle")
    content: str = Field(..., description="Full content of the principle (e.g., YAML, JSON, or structured text)")
    version: int = Field(1, gt=0, description="Version number of the principle")
    status: str = Field("draft", description="Status of the principle (e.g., 'draft', 'approved', 'deprecated')")

class PrincipleCreate(PrincipleBase):
    created_by_user_id: Optional[int] = Field(None, description="ID of the user who created this principle")

class PrincipleUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    content: Optional[str] = None
    version: Optional[int] = Field(None, gt=0)
    status: Optional[str] = None # Consider enum for status

class Principle(PrincipleBase, TimestampMixin):
    id: int = Field(..., description="Principle ID")
    created_by_user_id: Optional[int] = Field(None, description="ID of the user who created this principle")

    class Config:
        from_attributes = True

# --- PolicyRule Schemas (for Integrity Service) ---

class PolicyRuleBase(BaseSchema):
    rule_name: Optional[str] = Field(None, max_length=255, description="Optional descriptive name for the rule")
    datalog_content: str = Field(..., description="Datalog rule content")
    version: int = Field(1, gt=0, description="Version of this rule entry")
    source_principle_ids: Optional[List[int]] = Field(None, description="IDs of AC principles informing this rule")
    status: str = Field("pending_synthesis", description="Status (e.g., 'pending_synthesis', 'active', 'deprecated')")
    verification_status: str = Field("pending", description="Verification status (e.g., 'pending', 'passed', 'failed', 'error')")
    verified_at: Optional[datetime] = Field(None, description="Timestamp of last verification attempt")
    verification_feedback: Optional[str] = Field(None, description="Feedback from the verification process")
    synthesized_by_gs_engine_id: Optional[str] = Field(None, description="ID of the GS engine that synthesized this rule")
    verified_by_fv_service_id: Optional[str] = Field(None, description="ID of the FV service that verified this rule")


class PolicyRuleCreate(PolicyRuleBase):
    pass # Inherits all fields from PolicyRuleBase

class PolicyRuleUpdate(BaseSchema):
    rule_name: Optional[str] = Field(None, max_length=255)
    datalog_content: Optional[str] = None
    version: Optional[int] = Field(None, gt=0)
    source_principle_ids: Optional[List[int]] = None
    status: Optional[str] = None
    verification_status: Optional[str] = None
    verified_at: Optional[datetime] = None
    verification_feedback: Optional[str] = None
    synthesized_by_gs_engine_id: Optional[str] = None
    verified_by_fv_service_id: Optional[str] = None

class PolicyRule(PolicyRuleBase, TimestampMixin):
    id: int = Field(..., description="Policy Rule ID")

    class Config:
        from_attributes = True

# --- AuditLog Schemas (for Integrity Service) ---

class AuditLogBase(BaseSchema):
    service_name: str = Field(..., max_length=100, description="Name of the service generating the log")
    event_type: str = Field(..., max_length=100, description="Type of event being logged")
    actor_id: Optional[str] = Field(None, max_length=255, description="Identifier for the actor (user, service, system)")
    entity_type: Optional[str] = Field(None, max_length=100, description="Type of entity affected (e.g., 'Principle', 'PolicyRule')")
    entity_id: Optional[str] = Field(None, max_length=255, description="ID of the entity affected")
    description: Optional[str] = Field(None, description="Human-readable description of the event")
    details: Optional[Dict[str, Any]] = Field(None, description="Structured details of the event")
    # For tamper evidence (conceptual, actual implementation is more complex)
    previous_hash: Optional[str] = Field(None, max_length=64)
    current_hash: Optional[str] = Field(None, max_length=64, unique=True) # Should be unique if used for chaining

class AuditLogCreate(AuditLogBase):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AuditLog(AuditLogBase):
    id: int = Field(..., description="Audit Log ID")
    timestamp: datetime # Already has a default in AuditLogCreate, will be populated by DB or on creation

    class Config:
        from_attributes = True

# --- PolicyTemplate Schemas (for GS Service) ---

class PolicyTemplateBase(BaseSchema):
    name: str = Field(..., min_length=3, max_length=255, unique=True, description="Unique name for the policy template")
    description: Optional[str] = Field(None, description="Description of the policy template")
    default_content: str = Field(..., description="Default template content (e.g., Datalog with placeholders)")
    parameters_schema: Optional[Dict[str, Any]] = Field(None, description="JSON schema defining customizable parameters")
    version: int = Field(1, gt=0, description="Version of the policy template")

class PolicyTemplateCreate(PolicyTemplateBase):
    created_by_user_id: Optional[int] = Field(None, description="ID of the user who created this template")

class PolicyTemplateUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    default_content: Optional[str] = None
    parameters_schema: Optional[Dict[str, Any]] = None
    version: Optional[int] = Field(None, gt=0)

class PolicyTemplate(PolicyTemplateBase, TimestampMixin):
    id: int = Field(..., description="Policy Template ID")
    created_by_user_id: Optional[int] = Field(None, description="ID of the user who created this template")

    class Config:
        from_attributes = True

# --- Policy Schemas (for GS Service, instantiated from templates or custom) ---

class PolicyBase(BaseSchema): # Renamed from GSPolicyBase to PolicyBase
    name: str = Field(..., max_length=255, description="Name of the instantiated/custom policy")
    description: Optional[str] = Field(None, description="Description of the policy")
    content: str = Field(..., description="Actual policy content (e.g., Datalog), possibly rendered from a template")
    status: str = Field("draft", description="Status (e.g., 'draft', 'active', 'deprecated')")
    version: int = Field(1, gt=0, description="Version of this policy instance")
    template_id: Optional[int] = Field(None, description="ID of the PolicyTemplate used, if any")
    customization_parameters: Optional[Dict[str, Any]] = Field(None, description="Parameters used for template customization")
    source_principle_ids: Optional[List[int]] = Field(None, description="IDs of AC principles informing this policy")

class PolicyCreate(PolicyBase): # Renamed from GSPolicyCreate to PolicyCreate
    created_by_user_id: Optional[int] = Field(None, description="ID of the user who created this policy")

class PolicyUpdate(BaseSchema): # Renamed from GSPolicyUpdate to PolicyUpdate
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None
    version: Optional[int] = Field(None, gt=0)
    customization_parameters: Optional[Dict[str, Any]] = None
    source_principle_ids: Optional[List[int]] = None

class Policy(PolicyBase, TimestampMixin): # Renamed from GSPolicy to Policy
    id: int = Field(..., description="Policy ID")
    created_by_user_id: Optional[int] = Field(None, description="ID of the user who created this policy")

    class Config:
        from_attributes = True


# --- General Purpose Schemas ---

class MessageResponse(BaseSchema):
    message: str

class ErrorDetail(BaseSchema):
    code: str # e.g., "VALIDATION_ERROR", "NOT_FOUND", "INTERNAL_SERVER_ERROR"
    message: str
    field: Optional[str] = None # For validation errors, indicates the problematic field

class ErrorResponse(BaseSchema):
    error: ErrorDetail

# --- Service Health Schemas ---
class ServiceStatus(BaseSchema):
    service_name: str
    status: str = Field("ok", description="Status of the service, e.g., 'ok', 'degraded', 'error'")
    version: Optional[str] = Field(None, description="Version of the running service")
    dependencies: Optional[List[Dict[str, str]]] = Field(None, description="Status of critical dependencies")

# --- Verification Service Specific Schemas ---

class VerificationRequest(BaseSchema):
    rule_id: Union[int, str] # ID of the PolicyRule to verify
    datalog_content: str # The actual Datalog code to be verified
    # Potentially add context, like other rules or facts, if verification needs them
    # context_datalog: Optional[str] = None

class VerificationResult(BaseSchema):
    rule_id: Union[int, str]
    is_consistent: bool
    is_compliant: Optional[bool] = None # If compliance against specific properties is checked
    feedback: Optional[str] = None # Detailed feedback, errors, or warnings
    verified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    engine_version: Optional[str] = None # Version of the verification engine used

# --- Synthesis Service Specific Schemas (Conceptual) ---

class SynthesisRequest(BaseSchema):
    principle_ids: List[Union[int, str]] # IDs of AC Principles to synthesize from
    target_description: Optional[str] = None # Description of desired policy properties
    # context_data: Optional[Dict[str, Any]] = None # Additional context for synthesis

class SynthesisResult(BaseSchema):
    synthesized_rules: List[PolicyRuleCreate] # List of datalog rules generated
    synthesis_report: Optional[str] = None # Report on the synthesis process
    engine_version: Optional[str] = None
