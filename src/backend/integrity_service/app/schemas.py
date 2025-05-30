from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime

# --- PolicyRule Schemas ---

class PolicyRuleBase(BaseModel):
    rule_content: str = Field(..., description="Datalog rule content")
    source_principle_ids: Optional[List[int]] = Field(None, description="List of AC principle IDs it's derived from")

    # Enhanced fields for audit findings
    framework: Optional[str] = Field("Datalog", max_length=50, description="Policy framework: Datalog, Rego, JSON, YAML")
    principle_text: Optional[str] = Field(None, description="Human-readable principle description")
    pgp_signature: Optional[str] = Field(None, description="PGP signature for integrity verification")
    source_file: Optional[str] = Field(None, max_length=500, description="Source file path for provenance")
    content_hash: Optional[str] = Field(None, max_length=128, description="SHA-256 hash of rule content")
    import_dependencies: Optional[List[str]] = Field(None, description="List of external modules/imports required")

class PolicyRuleCreate(PolicyRuleBase):
    # version will be defaulted in CRUD or model
    # verification_status will be defaulted
    pass

class PolicyRuleUpdate(BaseModel):
    rule_content: Optional[str] = None
    source_principle_ids: Optional[List[int]] = None
    verification_status: Optional[str] = Field(None, description="e.g., 'pending', 'verified', 'failed'")
    # version might be incremented automatically on content change in CRUD

class PolicyRule(PolicyRuleBase): # For API responses
    id: int
    version: int
    verification_status: str
    verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class PolicyRuleList(BaseModel):
    rules: List[PolicyRule]
    total: int

# --- AuditLog Schemas ---

class AuditLogBase(BaseModel):
    service_name: str = Field(..., description="Name of the service generating the log (e.g., 'ac_service')")
    action: str = Field(..., description="Action performed (e.g., 'CREATE_PRINCIPLE')")
    user_id: Optional[str] = Field(None, description="Identifier of the user performing the action")
    details: Optional[Dict[str, Any]] = Field(None, description="Event-specific data")

class AuditLogCreate(AuditLogBase):
    # timestamp will be defaulted in model or CRUD
    pass

class AuditLog(AuditLogBase): # For API responses
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True

class AuditLogList(BaseModel):
    logs: List[AuditLog]
    total: int

# --- Appeal and Dispute Resolution Schemas (Phase 3) ---

class AppealBase(BaseModel):
    decision_id: str = Field(..., description="ID of the decision being appealed")
    appeal_reason: str = Field(..., description="Reason for the appeal")
    evidence: Optional[str] = Field(None, description="Supporting evidence for the appeal")
    requested_remedy: str = Field(..., description="What remedy is being requested")
    appellant_contact: Optional[str] = Field(None, description="Contact information for the appellant")

class AppealCreate(AppealBase):
    pass

class AppealUpdate(BaseModel):
    status: Optional[str] = Field(None, description="Appeal status: pending, under_review, resolved, rejected")
    resolution: Optional[str] = Field(None, description="Resolution details")
    reviewer_notes: Optional[str] = Field(None, description="Notes from the reviewer")

class Appeal(AppealBase):
    id: int
    status: str = "pending"  # pending, under_review, resolved, rejected
    resolution: Optional[str] = None
    reviewer_notes: Optional[str] = None
    submitted_at: datetime
    resolved_at: Optional[datetime] = None
    assigned_reviewer_id: Optional[str] = None
    escalation_level: int = 1  # 1=ombudsperson, 2=technical, 3=council_subcommittee, 4=full_council

    class Config:
        orm_mode = True

class AppealList(BaseModel):
    appeals: List[Appeal]
    total: int

class DisputeResolutionBase(BaseModel):
    appeal_id: int = Field(..., description="ID of the appeal this dispute resolution is for")
    resolution_method: str = Field(..., description="Method of resolution: ombudsperson, technical_review, council_subcommittee, full_council")
    panel_composition: Optional[List[str]] = Field(None, description="Composition of the review panel")
    timeline_days: int = Field(default=30, description="Expected timeline for resolution in days")

class DisputeResolutionCreate(DisputeResolutionBase):
    pass

class DisputeResolutionUpdate(BaseModel):
    status: Optional[str] = Field(None, description="Resolution status: initiated, in_progress, completed, escalated")
    findings: Optional[str] = Field(None, description="Findings from the dispute resolution process")
    recommendations: Optional[List[str]] = Field(None, description="Recommendations from the panel")
    final_decision: Optional[str] = Field(None, description="Final decision on the dispute")

class DisputeResolution(DisputeResolutionBase):
    id: int
    status: str = "initiated"  # initiated, in_progress, completed, escalated
    findings: Optional[str] = None
    recommendations: Optional[List[str]] = None
    final_decision: Optional[str] = None
    initiated_at: datetime
    completed_at: Optional[datetime] = None
    panel_members: Optional[List[str]] = None

    class Config:
        orm_mode = True

class DisputeResolutionList(BaseModel):
    resolutions: List[DisputeResolution]
    total: int

class ExplainabilityRequest(BaseModel):
    decision_id: str = Field(..., description="ID of the decision to explain")
    explanation_level: str = Field(default="standard", description="Level of explanation: basic, standard, detailed")
    include_counterfactuals: bool = Field(default=False, description="Whether to include counterfactual examples")
    target_audience: str = Field(default="general", description="Target audience: general, technical, affected_individual")

class ExplainabilityResponse(BaseModel):
    decision_id: str
    explanation: str
    rule_provenance: List[Dict[str, Any]]
    counterfactual_examples: Optional[List[Dict[str, Any]]] = None
    confidence_score: float
    generated_at: datetime

class RuleProvenanceResponse(BaseModel):
    rule_id: str
    source_principles: List[Dict[str, Any]]
    creation_context: Dict[str, Any]
    modification_history: List[Dict[str, Any]]
    verification_history: List[Dict[str, Any]]
    usage_statistics: Dict[str, Any]

# Placeholder for user information, similar to other services if needed for auth context
class User(BaseModel):
    id: str # Assuming user ID is a string from JWT sub
    roles: List[str] = [] # e.g., ["integrity_admin", "auditor"]


# --- Phase 3: Cryptographic Integrity Schemas ---

class CryptoKeyBase(BaseModel):
    key_type: str = Field(..., description="Key type (RSA, ECDSA, Ed25519)")
    key_size: int = Field(..., description="Key size in bits")
    key_purpose: str = Field(..., description="Key purpose (signing, encryption, timestamping)")
    expires_at: Optional[datetime] = Field(None, description="Key expiration date")

class CryptoKeyCreate(CryptoKeyBase):
    pass

class CryptoKey(CryptoKeyBase):
    id: int
    key_id: str = Field(..., description="Unique key identifier")
    public_key_pem: str = Field(..., description="PEM-encoded public key")
    is_active: bool = Field(..., description="Whether key is active")
    created_at: datetime
    revoked_at: Optional[datetime] = None
    parent_key_id: Optional[str] = Field(None, description="Previous key in rotation chain")
    rotation_reason: Optional[str] = Field(None, description="Reason for key rotation")
    hsm_key_reference: Optional[str] = Field(None, description="HSM key reference")

    class Config:
        orm_mode = True

class CryptoKeyList(BaseModel):
    keys: List[CryptoKey]
    total: int

class SignatureRequest(BaseModel):
    data: str = Field(..., description="Data to sign")
    key_id: Optional[str] = Field(None, description="Specific key ID to use for signing")
    purpose: str = Field(default="signing", description="Key purpose")

class SignatureResponse(BaseModel):
    signature: str = Field(..., description="Base64-encoded digital signature")
    key_id: str = Field(..., description="Key ID used for signing")
    algorithm: str = Field(..., description="Signature algorithm used")
    signed_at: datetime = Field(..., description="Signature timestamp")

class SignatureVerification(BaseModel):
    data: str = Field(..., description="Original data")
    signature: str = Field(..., description="Base64-encoded signature to verify")
    key_id: str = Field(..., description="Key ID to use for verification")

class SignatureVerificationResult(BaseModel):
    is_valid: bool = Field(..., description="Whether signature is valid")
    key_id: str = Field(..., description="Key ID used for verification")
    verified_at: datetime = Field(..., description="Verification timestamp")

class MerkleTreeNode(BaseModel):
    node_hash: str = Field(..., description="SHA3-256 hash of the node")
    parent_hash: Optional[str] = Field(None, description="Parent node hash")
    left_child_hash: Optional[str] = None
    right_child_hash: Optional[str] = None
    level: int = Field(..., description="Tree level (0 = leaf)")
    batch_id: str = Field(..., description="Batch identifier")
    audit_log_ids: Optional[List[int]] = Field(None, description="Audit log IDs for leaf nodes")
    created_at: datetime

    class Config:
        orm_mode = True

class MerkleTreeBuild(BaseModel):
    data_hashes: List[str] = Field(..., description="List of SHA3-256 hashes to build tree from")
    batch_id: str = Field(..., description="Batch identifier")

class MerkleTreeResult(BaseModel):
    root_hash: str = Field(..., description="Merkle tree root hash")
    tree_levels: List[List[str]] = Field(..., description="Complete tree structure")
    leaf_count: int = Field(..., description="Number of leaf nodes")
    batch_id: str = Field(..., description="Batch identifier")

class MerkleProof(BaseModel):
    data_hash: str = Field(..., description="Hash to generate proof for")
    proof_elements: List[Dict[str, str]] = Field(..., description="Proof path elements")
    root_hash: str = Field(..., description="Expected root hash")

class MerkleProofVerification(BaseModel):
    data_hash: str = Field(..., description="Original data hash")
    proof_elements: List[Dict[str, str]] = Field(..., description="Merkle proof elements")
    root_hash: str = Field(..., description="Expected root hash")

class MerkleProofResult(BaseModel):
    is_valid: bool = Field(..., description="Whether proof is valid")
    data_hash: str = Field(..., description="Verified data hash")
    root_hash: str = Field(..., description="Root hash used for verification")

class TimestampRequest(BaseModel):
    data: str = Field(..., description="Data to timestamp")
    hash_algorithm: str = Field(default="SHA3-256", description="Hash algorithm to use")

class TimestampResponse(BaseModel):
    timestamp_token: str = Field(..., description="Base64-encoded RFC 3161 timestamp token")
    timestamp_value: datetime = Field(..., description="Extracted timestamp value")
    tsa_url: str = Field(..., description="Timestamp Authority URL")
    hash_algorithm: str = Field(..., description="Hash algorithm used")
    message_imprint: str = Field(..., description="Hex-encoded message hash")

class TimestampVerification(BaseModel):
    timestamp_token: str = Field(..., description="Base64-encoded timestamp token")
    original_data: str = Field(..., description="Original data that was timestamped")

class TimestampVerificationResult(BaseModel):
    is_valid: bool = Field(..., description="Whether timestamp is valid")
    timestamp_value: Optional[datetime] = Field(None, description="Extracted timestamp value")
    tsa_url: Optional[str] = Field(None, description="Timestamp Authority URL")

class IntegrityReport(BaseModel):
    """Comprehensive integrity report for audit logs or policy rules"""
    entity_type: str = Field(..., description="Type of entity (audit_log, policy_rule)")
    entity_id: int = Field(..., description="Entity ID")
    content_hash: str = Field(..., description="SHA3-256 hash of content")
    signature_verified: bool = Field(..., description="Digital signature verification status")
    timestamp_verified: bool = Field(..., description="Timestamp verification status")
    merkle_verified: bool = Field(..., description="Merkle proof verification status")
    chain_integrity: bool = Field(..., description="Chain integrity status (for audit logs)")
    overall_integrity: bool = Field(..., description="Overall integrity status")
    verification_details: Dict[str, Any] = Field(..., description="Detailed verification results")
    verified_at: datetime = Field(..., description="Verification timestamp")
