"""
semantic_validator.py

This module defines the SemanticValidator, responsible for assessing
whether policies align with their intended meaning, purpose, and ethical
guidelines, often by comparing them against 'golden' test cases or scenarios,
or by using LLMs for interpretation.

Classes:
    SemanticValidator: Interface for semantic validation.
    ScenarioBasedSemanticValidator: Validates policies using predefined scenarios.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional
import subprocess # For OPA eval if used
import os # For file operations

from alphaevolve_gs_engine.utils.logging_utils import setup_logger
# from alphaevolve_gs_engine.core.constitutional_principle import ConstitutionalPrinciple
# from alphaevolve_gs_engine.core.operational_rule import OperationalRule
# from alphaevolve_gs_engine.services.llm_service import LLMService, get_llm_service

logger = setup_logger(__name__)

class SemanticTestCase:
    """
    Represents a single test case for semantic validation.

    Attributes:
        case_id (str): Unique identifier for the test case.
        description (str): Description of the scenario being tested.
        input_data (Dict[str, Any]): The input data for the policy evaluation.
        expected_outcome (Any): The expected result from the policy evaluation
                                (e.g., True for allow, specific JSON object).
        policy_under_test_id (str): ID of the policy this test case applies to.
        metadata (Optional[Dict[str, str]]): Additional info like source, author.
    """
    def __init__(self,
                 case_id: str,
                 description: str,
                 input_data: Dict[str, Any],
                 expected_outcome: Any, # Could be boolean, string, dict, etc.
                 policy_under_test_id: str,
                 metadata: Optional[Dict[str, str]] = None):
        self.case_id = case_id
        self.description = description
        self.input_data = input_data
        self.expected_outcome = expected_outcome
        self.policy_under_test_id = policy_under_test_id
        self.metadata = metadata if metadata else {}

    def __repr__(self) -> str:
        return (f"SemanticTestCase(id='{self.case_id}', "
                f"policy_id='{self.policy_under_test_id}')")


class SemanticValidator(ABC):
    """
    Abstract base class for semantic validation services.
    """

    @abstractmethod
    def validate_semantics(self,
                           policy_code: str, # The actual policy code (e.g. Rego)
                           policy_id: str,   # ID of the policy
                           test_cases: List[SemanticTestCase],
                           policy_language: str = "rego"
                          ) -> List[Tuple[str, bool, str, Any, Any]]: # case_id, passed, message, actual_outcome, expected_outcome
        """
        Validates the semantics of a given policy using a set of test cases.

        Args:
            policy_code (str): The policy code to be validated.
            policy_id (str): Identifier of the policy being validated.
            test_cases (List[SemanticTestCase]): A list of semantic test cases
                                                 relevant to this policy.
            policy_language (str): The language of the policy (default: "rego").

        Returns:
            List[Tuple[str, bool, str, Any, Any]]: A list of results, one for each test case.
                Each tuple contains: (case_id, passed, message, actual_outcome, expected_outcome).
                'passed' is True if the actual outcome matches the expected outcome.
        """
        pass


class ScenarioBasedSemanticValidator(SemanticValidator):
    """
    A semantic validator that uses predefined scenarios (test cases) and
    an OPA evaluation engine (for Rego policies) to check semantic correctness.
    """

    def __init__(self, opa_executable_path: str = "opa", default_rego_query_path: str = "data.system.allow"):
        """
        Initializes the ScenarioBasedSemanticValidator.

        Args:
            opa_executable_path (str): Path to the OPA executable.
            default_rego_query_path (str): Default Rego query path to evaluate if not
                                           specified implicitly by the policy structure
                                           (e.g. for policies that are not simple `allow` checks).
                                           This path points to the rule that yields the decision.
        """
        self.opa_executable_path = opa_executable_path
        self.default_rego_query_path = default_rego_query_path # e.g. "data.example.authz.allow"
        self._check_opa_availability()


    def _check_opa_availability(self):
        """Checks if the OPA executable is available."""
        try:
            subprocess.run([self.opa_executable_path, "version"], capture_output=True, text=True, check=True, timeout=5)
            logger.info(f"OPA executable found at '{self.opa_executable_path}'.")
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            logger.error(f"OPA executable not found or not working at '{self.opa_executable_path}'. "
                         f"Semantic validation of Rego policies will be impacted. Error: {e}")
            # Depending on strictness, could raise an error here.

    def _evaluate_rego_policy(self,
                              policy_code: str,
                              input_data: Dict[str, Any],
                              query_path: str,
                              policy_id_for_log: str) -> Tuple[Optional[Any], Optional[str]]:
        """
        Evaluates a Rego policy with given input using `opa eval`.

        Args:
            policy_code (str): The Rego policy code.
            input_data (Dict[str, Any]): The input for the policy.
            query_path (str): The Rego query path (e.g., "data.mypolicy.allow").
            policy_id_for_log (str): Policy ID for logging.

        Returns:
            Tuple[Optional[Any], Optional[str]]: (evaluation_result, error_message).
                                                 Result is None if an error occurs.
        """
        import json
        policy_file_path = None # Initialize to ensure it's defined in finally
        input_file_path = None  # Initialize to ensure it's defined in finally
        try:
            # Create a temporary file for the policy code
            # This is often more robust for complex policies than stdin.
            import tempfile
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".rego") as tmp_policy_file:
                tmp_policy_file.write(policy_code)
                policy_file_path = tmp_policy_file.name
            
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as tmp_input_file:
                json.dump(input_data, tmp_input_file)
                input_file_path = tmp_input_file.name

            cmd = [
                self.opa_executable_path,
                "eval",
                "--format", "json", # Get output as JSON
                "--data", policy_file_path,
                "--input", input_file_path,
                query_path
            ]
            
            logger.debug(f"Executing OPA eval for policy '{policy_id_for_log}', query '{query_path}': {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=15)

            if result.returncode != 0:
                error_msg = f"OPA evaluation failed for policy '{policy_id_for_log}', query '{query_path}'. Error: {result.stderr.strip()}"
                logger.error(error_msg)
                return None, error_msg
            
            # Parse the JSON output from OPA
            # `opa eval --format json` typically returns a list of results for the query.
            # Example: [{"result": true}] or [{"result": [{"value": 1}, {"value": 2}]}]
            # We need to extract the actual result value.
            try:
                opa_output = json.loads(result.stdout)
                # If 'result' key exists and is not empty, take the first result's value.
                # This handles cases like `data.mypolicy.allow` which results in `[{"result": true/false}]`
                # or `data.mypolicy.violations` which results in `[{"result": [...]}]`
                if opa_output and isinstance(opa_output, list) and opa_output[0] and "result" in opa_output[0]:
                    eval_result = opa_output[0]["result"]
                # Handles cases where the output is directly the result, e.g. `opa eval "1+1"` -> `[{"result": 2}]`
                # or specific queries like `opa eval "data.foo"` where `data.foo` is defined.
                # Sometimes, if the query path itself is the result (e.g., a specific variable or a non-boolean rule),
                # the structure might be different or might not have "result" key if it's a direct value.
                # This part might need refinement based on diverse Rego outputs.
                # A common pattern for simple boolean rules is `[{"result": true/false}]`.
                # For rules returning sets or objects, it might be `[{"result": [...]}]` or `[{"result": {...}}]`.
                # If the query is just `x=1;y=2;{x,y}` it might be `[{"result": [{"x":1,"y":2}]}]` (if x,y are in a set)
                # or more complex. The current logic is a common case.
                else: 
                    # If the output doesn't fit the `[{"result": ...}]` pattern directly,
                    # it could be that the query itself produced a raw value or a different structure.
                    # For instance, `opa eval "count(input.items)"` might return `[{"result": 3}]`.
                    # If `opa_output` is `[{"some_other_key": ...}]` or just `[]` for undefined, this needs care.
                    # If the query is undefined, OPA eval usually returns an empty list `[]` or no output.
                    # If `opa_output` is `[]`, it means the query was undefined or produced no results.
                    # This should often be treated as `None` or `False` depending on context.
                    if not opa_output: # Empty list means undefined
                        eval_result = None # Or False, depending on interpretation for boolean queries
                    else:
                        # Fallback: take the whole first element if structure is unexpected but non-empty
                        # This is a guess and might need adjustment.
                        eval_result = opa_output[0] if isinstance(opa_output, list) and opa_output else opa_output


                logger.debug(f"OPA eval successful for '{policy_id_for_log}', query '{query_path}'. Raw output: {result.stdout[:200]}, Parsed result: {eval_result}")
                return eval_result, None
            except (json.JSONDecodeError, IndexError, KeyError) as e:
                error_msg = f"Failed to parse OPA output for policy '{policy_id_for_log}', query '{query_path}'. Error: {e}. Output: {result.stdout[:500]}"
                logger.error(error_msg)
                return None, error_msg

        except FileNotFoundError:
            err = f"OPA executable not found at '{self.opa_executable_path}'."
            logger.error(err)
            return None, err
        except subprocess.TimeoutExpired:
            err = f"OPA evaluation timed out for policy '{policy_id_for_log}', query '{query_path}'."
            logger.error(err)
            return None, err
        except Exception as e:
            err = f"An unexpected error occurred during OPA evaluation for policy '{policy_id_for_log}': {e}"
            logger.error(err, exc_info=True)
            return None, err
        finally:
            # Clean up temporary files
            if policy_file_path and os.path.exists(policy_file_path):
                os.remove(policy_file_path)
            if input_file_path and os.path.exists(input_file_path):
                os.remove(input_file_path)


    def validate_semantics(self,
                           policy_code: str,
                           policy_id: str,
                           test_cases: List[SemanticTestCase],
                           policy_language: str = "rego"
                          ) -> List[Tuple[str, bool, str, Any, Any]]:
        if policy_language.lower() != "rego":
            raise NotImplementedError(f"Semantic validation for '{policy_language}' is not implemented by ScenarioBasedSemanticValidator.")

        results: List[Tuple[str, bool, str, Any, Any]] = []

        # Filter test cases relevant to the current policy_id
        relevant_test_cases = [tc for tc in test_cases if tc.policy_under_test_id == policy_id]
        if not relevant_test_cases:
            logger.info(f"No semantic test cases found for policy_id '{policy_id}'. Skipping semantic validation for it.")
            return []
            
        logger.info(f"Starting semantic validation for policy '{policy_id}' with {len(relevant_test_cases)} test cases.")

        for tc in relevant_test_cases:
            # Determine the query path.
            query_path = tc.metadata.get("rego_query_path") or self.default_rego_query_path
            
            # If default_rego_query_path is generic (like "data.system.allow") and policy has a package,
            # try to make it more specific, unless test case metadata already specified one.
            if (self.default_rego_query_path == "data.system.allow" and 
                not tc.metadata.get("rego_query_path")): # only adjust if not specified in TC
                try:
                    package_line = next((line for line in policy_code.splitlines() if line.strip().startswith("package ")), None)
                    if package_line:
                        package_name = package_line.strip().split(" ")[1]
                        # Assuming a common rule like 'allow'. This is a big assumption.
                        # The actual rule name to query should ideally be part of the test case
                        # or derived more reliably.
                        rule_name = self.default_rego_query_path.split('.')[-1] # e.g. "allow" from "data.system.allow"
                        potential_query_path = f"data.{package_name}.{rule_name}" 
                        query_path = potential_query_path
                except Exception as e:
                    logger.warning(f"Could not reliably determine query path for policy '{policy_id}', tc '{tc.case_id}'. Using: '{query_path}'. Error: {e}")


            actual_outcome, error_msg = self._evaluate_rego_policy(policy_code, tc.input_data, query_path, policy_id)

            if error_msg:
                results.append((tc.case_id, False, f"Evaluation error: {error_msg}", None, tc.expected_outcome))
                continue

            # Comparison logic might need to be sophisticated depending on outcome types
            # For now, direct equality.
            passed = (actual_outcome == tc.expected_outcome)
            message = "Passed." if passed else f"Failed. Expected: {tc.expected_outcome}, Got: {actual_outcome}"
            
            if not passed:
                 logger.warning(f"Semantic test case '{tc.case_id}' for policy '{policy_id}' {message}")
            else:
                 logger.info(f"Semantic test case '{tc.case_id}' for policy '{policy_id}' passed.")

            results.append((tc.case_id, passed, message, actual_outcome, tc.expected_outcome))
            
        return results

# Example Usage
if __name__ == "__main__":
    # --- Example Policies ---
    auth_policy_code = """
    package example.authz

    default allow = false

    allow {
        input.user.role == "admin"
    }
    allow {
        input.user.role == "editor"
        input.resource.type == "document"
        input.action == "edit"
    }
    """
    auth_policy_id = "AuthPolicy_v1"

    # --- Example Test Cases ---
    tc1 = SemanticTestCase(
        case_id="AdminAccessToAny",
        description="Admin should be allowed access regardless of resource/action.",
        input_data={"user": {"role": "admin"}, "resource": {"type": "config"}, "action": "read"},
        expected_outcome=True, # Expected result of 'data.example.authz.allow'
        policy_under_test_id=auth_policy_id,
        metadata={"rego_query_path": "data.example.authz.allow"}
    )
    tc2 = SemanticTestCase(
        case_id="EditorAccessToDocument",
        description="Editor should be allowed to edit documents.",
        input_data={"user": {"role": "editor"}, "resource": {"type": "document"}, "action": "edit"},
        expected_outcome=True,
        policy_under_test_id=auth_policy_id,
        metadata={"rego_query_path": "data.example.authz.allow"}
    )
    tc3 = SemanticTestCase(
        case_id="EditorDeniedOtherResource",
        description="Editor should be denied access to non-document resources like 'config'.",
        input_data={"user": {"role": "editor"}, "resource": {"type": "config"}, "action": "edit"},
        expected_outcome=False, # Expect 'allow' to be false
        policy_under_test_id=auth_policy_id,
        metadata={"rego_query_path": "data.example.authz.allow"}
    )
    tc4 = SemanticTestCase( # Test case for a different policy (won't be run in this example call)
        case_id="OtherPolicyCase",
        description="A test for a different policy.",
        input_data={}, expected_outcome=True, policy_under_test_id="OtherPolicy_v1"
    )

    all_test_cases = [tc1, tc2, tc3, tc4]
    
    print("--- Using ScenarioBasedSemanticValidator ---")
    # Initialize validator. Ensure OPA is in PATH or provide path.
    # The default_rego_query_path is a fallback; metadata in test cases is preferred.
    # If metadata.rego_query_path is not set, it will try to construct from package + default rule name.
    semantic_validator = ScenarioBasedSemanticValidator(default_rego_query_path="data.system.allow") # Generic default

    validation_results = semantic_validator.validate_semantics(
        policy_code=auth_policy_code,
        policy_id=auth_policy_id,
        test_cases=all_test_cases # Validator will filter by policy_id
    )

    print(f"\nSemantic Validation Results for Policy '{auth_policy_id}':")
    passed_count = 0
    failed_cases = []
    if validation_results: # Check if any results were returned
        for case_id, passed, message, actual, expected in validation_results:
            print(f"  Test Case ID: {case_id}")
            print(f"    Passed: {passed}")
            print(f"    Message: {message}")
            if passed:
                passed_count +=1
            else:
                failed_cases.append(case_id)
        
        total_relevant_cases = len([tc for tc in all_test_cases if tc.policy_under_test_id == auth_policy_id])
        print(f"\nSummary: {passed_count}/{total_relevant_cases} test cases passed for policy '{auth_policy_id}'.")
        if failed_cases:
            print(f"Failed cases: {', '.join(failed_cases)}")

        # Basic assertions for the example
        # These depend on OPA being correctly installed and configured.
        if total_relevant_cases > 0:
            assert len(validation_results) == total_relevant_cases
            # Find results by case_id for robust assertion
            results_map = {res[0]: res for res in validation_results}
            assert results_map[tc1.case_id][1] is True # AdminAccessToAny
            assert results_map[tc2.case_id][1] is True # EditorAccessToDocument
            assert results_map[tc3.case_id][1] is True # EditorDeniedOtherResource (expected False, got False -> test passes)
            print("\nAll assertions passed for ScenarioBasedSemanticValidator example (if OPA is functional).")
    else:
        print("\nNote: Validation results were empty or not generated. This might indicate an issue with OPA setup "
              "or that no relevant test cases were found (though example has relevant cases).")
    
    print("\nScenarioBasedSemanticValidator example completed.")
    print("Note: For these examples to pass as asserted, OPA executable must be installed and in the PATH.")
