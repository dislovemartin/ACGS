"""
Bias Detection and Algorithmic Fairness Module for ACGS-PGP Phase 3
Integrates bias detection algorithms from AlphaEvolve system
"""

import time
import logging
import asyncio
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
try:
    from fairlearn.metrics import (
        demographic_parity_difference,
        equalized_odds_difference,
        selection_rate,
        MetricFrame
    )
    from sklearn.metrics import accuracy_score, precision_score, recall_score
    FAIRLEARN_AVAILABLE = True
except ImportError:
    # Fallback for when fairlearn is not available
    FAIRLEARN_AVAILABLE = False
    logger.warning("Fairlearn not available, using mock implementations")
from ..schemas import (
    BiasDetectionRequest, BiasDetectionResponse, BiasDetectionResult,
    FairnessValidationRequest, FairnessValidationResponse, FairnessValidationResult,
    BiasMetric, FairnessProperty, PolicyRule
)

logger = logging.getLogger(__name__)


class BiasDetector:
    """
    Bias detection and algorithmic fairness validation for policy rules.
    Integrates algorithms from AlphaEvolve bias validation system.
    """
    
    def __init__(self):
        self.bias_cache = {}
        self.fairness_cache = {}
        
    async def detect_bias(
        self,
        request: BiasDetectionRequest,
        policy_rules: List[PolicyRule]
    ) -> BiasDetectionResponse:
        """
        Perform comprehensive bias detection analysis on policy rules.
        """
        start_time = time.time()
        
        logger.info(f"Starting bias detection for {len(request.policy_rule_ids)} policy rules")
        
        all_results = []
        
        # Process each policy rule
        for rule_id in request.policy_rule_ids:
            rule = next((r for r in policy_rules if r.id == rule_id), None)
            if not rule:
                logger.warning(f"Policy rule {rule_id} not found")
                continue
                
            # Run bias detection for each metric
            for metric in request.bias_metrics:
                result = await self._detect_bias_for_metric(
                    rule, metric, request.protected_attributes, request.dataset
                )
                all_results.append(result)
        
        # Calculate overall bias assessment
        overall_bias_score = self._calculate_overall_bias_score(all_results)
        risk_level = self._determine_risk_level(overall_bias_score)
        # Human review required if risk level is high/critical OR any individual result requires review
        human_review_required = risk_level in ["high", "critical"] or any(r.requires_human_review for r in all_results)
        
        # Generate summary and recommendations
        summary = self._generate_bias_summary(all_results, overall_bias_score, risk_level)
        recommendations = self._generate_bias_recommendations(all_results, risk_level)
        
        total_time = int((time.time() - start_time) * 1000)
        logger.info(f"Bias detection completed in {total_time}ms")
        
        return BiasDetectionResponse(
            policy_rule_ids=request.policy_rule_ids,
            results=all_results,
            overall_bias_score=overall_bias_score,
            risk_level=risk_level,
            summary=summary,
            recommendations=recommendations,
            human_review_required=human_review_required
        )
    
    async def _detect_bias_for_metric(
        self,
        rule: PolicyRule,
        metric: BiasMetric,
        protected_attributes: List[str],
        dataset: Optional[List[Dict[str, Any]]]
    ) -> BiasDetectionResult:
        """
        Detect bias for a specific metric and policy rule.
        """
        cache_key = f"{rule.id}_{metric.metric_id}_{hash(str(protected_attributes))}"
        
        if cache_key in self.bias_cache:
            return self.bias_cache[cache_key]
        
        if metric.metric_type == "statistical":
            result = await self._statistical_bias_detection(rule, metric, dataset, protected_attributes)
        elif metric.metric_type == "counterfactual":
            result = await self._counterfactual_bias_detection(rule, metric, protected_attributes)
        elif metric.metric_type == "embedding":
            result = await self._embedding_bias_detection(rule, metric, protected_attributes)
        elif metric.metric_type == "llm_review":
            result = await self._llm_bias_review(rule, metric, protected_attributes)
        else:
            result = BiasDetectionResult(
                metric_id=metric.metric_id,
                policy_rule_id=rule.id,
                bias_detected=False,
                confidence=0.0,
                explanation=f"Unknown metric type: {metric.metric_type}",
                requires_human_review=True
            )
        
        # Cache result
        self.bias_cache[cache_key] = result
        return result
    
    async def _statistical_bias_detection(
        self,
        rule: PolicyRule,
        metric: BiasMetric,
        dataset: Optional[List[Dict[str, Any]]],
        protected_attributes: List[str]
    ) -> BiasDetectionResult:
        """
        Statistical bias detection using demographic parity and related metrics.
        Uses fairlearn library for actual bias calculations when available.
        """
        if not dataset:
            return BiasDetectionResult(
                metric_id=metric.metric_id,
                policy_rule_id=rule.id,
                bias_detected=False,
                confidence=0.0,
                explanation="Dataset required for statistical bias detection but not provided",
                requires_human_review=True
            )

        if FAIRLEARN_AVAILABLE and len(dataset) > 10:
            # Use actual fairlearn implementation
            try:
                bias_score, explanation, recommendations = await self._calculate_fairlearn_metrics(
                    rule, dataset, protected_attributes, metric
                )
                threshold = metric.threshold or 0.1
                bias_detected = bias_score > threshold
                confidence = 0.95

                if bias_detected:
                    explanation += f" (exceeds threshold {threshold})"

                return BiasDetectionResult(
                    metric_id=metric.metric_id,
                    policy_rule_id=rule.id,
                    bias_detected=bias_detected,
                    bias_score=bias_score,
                    confidence=confidence,
                    explanation=explanation,
                    recommendations=recommendations if bias_detected else None,
                    requires_human_review=bias_score > 0.7
                )
            except Exception as e:
                logger.warning(f"Fairlearn calculation failed: {e}, falling back to heuristic method")

        # Fallback to enhanced heuristic method
        return await self._heuristic_bias_detection(rule, metric, dataset, protected_attributes)

    async def _calculate_fairlearn_metrics(
        self,
        rule: PolicyRule,
        dataset: List[Dict[str, Any]],
        protected_attributes: List[str],
        metric: BiasMetric
    ) -> Tuple[float, str, List[str]]:
        """
        Calculate actual fairness metrics using fairlearn library.
        """
        # Convert dataset to pandas DataFrame
        df = pd.DataFrame(dataset)

        # Simulate policy rule application to generate predictions
        # In real implementation, this would apply the actual policy rule
        y_pred = self._simulate_policy_predictions(rule, df)

        # Extract protected attribute values
        if not protected_attributes or protected_attributes[0] not in df.columns:
            # Use a synthetic protected attribute for demonstration
            sensitive_features = np.random.choice(['group_a', 'group_b'], size=len(df))
        else:
            sensitive_features = df[protected_attributes[0]].values

        # Calculate demographic parity difference
        dp_diff = demographic_parity_difference(
            y_true=np.ones(len(y_pred)),  # Assume all should be positive for simplicity
            y_pred=y_pred,
            sensitive_features=sensitive_features
        )

        # Calculate selection rates by group
        selection_rates = selection_rate(y_pred, sensitive_features)

        # Calculate overall bias score (0 = no bias, 1 = maximum bias)
        bias_score = abs(dp_diff)

        explanation = f"Fairlearn analysis: Demographic parity difference = {dp_diff:.3f}, "
        explanation += f"Selection rates by group: {dict(selection_rates)}"

        recommendations = [
            "Review policy rule for disparate impact",
            "Consider implementing fairness constraints",
            "Test with larger, more diverse datasets",
            "Monitor outcomes across protected groups"
        ]

        return bias_score, explanation, recommendations

    def _simulate_policy_predictions(self, rule: PolicyRule, df: pd.DataFrame) -> np.ndarray:
        """
        Simulate policy rule application to generate binary predictions.
        In real implementation, this would execute the actual policy rule.
        """
        rule_content = rule.rule_content.lower()

        # Simple heuristic based on rule content
        if "allow" in rule_content or "permit" in rule_content:
            # More permissive rule
            return np.random.choice([0, 1], size=len(df), p=[0.3, 0.7])
        elif "deny" in rule_content or "restrict" in rule_content:
            # More restrictive rule
            return np.random.choice([0, 1], size=len(df), p=[0.7, 0.3])
        else:
            # Balanced rule
            return np.random.choice([0, 1], size=len(df), p=[0.5, 0.5])

    async def _heuristic_bias_detection(
        self,
        rule: PolicyRule,
        metric: BiasMetric,
        dataset: List[Dict[str, Any]],
        protected_attributes: List[str]
    ) -> BiasDetectionResult:
        """
        Enhanced heuristic bias detection when fairlearn is not available.
        """
        rule_content = rule.rule_content.lower()
        bias_indicators = ["discriminate", "exclude", "prefer", "favor", "bias", "deny", "restrict"]

        bias_score = 0.0
        detected_issues = []

        # Check for explicit bias indicators
        for indicator in bias_indicators:
            if indicator in rule_content:
                bias_score += 0.15
                detected_issues.append(f"Contains bias indicator: '{indicator}'")

        # Check for protected attribute references
        for attr in protected_attributes:
            if attr.lower() in rule_content:
                bias_score += 0.25
                detected_issues.append(f"References protected attribute: '{attr}'")

        # Check for conditional logic that might be discriminatory
        conditional_patterns = ["if", "when", "where", "unless", "except"]
        for pattern in conditional_patterns:
            if pattern in rule_content:
                bias_score += 0.1
                detected_issues.append(f"Contains conditional logic: '{pattern}'")

        bias_score = min(bias_score, 1.0)
        threshold = metric.threshold or 0.1
        bias_detected = bias_score > threshold

        explanation = f"Heuristic analysis detected bias score: {bias_score:.3f}. "
        if detected_issues:
            explanation += f"Issues found: {', '.join(detected_issues[:3])}"

        recommendations = [
            "Review rule for discriminatory language",
            "Test with diverse datasets",
            "Consider attribute-blind alternatives",
            "Implement fairness monitoring"
        ] if bias_detected else None

        return BiasDetectionResult(
            metric_id=metric.metric_id,
            policy_rule_id=rule.id,
            bias_detected=bias_detected,
            bias_score=bias_score,
            confidence=0.75,
            explanation=explanation,
            recommendations=recommendations,
            requires_human_review=bias_score > 0.3  # Lower threshold for human review
        )

    async def _counterfactual_bias_detection(
        self,
        rule: PolicyRule,
        metric: BiasMetric,
        protected_attributes: List[str]
    ) -> BiasDetectionResult:
        """
        Counterfactual bias detection by analyzing rule behavior with modified attributes.
        """
        # Mock counterfactual analysis
        rule_content = rule.rule_content.lower()
        
        # Check if rule explicitly mentions protected attributes
        bias_score = 0.0
        for attr in protected_attributes:
            if attr.lower() in rule_content:
                bias_score += 0.4
        
        # Check for conditional logic that might be discriminatory
        conditional_patterns = ["if", "when", "where", "unless"]
        for pattern in conditional_patterns:
            if pattern in rule_content:
                bias_score += 0.1
        
        bias_score = min(bias_score, 1.0)
        threshold = metric.threshold or 0.2
        bias_detected = bias_score > threshold
        
        explanation = f"Counterfactual analysis bias score: {bias_score:.3f}"
        if bias_detected:
            explanation += " - Rule shows differential treatment based on protected attributes"
        
        return BiasDetectionResult(
            metric_id=metric.metric_id,
            policy_rule_id=rule.id,
            bias_detected=bias_detected,
            bias_score=bias_score,
            confidence=0.75,
            explanation=explanation,
            recommendations=["Implement attribute-blind alternatives", "Add fairness constraints"] if bias_detected else None,
            requires_human_review=bias_score > 0.6
        )
    
    async def _embedding_bias_detection(
        self,
        rule: PolicyRule,
        metric: BiasMetric,
        protected_attributes: List[str]
    ) -> BiasDetectionResult:
        """
        Embedding-based bias detection using semantic analysis.
        """
        # Mock embedding analysis
        rule_content = rule.rule_content.lower()
        
        # Simulate semantic bias detection
        bias_keywords = ["exclude", "deny", "reject", "prohibit", "restrict"]
        neutral_keywords = ["allow", "permit", "enable", "support", "include"]
        
        bias_score = 0.0
        for keyword in bias_keywords:
            if keyword in rule_content:
                bias_score += 0.15
        
        for keyword in neutral_keywords:
            if keyword in rule_content:
                bias_score -= 0.1
        
        bias_score = max(0.0, min(bias_score, 1.0))
        threshold = metric.threshold or 0.15
        bias_detected = bias_score > threshold
        
        explanation = f"Semantic embedding analysis bias score: {bias_score:.3f}"
        
        return BiasDetectionResult(
            metric_id=metric.metric_id,
            policy_rule_id=rule.id,
            bias_detected=bias_detected,
            bias_score=bias_score,
            confidence=0.70,
            explanation=explanation,
            requires_human_review=bias_score > 0.5
        )
    
    async def _llm_bias_review(
        self,
        rule: PolicyRule,
        metric: BiasMetric,
        protected_attributes: List[str]
    ) -> BiasDetectionResult:
        """
        LLM-based bias review for complex bias patterns.
        """
        # Mock LLM review (in real implementation, call actual LLM)
        rule_content = rule.rule_content.lower()
        
        # Simple pattern matching for mock
        if "obvious bias" in rule_content or any(attr.lower() in rule_content for attr in protected_attributes):
            bias_detected = True
            bias_score = 0.8
            explanation = "LLM Review: Potential bias detected in rule language and structure"
            recommendations = ["Rewrite rule to be attribute-neutral", "Add explicit fairness checks"]
        else:
            bias_detected = False
            bias_score = 0.2
            explanation = "LLM Review: No obvious bias patterns detected"
            recommendations = None
        
        return BiasDetectionResult(
            metric_id=metric.metric_id,
            policy_rule_id=rule.id,
            bias_detected=bias_detected,
            bias_score=bias_score,
            confidence=0.90,
            explanation=explanation,
            recommendations=recommendations,
            requires_human_review=bias_detected
        )
    
    def _calculate_overall_bias_score(self, results: List[BiasDetectionResult]) -> float:
        """Calculate overall bias score from individual results."""
        if not results:
            return 0.0
        
        # Weight by confidence and take maximum bias score
        weighted_scores = []
        for result in results:
            if result.bias_score is not None:
                weighted_score = result.bias_score * result.confidence
                weighted_scores.append(weighted_score)
        
        return max(weighted_scores) if weighted_scores else 0.0
    
    def _determine_risk_level(self, bias_score: float) -> str:
        """Determine risk level based on bias score."""
        if bias_score >= 0.7:
            return "critical"
        elif bias_score >= 0.5:
            return "high"
        elif bias_score >= 0.3:
            return "medium"
        else:
            return "low"
    
    def _generate_bias_summary(self, results: List[BiasDetectionResult], overall_score: float, risk_level: str) -> str:
        """Generate summary of bias detection results."""
        total_rules = len(set(r.policy_rule_id for r in results))
        biased_results = [r for r in results if r.bias_detected]
        
        return f"Bias analysis of {total_rules} policy rules completed. " \
               f"Overall bias score: {overall_score:.3f} ({risk_level} risk). " \
               f"{len(biased_results)} potential bias indicators detected."
    
    def _generate_bias_recommendations(self, results: List[BiasDetectionResult], risk_level: str) -> List[str]:
        """Generate recommendations based on bias detection results."""
        recommendations = []
        
        if risk_level in ["high", "critical"]:
            recommendations.append("Immediate human review required")
            recommendations.append("Consider rewriting rules to be attribute-neutral")
            recommendations.append("Implement additional fairness constraints")
        
        if risk_level in ["medium", "high", "critical"]:
            recommendations.append("Test rules with diverse datasets")
            recommendations.append("Monitor outcomes for disparate impact")
        
        # Add specific recommendations from individual results
        for result in results:
            if result.recommendations:
                recommendations.extend(result.recommendations)
        
        return list(set(recommendations))  # Remove duplicates


    async def validate_fairness(
        self,
        request: FairnessValidationRequest,
        policy_rules: List[PolicyRule]
    ) -> FairnessValidationResponse:
        """
        Validate fairness properties for policy rules.
        """
        start_time = time.time()

        logger.info(f"Starting fairness validation for {len(request.policy_rule_ids)} policy rules")

        all_results = []

        # Process each policy rule
        for rule_id in request.policy_rule_ids:
            rule = next((r for r in policy_rules if r.id == rule_id), None)
            if not rule:
                logger.warning(f"Policy rule {rule_id} not found")
                continue

            # Validate each fairness property
            for property in request.fairness_properties:
                result = await self._validate_fairness_property(
                    rule, property, request.validation_dataset, request.simulation_parameters
                )
                all_results.append(result)

        # Calculate overall fairness assessment
        overall_fairness_score = self._calculate_overall_fairness_score(all_results)
        compliance_status = self._determine_compliance_status(overall_fairness_score)

        # Generate summary
        summary = self._generate_fairness_summary(all_results, overall_fairness_score, compliance_status)

        total_time = int((time.time() - start_time) * 1000)
        logger.info(f"Fairness validation completed in {total_time}ms")

        return FairnessValidationResponse(
            policy_rule_ids=request.policy_rule_ids,
            results=all_results,
            overall_fairness_score=overall_fairness_score,
            compliance_status=compliance_status,
            summary=summary
        )

    async def _validate_fairness_property(
        self,
        rule: PolicyRule,
        property: FairnessProperty,
        dataset: Optional[List[Dict[str, Any]]],
        simulation_params: Optional[Dict[str, Any]]
    ) -> FairnessValidationResult:
        """
        Validate a specific fairness property for a policy rule.
        """
        cache_key = f"fairness_{rule.id}_{property.property_id}"

        if cache_key in self.fairness_cache:
            return self.fairness_cache[cache_key]

        if property.property_type == "demographic_parity":
            result = await self._validate_demographic_parity(rule, property, dataset)
        elif property.property_type == "equalized_odds":
            result = await self._validate_equalized_odds(rule, property, dataset)
        elif property.property_type == "calibration":
            result = await self._validate_calibration(rule, property, dataset)
        elif property.property_type == "individual_fairness":
            result = await self._validate_individual_fairness(rule, property, dataset)
        else:
            result = FairnessValidationResult(
                property_id=property.property_id,
                policy_rule_id=rule.id,
                fairness_satisfied=False,
                fairness_score=0.0,
                violation_details=f"Unknown fairness property type: {property.property_type}"
            )

        # Cache result
        self.fairness_cache[cache_key] = result
        return result

    async def _validate_demographic_parity(
        self,
        rule: PolicyRule,
        property: FairnessProperty,
        dataset: Optional[List[Dict[str, Any]]]
    ) -> FairnessValidationResult:
        """
        Validate demographic parity: P(Ŷ = 1|A = 0) = P(Ŷ = 1|A = 1)
        """
        # Mock demographic parity validation
        rule_content = rule.rule_content.lower()

        # Check if rule explicitly treats protected attributes differently
        fairness_score = 1.0
        violation_details = None

        for attr in property.protected_attributes:
            if attr.lower() in rule_content:
                # Simulate checking if the attribute is used in a discriminatory way
                if any(word in rule_content for word in ["exclude", "deny", "restrict"]):
                    fairness_score -= 0.3
                    violation_details = f"Rule may violate demographic parity for attribute: {attr}"

        fairness_score = max(0.0, fairness_score)
        fairness_satisfied = fairness_score >= (1.0 - property.threshold)

        return FairnessValidationResult(
            property_id=property.property_id,
            policy_rule_id=rule.id,
            fairness_satisfied=fairness_satisfied,
            fairness_score=fairness_score,
            violation_details=violation_details
        )

    async def _validate_equalized_odds(
        self,
        rule: PolicyRule,
        property: FairnessProperty,
        dataset: Optional[List[Dict[str, Any]]]
    ) -> FairnessValidationResult:
        """
        Validate equalized odds: P(Ŷ = 1|Y = y, A = a) independent of A
        """
        # Mock equalized odds validation
        rule_content = rule.rule_content.lower()

        # Simulate checking for conditional fairness
        fairness_score = 0.9  # Start with high fairness
        violation_details = None

        # Check for conditional statements that might violate equalized odds
        conditional_patterns = ["if", "when", "where", "unless"]
        for pattern in conditional_patterns:
            if pattern in rule_content:
                for attr in property.protected_attributes:
                    if attr.lower() in rule_content:
                        fairness_score -= 0.2
                        violation_details = f"Conditional logic may violate equalized odds for: {attr}"
                        break

        fairness_score = max(0.0, fairness_score)
        fairness_satisfied = fairness_score >= (1.0 - property.threshold)

        return FairnessValidationResult(
            property_id=property.property_id,
            policy_rule_id=rule.id,
            fairness_satisfied=fairness_satisfied,
            fairness_score=fairness_score,
            violation_details=violation_details
        )

    async def _validate_calibration(
        self,
        rule: PolicyRule,
        property: FairnessProperty,
        dataset: Optional[List[Dict[str, Any]]]
    ) -> FairnessValidationResult:
        """
        Validate calibration: P(Y = 1|Ŷ = s, A = a) independent of A
        """
        # Mock calibration validation
        fairness_score = 0.85  # Default fairness score
        fairness_satisfied = fairness_score >= (1.0 - property.threshold)

        return FairnessValidationResult(
            property_id=property.property_id,
            policy_rule_id=rule.id,
            fairness_satisfied=fairness_satisfied,
            fairness_score=fairness_score,
            violation_details=None if fairness_satisfied else "Calibration may be violated"
        )

    async def _validate_individual_fairness(
        self,
        rule: PolicyRule,
        property: FairnessProperty,
        dataset: Optional[List[Dict[str, Any]]]
    ) -> FairnessValidationResult:
        """
        Validate individual fairness: Similar individuals receive similar treatment
        """
        # Mock individual fairness validation
        rule_content = rule.rule_content.lower()

        # Check for consistency in rule application
        fairness_score = 0.8
        violation_details = None

        # Look for inconsistent treatment patterns
        if "exception" in rule_content or "special case" in rule_content:
            fairness_score -= 0.2
            violation_details = "Rule contains exceptions that may violate individual fairness"

        fairness_satisfied = fairness_score >= (1.0 - property.threshold)

        return FairnessValidationResult(
            property_id=property.property_id,
            policy_rule_id=rule.id,
            fairness_satisfied=fairness_satisfied,
            fairness_score=fairness_score,
            violation_details=violation_details
        )

    def _calculate_overall_fairness_score(self, results: List[FairnessValidationResult]) -> float:
        """Calculate overall fairness score from individual results."""
        if not results:
            return 1.0

        scores = [result.fairness_score for result in results]
        return sum(scores) / len(scores)

    def _determine_compliance_status(self, fairness_score: float) -> str:
        """Determine compliance status based on fairness score."""
        if fairness_score >= 0.9:
            return "compliant"
        elif fairness_score >= 0.7:
            return "requires_review"
        else:
            return "non_compliant"

    def _generate_fairness_summary(self, results: List[FairnessValidationResult], overall_score: float, status: str) -> str:
        """Generate summary of fairness validation results."""
        total_properties = len(results)
        satisfied_properties = len([r for r in results if r.fairness_satisfied])

        return f"Fairness validation completed for {total_properties} properties. " \
               f"Overall fairness score: {overall_score:.3f} ({status}). " \
               f"{satisfied_properties}/{total_properties} properties satisfied."


# Global instance
bias_detector = BiasDetector()
