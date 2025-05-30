#!/usr/bin/env python3
"""
Enhanced validation algorithms for AlphaEvolve-ACGS policy synthesis and enforcement.
Implements multi-tier validation, adaptive thresholds, and formal verification integration.
"""

import numpy as np
import re
import ast
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import hashlib
import json

class ValidationLevel(Enum):
    SYNTAX = "syntax"
    SEMANTIC = "semantic"
    FORMAL = "formal"
    EMPIRICAL = "empirical"

@dataclass
class ValidationResult:
    level: ValidationLevel
    score: float
    confidence: float
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]

class EnhancedPolicyValidator:
    """Enhanced multi-tier validation for LLM-generated policies."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()
        self.validation_history = []
        
    def _default_config(self) -> Dict[str, Any]:
        return {
            "syntax_weight": 0.3,
            "semantic_weight": 0.4,
            "formal_weight": 0.2,
            "empirical_weight": 0.1,
            "min_confidence": 0.85,
            "adaptive_thresholds": True,
            "formal_verification_enabled": False
        }
    
    def validate_policy(self, policy_text: str, principle: Dict[str, Any]) -> ValidationResult:
        """
        Comprehensive multi-tier policy validation.
        
        Args:
            policy_text: Generated Rego policy text
            principle: Constitutional principle specification
            
        Returns:
            ValidationResult with aggregated scores and diagnostics
        """
        results = []
        
        # Tier 1: Syntax Validation
        syntax_result = self._validate_syntax(policy_text)
        results.append(syntax_result)
        
        # Tier 2: Semantic Validation
        semantic_result = self._validate_semantic_alignment(policy_text, principle)
        results.append(semantic_result)
        
        # Tier 3: Formal Verification (if enabled)
        if self.config["formal_verification_enabled"]:
            formal_result = self._validate_formal_properties(policy_text, principle)
            results.append(formal_result)
        
        # Tier 4: Empirical Validation
        empirical_result = self._validate_empirical_behavior(policy_text, principle)
        results.append(empirical_result)
        
        # Aggregate results
        return self._aggregate_validation_results(results)
    
    def _validate_syntax(self, policy_text: str) -> ValidationResult:
        """Validate Rego syntax and structure."""
        errors = []
        warnings = []
        score = 1.0
        
        # Check basic Rego structure
        if not re.search(r'package\s+\w+', policy_text):
            errors.append("Missing package declaration")
            score -= 0.3
            
        # Check for rule definitions
        if not re.search(r'(allow|deny)\s*\[.*?\]\s*\{', policy_text):
            errors.append("No valid rule definitions found")
            score -= 0.4
            
        # Check for proper variable usage
        undefined_vars = self._check_undefined_variables(policy_text)
        if undefined_vars:
            warnings.extend([f"Potentially undefined variable: {var}" for var in undefined_vars])
            score -= 0.1 * len(undefined_vars)
        
        # Check for syntax patterns
        if re.search(r'\{[^}]*\{', policy_text):
            warnings.append("Nested braces detected - check syntax")
            score -= 0.05
            
        return ValidationResult(
            level=ValidationLevel.SYNTAX,
            score=max(0.0, score),
            confidence=0.95 if not errors else 0.7,
            errors=errors,
            warnings=warnings,
            metadata={"line_count": len(policy_text.split('\n'))}
        )
    
    def _validate_semantic_alignment(self, policy_text: str, principle: Dict[str, Any]) -> ValidationResult:
        """Validate semantic alignment with constitutional principle."""
        errors = []
        warnings = []
        score = 0.0
        
        principle_keywords = self._extract_principle_keywords(principle)
        policy_concepts = self._extract_policy_concepts(policy_text)
        
        # Calculate semantic overlap
        overlap = len(set(principle_keywords) & set(policy_concepts))
        total_keywords = len(principle_keywords)
        
        if total_keywords > 0:
            score = overlap / total_keywords
        
        # Check for intent preservation
        intent_score = self._check_intent_preservation(policy_text, principle)
        score = (score + intent_score) / 2
        
        # Validate logical consistency
        consistency_issues = self._check_logical_consistency(policy_text)
        if consistency_issues:
            errors.extend(consistency_issues)
            score *= 0.8
        
        # Check for completeness
        completeness_score = self._check_completeness(policy_text, principle)
        score = (score + completeness_score) / 2
        
        return ValidationResult(
            level=ValidationLevel.SEMANTIC,
            score=score,
            confidence=0.8,
            errors=errors,
            warnings=warnings,
            metadata={
                "keyword_overlap": overlap,
                "total_keywords": total_keywords,
                "intent_score": intent_score,
                "completeness_score": completeness_score
            }
        )
    
    def _validate_formal_properties(self, policy_text: str, principle: Dict[str, Any]) -> ValidationResult:
        """Formal verification using SMT solvers (placeholder for Z3 integration)."""
        # This would integrate with Z3 or other SMT solvers
        # For now, implement basic formal property checking
        
        errors = []
        warnings = []
        score = 0.8  # Placeholder score
        
        # Check for safety properties
        safety_properties = self._extract_safety_properties(principle)
        verified_properties = []
        
        for prop in safety_properties:
            if self._verify_safety_property(policy_text, prop):
                verified_properties.append(prop)
        
        if safety_properties:
            score = len(verified_properties) / len(safety_properties)
        
        return ValidationResult(
            level=ValidationLevel.FORMAL,
            score=score,
            confidence=0.9,
            errors=errors,
            warnings=warnings,
            metadata={
                "safety_properties": safety_properties,
                "verified_properties": verified_properties
            }
        )
    
    def _validate_empirical_behavior(self, policy_text: str, principle: Dict[str, Any]) -> ValidationResult:
        """Validate policy behavior through empirical testing."""
        errors = []
        warnings = []
        
        # Generate test cases
        test_cases = self._generate_test_cases(principle)
        
        # Simulate policy execution
        passed_tests = 0
        for test_case in test_cases:
            if self._simulate_policy_execution(policy_text, test_case):
                passed_tests += 1
        
        score = passed_tests / len(test_cases) if test_cases else 0.0
        
        return ValidationResult(
            level=ValidationLevel.EMPIRICAL,
            score=score,
            confidence=0.75,
            errors=errors,
            warnings=warnings,
            metadata={
                "total_tests": len(test_cases),
                "passed_tests": passed_tests
            }
        )
    
    def _aggregate_validation_results(self, results: List[ValidationResult]) -> ValidationResult:
        """Aggregate multi-tier validation results."""
        weights = {
            ValidationLevel.SYNTAX: self.config["syntax_weight"],
            ValidationLevel.SEMANTIC: self.config["semantic_weight"],
            ValidationLevel.FORMAL: self.config["formal_weight"],
            ValidationLevel.EMPIRICAL: self.config["empirical_weight"]
        }
        
        total_score = 0.0
        total_weight = 0.0
        all_errors = []
        all_warnings = []
        metadata = {}
        
        for result in results:
            weight = weights.get(result.level, 0.0)
            total_score += result.score * weight
            total_weight += weight
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
            metadata[f"{result.level.value}_result"] = {
                "score": result.score,
                "confidence": result.confidence,
                "metadata": result.metadata
            }
        
        final_score = total_score / total_weight if total_weight > 0 else 0.0
        
        # Calculate overall confidence
        confidences = [r.confidence for r in results]
        overall_confidence = np.mean(confidences) if confidences else 0.0
        
        return ValidationResult(
            level=ValidationLevel.EMPIRICAL,  # Represents aggregated result
            score=final_score,
            confidence=overall_confidence,
            errors=all_errors,
            warnings=all_warnings,
            metadata=metadata
        )
    
    # Helper methods (simplified implementations)
    
    def _check_undefined_variables(self, policy_text: str) -> List[str]:
        """Check for potentially undefined variables."""
        # Simplified implementation
        variables = re.findall(r'\b[a-z_][a-z0-9_]*\b', policy_text)
        defined_vars = set(re.findall(r'(\w+)\s*:=', policy_text))
        return list(set(variables) - defined_vars - {'input', 'data', 'allow', 'deny'})
    
    def _extract_principle_keywords(self, principle: Dict[str, Any]) -> List[str]:
        """Extract keywords from constitutional principle."""
        text = principle.get('description', '') + ' ' + principle.get('rationale', '')
        return re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    
    def _extract_policy_concepts(self, policy_text: str) -> List[str]:
        """Extract conceptual terms from policy text."""
        # Remove Rego syntax and extract meaningful terms
        cleaned = re.sub(r'[{}()\[\];:=]', ' ', policy_text)
        return re.findall(r'\b[a-zA-Z]{3,}\b', cleaned.lower())
    
    def _check_intent_preservation(self, policy_text: str, principle: Dict[str, Any]) -> float:
        """Check if policy preserves principle intent."""
        # Simplified semantic similarity check
        return 0.8  # Placeholder
    
    def _check_logical_consistency(self, policy_text: str) -> List[str]:
        """Check for logical inconsistencies."""
        issues = []
        # Check for contradictory rules
        if 'allow' in policy_text and 'deny' in policy_text:
            # More sophisticated analysis needed
            pass
        return issues
    
    def _check_completeness(self, policy_text: str, principle: Dict[str, Any]) -> float:
        """Check policy completeness against principle requirements."""
        return 0.75  # Placeholder
    
    def _extract_safety_properties(self, principle: Dict[str, Any]) -> List[str]:
        """Extract formal safety properties from principle."""
        return principle.get('safety_properties', [])
    
    def _verify_safety_property(self, policy_text: str, property_spec: str) -> bool:
        """Verify a safety property (placeholder for SMT integration)."""
        return True  # Placeholder
    
    def _generate_test_cases(self, principle: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate empirical test cases."""
        return [{"test": "placeholder"}]  # Placeholder
    
    def _simulate_policy_execution(self, policy_text: str, test_case: Dict[str, Any]) -> bool:
        """Simulate policy execution on test case."""
        return True  # Placeholder

class AdaptiveThresholdManager:
    """Manages adaptive thresholds based on system performance and context."""
    
    def __init__(self, base_threshold: float = 0.85):
        self.base_threshold = base_threshold
        self.performance_history = []
        self.context_factors = {}
    
    def calculate_adaptive_threshold(self, 
                                   historical_performance: List[float],
                                   current_context: Dict[str, Any]) -> float:
        """
        Calculate adaptive threshold based on historical performance and current context.
        
        Args:
            historical_performance: List of recent performance scores
            current_context: Current system context (risk level, domain, etc.)
            
        Returns:
            Adjusted threshold value
        """
        # Calculate performance trend
        performance_factor = self._calculate_performance_factor(historical_performance)
        
        # Assess context risk
        context_factor = self._assess_context_risk(current_context)
        
        # Apply domain-specific adjustments
        domain_factor = self._get_domain_factor(current_context.get('domain', 'general'))
        
        # Calculate final threshold
        adjusted_threshold = (self.base_threshold * 
                            performance_factor * 
                            context_factor * 
                            domain_factor)
        
        # Ensure threshold stays within reasonable bounds
        return max(0.5, min(0.95, adjusted_threshold))
    
    def _calculate_performance_factor(self, performance_history: List[float]) -> float:
        """Calculate performance trend factor."""
        if len(performance_history) < 2:
            return 1.0
            
        recent_avg = np.mean(performance_history[-5:])
        overall_avg = np.mean(performance_history)
        
        if recent_avg > overall_avg:
            return 0.95  # Lower threshold if performing well
        else:
            return 1.05  # Raise threshold if performance declining
    
    def _assess_context_risk(self, context: Dict[str, Any]) -> float:
        """Assess risk level from current context."""
        risk_level = context.get('risk_level', 'medium')
        
        risk_factors = {
            'low': 0.95,
            'medium': 1.0,
            'high': 1.1,
            'critical': 1.2
        }
        
        return risk_factors.get(risk_level, 1.0)
    
    def _get_domain_factor(self, domain: str) -> float:
        """Get domain-specific threshold adjustment."""
        domain_factors = {
            'safety_critical': 1.15,
            'financial': 1.1,
            'healthcare': 1.15,
            'general': 1.0,
            'research': 0.95
        }
        
        return domain_factors.get(domain, 1.0)

class IntersectionalBiasDetectionEngine:
    """
    Enhanced bias detection engine that analyzes intersectional bias
    across multiple protected attributes and temporal evolution.
    """

    def __init__(self):
        self.protected_attributes = ['race', 'gender', 'age', 'disability', 'religion']
        self.fairness_metrics = ['demographic_parity', 'equalized_odds', 'predictive_parity']
        self.bias_history = []

    def detect_bias(self, policy_text: str, principle: Dict[str, Any],
                   threshold: float = 0.7) -> ValidationResult:
        """
        Comprehensive bias detection including intersectional analysis.

        Args:
            policy_text: Generated Rego policy code
            principle: Constitutional principle specification
            threshold: Bias detection threshold

        Returns:
            ValidationResult with bias analysis
        """
        errors = []
        warnings = []
        bias_score = 1.0  # Start with no bias detected

        # Individual attribute bias analysis
        individual_bias = self._analyze_individual_bias(policy_text, principle)

        # Intersectional bias analysis
        intersectional_bias = self._analyze_intersectional_bias(policy_text, principle)

        # Temporal bias evolution analysis
        temporal_bias = self._analyze_temporal_bias_evolution(policy_text, principle)

        # Counterfactual fairness analysis
        counterfactual_bias = self._analyze_counterfactual_fairness(policy_text, principle)

        # Aggregate bias scores
        bias_components = {
            'individual': individual_bias,
            'intersectional': intersectional_bias,
            'temporal': temporal_bias,
            'counterfactual': counterfactual_bias
        }

        # Calculate weighted bias score
        weights = {'individual': 0.3, 'intersectional': 0.4, 'temporal': 0.2, 'counterfactual': 0.1}
        bias_score = sum(weights[k] * v for k, v in bias_components.items())

        # Generate warnings and errors based on bias levels
        if bias_score < threshold:
            if intersectional_bias < 0.6:
                errors.append("Significant intersectional bias detected")
            if temporal_bias < 0.7:
                warnings.append("Potential temporal bias evolution detected")
            if counterfactual_bias < 0.8:
                warnings.append("Counterfactual fairness concerns identified")

        return ValidationResult(
            level=ValidationLevel.SEMANTIC,  # Bias is part of semantic validation
            score=bias_score,
            confidence=0.85,
            errors=errors,
            warnings=warnings,
            metadata={
                'bias_components': bias_components,
                'protected_attributes_analyzed': self.protected_attributes,
                'fairness_metrics_used': self.fairness_metrics
            }
        )

    def _analyze_individual_bias(self, policy_text: str, principle: Dict[str, Any]) -> float:
        """Analyze bias for individual protected attributes."""
        # Simplified implementation - would use actual fairness metrics
        bias_indicators = []

        for attribute in self.protected_attributes:
            if attribute.lower() in policy_text.lower():
                # Check if attribute is used in discriminatory context
                bias_indicators.append(self._check_discriminatory_usage(policy_text, attribute))

        return 1.0 - (sum(bias_indicators) / len(self.protected_attributes))

    def _analyze_intersectional_bias(self, policy_text: str, principle: Dict[str, Any]) -> float:
        """Analyze bias across intersections of protected attributes."""
        intersectional_scores = []

        # Check all pairs of protected attributes
        for i, attr1 in enumerate(self.protected_attributes):
            for attr2 in self.protected_attributes[i+1:]:
                intersection_score = self._check_intersection_bias(policy_text, attr1, attr2)
                intersectional_scores.append(intersection_score)

        return np.mean(intersectional_scores) if intersectional_scores else 1.0

    def _analyze_temporal_bias_evolution(self, policy_text: str, principle: Dict[str, Any]) -> float:
        """Analyze how bias might evolve over time in evolutionary systems."""
        # Check if policy has temporal components that could lead to bias drift
        temporal_keywords = ['generation', 'evolution', 'time', 'iteration', 'adaptive']

        has_temporal_component = any(keyword in policy_text.lower() for keyword in temporal_keywords)

        if has_temporal_component:
            # Analyze potential for bias amplification over time
            return self._assess_bias_amplification_risk(policy_text)

        return 1.0  # No temporal bias risk if no temporal components

    def _analyze_counterfactual_fairness(self, policy_text: str, principle: Dict[str, Any]) -> float:
        """Analyze counterfactual fairness - would decisions change if protected attributes were different."""
        # Simplified implementation - would require causal analysis
        causal_keywords = ['because', 'due to', 'caused by', 'results from']

        has_causal_language = any(keyword in policy_text.lower() for keyword in causal_keywords)

        if has_causal_language:
            return self._assess_causal_fairness(policy_text)

        return 0.9  # Slight concern if no explicit causal reasoning

    def _check_discriminatory_usage(self, policy_text: str, attribute: str) -> float:
        """Check if protected attribute is used in potentially discriminatory way."""
        # Simplified heuristic - would use more sophisticated NLP
        discriminatory_patterns = [
            f"{attribute} == ",
            f"{attribute} != ",
            f"not {attribute}",
            f"exclude {attribute}"
        ]

        for pattern in discriminatory_patterns:
            if pattern in policy_text.lower():
                return 0.8  # High bias indicator

        return 0.0  # No obvious discriminatory usage

    def _check_intersection_bias(self, policy_text: str, attr1: str, attr2: str) -> float:
        """Check for bias at intersection of two protected attributes."""
        # Look for compound conditions involving both attributes
        intersection_patterns = [
            f"{attr1}.*{attr2}",
            f"{attr2}.*{attr1}",
            f"({attr1}.*and.*{attr2})",
            f"({attr2}.*and.*{attr1})"
        ]

        for pattern in intersection_patterns:
            if re.search(pattern, policy_text.lower()):
                return 0.7  # Potential intersectional bias

        return 1.0  # No intersectional bias detected

    def _assess_bias_amplification_risk(self, policy_text: str) -> float:
        """Assess risk of bias amplification over evolutionary generations."""
        # Check for feedback loops that could amplify bias
        amplification_indicators = [
            'feedback',
            'reinforcement',
            'accumulate',
            'compound',
            'amplify'
        ]

        risk_score = sum(1 for indicator in amplification_indicators
                        if indicator in policy_text.lower())

        return max(0.3, 1.0 - (risk_score * 0.2))

    def _assess_causal_fairness(self, policy_text: str) -> float:
        """Assess causal fairness in policy decisions."""
        # Simplified assessment - would require causal graph analysis
        return 0.8  # Placeholder for sophisticated causal analysis

# Example usage and testing
if __name__ == "__main__":
    # Example policy validation
    validator = EnhancedPolicyValidator()
    
    sample_policy = """
    package alphaevolve.safety
    
    deny[msg] {
        input.solution.risk_score > 0.8
        msg := "Solution exceeds safety risk threshold"
    }
    """
    
    sample_principle = {
        "id": "SAFETY-001",
        "description": "Ensure all solutions maintain safety risk below threshold",
        "rationale": "Safety is paramount in evolutionary computation",
        "safety_properties": ["risk_score <= 0.8"]
    }
    
    result = validator.validate_policy(sample_policy, sample_principle)
    print(f"Validation Score: {result.score:.3f}")
    print(f"Confidence: {result.confidence:.3f}")
    print(f"Errors: {result.errors}")
    print(f"Warnings: {result.warnings}")
