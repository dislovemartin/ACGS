from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

# --- Schemas for FV Service's own API ---

class PolicyRuleRef(BaseModel):
    id: int # ID of the policy rule in Integrity Service
    # content: Optional[str] = None # Optionally pass content if already fetched

class ACPrincipleRef(BaseModel):
    id: int # ID of the AC principle
    # content: Optional[str] = None # Optionally pass content if already fetched for context

class VerificationRequest(BaseModel):
    policy_rule_refs: List[PolicyRuleRef] = Field(..., description="References to policy rules to be verified.")
    # Optionally, principles can be referenced directly if verification is triggered per principle
    ac_principle_refs: Optional[List[ACPrincipleRef]] = Field(None, description="References to AC principles to derive proof obligations from. If not provided, obligations might be derived from principles linked to the policy rules.")

class VerificationResult(BaseModel):
    policy_rule_id: int
    status: str # e.g., "verified", "failed", "error"
    message: Optional[str] = None
    counter_example: Optional[str] = None # If applicable and found by SMT solver

class VerificationResponse(BaseModel):
    results: List[VerificationResult]
    overall_status: str # e.g., "all_verified", "some_failed", "error"
    summary_message: Optional[str] = None

# --- Schemas for internal logic and SMT interaction ---

class ProofObligation(BaseModel):
    principle_id: int
    obligation_content: str # e.g., a formal representation of the principle's intent
    description: Optional[str] = None

class SMTSolverInput(BaseModel):
    datalog_rules: List[str] # List of Datalog rule strings
    proof_obligations: List[str] # List of proof obligation strings (formalized)

class SMTSolverOutput(BaseModel):
    is_satisfiable: bool # True if rules + NOT(obligation) is satisfiable (meaning obligation NOT entailed)
    is_unsatisfiable: bool # True if rules + NOT(obligation) is unsatisfiable (meaning obligation IS entailed)
    # In a real SMT solver, satisfiability refers to whether a model exists for the given assertions.
    # For verifying if Rules => Obligation, we check if Rules AND (NOT Obligation) is UNSATISFIABLE.
    # If UNSAT, then Obligation is entailed by Rules.
    counter_example: Optional[str] = None # If satisfiable, a model might be a counter-example to the obligation
    error_message: Optional[str] = None

# --- Schemas for interacting with external services ---

# For AC Service (ac_service)
class ACPrinciple(BaseModel): # Simplified version of AC's Principle schema
    id: int
    name: str
    content: str
    description: Optional[str] = None

# For Integrity Service (integrity_service)
class PolicyRule(BaseModel): # Matches Integrity Service's PolicyRule response
    id: int
    rule_content: str
    source_principle_ids: Optional[List[int]] = []
    version: int
    verification_status: str

class PolicyRuleStatusUpdate(BaseModel): # For updating status in Integrity Service
    verification_status: str # "verified", "failed", "pending"
    # verified_at: Optional[datetime] # Integrity service might set this automatically

# --- Phase 3: Algorithmic Fairness Schemas ---

class BiasMetric(BaseModel):
    """Bias detection metric configuration."""
    metric_id: str
    metric_type: str  # "statistical", "counterfactual", "embedding", "llm_review"
    metric_name: str
    description: str
    threshold: Optional[float] = None
    parameters: Optional[Dict[str, Any]] = None

class FairnessProperty(BaseModel):
    """Fairness property definition."""
    property_id: str
    property_type: str  # "demographic_parity", "equalized_odds", "calibration", "individual_fairness"
    property_name: str
    description: str
    protected_attributes: List[str]
    threshold: float = 0.1
    criticality_level: str = "medium"  # "low", "medium", "high", "critical"

class BiasDetectionRequest(BaseModel):
    """Request for bias detection analysis."""
    policy_rule_ids: List[int]
    bias_metrics: List[BiasMetric]
    fairness_properties: List[FairnessProperty]
    dataset: Optional[List[Dict[str, Any]]] = None
    protected_attributes: List[str]
    analysis_type: str = "comprehensive"  # "basic", "comprehensive", "expert_review"

class BiasDetectionResult(BaseModel):
    """Result of bias detection for a single metric."""
    metric_id: str
    policy_rule_id: int
    bias_detected: bool
    bias_score: Optional[float] = None
    confidence: float
    explanation: str
    recommendations: Optional[List[str]] = None
    requires_human_review: bool = False

class BiasDetectionResponse(BaseModel):
    """Response from bias detection analysis."""
    policy_rule_ids: List[int]
    results: List[BiasDetectionResult]
    overall_bias_score: float
    risk_level: str  # "low", "medium", "high", "critical"
    summary: str
    recommendations: List[str]
    human_review_required: bool

class FairnessValidationRequest(BaseModel):
    """Request for fairness validation."""
    policy_rule_ids: List[int]
    fairness_properties: List[FairnessProperty]
    validation_dataset: Optional[List[Dict[str, Any]]] = None
    simulation_parameters: Optional[Dict[str, Any]] = None

class FairnessValidationResult(BaseModel):
    """Result of fairness validation."""
    property_id: str
    policy_rule_id: int
    fairness_satisfied: bool
    fairness_score: float
    violation_details: Optional[str] = None
    counterfactual_examples: Optional[List[Dict[str, Any]]] = None

class FairnessValidationResponse(BaseModel):
    """Response from fairness validation."""
    policy_rule_ids: List[int]
    results: List[FairnessValidationResult]
    overall_fairness_score: float
    compliance_status: str  # "compliant", "non_compliant", "requires_review"
    summary: str


# --- Enhanced Schemas for Tiered Validation Pipeline (Phase 3) ---

class ValidationTier(str, Enum):
    """Validation tiers for formal verification."""
    AUTOMATED = "automated"
    HITL = "human_in_the_loop"
    RIGOROUS = "rigorous"

class ValidationLevel(str, Enum):
    """Validation levels within each tier."""
    BASELINE = "baseline"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"
    CRITICAL = "critical"

class SafetyProperty(BaseModel):
    """Safety property for formal verification."""
    property_id: str
    property_type: str  # "safety", "liveness", "security", "fairness"
    property_description: str
    formal_specification: str
    criticality_level: str  # "low", "medium", "high", "critical"

class TieredVerificationRequest(BaseModel):
    """Request for tiered formal verification."""
    policy_rule_refs: List[PolicyRuleRef]
    validation_tier: ValidationTier
    validation_level: ValidationLevel = ValidationLevel.STANDARD
    safety_properties: Optional[List[SafetyProperty]] = None
    timeout_seconds: Optional[int] = 300
    require_proof: bool = False
    human_reviewer_id: Optional[str] = None  # For HITL validation

class TieredVerificationResult(BaseModel):
    """Result from tiered formal verification."""
    policy_rule_id: int
    validation_tier: ValidationTier
    validation_level: ValidationLevel
    status: str  # "verified", "failed", "inconclusive", "timeout"
    confidence_score: float  # 0.0 to 1.0
    verification_method: str
    proof_trace: Optional[str] = None
    counter_example: Optional[str] = None
    safety_violations: Optional[List[str]] = None
    human_review_notes: Optional[str] = None
    verification_time_ms: Optional[int] = None

class TieredVerificationResponse(BaseModel):
    """Response from tiered formal verification."""
    results: List[TieredVerificationResult]
    overall_status: str
    overall_confidence: float
    summary_message: Optional[str] = None
    escalation_required: bool = False
    next_tier_recommendation: Optional[ValidationTier] = None

# --- Schemas for Safety and Conflict Checking ---

class ConflictType(str, Enum):
    """Types of conflicts that can be detected."""
    LOGICAL_CONTRADICTION = "logical_contradiction"
    PRACTICAL_INCOMPATIBILITY = "practical_incompatibility"
    PRIORITY_CONFLICT = "priority_conflict"
    RESOURCE_CONFLICT = "resource_conflict"

class ConflictCheckRequest(BaseModel):
    """Request for conflict detection between rules."""
    rule_sets: List[str]  # Names or IDs of rule sets to check
    conflict_types: List[ConflictType]
    resolution_strategy: Optional[str] = "principle_priority_based"
    include_suggestions: bool = True

class ConflictDetectionResult(BaseModel):
    """Result of conflict detection."""
    conflict_id: str
    conflict_type: ConflictType
    conflicting_rules: List[int]  # Rule IDs
    conflict_description: str
    severity: str  # "low", "medium", "high", "critical"
    resolution_suggestion: Optional[str] = None
    affected_principles: Optional[List[int]] = None

class ConflictCheckResponse(BaseModel):
    """Response from conflict checking."""
    conflicts: List[ConflictDetectionResult]
    total_conflicts: int
    critical_conflicts: int
    resolution_required: bool
    summary: str

class SafetyCheckRequest(BaseModel):
    """Request for safety property validation."""
    system_model: str
    safety_properties: List[SafetyProperty]
    verification_method: str = "bounded_model_checking"
    depth_limit: Optional[int] = 100
    time_limit_seconds: Optional[int] = 600

class SafetyCheckResult(BaseModel):
    """Result of safety property checking."""
    property_id: str
    status: str  # "satisfied", "violated", "unknown"
    witness_trace: Optional[str] = None
    counter_example_trace: Optional[str] = None
    verification_depth: Optional[int] = None
    verification_time_ms: Optional[int] = None

class SafetyCheckResponse(BaseModel):
    """Response from safety property checking."""
    results: List[SafetyCheckResult]
    overall_safety_status: str
    critical_violations: List[str]
    summary: str

# Placeholder for User (if FV Service needs to be auth-aware for its own endpoints)
class User(BaseModel):
    id: str
    roles: List[str] = []


# --- Enhanced Multi-Model Validation Schemas ---

class ValidationResult(BaseModel):
    """Result of a validation operation."""
    rule_id: int
    principle_id: int
    validation_type: str
    is_valid: bool
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    error_details: Optional[str] = None
    suggestions: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class ValidationContext(BaseModel):
    """Context for multi-model validation."""
    request_id: str
    models: Dict[str, List[Dict[str, Any]]]
    validation_rules: Optional[List[str]] = None
    performance_budget: Optional[Dict[str, float]] = None

class MultiModelValidationResult(BaseModel):
    """Result of multi-model validation."""
    request_id: str
    overall_valid: bool
    validation_results: List[ValidationResult]
    performance_metrics: Dict[str, float]
    recommendations: List[str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ConflictCheckResult(BaseModel):
    """Result of conflict checking between models."""
    has_conflicts: bool
    conflict_details: List[str]
    severity: str = Field(..., pattern="^(low|medium|high|critical)$")
    resolution_suggestions: List[str]
    affected_principles: List[int]


# --- Task 13: Cross-Domain Principle Testing Framework Schemas ---

class DomainContextBase(BaseModel):
    """Base schema for domain context."""
    domain_name: str = Field(..., max_length=100, description="Domain name (e.g., healthcare, finance)")
    domain_description: Optional[str] = Field(None, description="Description of the domain")
    regulatory_frameworks: Optional[List[str]] = Field(None, description="Applicable regulatory frameworks")
    compliance_requirements: Optional[Dict[str, Any]] = Field(None, description="Specific compliance requirements")
    cultural_contexts: Optional[Dict[str, Any]] = Field(None, description="Cultural and social context factors")
    domain_constraints: Optional[Dict[str, Any]] = Field(None, description="Technical and operational constraints")
    risk_factors: Optional[List[str]] = Field(None, description="Domain-specific risk factors")
    stakeholder_groups: Optional[List[str]] = Field(None, description="Relevant stakeholder groups")

class DomainContextCreate(DomainContextBase):
    """Schema for creating domain context."""
    pass

class DomainContextUpdate(BaseModel):
    """Schema for updating domain context."""
    domain_description: Optional[str] = None
    regulatory_frameworks: Optional[List[str]] = None
    compliance_requirements: Optional[Dict[str, Any]] = None
    cultural_contexts: Optional[Dict[str, Any]] = None
    domain_constraints: Optional[Dict[str, Any]] = None
    risk_factors: Optional[List[str]] = None
    stakeholder_groups: Optional[List[str]] = None
    is_active: Optional[bool] = None

class DomainContext(DomainContextBase):
    """Schema for domain context response."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by_user_id: Optional[int] = None

    class Config:
        from_attributes = True

class CrossDomainTestScenarioBase(BaseModel):
    """Base schema for cross-domain test scenario."""
    scenario_name: str = Field(..., max_length=255, description="Name of the test scenario")
    scenario_description: Optional[str] = Field(None, description="Description of the test scenario")
    primary_domain_id: int = Field(..., description="Primary domain ID for testing")
    secondary_domains: Optional[List[int]] = Field(None, description="Secondary domain IDs")
    test_type: str = Field(..., description="Type of test (consistency, adaptation, conflict_detection)")
    test_parameters: Optional[Dict[str, Any]] = Field(None, description="Configurable test parameters")
    expected_outcomes: Optional[Dict[str, Any]] = Field(None, description="Expected test results")
    principle_ids: List[int] = Field(..., description="List of principle IDs to test")
    principle_adaptations: Optional[Dict[str, Any]] = Field(None, description="Domain-specific adaptations")

class CrossDomainTestScenarioCreate(CrossDomainTestScenarioBase):
    """Schema for creating cross-domain test scenario."""
    pass

class CrossDomainTestScenarioUpdate(BaseModel):
    """Schema for updating cross-domain test scenario."""
    scenario_description: Optional[str] = None
    secondary_domains: Optional[List[int]] = None
    test_parameters: Optional[Dict[str, Any]] = None
    expected_outcomes: Optional[Dict[str, Any]] = None
    principle_adaptations: Optional[Dict[str, Any]] = None
    status: Optional[str] = None

class CrossDomainTestScenario(CrossDomainTestScenarioBase):
    """Schema for cross-domain test scenario response."""
    id: int
    status: str
    last_run_at: Optional[datetime] = None
    accuracy_score: Optional[float] = None
    consistency_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    created_by_user_id: Optional[int] = None

    class Config:
        from_attributes = True

class CrossDomainTestResultBase(BaseModel):
    """Base schema for cross-domain test result."""
    scenario_id: int = Field(..., description="Test scenario ID")
    test_run_id: str = Field(..., description="Unique test run identifier")
    domain_id: int = Field(..., description="Domain ID being tested")
    principle_id: int = Field(..., description="Principle ID being tested")
    test_type: str = Field(..., description="Type of test performed")
    is_consistent: bool = Field(..., description="Whether the principle is consistent across domains")
    consistency_score: float = Field(..., ge=0.0, le=1.0, description="Consistency score (0.0 to 1.0)")
    adaptation_required: bool = Field(..., description="Whether adaptation is required")
    adaptation_suggestions: Optional[List[str]] = Field(None, description="Suggested adaptations")
    validation_details: Optional[Dict[str, Any]] = Field(None, description="Detailed validation results")
    conflict_detected: bool = Field(False, description="Whether conflicts were detected")
    conflict_details: Optional[Dict[str, Any]] = Field(None, description="Details of conflicts found")
    execution_time_ms: Optional[int] = Field(None, description="Execution time in milliseconds")
    memory_usage_mb: Optional[float] = Field(None, description="Memory usage in MB")

class CrossDomainTestResult(CrossDomainTestResultBase):
    """Schema for cross-domain test result response."""
    id: int
    executed_at: datetime
    executed_by_user_id: Optional[int] = None

    class Config:
        from_attributes = True

class CrossDomainTestRequest(BaseModel):
    """Schema for requesting cross-domain testing."""
    scenario_ids: List[int] = Field(..., description="List of scenario IDs to execute")
    target_accuracy: float = Field(0.9, ge=0.0, le=1.0, description="Target accuracy threshold")
    enable_parallel: bool = Field(True, description="Enable parallel execution")
    max_execution_time_seconds: int = Field(300, description="Maximum execution time per scenario")

class CrossDomainTestResponse(BaseModel):
    """Schema for cross-domain testing response."""
    test_run_id: str = Field(..., description="Unique test run identifier")
    scenarios_executed: int = Field(..., description="Number of scenarios executed")
    overall_accuracy: float = Field(..., description="Overall accuracy across all tests")
    overall_consistency: float = Field(..., description="Overall consistency score")
    results: List[CrossDomainTestResult] = Field(..., description="Detailed test results")
    execution_summary: Dict[str, Any] = Field(..., description="Execution summary and metrics")
    recommendations: List[str] = Field(..., description="Recommendations based on results")
