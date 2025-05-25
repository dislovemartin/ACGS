# ACGS/shared/models.py
from .database import Base
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func, JSON
)
from sqlalchemy.dialects.postgresql import JSONB, UUID # For PostgreSQL specific JSONB and UUID types
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid # For generating UUIDs

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    # Using UUID for a more globally unique ID, if desired, though integer ID is also fine.
    # id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False) # Increased length for stronger hashes
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    # Roles: e.g., "system_admin", "principle_author", "policy_auditor", "service_account", "user"
    role = Column(String(50), default="user", nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    # Relationships for created_by in other models
    created_principles = relationship("Principle", back_populates="created_by_user", foreign_keys="Principle.created_by_user_id")
    created_policy_templates = relationship("PolicyTemplate", back_populates="created_by_user", foreign_keys="PolicyTemplate.created_by_user_id")
    created_policies = relationship("Policy", back_populates="created_by_user", foreign_keys="Policy.created_by_user_id")
    audit_logs_as_actor = relationship("AuditLog", back_populates="actor", foreign_keys="AuditLog.actor_id")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    # Or if User.id is UUID:
    # user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    jti = Column(String(36), unique=True, index=True, nullable=False)  # JWT ID (standard UUID length)
    token = Column(String(512), nullable=False, index=True) # The actual refresh token string, if storing it directly (hashed recommended)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="refresh_tokens")


class Principle(Base):
    __tablename__ = "principles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=False)  # Actual constitutional text
    version = Column(Integer, default=1, nullable=False)
    # Status: e.g., "draft", "active", "archived", "under_review", "deprecated"
    status = Column(String(50), default="draft", nullable=False, index=True) 
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # Or if User.id is UUID:
    # created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_by_user = relationship("User", back_populates="created_principles")


class PolicyRule(Base):
    __tablename__ = "policy_rules" # Corresponds to Datalog rules in Integrity Service

    id = Column(Integer, primary_key=True, index=True)
    rule_name = Column(String(255), index=True, nullable=True) # Optional: a human-readable name for the rule, not necessarily unique
    datalog_content = Column(Text, nullable=False, unique=True) # Assuming datalog content should be unique for a given version
    version = Column(Integer, default=1, nullable=False)
    
    # Link to the overarching Policy object this rule belongs to/is derived from (if any)
    policy_id = Column(Integer, ForeignKey("policies.id"), nullable=True)
    policy = relationship("Policy", back_populates="rules")

    source_principle_ids = Column(JSONB, nullable=True) # e.g., [1, 2, 3] - IDs from Principle table
    
    # Status: "pending_synthesis", "synthesized", "pending_verification", "verified_passed", "verified_failed", "active", "inactive", "archived"
    status = Column(String(50), default="pending_synthesis", nullable=False, index=True)
    
    # Verification details
    verification_status = Column(String(50), default="not_verified", nullable=False, index=True) # "not_verified", "pending", "passed", "failed", "error"
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verification_feedback = Column(JSONB, nullable=True) # E.g., counter-example, report summary from FV service

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Optional: IDs from external systems if this rule was synthesized or verified by a specific run/job
    synthesized_by_gs_run_id = Column(String(100), nullable=True) 
    verified_by_fv_run_id = Column(String(100), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4) # Using UUID for audit logs
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    
    service_name = Column(String(100), nullable=False, index=True) # e.g., "auth_service", "gs_service"
    event_type = Column(String(100), nullable=False, index=True) # e.g., "USER_LOGIN", "POLICY_RULE_CREATED"
    
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True) # User performing action
    # Or if User.id is UUID:
    # actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    actor = relationship("User", back_populates="audit_logs_as_actor")
    
    # Entity being acted upon (optional and polymorphic)
    # Consider a more robust polymorphic relationship if many entity types need linking
    # Or keep it simple with string identifiers.
    entity_type = Column(String(100), nullable=True, index=True) # e.g., "Principle", "PolicyRule", "User"
    entity_id_int = Column(Integer, nullable=True, index=True) # If entity has integer PK
    entity_id_uuid = Column(UUID(as_uuid=True), nullable=True, index=True) # If entity has UUID PK
    entity_id_str = Column(String(255), nullable=True, index=True) # If entity has string PK or for general refs

    description = Column(Text, nullable=True) # Human-readable summary
    details = Column(JSONB, nullable=True) # Structured details of the event (e.g., changes made, request payload)
    
    # For tamper evidence (optional, can be complex to manage)
    # previous_hash = Column(String(64), nullable=True) # Hash of the previous log entry for this stream/entity
    # current_hash = Column(String(64), nullable=True, index=True, unique=True) # Hash of this log entry's content


class PolicyTemplate(Base):
    __tablename__ = "policy_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    # Template content (e.g., Datalog with placeholders like {{param_name}})
    template_content = Column(Text, nullable=False) 
    # JSON schema describing customizable parameters and their types/constraints
    parameters_schema = Column(JSONB, nullable=True) 
    version = Column(Integer, default=1, nullable=False)
    status = Column(String(50), default="draft", nullable=False, index=True) # "draft", "active", "deprecated"
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # Or if User.id is UUID:
    # created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_by_user = relationship("User", back_populates="created_policy_templates")

    # Policies instantiated from this template
    generated_policies = relationship("Policy", back_populates="template")


class Policy(Base): 
    __tablename__ = "policies" # A high-level policy object, potentially composed of multiple rules

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False, unique=True) # Policy name should be unique
    description = Column(Text, nullable=True)
    # Overall policy intent or summary, if not directly executable content like PolicyRule
    # This 'content' could be natural language, or a structured representation.
    # If this Policy directly translates to a single rule, its content might be similar to PolicyRule.datalog_content.
    # However, a Policy could also be a collection of PolicyRules.
    # For now, let's assume 'content' here is a textual description or high-level definition.
    # The actual enforceable rules are in PolicyRule.
    high_level_content = Column(Text, nullable=True) 
    version = Column(Integer, default=1, nullable=False)
    # Status: "draft", "active", "archived", "under_review", "deprecated"
    status = Column(String(50), default="draft", nullable=False, index=True) # Corrected from index=true
    
    template_id = Column(Integer, ForeignKey("policy_templates.id"), nullable=True)
    template = relationship("PolicyTemplate", back_populates="generated_policies")
    
    # Parameters used if this policy was instantiated from a template
    customization_parameters = Column(JSONB, nullable=True) 
    # Links to AC principles this policy is derived from or aims to uphold
    source_principle_ids = Column(JSONB, nullable=True) 
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # Or if User.id is UUID:
    # created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_by_user = relationship("User", back_populates="created_policies")
    
    # Relationship to the actual Datalog rules that implement this policy
    rules = relationship("PolicyRule", back_populates="policy", cascade="all, delete-orphan")

    # For version history (simplified: link to previous version)
    # previous_version_id = Column(Integer, ForeignKey("policies.id"), nullable=True)
    # For a full version history, a separate versioning table or pattern might be better.

# Example of how models might be related if a Policy is a collection of PolicyRules:
# In Policy model:
# rules = relationship("PolicyRule", back_populates="policy_group")
# In PolicyRule model:
# policy_group_id = Column(Integer, ForeignKey("policies.id"))
# policy_group = relationship("Policy", back_populates="rules")
# The current setup with policy_id in PolicyRule and rules in Policy achieves this.
