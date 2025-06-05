from sqlalchemy import Column, Integer, String, Text, DateTime, func, JSON, Index, LargeBinary, Boolean
from sqlalchemy.dialects.postgresql import ARRAY # For PostgreSQL specific ARRAY type
from sqlalchemy.orm import declarative_base
from datetime import datetime

# Create a local Base for this service to avoid import issues
Base = declarative_base()

# Define local models for integrity service to avoid shared module import issues
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

class PolicyRule(Base):
    """Policy Rule model for integrity service"""
    __tablename__ = "policy_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_content = Column(Text, nullable=False)
    source_principle_ids = Column(JSONB, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    verification_status = Column(String(50), default="pending", nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Cryptographic integrity fields
    content_hash = Column(String(64), nullable=True, index=True)
    pgp_signature = Column(Text, nullable=True)
    signed_at = Column(DateTime, nullable=True)
    signed_by_key_id = Column(String(100), nullable=True)

class AuditLog(Base):
    """Audit Log model for integrity service"""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    service_name = Column(String(100), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)
    user_id = Column(String(255), nullable=True)
    details = Column(JSONB, nullable=True)

    # Cryptographic integrity fields
    content_hash = Column(String(64), nullable=True, index=True)
    pgp_signature = Column(Text, nullable=True)
    signed_at = Column(DateTime, nullable=True)
    signed_by_key_id = Column(String(100), nullable=True)

class Appeal(Base):
    """Appeal model for integrity service"""
    __tablename__ = "appeals"

    id = Column(Integer, primary_key=True, index=True)
    decision_id = Column(String, nullable=False, index=True)
    appeal_reason = Column(Text, nullable=False)
    evidence = Column(Text, nullable=True)
    requested_remedy = Column(Text, nullable=False)
    appellant_contact = Column(String, nullable=True)
    status = Column(String, default="pending", nullable=False, index=True)
    resolution = Column(Text, nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    resolved_at = Column(DateTime, nullable=True)
    assigned_reviewer_id = Column(String, nullable=True, index=True)
    escalation_level = Column(Integer, default=1, nullable=False, index=True)

class DisputeResolution(Base):
    """Dispute Resolution model for integrity service"""
    __tablename__ = "dispute_resolutions"

    id = Column(Integer, primary_key=True, index=True)
    appeal_id = Column(Integer, nullable=False, index=True)
    resolution_method = Column(String, nullable=False, index=True)
    panel_composition = Column(JSONB, nullable=True)
    timeline_days = Column(Integer, default=30, nullable=False)
    status = Column(String, default="initiated", nullable=False, index=True)
    findings = Column(Text, nullable=True)
    recommendations = Column(JSONB, nullable=True)
    final_decision = Column(Text, nullable=True)
    initiated_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    panel_members = Column(JSONB, nullable=True)


# --- Phase 3: Cryptographic Integrity Models ---

class CryptoKey(Base):
    """Cryptographic Key Management for digital signatures and encryption"""
    __tablename__ = "crypto_keys"

    id = Column(Integer, primary_key=True, index=True)
    key_id = Column(String(64), unique=True, nullable=False, index=True) # Unique key identifier (SHA256 of public key)
    key_type = Column(String(20), nullable=False, index=True) # "RSA", "ECDSA", "Ed25519"
    key_size = Column(Integer, nullable=False) # Key size in bits
    public_key_pem = Column(Text, nullable=False) # PEM-encoded public key
    private_key_encrypted = Column(LargeBinary, nullable=True) # Encrypted private key (for storage)
    key_purpose = Column(String(50), nullable=False, index=True) # "signing", "encryption", "timestamping"
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True) # Key expiration date
    revoked_at = Column(DateTime, nullable=True) # Key revocation date
    hsm_key_reference = Column(String(255), nullable=True) # HSM key reference if using HSM

    # Key rotation and lifecycle
    parent_key_id = Column(String(64), nullable=True, index=True) # Previous key in rotation chain
    rotation_reason = Column(String(100), nullable=True) # Reason for key rotation

    def __repr__(self):
        return f"<CryptoKey(key_id='{self.key_id}', type='{self.key_type}', purpose='{self.key_purpose}')>"


class MerkleTreeNode(Base):
    """Merkle Tree Nodes for batch verification of audit logs"""
    __tablename__ = "merkle_tree_nodes"

    id = Column(Integer, primary_key=True, index=True)
    node_hash = Column(String(64), nullable=False, index=True) # SHA3-256 hash of the node
    parent_hash = Column(String(64), nullable=True, index=True) # Parent node hash
    left_child_hash = Column(String(64), nullable=True) # Left child hash
    right_child_hash = Column(String(64), nullable=True) # Right child hash
    level = Column(Integer, nullable=False, index=True) # Tree level (0 = leaf, higher = internal nodes)
    batch_id = Column(String(64), nullable=False, index=True) # Batch identifier
    audit_log_ids = Column(JSON, nullable=True) # List of audit log IDs for leaf nodes
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<MerkleTreeNode(hash='{self.node_hash[:16]}...', level={self.level}, batch='{self.batch_id}')>"


class TimestampToken(Base):
    """RFC 3161 Timestamp Tokens for trusted timestamping"""
    __tablename__ = "timestamp_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True) # SHA3-256 hash of the token
    timestamp_token = Column(LargeBinary, nullable=False) # RFC 3161 timestamp token (ASN.1 DER encoded)
    tsa_url = Column(String(255), nullable=False) # Timestamp Authority URL
    timestamp_value = Column(DateTime, nullable=False, index=True) # Extracted timestamp value
    policy_oid = Column(String(100), nullable=True) # TSA policy OID
    hash_algorithm = Column(String(50), nullable=False) # Hash algorithm used (e.g., "SHA3-256")
    message_imprint = Column(LargeBinary, nullable=False) # Original message hash
    serial_number = Column(String(100), nullable=True) # TSA serial number
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<TimestampToken(hash='{self.token_hash[:16]}...', tsa='{self.tsa_url}', time='{self.timestamp_value}')>"


# --- Phase 3: Appeal and Dispute Resolution Models ---
# Note: Appeal and DisputeResolution models are imported from shared.models to avoid table conflicts
# Note: Indexes for these models are defined in shared.models

# Indexes for cryptographic integrity models
Index('ix_crypto_key_purpose_active', CryptoKey.key_purpose, CryptoKey.is_active)
Index('ix_crypto_key_type_created', CryptoKey.key_type, CryptoKey.created_at)
Index('ix_merkle_node_batch_level', MerkleTreeNode.batch_id, MerkleTreeNode.level)
Index('ix_timestamp_token_tsa_time', TimestampToken.tsa_url, TimestampToken.timestamp_value)
# Note: Indexes for AuditLog and PolicyRule cryptographic fields are created via Alembic migrations
