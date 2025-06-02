# Enhanced Multi-Model Validation System
# Provides improved cross-model validation, error aggregation, and performance optimization

import asyncio
import time
import logging
from typing import List, Dict, Any, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import json

from ..schemas import (
    VerificationRequest, VerificationResponse, PolicyRule, ACPrinciple,
    ValidationResult, SafetyCheckResult, ConflictCheckResult
)

logger = logging.getLogger(__name__)


class ValidationSeverity(str, Enum):
    """Validation error severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class CrossModelValidationType(str, Enum):
    """Types of cross-model validation."""
    CONSISTENCY = "consistency"
    COMPLETENESS = "completeness"
    COHERENCE = "coherence"
    COMPLIANCE = "compliance"
    SAFETY = "safety"


@dataclass
class ValidationError:
    """Enhanced validation error with detailed context."""
    error_id: str
    error_type: str
    severity: ValidationSeverity
    message: str
    detailed_description: str
    affected_models: List[str]
    source_location: Optional[Dict[str, Any]] = None
    suggested_fix: Optional[str] = None
    related_errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CrossModelValidationRule:
    """Cross-model validation rule definition."""
    rule_id: str
    rule_name: str
    validation_type: CrossModelValidationType
    description: str
    affected_model_types: List[str]
    validation_function: str  # Function name to execute
    severity: ValidationSeverity
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationContext:
    """Context for validation execution."""
    request_id: str
    models: Dict[str, Any]
    validation_rules: List[CrossModelValidationRule]
    performance_budget_ms: int = 30000
    max_concurrent_validations: int = 10
    enable_caching: bool = True
    cache_ttl_seconds: int = 300


@dataclass
class AggregatedValidationResult:
    """Aggregated validation results with enhanced error reporting."""
    request_id: str
    overall_status: str
    total_validations: int
    successful_validations: int
    failed_validations: int
    errors: List[ValidationError]
    warnings: List[ValidationError]
    performance_metrics: Dict[str, Any]
    cross_model_issues: List[Dict[str, Any]]
    recommendations: List[str]
    execution_time_ms: int


class EnhancedMultiModelValidator:
    """Enhanced multi-model validation system with improved capabilities."""
    
    def __init__(self):
        self.validation_cache: Dict[str, Any] = {}
        self.performance_metrics: Dict[str, Any] = defaultdict(list)
        self.cross_model_rules: List[CrossModelValidationRule] = []
        self._initialize_cross_model_rules()
    
    def _initialize_cross_model_rules(self) -> None:
        """Initialize built-in cross-model validation rules."""
        self.cross_model_rules = [
            CrossModelValidationRule(
                rule_id="consistency_policy_principle_alignment",
                rule_name="Policy-Principle Consistency",
                validation_type=CrossModelValidationType.CONSISTENCY,
                description="Ensure policy rules align with AC principles",
                affected_model_types=["policy_rule", "ac_principle"],
                validation_function="validate_policy_principle_consistency",
                severity=ValidationSeverity.HIGH
            ),
            CrossModelValidationRule(
                rule_id="completeness_coverage_analysis",
                rule_name="Coverage Completeness",
                validation_type=CrossModelValidationType.COMPLETENESS,
                description="Verify all principles have corresponding policy coverage",
                affected_model_types=["policy_rule", "ac_principle"],
                validation_function="validate_coverage_completeness",
                severity=ValidationSeverity.MEDIUM
            ),
            CrossModelValidationRule(
                rule_id="coherence_semantic_consistency",
                rule_name="Semantic Coherence",
                validation_type=CrossModelValidationType.COHERENCE,
                description="Check semantic consistency across model types",
                affected_model_types=["policy_rule", "ac_principle", "safety_property"],
                validation_function="validate_semantic_coherence",
                severity=ValidationSeverity.HIGH
            ),
            CrossModelValidationRule(
                rule_id="safety_conflict_detection",
                rule_name="Safety Conflict Detection",
                validation_type=CrossModelValidationType.SAFETY,
                description="Detect conflicts between safety properties and policies",
                affected_model_types=["policy_rule", "safety_property"],
                validation_function="validate_safety_conflicts",
                severity=ValidationSeverity.CRITICAL
            ),
            CrossModelValidationRule(
                rule_id="compliance_regulatory_alignment",
                rule_name="Regulatory Compliance",
                validation_type=CrossModelValidationType.COMPLIANCE,
                description="Ensure compliance with regulatory requirements",
                affected_model_types=["policy_rule", "ac_principle", "compliance_requirement"],
                validation_function="validate_regulatory_compliance",
                severity=ValidationSeverity.CRITICAL
            )
        ]
    
    async def validate_multi_model(
        self, 
        context: ValidationContext
    ) -> AggregatedValidationResult:
        """
        Enhanced multi-model validation with improved error handling and performance.
        """
        start_time = time.time()
        logger.info(f"Starting enhanced multi-model validation for request {context.request_id}")
        
        # Initialize result tracking
        errors: List[ValidationError] = []
        warnings: List[ValidationError] = []
        cross_model_issues: List[Dict[str, Any]] = []
        recommendations: List[str] = []
        
        try:
            # Phase 1: Individual model validation
            individual_results = await self._validate_individual_models(context)
            
            # Phase 2: Cross-model validation
            cross_model_results = await self._validate_cross_model_rules(context)
            
            # Phase 3: Aggregate and analyze results
            aggregated_result = await self._aggregate_validation_results(
                context, individual_results, cross_model_results, start_time
            )
            
            # Phase 4: Generate recommendations
            recommendations = await self._generate_recommendations(aggregated_result)
            aggregated_result.recommendations = recommendations
            
            return aggregated_result
            
        except Exception as e:
            logger.error(f"Multi-model validation failed: {e}")
            execution_time = int((time.time() - start_time) * 1000)
            
            return AggregatedValidationResult(
                request_id=context.request_id,
                overall_status="error",
                total_validations=0,
                successful_validations=0,
                failed_validations=1,
                errors=[ValidationError(
                    error_id=f"system_error_{context.request_id}",
                    error_type="system_error",
                    severity=ValidationSeverity.CRITICAL,
                    message="Multi-model validation system error",
                    detailed_description=str(e),
                    affected_models=list(context.models.keys())
                )],
                warnings=[],
                performance_metrics={},
                cross_model_issues=[],
                recommendations=[],
                execution_time_ms=execution_time
            )
    
    async def _validate_individual_models(
        self, 
        context: ValidationContext
    ) -> Dict[str, List[ValidationResult]]:
        """Validate individual models with performance optimization."""
        results = {}
        
        # Create validation tasks
        tasks = []
        for model_type, model_data in context.models.items():
            task = self._validate_single_model(model_type, model_data, context)
            tasks.append((model_type, task))
        
        # Execute with concurrency control
        semaphore = asyncio.Semaphore(context.max_concurrent_validations)
        
        async def bounded_validate(model_type, task):
            async with semaphore:
                return model_type, await task
        
        # Execute all validations
        bounded_tasks = [bounded_validate(mt, t) for mt, t in tasks]
        completed_results = await asyncio.gather(*bounded_tasks, return_exceptions=True)
        
        # Process results
        for result in completed_results:
            if isinstance(result, Exception):
                logger.error(f"Individual model validation failed: {result}")
                continue
            
            model_type, validation_results = result
            results[model_type] = validation_results
        
        return results
    
    async def _validate_single_model(
        self, 
        model_type: str, 
        model_data: Any, 
        context: ValidationContext
    ) -> List[ValidationResult]:
        """Validate a single model with caching."""
        cache_key = f"{model_type}_{hash(str(model_data))}"
        
        # Check cache
        if context.enable_caching and cache_key in self.validation_cache:
            cached_result = self.validation_cache[cache_key]
            if time.time() - cached_result['timestamp'] < context.cache_ttl_seconds:
                logger.debug(f"Using cached validation result for {model_type}")
                return cached_result['results']
        
        # Perform validation
        start_time = time.time()
        results = []
        
        try:
            # Model-specific validation logic
            if model_type == "policy_rule":
                results = await self._validate_policy_rules(model_data)
            elif model_type == "ac_principle":
                results = await self._validate_ac_principles(model_data)
            elif model_type == "safety_property":
                results = await self._validate_safety_properties(model_data)
            else:
                logger.warning(f"Unknown model type: {model_type}")
        
        except Exception as e:
            logger.error(f"Validation failed for {model_type}: {e}")
            results = [ValidationResult(
                rule_id=0,  # Error case
                principle_id=0,  # Error case
                validation_type=f"error_{model_type}",
                is_valid=False,
                confidence_score=0.0,
                error_details=str(e),
                suggestions=["Check model data format", "Review validation logic"],
                metadata={
                    'execution_time_ms': int((time.time() - start_time) * 1000)
                }
            )]
        
        # Cache results
        if context.enable_caching:
            self.validation_cache[cache_key] = {
                'results': results,
                'timestamp': time.time()
            }
        
        # Track performance
        execution_time = (time.time() - start_time) * 1000
        self.performance_metrics[model_type].append(execution_time)
        
        return results

    async def _validate_cross_model_rules(
        self,
        context: ValidationContext
    ) -> List[ValidationError]:
        """Execute cross-model validation rules."""
        errors = []

        for rule in self.cross_model_rules:
            if not rule.enabled:
                continue

            try:
                # Check if required models are available
                if not all(model_type in context.models for model_type in rule.affected_model_types):
                    continue

                # Execute validation function
                rule_errors = await self._execute_cross_model_rule(rule, context)
                errors.extend(rule_errors)

            except Exception as e:
                logger.error(f"Cross-model rule {rule.rule_id} failed: {e}")
                errors.append(ValidationError(
                    error_id=f"cross_model_error_{rule.rule_id}",
                    error_type="cross_model_validation_error",
                    severity=ValidationSeverity.HIGH,
                    message=f"Cross-model validation rule failed: {rule.rule_name}",
                    detailed_description=str(e),
                    affected_models=rule.affected_model_types
                ))

        return errors

    async def _execute_cross_model_rule(
        self,
        rule: CrossModelValidationRule,
        context: ValidationContext
    ) -> List[ValidationError]:
        """Execute a specific cross-model validation rule."""
        if rule.validation_function == "validate_policy_principle_consistency":
            return await self._validate_policy_principle_consistency(context)
        elif rule.validation_function == "validate_coverage_completeness":
            return await self._validate_coverage_completeness(context)
        elif rule.validation_function == "validate_semantic_coherence":
            return await self._validate_semantic_coherence(context)
        elif rule.validation_function == "validate_safety_conflicts":
            return await self._validate_safety_conflicts(context)
        elif rule.validation_function == "validate_regulatory_compliance":
            return await self._validate_regulatory_compliance(context)
        else:
            logger.warning(f"Unknown validation function: {rule.validation_function}")
            return []

    async def _validate_policy_principle_consistency(
        self,
        context: ValidationContext
    ) -> List[ValidationError]:
        """Validate consistency between policy rules and AC principles."""
        errors = []

        policy_rules = context.models.get("policy_rule", [])
        ac_principles = context.models.get("ac_principle", [])

        if not policy_rules or not ac_principles:
            return errors

        # Check for policy rules without corresponding principles
        principle_topics = {p.get('topic', '').lower() for p in ac_principles}

        for rule in policy_rules:
            rule_content = rule.get('content', '').lower()
            rule_id = rule.get('id', 'unknown')

            # Simple topic matching (can be enhanced with NLP)
            has_matching_principle = any(
                topic in rule_content for topic in principle_topics if topic
            )

            if not has_matching_principle:
                errors.append(ValidationError(
                    error_id=f"consistency_error_{rule_id}",
                    error_type="policy_principle_mismatch",
                    severity=ValidationSeverity.MEDIUM,
                    message=f"Policy rule {rule_id} lacks corresponding AC principle",
                    detailed_description=f"Policy rule '{rule_content[:100]}...' does not align with any AC principle topics",
                    affected_models=["policy_rule", "ac_principle"],
                    suggested_fix="Review policy rule and ensure it aligns with established AC principles"
                ))

        return errors

    async def _validate_coverage_completeness(
        self,
        context: ValidationContext
    ) -> List[ValidationError]:
        """Validate completeness of policy coverage for AC principles."""
        errors = []

        policy_rules = context.models.get("policy_rule", [])
        ac_principles = context.models.get("ac_principle", [])

        if not ac_principles:
            return errors

        # Check for principles without policy coverage
        policy_topics = {self._extract_topic(rule.get('content', '')) for rule in policy_rules}

        for principle in ac_principles:
            principle_topic = principle.get('topic', '').lower()
            principle_id = principle.get('id', 'unknown')

            if principle_topic and principle_topic not in policy_topics:
                errors.append(ValidationError(
                    error_id=f"coverage_error_{principle_id}",
                    error_type="incomplete_policy_coverage",
                    severity=ValidationSeverity.HIGH,
                    message=f"AC principle {principle_id} lacks policy implementation",
                    detailed_description=f"Principle '{principle_topic}' has no corresponding policy rules",
                    affected_models=["policy_rule", "ac_principle"],
                    suggested_fix=f"Create policy rules to implement principle: {principle_topic}"
                ))

        return errors

    async def _validate_semantic_coherence(
        self,
        context: ValidationContext
    ) -> List[ValidationError]:
        """Validate semantic coherence across model types."""
        errors = []

        # Check for semantic conflicts between models
        models = context.models

        # Example: Check for contradictory statements
        policy_rules = models.get("policy_rule", [])
        safety_properties = models.get("safety_property", [])

        for rule in policy_rules:
            rule_content = rule.get('content', '').lower()
            rule_id = rule.get('id', 'unknown')

            for safety_prop in safety_properties:
                safety_desc = safety_prop.get('description', '').lower()
                safety_id = safety_prop.get('id', 'unknown')

                # Simple contradiction detection (can be enhanced with NLP)
                if self._detect_semantic_conflict(rule_content, safety_desc):
                    errors.append(ValidationError(
                        error_id=f"coherence_error_{rule_id}_{safety_id}",
                        error_type="semantic_conflict",
                        severity=ValidationSeverity.HIGH,
                        message=f"Semantic conflict between rule {rule_id} and safety property {safety_id}",
                        detailed_description=f"Policy rule and safety property contain contradictory statements",
                        affected_models=["policy_rule", "safety_property"],
                        suggested_fix="Review and resolve contradictory statements between models"
                    ))

        return errors

    def _extract_topic(self, content: str) -> str:
        """Extract topic from content (simplified implementation)."""
        # This is a simplified implementation - in practice, you'd use NLP
        content_lower = content.lower()

        # Common policy topics
        topics = ['access', 'privacy', 'security', 'data', 'user', 'admin', 'role']

        for topic in topics:
            if topic in content_lower:
                return topic

        return "general"

    def _detect_semantic_conflict(self, content1: str, content2: str) -> bool:
        """Detect semantic conflicts between two pieces of content."""
        # Simplified conflict detection - in practice, use NLP/semantic analysis

        # Look for contradictory keywords
        positive_keywords = ['allow', 'permit', 'enable', 'grant']
        negative_keywords = ['deny', 'forbid', 'disable', 'revoke']

        content1_positive = any(kw in content1 for kw in positive_keywords)
        content1_negative = any(kw in content1 for kw in negative_keywords)

        content2_positive = any(kw in content2 for kw in positive_keywords)
        content2_negative = any(kw in content2 for kw in negative_keywords)

        # Check for contradictions
        return ((content1_positive and content2_negative) or
                (content1_negative and content2_positive))

    async def _validate_safety_conflicts(
        self,
        context: ValidationContext
    ) -> List[ValidationError]:
        """Validate safety conflicts between policies and safety properties."""
        errors = []

        policy_rules = context.models.get("policy_rule", [])
        safety_properties = context.models.get("safety_property", [])

        if not policy_rules or not safety_properties:
            return errors

        for safety_prop in safety_properties:
            safety_desc = safety_prop.get('description', '').lower()
            safety_id = safety_prop.get('id', 'unknown')
            criticality = safety_prop.get('criticality_level', 'medium')

            for rule in policy_rules:
                rule_content = rule.get('content', '').lower()
                rule_id = rule.get('id', 'unknown')

                # Check for potential safety violations
                if self._check_safety_violation(rule_content, safety_desc):
                    severity = (ValidationSeverity.CRITICAL if criticality == 'critical'
                              else ValidationSeverity.HIGH)

                    errors.append(ValidationError(
                        error_id=f"safety_conflict_{rule_id}_{safety_id}",
                        error_type="safety_violation",
                        severity=severity,
                        message=f"Policy rule {rule_id} may violate safety property {safety_id}",
                        detailed_description=(
                            f"Policy rule content conflicts with safety requirement: "
                            f"{safety_desc[:100]}..."
                        ),
                        affected_models=["policy_rule", "safety_property"],
                        suggested_fix="Review policy rule to ensure safety compliance"
                    ))

        return errors

    async def _validate_regulatory_compliance(
        self,
        context: ValidationContext
    ) -> List[ValidationError]:
        """Validate regulatory compliance across models."""
        errors = []

        policy_rules = context.models.get("policy_rule", [])
        compliance_requirements = context.models.get("compliance_requirement", [])

        if not policy_rules or not compliance_requirements:
            return errors

        for requirement in compliance_requirements:
            req_desc = requirement.get('description', '').lower()
            req_id = requirement.get('id', 'unknown')
            regulation = requirement.get('regulation', 'unknown')

            # Check if requirement is addressed by any policy
            is_addressed = False

            for rule in policy_rules:
                rule_content = rule.get('content', '').lower()

                if self._check_compliance_coverage(rule_content, req_desc):
                    is_addressed = True
                    break

            if not is_addressed:
                errors.append(ValidationError(
                    error_id=f"compliance_gap_{req_id}",
                    error_type="regulatory_compliance_gap",
                    severity=ValidationSeverity.CRITICAL,
                    message=f"Regulatory requirement {req_id} not addressed",
                    detailed_description=(
                        f"Requirement from {regulation} is not covered by any policy: "
                        f"{req_desc[:100]}..."
                    ),
                    affected_models=["policy_rule", "compliance_requirement"],
                    suggested_fix=f"Create policy rules to address {regulation} requirement"
                ))

        return errors

    def _check_safety_violation(self, rule_content: str, safety_desc: str) -> bool:
        """Check if rule content violates safety description."""
        # Simplified safety violation detection
        safety_keywords = ['safe', 'secure', 'protect', 'prevent']
        violation_keywords = ['unsafe', 'insecure', 'expose', 'allow_all']

        has_safety_requirement = any(kw in safety_desc for kw in safety_keywords)
        has_violation_pattern = any(kw in rule_content for kw in violation_keywords)

        return has_safety_requirement and has_violation_pattern

    def _check_compliance_coverage(self, rule_content: str, requirement_desc: str) -> bool:
        """Check if rule content addresses compliance requirement."""
        # Extract key terms from requirement
        req_terms = set(requirement_desc.split())
        rule_terms = set(rule_content.split())

        # Simple overlap check (can be enhanced with semantic analysis)
        overlap = len(req_terms.intersection(rule_terms))
        return overlap >= min(3, len(req_terms) * 0.3)  # At least 30% overlap

    async def _validate_policy_rules(self, policy_rules: List[Any]) -> List[ValidationResult]:
        """Validate individual policy rules."""
        results = []

        for rule in policy_rules:
            rule_id = rule.get('id', 'unknown')
            rule_content = rule.get('content', '')

            # Basic validation checks
            issues = []

            if not rule_content.strip():
                issues.append("Empty rule content")

            if len(rule_content) < 10:
                issues.append("Rule content too short")

            # Check for basic syntax patterns
            if 'allow' not in rule_content.lower() and 'deny' not in rule_content.lower():
                issues.append("Rule lacks clear allow/deny directive")

            status = "failed" if issues else "verified"
            confidence = 0.3 if issues else 0.8

            # Convert string IDs to integers
            rule_id_int = int(rule_id.split('_')[-1]) if isinstance(rule_id, str) and '_' in rule_id else (int(rule_id) if str(rule_id).isdigit() else 1)
            principle_id_int = rule.get('principle_id', 1)
            if isinstance(principle_id_int, str):
                principle_id_int = int(principle_id_int.split('_')[-1]) if '_' in principle_id_int else (int(principle_id_int) if principle_id_int.isdigit() else 1)

            results.append(ValidationResult(
                rule_id=rule_id_int,
                principle_id=principle_id_int,
                validation_type="policy_rule",
                is_valid=(status == "verified"),
                confidence_score=confidence,
                error_details="; ".join(issues) if issues else None,
                suggestions=["Review rule content", "Add clear allow/deny directive"] if issues else None,
                metadata={
                    'rule_id': rule_id,
                    'execution_time_ms': 10
                }
            ))

        return results

    async def _validate_ac_principles(self, ac_principles: List[Any]) -> List[ValidationResult]:
        """Validate individual AC principles."""
        results = []

        for principle in ac_principles:
            principle_id = principle.get('id', 'unknown')
            principle_content = principle.get('content', '')

            # Basic validation checks
            issues = []

            if not principle_content.strip():
                issues.append("Empty principle content")

            if len(principle_content) < 20:
                issues.append("Principle content too brief")

            status = "failed" if issues else "verified"
            confidence = 0.3 if issues else 0.9

            # Convert string IDs to integers
            principle_id_int = int(principle_id.split('_')[-1]) if isinstance(principle_id, str) and '_' in principle_id else (int(principle_id) if str(principle_id).isdigit() else 1)

            results.append(ValidationResult(
                rule_id=1,  # Default rule_id for AC principles
                principle_id=principle_id_int,
                validation_type="ac_principle",
                is_valid=(status == "verified"),
                confidence_score=confidence,
                error_details="; ".join(issues) if issues else None,
                suggestions=["Expand principle content", "Add more detail"] if issues else None,
                metadata={
                    'principle_id': principle_id,
                    'execution_time_ms': 15
                }
            ))

        return results

    async def _validate_safety_properties(self, safety_properties: List[Any]) -> List[ValidationResult]:
        """Validate individual safety properties."""
        results = []

        for prop in safety_properties:
            prop_id = prop.get('id', 'unknown')
            prop_desc = prop.get('description', '')

            # Basic validation checks
            issues = []

            if not prop_desc.strip():
                issues.append("Empty safety property description")

            if 'safe' not in prop_desc.lower() and 'secure' not in prop_desc.lower():
                issues.append("Safety property lacks safety/security keywords")

            status = "failed" if issues else "verified"
            confidence = 0.4 if issues else 0.85

            # Convert string IDs to integers
            prop_id_int = int(prop_id.split('_')[-1]) if isinstance(prop_id, str) and '_' in prop_id else (int(prop_id) if str(prop_id).isdigit() else 1)

            results.append(ValidationResult(
                rule_id=1,  # Default rule_id for safety properties
                principle_id=prop_id_int,
                validation_type="safety_property",
                is_valid=(status == "verified"),
                confidence_score=confidence,
                error_details="; ".join(issues) if issues else None,
                suggestions=["Add safety keywords", "Improve description"] if issues else None,
                metadata={
                    'property_id': prop_id,
                    'execution_time_ms': 12
                }
            ))

        return results

    async def _aggregate_validation_results(
        self,
        context: ValidationContext,
        individual_results: Dict[str, List[ValidationResult]],
        cross_model_errors: List[ValidationError],
        start_time: float
    ) -> AggregatedValidationResult:
        """Aggregate all validation results into a comprehensive report."""

        # Count totals
        total_validations = sum(len(results) for results in individual_results.values())
        successful_validations = sum(
            1 for results in individual_results.values()
            for result in results
            if result.is_valid
        )
        failed_validations = total_validations - successful_validations

        # Separate errors by severity
        errors = [err for err in cross_model_errors if err.severity in [
            ValidationSeverity.CRITICAL, ValidationSeverity.HIGH
        ]]
        warnings = [err for err in cross_model_errors if err.severity in [
            ValidationSeverity.MEDIUM, ValidationSeverity.LOW, ValidationSeverity.INFO
        ]]

        # Calculate performance metrics
        execution_time = int((time.time() - start_time) * 1000)
        performance_metrics = {
            'total_execution_time_ms': execution_time,
            'individual_validation_times': {
                model_type: [r.metadata.get('execution_time_ms', 0) for r in results]
                for model_type, results in individual_results.items()
            },
            'average_validation_time_ms': (
                execution_time / total_validations if total_validations > 0 else 0
            ),
            'cache_hit_rate': len(self.validation_cache) / max(total_validations, 1),
            'performance_budget_utilization': execution_time / context.performance_budget_ms
        }

        # Identify cross-model issues
        cross_model_issues = []
        for error in cross_model_errors:
            cross_model_issues.append({
                'issue_type': error.error_type,
                'severity': error.severity.value,
                'affected_models': error.affected_models,
                'description': error.message
            })

        # Determine overall status
        if errors:
            overall_status = "failed"
        elif warnings:
            overall_status = "warning"
        elif failed_validations > 0:
            overall_status = "partial_success"
        else:
            overall_status = "success"

        return AggregatedValidationResult(
            request_id=context.request_id,
            overall_status=overall_status,
            total_validations=total_validations,
            successful_validations=successful_validations,
            failed_validations=failed_validations,
            errors=errors,
            warnings=warnings,
            performance_metrics=performance_metrics,
            cross_model_issues=cross_model_issues,
            recommendations=[],  # Will be filled by _generate_recommendations
            execution_time_ms=execution_time
        )

    async def _generate_recommendations(
        self,
        result: AggregatedValidationResult
    ) -> List[str]:
        """Generate actionable recommendations based on validation results."""
        recommendations = []

        # Performance recommendations
        if result.performance_metrics['performance_budget_utilization'] > 0.8:
            recommendations.append(
                "Consider optimizing validation performance - "
                "current execution time exceeds 80% of budget"
            )

        # Error-based recommendations
        error_types = [error.error_type for error in result.errors]

        if 'policy_principle_mismatch' in error_types:
            recommendations.append(
                "Review policy rules to ensure alignment with AC principles"
            )

        if 'incomplete_policy_coverage' in error_types:
            recommendations.append(
                "Create additional policy rules to cover all AC principles"
            )

        if 'safety_violation' in error_types:
            recommendations.append(
                "Critical: Review and fix safety violations in policy rules"
            )

        if 'regulatory_compliance_gap' in error_types:
            recommendations.append(
                "Address regulatory compliance gaps by creating appropriate policies"
            )

        # Success rate recommendations
        success_rate = (result.successful_validations /
                       max(result.total_validations, 1))

        if success_rate < 0.7:
            recommendations.append(
                f"Low validation success rate ({success_rate:.1%}) - "
                "review model quality and validation criteria"
            )

        # Cross-model issue recommendations
        if result.cross_model_issues:
            recommendations.append(
                "Address cross-model consistency issues to improve overall system coherence"
            )

        return recommendations


# Factory function for creating enhanced validator
def create_enhanced_multi_model_validator() -> EnhancedMultiModelValidator:
    """Create and configure an enhanced multi-model validator."""
    return EnhancedMultiModelValidator()


# Utility functions for validation context creation
def create_validation_context(
    request_id: str,
    models: Dict[str, Any],
    performance_budget_ms: int = 30000,
    max_concurrent_validations: int = 10,
    enable_caching: bool = True
) -> ValidationContext:
    """Create a validation context with default settings."""
    validator = create_enhanced_multi_model_validator()

    return ValidationContext(
        request_id=request_id,
        models=models,
        validation_rules=validator.cross_model_rules,
        performance_budget_ms=performance_budget_ms,
        max_concurrent_validations=max_concurrent_validations,
        enable_caching=enable_caching
    )
