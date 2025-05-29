"""
Fairness Evaluation Framework

This module addresses the technical review finding about meaningless fairness
claims in domains without protected attributes, and provides proper fairness
evaluation for appropriate domains.
"""

import logging
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)


class DomainType(Enum):
    """Types of evaluation domains."""
    ARITHMETIC = "arithmetic"
    HIRING = "hiring"
    LENDING = "lending"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    CRIMINAL_JUSTICE = "criminal_justice"


@dataclass
class ProtectedAttribute:
    """Definition of a protected attribute for fairness evaluation."""
    name: str
    values: List[str]
    is_binary: bool
    description: str


@dataclass
class FairnessMetric:
    """A fairness metric with its calculation and interpretation."""
    name: str
    value: float
    interpretation: str
    threshold: float
    is_satisfied: bool
    calculation_method: str


@dataclass
class DomainFairnessConfig:
    """Configuration for fairness evaluation in a specific domain."""
    domain_type: DomainType
    has_protected_attributes: bool
    protected_attributes: List[ProtectedAttribute]
    applicable_metrics: List[str]
    fairness_thresholds: Dict[str, float]
    rationale: str


class FairnessEvaluationFramework:
    """Framework for evaluating fairness in different domains."""
    
    def __init__(self):
        self.domain_configs = self._initialize_domain_configs()
    
    def _initialize_domain_configs(self) -> Dict[DomainType, DomainFairnessConfig]:
        """Initialize fairness configurations for different domains."""
        return {
            DomainType.ARITHMETIC: DomainFairnessConfig(
                domain_type=DomainType.ARITHMETIC,
                has_protected_attributes=False,
                protected_attributes=[],
                applicable_metrics=[],
                fairness_thresholds={},
                rationale="Arithmetic expressions have no protected attributes; fairness evaluation is not applicable"
            ),
            
            DomainType.HIRING: DomainFairnessConfig(
                domain_type=DomainType.HIRING,
                has_protected_attributes=True,
                protected_attributes=[
                    ProtectedAttribute("gender", ["male", "female", "non-binary"], False, "Gender identity"),
                    ProtectedAttribute("race", ["white", "black", "hispanic", "asian", "other"], False, "Racial/ethnic background"),
                    ProtectedAttribute("age_group", ["young", "middle", "senior"], False, "Age category"),
                    ProtectedAttribute("disability", ["yes", "no"], True, "Disability status")
                ],
                applicable_metrics=["demographic_parity", "equalized_odds", "calibration"],
                fairness_thresholds={
                    "demographic_parity": 0.1,  # Max 10% difference in selection rates
                    "equalized_odds": 0.1,      # Max 10% difference in TPR/FPR
                    "calibration": 0.05          # Max 5% difference in calibration
                },
                rationale="Hiring decisions must be fair across protected demographic groups"
            ),
            
            DomainType.LENDING: DomainFairnessConfig(
                domain_type=DomainType.LENDING,
                has_protected_attributes=True,
                protected_attributes=[
                    ProtectedAttribute("race", ["white", "black", "hispanic", "asian", "other"], False, "Racial/ethnic background"),
                    ProtectedAttribute("gender", ["male", "female"], True, "Gender identity"),
                    ProtectedAttribute("age_group", ["young", "middle", "senior"], False, "Age category")
                ],
                applicable_metrics=["demographic_parity", "equalized_odds", "predictive_parity"],
                fairness_thresholds={
                    "demographic_parity": 0.08,  # Stricter for lending
                    "equalized_odds": 0.08,
                    "predictive_parity": 0.05
                },
                rationale="Lending decisions are regulated and must ensure equal access to credit"
            ),
            
            DomainType.HEALTHCARE: DomainFairnessConfig(
                domain_type=DomainType.HEALTHCARE,
                has_protected_attributes=True,
                protected_attributes=[
                    ProtectedAttribute("race", ["white", "black", "hispanic", "asian", "other"], False, "Racial/ethnic background"),
                    ProtectedAttribute("gender", ["male", "female"], True, "Gender identity"),
                    ProtectedAttribute("insurance_type", ["private", "public", "uninsured"], False, "Insurance status"),
                    ProtectedAttribute("socioeconomic_status", ["low", "middle", "high"], False, "Socioeconomic background")
                ],
                applicable_metrics=["equalized_odds", "calibration", "treatment_equality"],
                fairness_thresholds={
                    "equalized_odds": 0.05,     # Very strict for healthcare
                    "calibration": 0.03,
                    "treatment_equality": 0.05
                },
                rationale="Healthcare decisions must ensure equitable treatment and outcomes"
            )
        }
    
    def evaluate_domain_fairness(
        self,
        domain_type: DomainType,
        predictions: List[int],
        ground_truth: List[int],
        protected_attributes: Dict[str, List[str]],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Evaluate fairness for a specific domain."""
        config = self.domain_configs.get(domain_type)
        if not config:
            return {
                "error": f"Unknown domain type: {domain_type}",
                "fairness_applicable": False
            }
        
        # Check if fairness evaluation is applicable
        if not config.has_protected_attributes:
            return {
                "domain_type": domain_type.value,
                "fairness_applicable": False,
                "rationale": config.rationale,
                "recommendation": "Fairness evaluation not applicable for this domain"
            }
        
        # Validate protected attributes
        validation_result = self._validate_protected_attributes(config, protected_attributes)
        if not validation_result["valid"]:
            return {
                "domain_type": domain_type.value,
                "fairness_applicable": True,
                "error": validation_result["error"],
                "missing_attributes": validation_result["missing_attributes"]
            }
        
        # Calculate fairness metrics
        fairness_metrics = self._calculate_fairness_metrics(
            config, predictions, ground_truth, protected_attributes
        )
        
        # Assess overall fairness
        overall_assessment = self._assess_overall_fairness(config, fairness_metrics)
        
        return {
            "domain_type": domain_type.value,
            "fairness_applicable": True,
            "protected_attributes_analyzed": list(protected_attributes.keys()),
            "fairness_metrics": [self._metric_to_dict(metric) for metric in fairness_metrics],
            "overall_assessment": overall_assessment,
            "recommendations": self._generate_fairness_recommendations(config, fairness_metrics),
            "context": context or {}
        }
    
    def _validate_protected_attributes(
        self,
        config: DomainFairnessConfig,
        provided_attributes: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """Validate that required protected attributes are provided."""
        required_attrs = {attr.name for attr in config.protected_attributes}
        provided_attrs = set(provided_attributes.keys())
        
        missing_attrs = required_attrs - provided_attrs
        
        if missing_attrs:
            return {
                "valid": False,
                "error": f"Missing required protected attributes: {missing_attrs}",
                "missing_attributes": list(missing_attrs)
            }
        
        # Validate attribute values
        for attr in config.protected_attributes:
            if attr.name in provided_attributes:
                provided_values = set(provided_attributes[attr.name])
                expected_values = set(attr.values)
                
                unexpected_values = provided_values - expected_values
                if unexpected_values:
                    logger.warning(f"Unexpected values for {attr.name}: {unexpected_values}")
        
        return {"valid": True}
    
    def _calculate_fairness_metrics(
        self,
        config: DomainFairnessConfig,
        predictions: List[int],
        ground_truth: List[int],
        protected_attributes: Dict[str, List[str]]
    ) -> List[FairnessMetric]:
        """Calculate applicable fairness metrics for the domain."""
        metrics = []
        
        for metric_name in config.applicable_metrics:
            if metric_name == "demographic_parity":
                metric = self._calculate_demographic_parity(
                    predictions, protected_attributes, config.fairness_thresholds[metric_name]
                )
            elif metric_name == "equalized_odds":
                metric = self._calculate_equalized_odds(
                    predictions, ground_truth, protected_attributes, config.fairness_thresholds[metric_name]
                )
            elif metric_name == "calibration":
                metric = self._calculate_calibration(
                    predictions, ground_truth, protected_attributes, config.fairness_thresholds[metric_name]
                )
            elif metric_name == "predictive_parity":
                metric = self._calculate_predictive_parity(
                    predictions, ground_truth, protected_attributes, config.fairness_thresholds[metric_name]
                )
            elif metric_name == "treatment_equality":
                metric = self._calculate_treatment_equality(
                    predictions, ground_truth, protected_attributes, config.fairness_thresholds[metric_name]
                )
            else:
                logger.warning(f"Unknown fairness metric: {metric_name}")
                continue
            
            if metric:
                metrics.append(metric)
        
        return metrics
    
    def _calculate_demographic_parity(
        self,
        predictions: List[int],
        protected_attributes: Dict[str, List[str]],
        threshold: float
    ) -> FairnessMetric:
        """Calculate demographic parity (statistical parity)."""
        # Use the first protected attribute for simplicity
        attr_name = list(protected_attributes.keys())[0]
        attr_values = protected_attributes[attr_name]
        
        # Calculate selection rates by group
        unique_groups = list(set(attr_values))
        selection_rates = {}
        
        for group in unique_groups:
            group_indices = [i for i, val in enumerate(attr_values) if val == group]
            group_predictions = [predictions[i] for i in group_indices]
            selection_rate = sum(group_predictions) / len(group_predictions) if group_predictions else 0
            selection_rates[group] = selection_rate
        
        # Calculate maximum difference
        rates = list(selection_rates.values())
        max_diff = max(rates) - min(rates) if rates else 0
        
        return FairnessMetric(
            name="demographic_parity",
            value=max_diff,
            interpretation=f"Maximum difference in selection rates: {max_diff:.3f}",
            threshold=threshold,
            is_satisfied=max_diff <= threshold,
            calculation_method=f"Selection rates by {attr_name}: {selection_rates}"
        )
    
    def _calculate_equalized_odds(
        self,
        predictions: List[int],
        ground_truth: List[int],
        protected_attributes: Dict[str, List[str]],
        threshold: float
    ) -> FairnessMetric:
        """Calculate equalized odds (equal TPR and FPR across groups)."""
        attr_name = list(protected_attributes.keys())[0]
        attr_values = protected_attributes[attr_name]
        
        unique_groups = list(set(attr_values))
        tpr_by_group = {}
        fpr_by_group = {}
        
        for group in unique_groups:
            group_indices = [i for i, val in enumerate(attr_values) if val == group]
            group_pred = [predictions[i] for i in group_indices]
            group_true = [ground_truth[i] for i in group_indices]
            
            # Calculate TPR and FPR
            tp = sum(1 for p, t in zip(group_pred, group_true) if p == 1 and t == 1)
            fp = sum(1 for p, t in zip(group_pred, group_true) if p == 1 and t == 0)
            tn = sum(1 for p, t in zip(group_pred, group_true) if p == 0 and t == 0)
            fn = sum(1 for p, t in zip(group_pred, group_true) if p == 0 and t == 1)
            
            tpr = tp / (tp + fn) if (tp + fn) > 0 else 0
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
            
            tpr_by_group[group] = tpr
            fpr_by_group[group] = fpr
        
        # Calculate maximum differences
        tpr_values = list(tpr_by_group.values())
        fpr_values = list(fpr_by_group.values())
        
        max_tpr_diff = max(tpr_values) - min(tpr_values) if tpr_values else 0
        max_fpr_diff = max(fpr_values) - min(fpr_values) if fpr_values else 0
        max_diff = max(max_tpr_diff, max_fpr_diff)
        
        return FairnessMetric(
            name="equalized_odds",
            value=max_diff,
            interpretation=f"Max TPR diff: {max_tpr_diff:.3f}, Max FPR diff: {max_fpr_diff:.3f}",
            threshold=threshold,
            is_satisfied=max_diff <= threshold,
            calculation_method=f"TPR by {attr_name}: {tpr_by_group}, FPR by {attr_name}: {fpr_by_group}"
        )
    
    def _calculate_calibration(
        self,
        predictions: List[int],
        ground_truth: List[int],
        protected_attributes: Dict[str, List[str]],
        threshold: float
    ) -> FairnessMetric:
        """Calculate calibration (predictive accuracy by group)."""
        attr_name = list(protected_attributes.keys())[0]
        attr_values = protected_attributes[attr_name]
        
        unique_groups = list(set(attr_values))
        accuracy_by_group = {}
        
        for group in unique_groups:
            group_indices = [i for i, val in enumerate(attr_values) if val == group]
            group_pred = [predictions[i] for i in group_indices]
            group_true = [ground_truth[i] for i in group_indices]
            
            correct = sum(1 for p, t in zip(group_pred, group_true) if p == t)
            accuracy = correct / len(group_pred) if group_pred else 0
            accuracy_by_group[group] = accuracy
        
        # Calculate maximum difference in accuracy
        accuracies = list(accuracy_by_group.values())
        max_diff = max(accuracies) - min(accuracies) if accuracies else 0
        
        return FairnessMetric(
            name="calibration",
            value=max_diff,
            interpretation=f"Maximum difference in accuracy: {max_diff:.3f}",
            threshold=threshold,
            is_satisfied=max_diff <= threshold,
            calculation_method=f"Accuracy by {attr_name}: {accuracy_by_group}"
        )
    
    def _calculate_predictive_parity(
        self,
        predictions: List[int],
        ground_truth: List[int],
        protected_attributes: Dict[str, List[str]],
        threshold: float
    ) -> FairnessMetric:
        """Calculate predictive parity (equal PPV across groups)."""
        attr_name = list(protected_attributes.keys())[0]
        attr_values = protected_attributes[attr_name]
        
        unique_groups = list(set(attr_values))
        ppv_by_group = {}
        
        for group in unique_groups:
            group_indices = [i for i, val in enumerate(attr_values) if val == group]
            group_pred = [predictions[i] for i in group_indices]
            group_true = [ground_truth[i] for i in group_indices]
            
            tp = sum(1 for p, t in zip(group_pred, group_true) if p == 1 and t == 1)
            fp = sum(1 for p, t in zip(group_pred, group_true) if p == 1 and t == 0)
            
            ppv = tp / (tp + fp) if (tp + fp) > 0 else 0
            ppv_by_group[group] = ppv
        
        # Calculate maximum difference
        ppv_values = list(ppv_by_group.values())
        max_diff = max(ppv_values) - min(ppv_values) if ppv_values else 0
        
        return FairnessMetric(
            name="predictive_parity",
            value=max_diff,
            interpretation=f"Maximum difference in PPV: {max_diff:.3f}",
            threshold=threshold,
            is_satisfied=max_diff <= threshold,
            calculation_method=f"PPV by {attr_name}: {ppv_by_group}"
        )
    
    def _calculate_treatment_equality(
        self,
        predictions: List[int],
        ground_truth: List[int],
        protected_attributes: Dict[str, List[str]],
        threshold: float
    ) -> FairnessMetric:
        """Calculate treatment equality (equal FN/FP ratio across groups)."""
        attr_name = list(protected_attributes.keys())[0]
        attr_values = protected_attributes[attr_name]
        
        unique_groups = list(set(attr_values))
        fn_fp_ratio_by_group = {}
        
        for group in unique_groups:
            group_indices = [i for i, val in enumerate(attr_values) if val == group]
            group_pred = [predictions[i] for i in group_indices]
            group_true = [ground_truth[i] for i in group_indices]
            
            fp = sum(1 for p, t in zip(group_pred, group_true) if p == 1 and t == 0)
            fn = sum(1 for p, t in zip(group_pred, group_true) if p == 0 and t == 1)
            
            ratio = fn / fp if fp > 0 else float('inf') if fn > 0 else 0
            fn_fp_ratio_by_group[group] = ratio
        
        # Calculate maximum difference (excluding infinite values)
        finite_ratios = [r for r in fn_fp_ratio_by_group.values() if r != float('inf')]
        max_diff = max(finite_ratios) - min(finite_ratios) if len(finite_ratios) > 1 else 0
        
        return FairnessMetric(
            name="treatment_equality",
            value=max_diff,
            interpretation=f"Maximum difference in FN/FP ratio: {max_diff:.3f}",
            threshold=threshold,
            is_satisfied=max_diff <= threshold,
            calculation_method=f"FN/FP ratio by {attr_name}: {fn_fp_ratio_by_group}"
        )
    
    def _assess_overall_fairness(
        self,
        config: DomainFairnessConfig,
        metrics: List[FairnessMetric]
    ) -> Dict[str, Any]:
        """Assess overall fairness based on all metrics."""
        if not metrics:
            return {
                "overall_fair": False,
                "reason": "No fairness metrics calculated"
            }
        
        satisfied_metrics = [m for m in metrics if m.is_satisfied]
        satisfaction_rate = len(satisfied_metrics) / len(metrics)
        
        overall_fair = satisfaction_rate >= 0.8  # 80% of metrics must be satisfied
        
        return {
            "overall_fair": overall_fair,
            "satisfaction_rate": satisfaction_rate,
            "satisfied_metrics": len(satisfied_metrics),
            "total_metrics": len(metrics),
            "critical_violations": [m.name for m in metrics if not m.is_satisfied]
        }
    
    def _generate_fairness_recommendations(
        self,
        config: DomainFairnessConfig,
        metrics: List[FairnessMetric]
    ) -> List[str]:
        """Generate recommendations for improving fairness."""
        recommendations = []
        
        violated_metrics = [m for m in metrics if not m.is_satisfied]
        
        for metric in violated_metrics:
            if metric.name == "demographic_parity":
                recommendations.append(
                    "Consider rebalancing training data or adjusting decision thresholds to achieve demographic parity."
                )
            elif metric.name == "equalized_odds":
                recommendations.append(
                    "Implement post-processing techniques to equalize true positive and false positive rates across groups."
                )
            elif metric.name == "calibration":
                recommendations.append(
                    "Improve model calibration through techniques like Platt scaling or isotonic regression."
                )
        
        if not violated_metrics:
            recommendations.append("All fairness metrics are satisfied. Continue monitoring for fairness drift.")
        
        return recommendations
    
    def _metric_to_dict(self, metric: FairnessMetric) -> Dict[str, Any]:
        """Convert fairness metric to dictionary."""
        return {
            "name": metric.name,
            "value": round(metric.value, 4),
            "interpretation": metric.interpretation,
            "threshold": metric.threshold,
            "is_satisfied": metric.is_satisfied,
            "calculation_method": metric.calculation_method
        }


# Example usage
def run_fairness_evaluation_example():
    """Example of running fairness evaluation."""
    framework = FairnessEvaluationFramework()
    
    # Example 1: Arithmetic domain (should not evaluate fairness)
    arithmetic_result = framework.evaluate_domain_fairness(
        domain_type=DomainType.ARITHMETIC,
        predictions=[1, 0, 1, 0],
        ground_truth=[1, 0, 1, 1],
        protected_attributes={}
    )
    print("Arithmetic domain result:")
    print(json.dumps(arithmetic_result, indent=2))
    
    # Example 2: Hiring domain (should evaluate fairness)
    hiring_result = framework.evaluate_domain_fairness(
        domain_type=DomainType.HIRING,
        predictions=[1, 0, 1, 0, 1, 0, 1, 0],
        ground_truth=[1, 0, 1, 1, 1, 0, 0, 0],
        protected_attributes={
            "gender": ["male", "female", "male", "female", "male", "female", "male", "female"],
            "race": ["white", "black", "white", "black", "white", "black", "white", "black"]
        }
    )
    print("\nHiring domain result:")
    print(json.dumps(hiring_result, indent=2))


if __name__ == "__main__":
    run_fairness_evaluation_example()
