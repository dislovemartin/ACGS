"""
test_validators.py

This module contains unit tests for the various validation services in
`alphaevolve_gs_engine.services.validation`.

It tests:
- SyntacticValidator
- SemanticValidator (ScenarioBased)
- FormalVerifier (Mock)
- SafetyValidator (PatternBased and Mocked SimulationBased)
- BiasValidator (FairnessMetricValidator - Mocked OPA, and LLMBiasReviewer - Mocked LLM)
- ConflictValidator (OPAConflictDetector - Mocked with temp Rego files)
"""

import unittest
import os
import sys
import tempfile
import shutil # For cleaning up temp directories if created

# Adjust import path
current_dir = os.path.dirname(os.path.abspath(__file__))
# Navigate up to 'alphaevolve_gs_engine' then into 'src'
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from alphaevolve_gs_engine.services.validation.syntactic_validator import SyntacticValidator
from alphaevolve_gs_engine.services.validation.semantic_validator import ScenarioBasedSemanticValidator, SemanticTestCase
from alphaevolve_gs_engine.services.validation.formal_verifier import MockFormalVerifier, FormalVerificationProperty
from alphaevolve_gs_engine.services.validation.safety_validator import (
    PatternBasedSafetyValidator, 
    SimulationBasedSafetyValidator, # This is mocked for simulation part
    SafetyAssertion
)
from alphaevolve_gs_engine.services.validation.bias_validator import (
    FairnessMetricValidator, # OPA part is mocked in its example, will be here too
    LLMBiasReviewer,         # LLM part is mocked
    BiasMetric
)
from alphaevolve_gs_engine.services.validation.conflict_validator import OPAConflictDetector, ConflictDefinition
from alphaevolve_gs_engine.services.llm_service import get_llm_service # For LLMBiasReviewer


# Helper: Define some common Rego policies for testing
VALID_REGO_POLICY = """
package test.valid
default allow = false
allow { input.user.role == "admin" }
"""

INVALID_REGO_POLICY_SYNTAX = """
package test.invalid_syntax
default allow = wrong_keyword # syntax error
allow { input.user.role = "admin" } 
"""

# For Semantic and Safety tests
COMPLEX_REGO_POLICY = """
package company.firewall
default allow = false
allow { input.action == "read"; input.user.clearance >= 5 }
allow { input.user.role == "superuser" }

# Unsafe if this pattern is present and should_match=True for pattern validator
unsafe_operation_debug_mode_active { input.system.debug_mode == true }

# For bias testing: Loan approval
default approve_loan = false
approve_loan { input.applicant.credit_score > 700; input.applicant.income > 50000 }
approve_loan = false { input.applicant.age < 21 } # Potential bias source
"""
POLICY_ID_COMPLEX = "FirewallAndLoanPolicy"


class TestSyntacticValidator(unittest.TestCase):
    """Tests for SyntacticValidator."""

    @classmethod
    def setUpClass(cls):
        # Check OPA availability once for this test class
        cls.opa_available = False
        try:
            validator = SyntacticValidator() # Tries to run 'opa version'
            # If SyntacticValidator's _check_opa_availability logs an error, it means OPA isn't found.
            # We can't directly check that log here easily without capturing stdout/stderr.
            # A more robust check would be to try validating a simple policy.
            is_valid, _ = validator.validate_rego_policy("package test\ndefault allow=false", "SetupCheck")
            if "OPA executable not found" not in _: # If message doesn't indicate OPA is missing
                cls.opa_available = True
        except Exception: # Broad exception if OPA interaction itself fails badly
            pass
        
        if not cls.opa_available:
            print("\nWARNING: OPA executable not found or not working. Some SyntacticValidator tests will be skipped or may fail expectedly.")
            
    def setUp(self):
        self.validator = SyntacticValidator()
        # Skip tests if OPA is not available and the test relies on it.
        if not TestSyntacticValidator.opa_available:
             # self.skipTest("OPA executable not available, skipping SyntacticValidator tests that rely on it.")
             # Instead of skipping, we'll let tests run and they should gracefully handle OPA absence
             # by returning (False, "OPA not found...") which we can assert.
             pass


    def test_valid_rego_policy(self):
        is_valid, message = self.validator.validate(VALID_REGO_POLICY, language="rego", policy_id="ValidSyntaxTest")
        if TestSyntacticValidator.opa_available:
            self.assertTrue(is_valid, f"Valid Rego policy failed validation. Message: {message}")
            self.assertIn("Policy is syntactically valid", message)
        else:
            self.assertFalse(is_valid)
            self.assertIn("OPA executable not found", message)


    def test_invalid_rego_policy_syntax(self):
        is_valid, message = self.validator.validate(INVALID_REGO_POLICY_SYNTAX, language="rego", policy_id="InvalidSyntaxTest")
        if TestSyntacticValidator.opa_available:
            self.assertFalse(is_valid, "Invalid Rego policy (syntax error) passed validation.")
            self.assertTrue("error" in message.lower() or "unexpected" in message.lower(), f"Error message for syntax error was not as expected: {message}")
        else:
            self.assertFalse(is_valid) # Should still be false if OPA not found
            self.assertIn("OPA executable not found", message)

    def test_empty_policy(self):
        is_valid, message = self.validator.validate("", language="rego", policy_id="EmptyPolicyTest")
        self.assertFalse(is_valid, "Empty policy should be considered invalid.")
        self.assertEqual(message, "Policy code is empty.")

    def test_unsupported_language(self):
        with self.assertRaises(NotImplementedError):
            self.validator.validate("some code", language="python_like")


class TestScenarioBasedSemanticValidator(unittest.TestCase):
    """Tests for ScenarioBasedSemanticValidator."""
    
    @classmethod
    def setUpClass(cls):
        cls.opa_available = False # Similar check as SyntacticValidator
        try:
            # ScenarioBasedSemanticValidator also checks OPA on init.
            # We can use its internal check or try a dummy eval.
            validator = ScenarioBasedSemanticValidator()
            # A more direct way to check if OPA is available for semantic validator
            # is to see if _evaluate_rego_policy returns an OPA-not-found error.
            _, err_msg = validator._evaluate_rego_policy("package test.sem", {}, "data.test.sem.allow", "SetupCheck")
            if not (err_msg and "OPA executable not found" in err_msg):
                cls.opa_available = True
        except Exception:
            pass
        if not cls.opa_available:
            print("\nWARNING: OPA executable not found or not working. ScenarioBasedSemanticValidator tests will be impacted.")

    def setUp(self):
        self.validator = ScenarioBasedSemanticValidator(default_rego_query_path="data.company.firewall.allow")
        if not TestScenarioBasedSemanticValidator.opa_available:
            # Most tests here will fail if OPA is not present, as they expect actual evaluation.
            # The validator itself should log errors but not crash.
            # Tests will assert based on expected outcomes, which will include OPA errors.
            pass

    def test_semantic_validation_correct_outcomes(self):
        test_cases = [
            SemanticTestCase(
                case_id="AdminSuperuserAccess",
                description="Superuser should always be allowed.",
                input_data={"user": {"role": "superuser"}, "action": "any", "clearance": 1},
                expected_outcome=True, # data.company.firewall.allow should be true
                policy_under_test_id=POLICY_ID_COMPLEX
            ),
            SemanticTestCase(
                case_id="NormalUserHighClearanceRead",
                description="Normal user with high clearance should be allowed to read.",
                input_data={"user": {"role": "user", "clearance": 6}, "action": "read"},
                expected_outcome=True,
                policy_under_test_id=POLICY_ID_COMPLEX
            ),
            SemanticTestCase(
                case_id="NormalUserLowClearanceRead",
                description="Normal user with low clearance should be denied read.",
                input_data={"user": {"role": "user", "clearance": 3}, "action": "read"},
                expected_outcome=False, # Should be denied
                policy_under_test_id=POLICY_ID_COMPLEX
            ),
        ]
        results = self.validator.validate_semantics(COMPLEX_REGO_POLICY, POLICY_ID_COMPLEX, test_cases)
        
        if TestScenarioBasedSemanticValidator.opa_available:
            self.assertEqual(len(results), 3)
            # Results are: (case_id, passed, message, actual_outcome, expected_outcome)
            self.assertTrue(results[0][1], f"Test case {results[0][0]} failed: {results[0][2]}") # AdminSuperuserAccess
            self.assertEqual(results[0][3], True) # Actual outcome for AdminSuperuserAccess
            self.assertTrue(results[1][1], f"Test case {results[1][0]} failed: {results[1][2]}") # NormalUserHighClearanceRead
            self.assertEqual(results[1][3], True)
            self.assertTrue(results[2][1], f"Test case {results[2][0]} failed: {results[2][2]}") # NormalUserLowClearanceRead
            self.assertEqual(results[2][3], False)
        else:
            # If OPA not available, all should "fail" with an OPA error message
            for res_tuple in results:
                self.assertFalse(res_tuple[1]) # Passed is False
                self.assertIn("OPA executable not found", res_tuple[2]) # Message indicates OPA error


    def test_no_relevant_test_cases(self):
        results = self.validator.validate_semantics(COMPLEX_REGO_POLICY, "NonExistentPolicyID", [])
        self.assertEqual(len(results), 0)


class TestMockFormalVerifier(unittest.TestCase):
    """Tests for MockFormalVerifier."""
    def setUp(self):
        self.verifier = MockFormalVerifier()

    def test_verify_properties_default_mock(self):
        props = [
            FormalVerificationProperty("Prop1_ExpectTrue", "Desc1", "query1", expected_outcome=True),
            FormalVerificationProperty("Prop2_ExpectFalse", "Desc2", "query2", expected_outcome=False)
        ]
        results = self.verifier.verify_properties([{"id": "P1", "code": "code1"}], props)
        
        self.assertTrue(results["Prop1_ExpectTrue"][0]) # Passed (mock aligns with expected_outcome=True)
        self.assertIn("holds", results["Prop1_ExpectTrue"][1].lower())
        
        self.assertTrue(results["Prop2_ExpectFalse"][0]) # Passed (mock aligns with expected_outcome=False)
        self.assertIn("correctly identified a scenario", results["Prop2_ExpectFalse"][1].lower())


    def test_verify_with_predefined_mock_results(self):
        mock_config = {
            "PropToFail": (False, "Mock: This property was configured to fail its expectation.")
        }
        verifier_configured = MockFormalVerifier(mock_results=mock_config)
        props = [
            FormalVerificationProperty("PropToFail", "Desc", "query", expected_outcome=True), # Expects True
            FormalVerificationProperty("PropToPass", "Desc", "query", expected_outcome=True)  # Expects True
        ]
        results = verifier_configured.verify_properties([{"id": "P1", "code": "code1"}], props)

        self.assertFalse(results["PropToFail"][0]) # Verification "failed" (result False != expected True)
        self.assertEqual(results["PropToFail"][1], "Mock: This property was configured to fail its expectation.")
        
        self.assertTrue(results["PropToPass"][0]) # Default mock behavior, passes


class TestPatternBasedSafetyValidator(unittest.TestCase):
    """Tests for PatternBasedSafetyValidator."""
    def setUp(self):
        self.validator = PatternBasedSafetyValidator()

    def test_unsafe_pattern_found(self):
        # This pattern exists in COMPLEX_REGO_POLICY
        assertion_unsafe_debug = SafetyAssertion(
            "SA_DebugMode", "Debug mode pattern should not be found.", "pattern_match",
            {"regex_pattern": r"unsafe_operation_debug_mode_active", "should_match": True}, # True means finding it is unsafe
            "critical"
        )
        results = self.validator.validate_safety(COMPLEX_REGO_POLICY, POLICY_ID_COMPLEX, [assertion_unsafe_debug])
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0][1], "Safety assertion should fail as unsafe pattern is present.") # passed = False
        self.assertIn("Unsafe pattern", results[0][2])
        self.assertIn("found", results[0][2])

    def test_required_safe_pattern_missing(self):
        assertion_require_specific_comment = SafetyAssertion(
            "SA_RequireComment", "A specific safety comment must be present.", "pattern_match",
            {"regex_pattern": r"# SAFETY_CRITICAL_SECTION_REVIEWED_BY_ALICE", "should_match": False}, # False means NOT finding it is unsafe
            "high"
        )
        results = self.validator.validate_safety(COMPLEX_REGO_POLICY, POLICY_ID_COMPLEX, [assertion_require_specific_comment])
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0][1], "Safety assertion should fail as required pattern is missing.") # passed = False
        self.assertIn("Required safe pattern", results[0][2])
        self.assertIn("NOT found", results[0][2])

    def test_safe_pattern_conditions_met(self):
        # Pattern for something that *should not* be there, and it isn't.
        assertion_no_hardcoded_secret = SafetyAssertion(
            "SA_NoSecret", "No hardcoded 'SECRET_KEY'.", "pattern_match",
            {"regex_pattern": r"SECRET_KEY\s*=\s*[\"']", "should_match": True}, # True means finding it is unsafe
            "critical"
        )
        results_no_secret = self.validator.validate_safety(COMPLEX_REGO_POLICY, POLICY_ID_COMPLEX, [assertion_no_hardcoded_secret])
        self.assertTrue(results_no_secret[0][1], "Assertion should pass as hardcoded secret pattern is not found.")

        # Pattern for something that *should* be there, and it is.
        assertion_has_package = SafetyAssertion(
            "SA_HasPackage", "Policy must have a package declaration.", "pattern_match",
            {"regex_pattern": r"^package\s+\w+", "should_match": False}, # False means NOT finding it is unsafe
            "medium"
        )
        results_has_package = self.validator.validate_safety(COMPLEX_REGO_POLICY, POLICY_ID_COMPLEX, [assertion_has_package])
        self.assertTrue(results_has_package[0][1], "Assertion should pass as package declaration is present.")


class TestSimulationBasedSafetyValidator(unittest.TestCase):
    """Tests for SimulationBasedSafetyValidator (mocked behavior)."""
    def setUp(self):
        self.validator = SimulationBasedSafetyValidator() # Mocked, no OPA needed for test logic

    def test_simulation_check_mocked(self):
        # This test relies on the mock behavior of _run_simulation
        sim_assertion = SafetyAssertion(
            "SA_SimTest", "Mock simulation for safety.", "simulation_check",
            {
                "scenario_input": {"user": "test", "action": "delete"},
                "expected_query_path": "data.company.firewall.allow", # Example
                "expected_query_result": False # Expect action to be disallowed
            },
            "high"
        )
        results = self.validator.validate_safety(COMPLEX_REGO_POLICY, POLICY_ID_COMPLEX, [sim_assertion])
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0][1], "Mocked simulation should pass by default.")
        self.assertIn("Mock simulation passed", results[0][2])


class TestFairnessMetricValidator(unittest.TestCase):
    """Tests for FairnessMetricValidator (mocked OPA)."""
    def setUp(self):
        self.validator = FairnessMetricValidator() # OPA part is mocked in its methods
        self.dataset = [
            {"applicant": {"credit_score": 750, "income": 60000, "age": 30, "ethnicity": "GroupA"}}, # Mock outcome: True
            {"applicant": {"credit_score": 650, "income": 70000, "age": 40, "ethnicity": "GroupA"}}, # Mock outcome: False
            {"applicant": {"credit_score": 720, "income": 80000, "age": 20, "ethnicity": "GroupB"}}, # Mock outcome: True (age rule ignored by mock outcome)
            {"applicant": {"credit_score": 780, "income": 55000, "age": 35, "ethnicity": "GroupB"}}, # Mock outcome: False
            {"applicant": {"credit_score": 710, "income": 60000, "age": 25, "ethnicity": "GroupA"}}, # Mock outcome: True
        ]
        self.dp_metric = BiasMetric(
            "DP001_Test", "Demographic Parity Test", "Desc", "statistical",
            {
                "protected_attribute_query": "applicant.ethnicity",
                "favorable_outcome_query": "data.company.firewall.approve_loan", # Matches COMPLEX_REGO_POLICY
                "group_definitions": {"Alpha": ["GroupA"], "Beta": ["GroupB"]},
                "threshold": 0.80
            }
        )

    def test_demographic_parity_calculation(self):
        # Mock outcomes: GroupA (T,F,T) -> 2/3 = 0.66; GroupB (T,F) -> 1/2 = 0.5
        # Ratio: 0.5 / 0.66 = ~0.75. Threshold 0.8. Should fail.
        results = self.validator.assess_bias(COMPLEX_REGO_POLICY, POLICY_ID_COMPLEX, [self.dp_metric], self.dataset)
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0][1], f"Demographic parity should fail. Msg: {results[0][2]}")
        self.assertAlmostEqual(results[0][3], 0.5 / (2/3), places=3) # metric_value

    def test_dataset_not_provided(self):
        results = self.validator.assess_bias(COMPLEX_REGO_POLICY, POLICY_ID_COMPLEX, [self.dp_metric], None) # No dataset
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0][1])
        self.assertIn("Dataset not provided", results[0][2])


class TestLLMBiasReviewer(unittest.TestCase):
    """Tests for LLMBiasReviewer (mocked LLM)."""
    def setUp(self):
        mock_llm_service = get_llm_service("mock") # Use a standard mock LLM
        self.reviewer = LLMBiasReviewer(llm_service=mock_llm_service)
        self.review_metric = BiasMetric(
            "QL_Review01", "LLM Qualitative Bias Review", "Desc", "qualitative_review",
            {"llm_prompt_template": "Review for bias: {policy_code}"}
        )

    def test_qualitative_review_mocked_llm(self):
        # MockLLMService's default response is generic.
        # We expect it to "pass" (i.e., mock doesn't find bias by default).
        results = self.reviewer.assess_bias(COMPLEX_REGO_POLICY, POLICY_ID_COMPLEX, [self.review_metric])
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0][1], "Mocked LLM review should pass by default.")
        self.assertIn("LLM Review (Mock)", results[0][2])


class TestOPAConflictDetector(unittest.TestCase):
    """Tests for OPAConflictDetector."""
    
    @classmethod
    def setUpClass(cls):
        cls.opa_available = False # Similar check as SyntacticValidator
        # Create a temporary Rego file for conflict checking logic for this test class
        cls.temp_conflict_rego_dir = tempfile.mkdtemp()
        cls.conflict_rules_rego_path = os.path.join(cls.temp_conflict_rego_dir, "test_conflict_rules.rego")
        
        # This is a simplified conflict detection rule for testing purposes.
        # It assumes policies are loaded into specific packages or paths.
        conflict_rego_content = """
        package test.conflict_checker
        # Conflict if policyA.allow is true and policyB.deny is true for the same input.
        # Assumes policyA code is in data.policyA and policyB code in data.policyB for OPA eval.
        # This is a very simplified model of how policies would be namespaced.
        permit_deny_conflict[info] {
            data.policyA.allow == true # hypothetical path for policy A
            data.policyB.deny == true   # hypothetical path for policy B
            info := {
                "type": "PermitDeny",
                "conflicting_policies_mock": ["PolicyA_ID", "PolicyB_ID"], # Hardcoded for test simplicity
                "trigger_input": input
            }
        }
        """
        with open(cls.conflict_rules_rego_path, "w") as f:
            f.write(conflict_rego_content)

        try:
            # Check OPA availability by attempting to init the detector
            # It runs 'opa version'
            detector = OPAConflictDetector(conflict_check_rego_files=[cls.conflict_rules_rego_path])
            # A more direct check:
            _, err_msg = detector._run_opa_eval_for_conflicts(
                [], "data.test.conflict_checker.permit_deny_conflict", None
            )
            if not (err_msg and "OPA executable not found" in err_msg):
                 cls.opa_available = True
        except Exception:
            pass
        if not cls.opa_available:
            print("\nWARNING: OPA executable not found. OPAConflictDetector tests will be impacted.")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_conflict_rego_dir) # Clean up temp directory and file

    def setUp(self):
        self.detector = OPAConflictDetector(conflict_check_rego_files=[self.conflict_rules_rego_path])
        
        # Define policies that would conflict based on the simple rule in test_conflict_rules.rego
        # For OPA eval, these need to be loadable such that `data.policyA.allow` and `data.policyB.deny` are valid paths.
        # This means their package names should align if loaded together.
        self.policy_A_code = """
        package policyA  # This makes its rules available under data.policyA
        default allow = false
        allow { input.user == "alice" }
        """
        self.policy_B_code = """
        package policyB  # This makes its rules available under data.policyB
        default deny = false
        deny { input.action == "delete" }
        """
        self.policies_to_check = [
            {"id": "PolicyA_ID", "code": self.policy_A_code},
            {"id": "PolicyB_ID", "code": self.policy_B_code}
        ]
        self.conflict_def = ConflictDefinition(
            "CD_PermitDeny_Test", "Permit-Deny Test", "Desc",
            "data.test.conflict_checker.permit_deny_conflict", # Query from our temp Rego file
            "high"
        )

    def test_conflict_detection_trigger(self):
        # Input that should make policyA.allow=true and policyB.deny=true
        triggering_input = {"user": "alice", "action": "delete"}
        
        results = self.detector.find_conflicts(
            self.policies_to_check, [self.conflict_def], input_scenario=triggering_input
        )
        
        if TestOPAConflictDetector.opa_available:
            self.assertEqual(len(results), 1, f"Expected 1 conflict, got {len(results)}. Details: {results}")
            conflict = results[0]
            self.assertEqual(conflict["conflict_definition_id"], "CD_PermitDeny_Test")
            self.assertEqual(conflict["details"]["type"], "PermitDeny")
            # The conflicting_policies_mock is hardcoded in the test Rego for simplicity
            self.assertListEqual(conflict["details"]["conflicting_policies_mock"], ["PolicyA_ID", "PolicyB_ID"]) 
            self.assertEqual(conflict["details"]["trigger_input"], triggering_input)
        else:
            # If OPA not available, should get an error entry or empty list
            if results: # If there's an error entry
                self.assertTrue("error" in results[0] and "OPA executable not found" in results[0]["error"])
            # else: self.assertEqual(len(results),0) # Or it might be empty if error handling is different

    def test_no_conflict_scenario(self):
        non_triggering_input = {"user": "bob", "action": "read"} # Should not trigger conflict
        results = self.detector.find_conflicts(
            self.policies_to_check, [self.conflict_def], input_scenario=non_triggering_input
        )
        if TestOPAConflictDetector.opa_available:
            self.assertEqual(len(results), 0, f"Expected 0 conflicts, got {len(results)}. Details: {results}")
        else:
            if results:
                self.assertTrue("error" in results[0] and "OPA executable not found" in results[0]["error"])


if __name__ == '__main__':
    # Important: For OPA-dependent tests to run meaningfully, OPA must be installed and in PATH.
    # The tests attempt to handle OPA absence gracefully, but assertions might behave differently.
    print("Running validator tests. OPA-dependent tests will indicate if OPA is unavailable.")
    print("Ensure OPA is installed and in your PATH for full test coverage of validators.")
    unittest.main(verbosity=2)
