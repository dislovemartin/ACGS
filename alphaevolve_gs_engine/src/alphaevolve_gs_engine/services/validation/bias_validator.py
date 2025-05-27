"""
bias_validator.py

This module defines the BiasValidator, responsible for assessing policies
for potential biases. This can involve statistical analysis of outcomes over
diverse inputs, checking against fairness metrics, or using LLMs for qualitative review.

Classes:
    BiasMetric: Defines a specific metric for fairness or bias.
    BiasValidator: Interface for bias validation.
    FairnessMetricValidator: Validates policies against quantitative fairness metrics.
    LLMBiasReviewer: Uses an LLM to qualitatively review policies for bias.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional, Callable

from alphaevolve_gs_engine.utils.logging_utils import setup_logger
# from alphaevolve_gs_engine.services.llm_service import LLMService, get_llm_service
# from alphaevolve_gs_engine.services.validation.semantic_validator import ScenarioBasedSemanticValidator # For outcome generation

logger = setup_logger(__name__)

class BiasMetric:
    """
    Represents a specific metric or test for evaluating bias/fairness.

    Attributes:
        metric_id (str): Unique identifier for the metric.
        name (str): Human-readable name (e.g., "Demographic Parity", "Equal Opportunity").
        description (str): Explanation of what the metric measures.
        metric_type (str): Type of metric (e.g., "statistical", "qualitative_review").
        configuration (Dict[str, Any]): Parameters for the metric.
            - For "statistical": {"protected_attribute": "gender", "favorable_outcome_query": "data.loan.approved",
                                  "threshold": 0.8} (e.g., ratio for disparate impact)
            - For "qualitative_review": {"llm_prompt_template": "Review for bias: {policy_code}"}
        evaluation_function (Optional[Callable]): A function to compute the metric if not standard.
    """
    def __init__(self,
                 metric_id: str,
                 name: str,
                 description: str,
                 metric_type: str, # "statistical", "qualitative_review"
                 configuration: Dict[str, Any],
                 evaluation_function: Optional[Callable] = None): # For complex custom metrics
        self.metric_id = metric_id
        self.name = name
        self.description = description
        self.metric_type = metric_type
        self.configuration = configuration
        self.evaluation_function = evaluation_function
        self._validate_configuration()

    def _validate_configuration(self):
        if self.metric_type == "statistical":
            required_keys = ["protected_attribute_query", "favorable_outcome_query", "threshold", "group_definitions"]
            if not all(key in self.configuration for key in required_keys):
                raise ValueError(f"Invalid config for statistical bias metric '{self.metric_id}'. "
                                 f"Missing one of: {required_keys}")
            if not isinstance(self.configuration["group_definitions"], dict):
                 raise ValueError(f"group_definitions in '{self.metric_id}' must be a dictionary.")
        elif self.metric_type == "qualitative_review":
            if "llm_prompt_template" not in self.configuration:
                 raise ValueError(f"llm_prompt_template missing for qualitative_review metric '{self.metric_id}'.")
        # Add more validations as needed

    def __repr__(self) -> str:
        return f"BiasMetric(id='{self.metric_id}', name='{self.name}', type='{self.metric_type}')"


class BiasValidator(ABC):
    """
    Abstract base class for bias validation services.
    """

    @abstractmethod
    def assess_bias(self,
                    policy_code: str,
                    policy_id: str,
                    metrics: List[BiasMetric],
                    # Data might be needed for statistical metrics, or scenarios for outcome generation
                    dataset: Optional[List[Dict[str, Any]]] = None, 
                    policy_language: str = "rego"
                   ) -> List[Tuple[str, bool, str, Optional[float]]]: # metric_id, passed, message, metric_value
        """
        Assesses a given policy for biases using a set of metrics.

        Args:
            policy_code (str): The policy code.
            policy_id (str): Identifier of the policy.
            metrics (List[BiasMetric]): Bias metrics to use for assessment.
            dataset (Optional[List[Dict[str, Any]]]): Dataset for statistical analysis.
                                                     Each item is an input instance.
            policy_language (str): Language of the policy (default: "rego").

        Returns:
            List[Tuple[str, bool, str, Optional[float]]]: Results for each metric.
                (metric_id, passed, message, metric_value)
                'passed' is True if the metric's criteria for fairness are met.
                'metric_value' is the computed value of the metric, if applicable.
        """
        pass


class FairnessMetricValidator(BiasValidator):
    """
    Validates policies against quantitative fairness metrics using a dataset of inputs
    and an OPA evaluation engine to determine outcomes.
    """
    def __init__(self, opa_executable_path: str = "opa"):
        self.opa_executable_path = opa_executable_path
        # This validator would need an OPA evaluation capability, similar to SemanticValidator
        # For simplicity, we'll mock the OPA evaluation part in this example.
        # In a real implementation, you'd instantiate something like:
        # self.opa_evaluator = ScenarioBasedSemanticValidator(opa_executable_path) # or a dedicated OPA runner
        logger.info("FairnessMetricValidator initialized (with mocked OPA evaluation).")

    def _get_outcomes_for_dataset(self, 
                                  policy_code: str, 
                                  policy_id: str, 
                                  dataset: List[Dict[str, Any]], 
                                  outcome_query: str,
                                  attribute_query: str) -> List[Dict[str, Any]]:
        """
        (Mocked) Evaluates policy for each item in dataset to get outcomes and protected attributes.
        A real version would call OPA for each item.
        """
        logger.debug(f"Mocking OPA evaluation for policy '{policy_id}' on {len(dataset)} data points.")
        results = []
        for i, data_point_input in enumerate(dataset):
            # Mock OPA evaluation for outcome
            # In real scenario: actual_outcome, err = self.opa_evaluator._evaluate_rego_policy(policy_code, data_point_input, outcome_query, policy_id)
            mock_outcome = (i % 2 == 0) # Alternate outcomes for variety
            
            # Mock OPA evaluation for protected attribute value
            # In real scenario: protected_attr_val, err = self.opa_evaluator._evaluate_rego_policy(policy_code, data_point_input, attribute_query, policy_id)
            # Assuming attribute is directly in input for simplicity here.
            # The attribute_query could be complex, e.g., `data.user_profile.demographics.group`
            # For this mock, let's assume `attribute_query` is a simple key in `data_point_input`
            # e.g., if attribute_query is "user.feature", we look for data_point_input["user"]["feature"]
            
            # Simplified extraction based on a simple dot-separated query string for mock
            current_level = data_point_input
            attr_val = None
            try:
                for part in attribute_query.split('.'):
                    current_level = current_level[part]
                attr_val = current_level
            except KeyError:
                logger.warning(f"Protected attribute '{attribute_query}' not found in data point {i} for policy '{policy_id}'. Skipping.")
                attr_val = "unknown" # Default if not found

            results.append({
                "input": data_point_input,
                "outcome": mock_outcome, # Result of outcome_query
                "protected_attribute_value": attr_val # Result of attribute_query
            })
        return results

    def _calculate_demographic_parity(self, 
                                      outcomes: List[Dict[str, Any]], 
                                      metric: BiasMetric) -> Tuple[bool, str, float]:
        """Calculates demographic parity (simplified)."""
        # Config: "protected_attribute_query", "favorable_outcome_query", "threshold", "group_definitions"
        # group_definitions: {"groupA": ["val1", "val2"], "groupB": ["val3"]}
        # threshold: e.g. 0.8 for 80% rule (min_ratio >= threshold)
        
        group_outcomes: Dict[str, List[bool]] = {group_name: [] for group_name in metric.configuration["group_definitions"]}
        
        for item in outcomes:
            item_attr_val = item["protected_attribute_value"]
            item_outcome = item["outcome"] # This should be the favorable outcome (True/False)

            for group_name, group_values in metric.configuration["group_definitions"].items():
                if item_attr_val in group_values:
                    group_outcomes[group_name].append(item_outcome)
                    break # Assuming non-overlapping groups for simplicity
        
        group_favor_rates: Dict[str, float] = {}
        for group_name, results in group_outcomes.items():
            if not results:
                group_favor_rates[group_name] = 0.0
                logger.warning(f"No data points found for group '{group_name}' in metric '{metric.metric_id}'. Rate set to 0.")
                continue
            favor_rate = sum(1 for res in results if res is True) / len(results) # Count favorable outcomes
            group_favor_rates[group_name] = favor_rate

        if not group_favor_rates or len(group_favor_rates) < 2:
            return False, "Not enough groups with data to compare for demographic parity.", 0.0

        # Demographic Parity often looks at ratio of favorable outcome rates
        # Example: min_rate / max_rate >= threshold (e.g., 80% rule for disparate impact)
        min_rate = min(group_favor_rates.values())
        max_rate = max(group_favor_rates.values())
        
        if max_rate == 0: # Avoid division by zero if no group has favorable outcomes
            metric_value = 1.0 if min_rate == 0 else 0.0 # All groups have 0% rate -> perfect parity
        else:
            metric_value = min_rate / max_rate
            
        passed = metric_value >= metric.configuration["threshold"]
        message = (f"Demographic Parity: Min rate = {min_rate:.3f}, Max rate = {max_rate:.3f}. "
                   f"Ratio = {metric_value:.3f}. Threshold = {metric.configuration['threshold']:.3f}. "
                   f"Rates by group: { {g: f'{r:.3f}' for g,r in group_favor_rates.items()} }")
        
        return passed, message, metric_value


    def assess_bias(self,
                    policy_code: str,
                    policy_id: str,
                    metrics: List[BiasMetric],
                    dataset: Optional[List[Dict[str, Any]]] = None,
                    policy_language: str = "rego"
                   ) -> List[Tuple[str, bool, str, Optional[float]]]:
        results: List[Tuple[str, bool, str, Optional[float]]] = []

        for metric in metrics:
            if metric.metric_type != "statistical":
                logger.debug(f"Skipping metric '{metric.metric_id}' as it's not statistical for FairnessMetricValidator.")
                continue

            if not dataset:
                results.append((metric.metric_id, False, "Dataset not provided for statistical metric.", None))
                logger.warning(f"Dataset required for statistical bias metric '{metric.metric_id}' but not provided.")
                continue

            # 1. Get outcomes for the entire dataset using the policy
            # The outcome_query and attribute_query are in metric.configuration
            outcome_query = metric.configuration["favorable_outcome_query"] # e.g. "data.policy.allow"
            attribute_query = metric.configuration["protected_attribute_query"] # e.g. "input.user.ethnicity"
            
            # This step involves running OPA for each data point. Mocked here.
            evaluated_outcomes = self._get_outcomes_for_dataset(policy_code, policy_id, dataset, outcome_query, attribute_query)

            # 2. Calculate the specific fairness metric
            # This example focuses on Demographic Parity. Others (Equalized Odds, etc.) would need their own functions.
            if metric.name.lower().replace(" ", "") == "demographicparity":
                passed, message, metric_val = self._calculate_demographic_parity(evaluated_outcomes, metric)
                results.append((metric.metric_id, passed, message, metric_val))
            elif metric.evaluation_function: # Custom function provided
                # The custom function would take `evaluated_outcomes` and `metric.configuration`
                # passed, message, metric_val = metric.evaluation_function(evaluated_outcomes, metric.configuration)
                # results.append((metric.metric_id, passed, message, metric_val))
                results.append((metric.metric_id, False, "Custom evaluation function not executed in this mock.", None))
                logger.info(f"Metric '{metric.metric_id}' has a custom eval function (not run in mock).")
            else:
                results.append((metric.metric_id, False, f"Unsupported statistical metric name: {metric.name}", None))
                logger.warning(f"No calculation logic for statistical metric '{metric.name}' (ID: {metric.metric_id}).")
        
        return results


class LLMBiasReviewer(BiasValidator):
    """
    Uses an LLM to qualitatively review policy code for potential biases.
    """
    def __init__(self, llm_service: Any): # Should be LLMService instance
        # self.llm_service = llm_service
        logger.info("LLMBiasReviewer initialized (mocked LLM interaction).")
        # A real implementation would take an LLMService instance.
        # For this example, we'll mock the LLM call.
        self.llm_service_is_mock = True # Flag that actual LLM is not used here

    def assess_bias(self,
                    policy_code: str,
                    policy_id: str,
                    metrics: List[BiasMetric],
                    dataset: Optional[List[Dict[str, Any]]] = None, # Dataset not typically used by LLM reviewer
                    policy_language: str = "rego"
                   ) -> List[Tuple[str, bool, str, Optional[float]]]:
        results: List[Tuple[str, bool, str, Optional[float]]] = []

        for metric in metrics:
            if metric.metric_type != "qualitative_review":
                logger.debug(f"Skipping metric '{metric.metric_id}' as it's not qualitative_review for LLMBiasReviewer.")
                continue

            prompt_template = metric.configuration.get("llm_prompt_template")
            if not prompt_template:
                results.append((metric.metric_id, False, "LLM prompt template missing in metric configuration.", None))
                continue
            
            try:
                prompt = prompt_template.format(
                    policy_code=policy_code,
                    policy_id=policy_id,
                    policy_language=policy_language
                )
            except KeyError as e:
                results.append((metric.metric_id, False, f"Invalid prompt template: {e}", None))
                continue
            
            # Mocked LLM Call
            logger.debug(f"Mocking LLM call for bias review of policy '{policy_id}', metric '{metric.metric_id}'. Prompt snippet: {prompt[:100]}...")
            # llm_response = self.llm_service.generate_text(prompt, max_tokens=300) # Real call
            
            # Example mock responses
            if "obvious bias" in policy_code.lower(): # Simple trigger for mock
                llm_response = "LLM Review (Mock): The policy code appears to contain potential bias related to [specific clause]. Recommendation: Modify [clause]."
                passed = False # Bias detected
            else:
                llm_response = "LLM Review (Mock): The policy code was reviewed and no obvious biases were detected based on the provided prompt."
                passed = True # No bias detected by mock LLM
            
            message = llm_response
            results.append((metric.metric_id, passed, message, None)) # No numeric value for qualitative review

        return results


# Example Usage:
if __name__ == "__main__":
    # --- Example Policy (Rego) ---
    loan_policy_code = """
    package company.loan

    default approve_loan = false

    # Rule: Approve loan if credit score > 700 and income > 50000
    approve_loan {
        input.applicant.credit_score > 700
        input.applicant.income > 50000
    }

    # Rule: Auto-reject if age < 21 (potentially biased or needs justification)
    approve_loan = false {
        input.applicant.age < 21
    }
    """
    policy_id = "LoanPolicy_v1"

    # --- Example Dataset (for FairnessMetricValidator) ---
    # In a real scenario, this would be much larger and more diverse.
    # Each dict is an "input" for OPA.
    example_dataset = [
        {"applicant": {"credit_score": 750, "income": 60000, "age": 30, "ethnicity": "GroupA"}}, # Expected: True
        {"applicant": {"credit_score": 650, "income": 70000, "age": 40, "ethnicity": "GroupA"}}, # Expected: False (score)
        {"applicant": {"credit_score": 720, "income": 80000, "age": 20, "ethnicity": "GroupB"}}, # Expected: False (age)
        {"applicant": {"credit_score": 780, "income": 55000, "age": 35, "ethnicity": "GroupB"}}, # Expected: True
        {"applicant": {"credit_score": 710, "income": 60000, "age": 25, "ethnicity": "GroupA"}}, # Expected: True
        {"applicant": {"credit_score": 790, "income": 90000, "age": 50, "ethnicity": "GroupC_Test"}},# Expected: True
    ]


    # --- Example Bias Metrics ---
    # Statistical Metric: Demographic Parity
    dp_metric = BiasMetric(
        metric_id="DP001",
        name="Demographic Parity",
        description="Checks if favorable outcomes are similar across protected groups (ethnicity).",
        metric_type="statistical",
        configuration={
            "protected_attribute_query": "applicant.ethnicity", # Path within input to find attribute
            "favorable_outcome_query": "data.company.loan.approve_loan", # Rego query for favorable outcome
            "group_definitions": { # How to map attribute values to groups
                "Alpha": ["GroupA"], 
                "Beta": ["GroupB"],
                "Gamma": ["GroupC_Test"] # Testing with a new group
            },
            "threshold": 0.80 # (e.g., 80% rule for disparate impact ratio)
        }
    )

    # Qualitative Metric: LLM Review
    llm_review_metric = BiasMetric(
        metric_id="QL001",
        name="LLM Bias Review",
        description="Uses an LLM to qualitatively review the policy for potential biases.",
        metric_type="qualitative_review",
        configuration={
            "llm_prompt_template": (
                "Review the following Rego policy code for any potential sources of bias "
                "(e.g., based on age, demographics, or other unfair criteria). "
                "Policy ID: {policy_id}, Language: {policy_language}.\n\nPolicy Code:\n{policy_code}\n\n"
                "Provide a brief assessment:"
            )
        }
    )
    all_bias_metrics = [dp_metric, llm_review_metric]

    # --- Using FairnessMetricValidator (Mocked OPA) ---
    print("--- FairnessMetricValidator (Mocked OPA Evaluation) ---")
    # In a real setup, ensure OPA is installed and path is correct.
    fairness_validator = FairnessMetricValidator(opa_executable_path="opa") # Path to OPA
    stat_results = fairness_validator.assess_bias(loan_policy_code, policy_id, all_bias_metrics, example_dataset)
    
    print(f"\nStatistical Bias Assessment Results for '{policy_id}':")
    for mid, passed, msg, val in stat_results:
        print(f"  Metric ID: {mid}, Passed: {passed}, Value: {val if val is not None else 'N/A'}\n    Message: {msg}")
    
    # Expected for stat_results (based on mock _get_outcomes_for_dataset which alternates outcomes):
    # DP001 might pass or fail based on the random mock outcomes. A real test would be deterministic.
    # For the given mock logic (alternate True/False):
    # GroupA: [True (30), False (40), True (25)] -> 2/3 = 0.66
    # GroupB: [False (20), True (35)] -> 1/2 = 0.5
    # GroupC_Test: [True (50)] -> 1/1 = 1.0
    # Rates: Alpha=0.66, Beta=0.5, Gamma=1.0. Min=0.5, Max=1.0. Ratio = 0.5 / 1.0 = 0.5. Threshold=0.8. Fails.
    if stat_results and stat_results[0][0] == "DP001":
         assert not stat_results[0][1] # Expecting DP to fail with the current mock data logic
         assert abs(stat_results[0][3] - 0.5) < 0.001 if stat_results[0][3] is not None else False

    # --- Using LLMBiasReviewer (Mocked LLM) ---
    print("\n--- LLMBiasReviewer (Mocked LLM Call) ---")
    # llm_service_mock = get_llm_service("mock") # Get a mock LLM service instance
    llm_reviewer = LLMBiasReviewer(llm_service=None) # Pass mock or real LLM service
    qual_results = llm_reviewer.assess_bias(loan_policy_code, policy_id, all_bias_metrics)

    print(f"\nQualitative Bias Assessment Results for '{policy_id}':")
    for mid, passed, msg, val in qual_results:
        print(f"  Metric ID: {mid}, Passed: {passed}\n    Message: {msg}")

    # Expected for qual_results:
    # QL001: Mock LLM might say "no bias" or "bias found" based on simple keywords.
    # The example policy has "age < 21" which is a common point for bias discussion.
    # The mock LLM logic is simple; a real one would be more nuanced.
    # Current mock logic for LLMReviewer passes if "obvious bias" isn't in policy_code.
    # The loan_policy_code does not contain "obvious bias" literally.
    # However, the age rule `input.applicant.age < 21` is a form of bias.
    # A sophisticated LLM prompt for bias detection should catch this.
    # The current mock LLM is too simple to catch it.
    if qual_results and qual_results[0][0] == "QL001":
        # The mock LLM does not detect bias in the example policy.
        # A real, well-prompted LLM might flag the age rule.
        assert qual_results[0][1] is True # Mock LLM says no bias.

    print("\nBias validator examples completed.")
    print("Note: Statistical results depend on (mocked) OPA output. Qualitative results are from a (mocked) LLM.")
