# ACGS/shared/models.py
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship, Mapped, mapped_column # For SQLAlchemy 2.0 style
from sqlalchemy.sql import func # For server-side default timestamps
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from .database import Base # Import Base from shared.database

# --- User Model (for Auth Service primarily) ---
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(50), default="user", nullable=False) # e.g., "user", "admin", "service_account"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False) # Specific for admin functionalities

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships (examples, adjust as needed)
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    # created_principles: Mapped[List["Principle"]] = relationship("Principle", back_populates="creator") # If tracking principle creator

    __table_args__ = (
        Index("ix_user_username", "username", unique=True),
        Index("ix_user_email", "email", unique=True),
    )

# --- RefreshToken Model (for Auth Service) ---
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    jti: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False) # JWT ID
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")


# --- Principle Model (for AC Service) ---
class Principle(Base):
    __tablename__ = "ac_principles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False) # Full content of the principle
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False) # e.g., 'draft', 'approved', 'deprecated'
    
    created_by_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    # created_by: Mapped[Optional["User"]] = relationship("User", back_populates="created_principles") # If User.created_principles is defined

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Link to PolicyRule (one Principle can inform many PolicyRules)
    # This relationship might be better represented implicitly or via a join table if many-to-many with PolicyRule is complex.
    # For now, assuming PolicyRule stores source_principle_ids as JSON or similar, or this is one-to-many.
    # informed_policy_rules: Mapped[List["PolicyRule"]] = relationship(secondary="policyrule_principle_link", back_populates="source_principles")

    # Link to Policy (one Principle can inform many GSPolicies)
    # informed_gs_policies: Mapped[List["Policy"]] = relationship(secondary="gspolicy_principle_link", back_populates="source_principles")


# --- PolicyRule Model (for Integrity Service) ---
class PolicyRule(Base):
    __tablename__ = "policy_rules" # Datalog rules

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    rule_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    datalog_content: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False) # Internal version of this rule entry
    
    # Store source AC principle IDs as a JSON array of integers.
    # This avoids complex join tables if the relationship is primarily for reference.
    source_principle_ids: Mapped[Optional[List[int]]] = mapped_column(JSON, nullable=True)
    
    status: Mapped[str] = mapped_column(String(50), default="pending_synthesis", nullable=False) # e.g., 'pending_synthesis', 'active', 'deprecated'
    verification_status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False) # e.g., 'pending', 'passed', 'failed', 'error'
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    verification_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Optional: Track which service/engine synthesized or verified this rule
    synthesized_by_gs_engine_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    verified_by_fv_service_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_policy_rule_name", "rule_name"),
        Index("ix_policy_rule_status", "status"),
        Index("ix_policy_rule_verification_status", "verification_status"),
    )

# --- AuditLog Model (for Integrity Service) ---
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    service_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    actor_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # Can be user ID, service name, system process
    entity_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True) # e.g., "Principle", "PolicyRule", "User"
    entity_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # ID of the entity being acted upon
    
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True) # Structured event details

    # For tamper evidence (mock for now, real implementation needs careful design)
    previous_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True) # SHA-256 hash
    current_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, unique=True) # SHA-256 hash

    __table_args__ = (
        Index("ix_audit_log_timestamp", "timestamp"),
    )


# --- PolicyTemplate Model (for GS Service) ---
class PolicyTemplate(Base):
    __tablename__ = "gs_policy_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    default_content: Mapped[str] = mapped_column(Text, nullable=False) # Template string
    parameters_schema: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True) # JSON schema for parameters
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    created_by_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    # created_by: Mapped[Optional["User"]] = relationship("User") # If tracking creator

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship: One template can be used by many Policies
    policies: Mapped[List["Policy"]] = relationship("Policy", back_populates="template")


# --- Policy Model (Instantiated policies, for GS Service) ---
class Policy(Base): # Renamed from GSPolicy to Policy to match shared.schemas.Policy
    __tablename__ = "gs_policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False) # Name of the policy instance
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Content is the rendered policy (e.g., Datalog) after applying parameters to a template, or direct content.
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False) # e.g., 'draft', 'active', 'deprecated'
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    template_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("gs_policy_templates.id"), nullable=True)
    template: Mapped[Optional["PolicyTemplate"]] = relationship("PolicyTemplate", back_populates="policies")
    
    customization_parameters: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True) # Parameters used for template customization
    
    # Link to AC principles informing this policy
    source_principle_ids: Mapped[Optional[List[int]]] = mapped_column(JSON, nullable=True)

    created_by_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    # created_by: Mapped[Optional["User"]] = relationship("User") # If tracking creator

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('name', 'version', name='uq_policy_name_version'), # Ensure name/version combo is unique
    )

# Note on Relationships and ForeignKeys:
# - Ensure ForeignKey constraints point to the correct table and column names.
# - `Mapped` and `mapped_column` are part of SQLAlchemy 2.0 style.
# - `server_default=func.now()` and `onupdate=func.now()` handle timestamps automatically at the DB level.
# - JSON type for fields like `source_principle_ids` and `parameters_schema` assumes PostgreSQL JSONB or similar.
