"""
Structured Output Models for GS Engine Multi-Model Enhancement

This module defines Pydantic models for structured output validation,
constitutional compliance validation, and Rego policy generation.

Task 18.3: Structured Output Validation
- Pydantic models for Rego policy generation
- Constitutional compliance validation with fidelity scoring
- Structured output parsers for each model type
- Target constitutional fidelity score >0.85
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
import re


class PolicyType(str, Enum):
    """Types of policies that can be generated."""
    REGO = "rego"
    JSON = "json"
    YAML = "yaml"
    NATURAL_LANGUAGE = "natural_language"


class ConstitutionalComplianceLevel(str, Enum):
    """Levels of constitutional compliance."""
    FULLY_COMPLIANT = "fully_compliant"      # Score >= 0.95
    MOSTLY_COMPLIANT = "mostly_compliant"    # Score >= 0.85
    PARTIALLY_COMPLIANT = "partially_compliant"  # Score >= 0.70
    NON_COMPLIANT = "non_compliant"          # Score < 0.70


class ViolationType(str, Enum):
    """Types of constitutional violations."""
    PRINCIPLE_VIOLATION = "principle_violation"
    LOGICAL_INCONSISTENCY = "logical_inconsistency"
    SCOPE_VIOLATION = "scope_violation"
    FAIRNESS_VIOLATION = "fairness_violation"
    BIAS_DETECTED = "bias_detected"


class ConstitutionalViolation(BaseModel):
    """Represents a constitutional violation detected in policy."""
    violation_type: ViolationType
    severity: float = Field(..., ge=0.0, le=1.0, description="Violation severity (0-1)")
    description: str
    affected_principle_ids: List[int] = Field(default_factory=list)
    suggested_fix: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence (0-1)")


class ConstitutionalFidelityScore(BaseModel):
    """Constitutional fidelity scoring for policy validation."""
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Overall fidelity score (0-1)")
    principle_coverage_score: float = Field(..., ge=0.0, le=1.0)
    logical_consistency_score: float = Field(..., ge=0.0, le=1.0)
    fairness_score: float = Field(..., ge=0.0, le=1.0)
    bias_mitigation_score: float = Field(..., ge=0.0, le=1.0)
    
    compliance_level: ConstitutionalComplianceLevel
    violations: List[ConstitutionalViolation] = Field(default_factory=list)
    
    # Metadata
    evaluation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    evaluator_model: str
    evaluation_duration_ms: float
    
    @validator('compliance_level', always=True)
    def determine_compliance_level(cls, v, values):
        """Automatically determine compliance level based on overall score."""
        score = values.get('overall_score', 0.0)
        if score >= 0.95:
            return ConstitutionalComplianceLevel.FULLY_COMPLIANT
        elif score >= 0.85:
            return ConstitutionalComplianceLevel.MOSTLY_COMPLIANT
        elif score >= 0.70:
            return ConstitutionalComplianceLevel.PARTIALLY_COMPLIANT
        else:
            return ConstitutionalComplianceLevel.NON_COMPLIANT
    
    @property
    def meets_target_fidelity(self) -> bool:
        """Check if score meets target fidelity of >0.85."""
        return self.overall_score > 0.85


class RegoPolicy(BaseModel):
    """Structured representation of a Rego policy."""
    package_name: str = Field(..., description="Rego package name")
    policy_name: str = Field(..., description="Policy identifier")
    rules: List[str] = Field(..., description="Rego rule statements")
    imports: List[str] = Field(default_factory=list, description="Import statements")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Constitutional compliance
    constitutional_fidelity: Optional[ConstitutionalFidelityScore] = None
    source_principles: List[int] = Field(default_factory=list, description="Source principle IDs")
    
    @validator('package_name')
    def validate_package_name(cls, v):
        """Validate Rego package name format."""
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_]*)*$', v):
            raise ValueError('Invalid Rego package name format')
        return v
    
    @validator('rules')
    def validate_rules(cls, v):
        """Basic validation of Rego rules."""
        if not v:
            raise ValueError('At least one rule is required')
        
        for rule in v:
            if not rule.strip():
                raise ValueError('Empty rules are not allowed')
            # Basic Rego syntax check
            if not any(keyword in rule for keyword in ['allow', 'deny', 'default', ':=']):
                raise ValueError(f'Rule appears to be invalid Rego syntax: {rule[:50]}...')
        
        return v
    
    def to_rego_string(self) -> str:
        """Convert to valid Rego policy string."""
        lines = []
        
        # Package declaration
        lines.append(f"package {self.package_name}")
        lines.append("")
        
        # Imports
        for import_stmt in self.imports:
            lines.append(f"import {import_stmt}")
        if self.imports:
            lines.append("")
        
        # Rules
        for rule in self.rules:
            lines.append(rule)
            lines.append("")
        
        return "\n".join(lines)


class PolicySynthesisRequest(BaseModel):
    """Request for policy synthesis from constitutional principles."""
    principle_ids: List[int] = Field(..., description="Constitutional principle IDs")
    context: str = Field(..., description="Policy context or scenario")
    policy_type: PolicyType = Field(default=PolicyType.REGO)
    
    # Synthesis parameters
    creativity_level: float = Field(default=0.3, ge=0.0, le=1.0)
    strictness_level: float = Field(default=0.8, ge=0.0, le=1.0)
    bias_mitigation_enabled: bool = Field(default=True)
    
    # Target requirements
    target_fidelity_score: float = Field(default=0.85, ge=0.0, le=1.0)
    max_violations: int = Field(default=0, ge=0)
    
    # Metadata
    request_id: str
    requester: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PolicySynthesisResponse(BaseModel):
    """Response from policy synthesis process."""
    request_id: str
    success: bool
    
    # Generated policy
    policy: Optional[RegoPolicy] = None
    alternative_policies: List[RegoPolicy] = Field(default_factory=list)
    
    # Synthesis metadata
    model_used: str
    synthesis_duration_ms: float
    attempt_count: int = Field(default=1)
    
    # Quality metrics
    constitutional_fidelity: Optional[ConstitutionalFidelityScore] = None
    synthesis_confidence: float = Field(..., ge=0.0, le=1.0)
    
    # Error handling
    error_message: Optional[str] = None
    fallback_used: bool = Field(default=False)
    
    # Recommendations
    improvement_suggestions: List[str] = Field(default_factory=list)
    
    @property
    def meets_quality_threshold(self) -> bool:
        """Check if synthesis meets quality requirements."""
        if not self.constitutional_fidelity:
            return False
        return (
            self.constitutional_fidelity.meets_target_fidelity and
            self.synthesis_confidence >= 0.8 and
            len(self.constitutional_fidelity.violations) == 0
        )


class ModelSpecializationConfig(BaseModel):
    """Configuration for specialized model usage."""
    constitutional_prompting_model: str = Field(default="meta-llama/llama-4-maverick-17b-128e-instruct")
    policy_synthesis_model: str = Field(default="grok-3-mini")
    conflict_resolution_model: str = Field(default="gemini-2.0-flash")
    bias_mitigation_model: str = Field(default="meta-llama/llama-4-maverick-17b-128e-instruct")
    fidelity_monitoring_model: str = Field(default="gemini-2.0-flash")
    
    # Model-specific parameters
    temperature_settings: Dict[str, float] = Field(default_factory=lambda: {
        "constitutional_prompting": 0.1,
        "policy_synthesis": 0.3,
        "conflict_resolution": 0.2,
        "bias_mitigation": 0.1,
        "fidelity_monitoring": 0.1
    })
    
    # Fallback configuration
    fallback_chains: Dict[str, List[str]] = Field(default_factory=lambda: {
        "constitutional_prompting": ["meta-llama/llama-4-maverick-17b-128e-instruct", "grok-3-mini", "gemini-2.0-flash"],
        "policy_synthesis": ["grok-3-mini", "meta-llama/llama-4-maverick-17b-128e-instruct", "gemini-2.0-flash"],
        "conflict_resolution": ["gemini-2.0-flash", "grok-3-mini", "meta-llama/llama-4-maverick-17b-128e-instruct"],
        "bias_mitigation": ["meta-llama/llama-4-maverick-17b-128e-instruct", "grok-3-mini"],
        "fidelity_monitoring": ["gemini-2.0-flash", "grok-3-mini"]
    })
    
    # Circuit breaker settings
    circuit_breaker_failure_threshold: int = Field(default=5)
    circuit_breaker_recovery_timeout: int = Field(default=60)
    circuit_breaker_success_threshold: int = Field(default=3)


class WorkflowState(BaseModel):
    """State for LangGraph workflow orchestration."""
    request: PolicySynthesisRequest
    current_step: str
    
    # Intermediate results
    constitutional_analysis: Optional[Dict[str, Any]] = None
    policy_draft: Optional[RegoPolicy] = None
    fidelity_assessment: Optional[ConstitutionalFidelityScore] = None
    
    # Workflow metadata
    workflow_id: str
    start_time: datetime = Field(default_factory=datetime.utcnow)
    step_history: List[str] = Field(default_factory=list)
    
    # Error handling
    errors: List[str] = Field(default_factory=list)
    retry_count: int = Field(default=0)
    max_retries: int = Field(default=3)
    
    def add_step(self, step_name: str):
        """Add a step to the workflow history."""
        self.step_history.append(f"{step_name}:{datetime.utcnow().isoformat()}")
        self.current_step = step_name
    
    def add_error(self, error_message: str):
        """Add an error to the workflow."""
        self.errors.append(f"{datetime.utcnow().isoformat()}: {error_message}")
    
    @property
    def duration_ms(self) -> float:
        """Calculate workflow duration in milliseconds."""
        return (datetime.utcnow() - self.start_time).total_seconds() * 1000
