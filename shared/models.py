from .database import Base  # Corrected import
from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func, JSON)
from sqlalchemy.dialects.postgresql import JSONB  # Import JSONB
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    # Roles: ac_admin, governance_auditor, ai_engineer, system_operator
    role = Column(String, default="user", nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    refresh_tokens = relationship("RefreshToken", back_populates="user")


class Principle(Base):
    __tablename__ = "principles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    content = Column(Text, nullable=False)  # Actual constitutional text
    status = Column(String, default="draft", nullable=False)  # e.g., draft, approved
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by_user_id = Column(Integer, ForeignKey("users.id"))
    created_by = relationship("User")


class PolicyRule(Base):
    __tablename__ = "policy_rules"

    id = Column(Integer, primary_key=True, index=True)
    # principle_id = Column(Integer, ForeignKey("principles.id")) # Removed single principle FK
    # principle = relationship("Principle") # Removed single principle relationship
    source_principle_ids = Column(JSON, nullable=True)  # Stores a list of principle IDs, e.g., [1, 2, 3]
    rule_name = Column(String, unique=True, index=True, nullable=False)
    datalog_content = Column(Text, nullable=False)  # The Datalog rule itself
    version = Column(Integer, default=1, nullable=False)
    # Status: synthesized, verified, rejected, deployed
    status = Column(String, default="synthesized", nullable=False)
    # Verification: pending, passed, failed
    verification_status = Column(String, default="pending", nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    synthesized_by_gs_engine_id = Column(String)  # ID of GS engine
    verified_by_fv_service_id = Column(String)  # ID of FV service


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    # Event: rule_issued, rule_evaluated, enforcement_action
    event_type = Column(String, nullable=False)
    # Entity: principle, policy_rule, user, ai_system
    entity_type = Column(String, nullable=False)
    entity_id = Column(Integer)
    description = Column(Text)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # User ID
    actor = relationship("User") # type: ignore
    metadata_json = Column(JSONB)  # Changed to JSONB. Additional JSON metadata
    # Cryptographic anchoring
    previous_hash = Column(String, nullable=True)  # Hash of previous log
    current_hash = Column(String, nullable=False)  # Hash of this log 


class PolicyTemplate(Base):
    __tablename__ = "policy_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    default_content = Column(Text, nullable=False)
    # For parameters, using Text to store JSON string for flexibility initially
    parameters_schema = Column(JSONB, nullable=True)  # Changed to JSONB. Describes the schema of parameters
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by = relationship("User", foreign_keys=[created_by_user_id]) # type: ignore
    # Add other relationships if needed, e.g., policies linked to this template
    policies = relationship("Policy", back_populates="template") # type: ignore


class Policy(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=False)  # The actual policy text
    version = Column(Integer, default=1, nullable=False)  # For basic versioning
    # Status examples: draft, active, archived, under_review
    status = Column(String, default="draft", nullable=False, index=True)
    template_id = Column(Integer, ForeignKey("policy_templates.id"), nullable=True)
    template = relationship("PolicyTemplate", back_populates="policies") # type: ignore
    # For customizationParameters, using Text to store JSON string
    customization_parameters = Column(JSONB, nullable=True) # Changed to JSONB
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by = relationship("User", foreign_keys=[created_by_user_id]) # type: ignore
    # If a policy can be a new version of another policy
    previous_version_id = Column(Integer, ForeignKey("policies.id"), nullable=True)
    # next_versions = relationship("Policy", backref=backref('parent_version', remote_side=[id]))


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    jti = Column(String, unique=True, index=True, nullable=False)  # JWT ID
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="refresh_tokens") # type: ignore