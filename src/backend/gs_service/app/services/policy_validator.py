"""
Policy Validation Engine Service

This service provides comprehensive policy validation using OPA/Rego integration
with performance optimization, conflict detection, and constitutional compliance
checking for the governance synthesis system.

Phase 2: Governance Synthesis Hardening with Rego/OPA Integration
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import json

from ..core.opa_integration import (
    get_opa_client, PolicyDecisionRequest, PolicyDecisionResponse,
    BatchPolicyDecision, PolicyValidationResult, OPAIntegrationError
)
from ..config.opa_config import get_opa_config

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Policy validation levels."""
    BASIC = "basic"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"
    CRITICAL = "critical"


class PolicyType(Enum):
    """Types of policies for validation."""
    CONSTITUTIONAL_PRINCIPLE = "constitutional_principle"
    OPERATIONAL_RULE = "operational_rule"
    GOVERNANCE_RULE = "governance_rule"
    COMPLIANCE_RULE = "compliance_rule"


@dataclass
class PolicyValidationRequest:
    """Request for policy validation."""
    policy_content: str
    policy_type: PolicyType
    constitutional_principles: List[Dict[str, Any]]
    existing_policies: List[Dict[str, Any]]
    context_data: Dict[str, Any]
    validation_level: ValidationLevel = ValidationLevel.STANDARD
    check_conflicts: bool = True
    check_compliance: bool = True
    check_constitutional: bool = True
    target_format: str = "rego"


@dataclass
class ConflictDetectionResult:
    """Result of policy conflict detection."""
    has_conflicts: bool
    logical_conflicts: List[Dict[str, Any]]
    semantic_conflicts: List[Dict[str, Any]]
    priority_conflicts: List[Dict[str, Any]]
    scope_conflicts: List[Dict[str, Any]]
    conflict_resolution_suggestions: List[str]


@dataclass
class ComplianceCheckResult:
    """Result of compliance checking."""
    is_compliant: bool
    compliance_score: float
    category_scores: Dict[str, float]
    violations: List[Dict[str, Any]]
    recommendations: List[str]
    requires_review: bool


@dataclass
class ConstitutionalValidationResult:
    """Result of constitutional validation."""
    is_constitutional: bool
    compliance_score: float
    principle_scores: Dict[str, float]
    violations: List[str]
    recommendations: List[str]


@dataclass
class PolicyValidationResponse:
    """Comprehensive policy validation response."""
    is_valid: bool
    overall_score: float
    validation_time_ms: float
    
    # Detailed results
    syntax_validation: PolicyValidationResult
    constitutional_validation: Optional[ConstitutionalValidationResult]
    compliance_check: Optional[ComplianceCheckResult]
    conflict_detection: Optional[ConflictDetectionResult]
    
    # Summary
    errors: List[str]
    warnings: List[str]
    recommendations: List[str]
    
    # Performance metrics
    decision_latency_ms: float
    cache_hit: bool


class PolicyValidationEngine:
    """
    High-performance policy validation engine with OPA/Rego integration.
    
    Provides comprehensive policy validation including:
    - Syntax and semantic validation
    - Constitutional compliance checking
    - Policy conflict detection
    - Regulatory compliance verification
    - Performance optimization with <50ms target latency
    """
    
    def __init__(self):
        self.config = get_opa_config()
        self.opa_client = None
        self._initialized = False
        
        # Performance tracking
        self.metrics = {
            "total_validations": 0,
            "average_latency_ms": 0.0,
            "max_latency_ms": 0.0,
            "cache_hit_rate": 0.0,
            "error_rate": 0.0
        }
    
    async def initialize(self):
        """Initialize the policy validation engine."""
        if self._initialized:
            return
        
        try:
            self.opa_client = await get_opa_client()
            self._initialized = True
            logger.info("Policy validation engine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize policy validation engine: {e}")
            raise
    
    async def validate_policy(self, request: PolicyValidationRequest) -> PolicyValidationResponse:
        """
        Validate policy with comprehensive checks and performance optimization.
        
        Args:
            request: Policy validation request
            
        Returns:
            Comprehensive validation response
            
        Raises:
            OPAIntegrationError: If validation fails
        """
        if not self._initialized:
            await self.initialize()
        
        start_time = time.time()
        errors = []
        warnings = []
        recommendations = []
        
        try:
            # 1. Syntax validation
            syntax_result = await self._validate_syntax(request)
            if not syntax_result.is_valid:
                errors.extend(syntax_result.errors)
                warnings.extend(syntax_result.warnings)
            
            # 2. Constitutional validation (if requested)
            constitutional_result = None
            if request.check_constitutional and syntax_result.is_valid:
                constitutional_result = await self._validate_constitutional(request)
                if constitutional_result and not constitutional_result.is_constitutional:
                    errors.extend(constitutional_result.violations)
                    recommendations.extend(constitutional_result.recommendations)
            
            # 3. Compliance checking (if requested)
            compliance_result = None
            if request.check_compliance and syntax_result.is_valid:
                compliance_result = await self._check_compliance(request)
                if compliance_result and not compliance_result.is_compliant:
                    recommendations.extend(compliance_result.recommendations)
            
            # 4. Conflict detection (if requested)
            conflict_result = None
            if request.check_conflicts and syntax_result.is_valid:
                conflict_result = await self._detect_conflicts(request)
                if conflict_result and conflict_result.has_conflicts:
                    warnings.append("Policy conflicts detected")
                    recommendations.extend(conflict_result.conflict_resolution_suggestions)
            
            # Calculate overall validation result
            is_valid = self._calculate_overall_validity(
                syntax_result, constitutional_result, compliance_result, conflict_result
            )
            
            overall_score = self._calculate_overall_score(
                syntax_result, constitutional_result, compliance_result, conflict_result
            )
            
            validation_time_ms = (time.time() - start_time) * 1000
            
            # Update metrics
            self._update_metrics(validation_time_ms, len(errors) == 0)
            
            # Check performance threshold
            if validation_time_ms > self.config.performance.max_policy_decision_latency_ms:
                warnings.append(f"Validation exceeded latency threshold: {validation_time_ms:.2f}ms")
            
            return PolicyValidationResponse(
                is_valid=is_valid,
                overall_score=overall_score,
                validation_time_ms=validation_time_ms,
                syntax_validation=syntax_result,
                constitutional_validation=constitutional_result,
                compliance_check=compliance_result,
                conflict_detection=conflict_result,
                errors=errors,
                warnings=warnings,
                recommendations=recommendations,
                decision_latency_ms=validation_time_ms,
                cache_hit=False  # Would be set by caching layer
            )
            
        except Exception as e:
            validation_time_ms = (time.time() - start_time) * 1000
            self._update_metrics(validation_time_ms, False)
            logger.error(f"Policy validation failed: {e}")
            raise OPAIntegrationError(f"Policy validation failed: {e}")
    
    async def _validate_syntax(self, request: PolicyValidationRequest) -> PolicyValidationResult:
        """Validate policy syntax using OPA."""
        try:
            return await self.opa_client.validate_policy(
                request.policy_content,
                f"{request.policy_type.value}_validation"
            )
        except Exception as e:
            logger.error(f"Syntax validation failed: {e}")
            return PolicyValidationResult(
                is_valid=False,
                policy_path=f"{request.policy_type.value}_validation",
                validation_time_ms=0.0,
                errors=[str(e)],
                warnings=[],
                syntax_errors=[str(e)],
                semantic_errors=[]
            )
    
    async def _validate_constitutional(self, request: PolicyValidationRequest) -> ConstitutionalValidationResult:
        """Validate policy against constitutional principles."""
        try:
            decision_request = PolicyDecisionRequest(
                input_data={
                    "policy_content": request.policy_content,
                    "policy_type": request.policy_type.value,
                    "constitutional_principles": request.constitutional_principles,
                    "context": request.context_data
                },
                policy_path="acgs/constitutional/compliance_report",
                explain=True
            )
            
            response = await self.opa_client.evaluate_policy(decision_request)
            
            if response.error:
                raise OPAIntegrationError(f"Constitutional validation failed: {response.error}")
            
            result = response.result
            return ConstitutionalValidationResult(
                is_constitutional=result.get("allowed", False),
                compliance_score=result.get("compliance_score", 0.0),
                principle_scores=result.get("principle_scores", {}),
                violations=result.get("constitutional_violations", []),
                recommendations=result.get("recommendations", [])
            )
            
        except Exception as e:
            logger.error(f"Constitutional validation failed: {e}")
            return ConstitutionalValidationResult(
                is_constitutional=False,
                compliance_score=0.0,
                principle_scores={},
                violations=[str(e)],
                recommendations=["Fix constitutional validation errors"]
            )
    
    async def _check_compliance(self, request: PolicyValidationRequest) -> ComplianceCheckResult:
        """Check policy compliance against regulatory requirements."""
        try:
            decision_request = PolicyDecisionRequest(
                input_data={
                    "policy_content": request.policy_content,
                    "compliance_context": {
                        "category": request.context_data.get("compliance_category", "operational"),
                        "jurisdiction": request.context_data.get("jurisdiction", "default"),
                        "requires_transparency": request.context_data.get("requires_transparency", False),
                        "requires_explicit_consent": request.context_data.get("requires_explicit_consent", False)
                    },
                    "governance_context": {
                        "system_type": request.context_data.get("target_system", "governance"),
                        "risk_level": request.context_data.get("risk_level", "medium"),
                        "handles_sensitive_data": request.context_data.get("handles_sensitive_data", False)
                    },
                    "compliance_declarations": request.context_data.get("compliance_declarations", [])
                },
                policy_path="acgs/compliance/compliance_report",
                explain=True
            )
            
            response = await self.opa_client.evaluate_policy(decision_request)
            
            if response.error:
                raise OPAIntegrationError(f"Compliance check failed: {response.error}")
            
            result = response.result
            return ComplianceCheckResult(
                is_compliant=result.get("compliant", False),
                compliance_score=result.get("compliance_score", 0.0),
                category_scores=result.get("category_scores", {}),
                violations=result.get("violations", {}),
                recommendations=result.get("recommendations", []),
                requires_review=result.get("requires_review", False)
            )
            
        except Exception as e:
            logger.error(f"Compliance check failed: {e}")
            return ComplianceCheckResult(
                is_compliant=False,
                compliance_score=0.0,
                category_scores={},
                violations={"error": str(e)},
                recommendations=["Fix compliance check errors"],
                requires_review=True
            )
    
    async def _detect_conflicts(self, request: PolicyValidationRequest) -> ConflictDetectionResult:
        """Detect conflicts with existing policies."""
        try:
            decision_request = PolicyDecisionRequest(
                input_data={
                    "policy_content": request.policy_content,
                    "synthesis_goal": f"Validate {request.policy_type.value}",
                    "policy_type": request.policy_type.value,
                    "target_format": request.target_format,
                    "constitutional_principles": request.constitutional_principles,
                    "existing_policies": request.existing_policies,
                    "context_data": request.context_data
                },
                policy_path="acgs/synthesis/synthesis_result",
                explain=True
            )
            
            response = await self.opa_client.evaluate_policy(decision_request)
            
            if response.error:
                raise OPAIntegrationError(f"Conflict detection failed: {response.error}")
            
            result = response.result
            conflict_details = result.get("conflict_details", {})
            
            return ConflictDetectionResult(
                has_conflicts=result.get("has_conflicts", False),
                logical_conflicts=self._extract_conflicts(conflict_details, "logical_conflicts"),
                semantic_conflicts=self._extract_conflicts(conflict_details, "semantic_conflicts"),
                priority_conflicts=self._extract_conflicts(conflict_details, "priority_conflicts"),
                scope_conflicts=self._extract_conflicts(conflict_details, "scope_conflicts"),
                conflict_resolution_suggestions=result.get("recommendations", [])
            )
            
        except Exception as e:
            logger.error(f"Conflict detection failed: {e}")
            return ConflictDetectionResult(
                has_conflicts=True,
                logical_conflicts=[{"error": str(e)}],
                semantic_conflicts=[],
                priority_conflicts=[],
                scope_conflicts=[],
                conflict_resolution_suggestions=["Fix conflict detection errors"]
            )
    
    def _extract_conflicts(self, conflict_details: Dict[str, Any], conflict_type: str) -> List[Dict[str, Any]]:
        """Extract specific type of conflicts from conflict details."""
        if conflict_details.get(conflict_type, False):
            return [{"type": conflict_type, "detected": True}]
        return []
    
    def _calculate_overall_validity(self, syntax_result: PolicyValidationResult,
                                  constitutional_result: Optional[ConstitutionalValidationResult],
                                  compliance_result: Optional[ComplianceCheckResult],
                                  conflict_result: Optional[ConflictDetectionResult]) -> bool:
        """Calculate overall policy validity."""
        # Syntax must be valid
        if not syntax_result.is_valid:
            return False
        
        # Constitutional validation must pass if checked
        if constitutional_result and not constitutional_result.is_constitutional:
            return False
        
        # Critical compliance issues must be resolved
        if compliance_result and not compliance_result.is_compliant:
            if compliance_result.requires_review:
                return False
        
        # Critical conflicts must be resolved
        if conflict_result and conflict_result.has_conflicts:
            # Allow minor conflicts but flag for review
            if len(conflict_result.logical_conflicts) > 0:
                return False
        
        return True
    
    def _calculate_overall_score(self, syntax_result: PolicyValidationResult,
                               constitutional_result: Optional[ConstitutionalValidationResult],
                               compliance_result: Optional[ComplianceCheckResult],
                               conflict_result: Optional[ConflictDetectionResult]) -> float:
        """Calculate overall policy quality score."""
        scores = []
        weights = []
        
        # Syntax score (weight: 0.2)
        syntax_score = 1.0 if syntax_result.is_valid else 0.0
        scores.append(syntax_score)
        weights.append(0.2)
        
        # Constitutional score (weight: 0.4)
        if constitutional_result:
            scores.append(constitutional_result.compliance_score)
            weights.append(0.4)
        
        # Compliance score (weight: 0.3)
        if compliance_result:
            scores.append(compliance_result.compliance_score)
            weights.append(0.3)
        
        # Conflict penalty (weight: 0.1)
        conflict_score = 1.0
        if conflict_result and conflict_result.has_conflicts:
            conflict_penalty = len(conflict_result.logical_conflicts) * 0.2
            conflict_score = max(0.0, 1.0 - conflict_penalty)
        scores.append(conflict_score)
        weights.append(0.1)
        
        # Calculate weighted average
        if sum(weights) > 0:
            return sum(score * weight for score, weight in zip(scores, weights)) / sum(weights)
        return 0.0
    
    def _update_metrics(self, latency_ms: float, success: bool):
        """Update performance metrics."""
        self.metrics["total_validations"] += 1
        
        # Update average latency
        total = self.metrics["total_validations"]
        current_avg = self.metrics["average_latency_ms"]
        self.metrics["average_latency_ms"] = ((current_avg * (total - 1)) + latency_ms) / total
        
        # Update max latency
        if latency_ms > self.metrics["max_latency_ms"]:
            self.metrics["max_latency_ms"] = latency_ms
        
        # Update error rate
        if not success:
            error_count = self.metrics["error_rate"] * (total - 1) + 1
            self.metrics["error_rate"] = error_count / total
        else:
            error_count = self.metrics["error_rate"] * (total - 1)
            self.metrics["error_rate"] = error_count / total
    
    async def batch_validate(self, requests: List[PolicyValidationRequest]) -> List[PolicyValidationResponse]:
        """Validate multiple policies in batch for improved performance."""
        if not requests:
            return []
        
        if self.config.performance.enable_batch_evaluation:
            # Use batch processing
            semaphore = asyncio.Semaphore(self.config.performance.max_parallel_workers)
            
            async def validate_with_semaphore(request):
                async with semaphore:
                    return await self.validate_policy(request)
            
            tasks = [validate_with_semaphore(request) for request in requests]
            return await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # Sequential processing
            results = []
            for request in requests:
                result = await self.validate_policy(request)
                results.append(result)
            return results
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return self.metrics.copy()


# Global policy validation engine instance
_policy_validator: Optional[PolicyValidationEngine] = None


async def get_policy_validator() -> PolicyValidationEngine:
    """Get or create the global policy validation engine instance."""
    global _policy_validator
    if _policy_validator is None:
        _policy_validator = PolicyValidationEngine()
        await _policy_validator.initialize()
    return _policy_validator
