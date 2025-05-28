"""
test_policy_synthesizer.py

This module contains unit tests for the policy synthesis services,
primarily focusing on the LLMPolicyGenerator.
"""

import unittest
import os
import sys
import re # For checking prompt/response contents

# Adjust import path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from alphaevolve_gs_engine.services.llm_service import MockLLMService, get_llm_service, LLMService
from alphaevolve_gs_engine.services.policy_synthesizer import LLMPolicyGenerator, PolicySynthesisInput, PolicySuggestion
from alphaevolve_gs_engine.core.constitutional_principle import ConstitutionalPrinciple
from alphaevolve_gs_engine.core.operational_rule import OperationalRule


class TestLLMPolicyGenerator(unittest.TestCase):
    """Tests for the LLMPolicyGenerator."""

    def setUp(self):
        # Use a predictable MockLLMService for testing
        self.mock_llm_service = MockLLMService()
        
        # Custom mock that provides more structured output for parsing tests
        class CustomParseableMockLLM(MockLLMService):
            def generate_text(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.7, model:str=None) -> str:
                package_name = "mock.package"
                # Try to extract package name if prompted for Rego
                if "rego" in prompt.lower() and "package name" in prompt.lower():
                    match = re.search(r"package name to '([^']*)'", prompt) # Example prompt phrase
                    if not match: # Another common phrase from examples
                         match = re.search(r"package named '([^']*)'", prompt)
                    if match:
                        package_name = match.group(1)
                
                # Default Rego structure
                code = f"package {package_name}\n\ndefault allow = false\n\n# Mock rule based on: {prompt[:30]}...\nallow {{ input.user == \"test_user\" }}"
                expl = f"This mock policy was generated for testing based on the goal: '{prompt[:50]}...'. It uses package '{package_name}'."
                conf = 0.85 # Mock confidence

                return (f"POLICY_CODE_START\n{code}\nPOLICY_CODE_END\n"
                        f"EXPLANATION_START\n{expl}\nEXPLANATION_END\n"
                        f"CONFIDENCE_SCORE_START\n{conf}\nCONFIDENCE_SCORE_END\n") # MockLLM doesn't use confidence_score yet.

        self.custom_mock_llm = CustomParseableMockLLM()
        self.synthesizer = LLMPolicyGenerator(llm_service=self.custom_mock_llm)


    def test_synthesize_operational_rule_rego(self):
        """Test generating an operational rule in Rego format."""
        s_input = PolicySynthesisInput(
            synthesis_goal="Deny access to '/admin' path for non-admin users.",
            policy_type="operational_rule",
            desired_format="rego",
            constraints=["Package name must be 'company.web_security'."],
            context_data={"http_methods": ["GET", "POST"]}
        )
        
        # Override the synthesizer to use the custom mock that respects package name for this test
        self.synthesizer.llm_service = self.custom_mock_llm 
        
        suggestion = self.synthesizer.synthesize_policy(s_input)

        self.assertIsNotNone(suggestion)
        self.assertIsInstance(suggestion, PolicySuggestion)
        self.assertTrue(suggestion.suggested_policy_code.strip().startswith("package company.web_security"))
        self.assertIn("default allow = false", suggestion.suggested_policy_code) # Common for deny-oriented rules
        self.assertIn("This mock policy was generated for testing", suggestion.explanation)
        # self.assertEqual(suggestion.confidence_score, 0.85) # If confidence parsing is added

    def test_synthesize_constitutional_principle_natural_language(self):
        """Test generating a constitutional principle in natural language."""
        s_input = PolicySynthesisInput(
            synthesis_goal="Ensure AI systems are transparent in their decision-making.",
            policy_type="constitutional_principle",
            desired_format="structured_natural_language", # Expecting text, not Rego
            constraints=["Must include a clause on auditability."]
        )
        # Use the default mock LLM for this, as custom one is Rego-focused
        self.synthesizer.llm_service = self.mock_llm_service 
        
        suggestion = self.synthesizer.synthesize_policy(s_input)

        self.assertIsNotNone(suggestion)
        self.assertIsInstance(suggestion, PolicySuggestion)
        # For natural language, code might be a formatted string. MockLLM is generic.
        # A real LLM would produce more structured natural language.
        self.assertIn("Mock response to: 'You are an expert AI policy engineer.", suggestion.suggested_policy_code)
        self.assertIn("Ensure AI systems are transparent", suggestion.explanation) # From the goal
        self.assertIn("auditability", suggestion.explanation) # From constraints

    def test_prompt_construction(self):
        """Test the _construct_prompt method for including all necessary details."""
        cp1 = ConstitutionalPrinciple("CP001", "Fairness", "Desc1", "Ethics", "code1")
        or1 = OperationalRule("OR001", "DataUsage", "Desc2", "code2", ["CP001"])
        
        s_input = PolicySynthesisInput(
            synthesis_goal="Goal XYZ.",
            policy_type="operational_rule",
            desired_format="rego",
            existing_policies=[cp1, or1],
            constraints=["Constraint A.", "Constraint B."],
            context_data={"key1": "value1", "sensitive_data_example": "long string" * 100}, # Test truncation
            target_id="OR_Refine_Target"
        )
        
        prompt = self.synthesizer._construct_prompt(s_input)

        self.assertIn("Goal XYZ.", prompt)
        self.assertIn("operational_rule", prompt)
        self.assertIn("refinement of an existing policy with ID 'OR_Refine_Target'", prompt)
        self.assertIn("rego", prompt)
        self.assertIn("package system.generated_policies", prompt) # Default package hint for Rego
        self.assertIn("Policy ID CP001: Desc1", prompt)
        self.assertIn("Policy ID OR001: Desc2", prompt)
        self.assertIn("Constraint A.", prompt)
        self.assertIn("Constraint B.", prompt)
        self.assertIn("key1: value1", prompt)
        self.assertTrue(len(prompt) < 5000, "Prompt should not be excessively long with truncated context.") # Rough check
        self.assertIn("POLICY_CODE_START", prompt) # Check for output structure hints
        self.assertIn("EXPLANATION_START", prompt)

    def test_parse_llm_response_full(self):
        """Test parsing a well-formed LLM response."""
        raw_response = (
            "Some preamble text.\n"
            "POLICY_CODE_START\npackage example\ndefault allow = true\nPOLICY_CODE_END\n"
            "Some intermediate text.\n"
            "EXPLANATION_START\nThis is the explanation.\nPOLICY_CODE_END\n" # Mistake: POLICY_CODE_END again
            "EXPLANATION_END\n" # Correct end for explanation
            "CONFIDENCE_SCORE_START\n0.9\nCONFIDENCE_SCORE_END\n"
            "Some postamble text."
        )
        # Fix the mistaken POLICY_CODE_END in the raw_response for this test path
        fixed_raw_response = raw_response.replace("POLICY_CODE_END\nSome intermediate text.\nEXPLANATION_START", 
                                                  "POLICY_CODE_END\nEXPLANATION_START")


        code, explanation, confidence = self.synthesizer._parse_llm_response(fixed_raw_response)
        
        self.assertEqual(code, "package example\ndefault allow = true")
        self.assertEqual(explanation, "This is the explanation.")
        # self.assertEqual(confidence, 0.9) # Confidence parsing not active in current PolicySynthesizer

    def test_parse_llm_response_missing_parts(self):
        """Test parsing when parts of the response are missing."""
        # Missing explanation
        raw_resp_no_expl = "POLICY_CODE_START\ncode here\nPOLICY_CODE_END\n"
        code, explanation, _ = self.synthesizer._parse_llm_response(raw_resp_no_expl)
        self.assertEqual(code, "code here")
        self.assertIsNone(explanation) # Should be None if block is entirely missing

        # Missing code
        raw_resp_no_code = "EXPLANATION_START\nexplanation here\nEXPLANATION_END\n"
        code, explanation, _ = self.synthesizer._parse_llm_response(raw_resp_no_code)
        self.assertIsNone(code)
        self.assertEqual(explanation, "explanation here")

        # Malformed (no delimiters) - should use full output as explanation, no code
        raw_resp_malformed = "This is just plain text without delimiters."
        code, explanation, _ = self.synthesizer._parse_llm_response(raw_resp_malformed)
        self.assertIsNone(code)
        self.assertEqual(explanation, raw_resp_malformed)


    def test_synthesis_failure_if_llm_fails(self):
        """Test that synthesis returns None or error indication if LLM service raises an error."""
        class FailingLLM(LLMService): # Minimal LLMService that always fails
            def generate_text(self, prompt: str, max_tokens: int = 1, temperature: float = 0, model:str=None) -> str:
                raise Exception("LLM API simulated error")
from typing import Dict

class FailingLLM(LLMService): # Minimal LLMService that always fails
    def generate_text(self, prompt: str, max_tokens: int = 1, temperature: float = 0, model:str=None) -> str:
        raise Exception("LLM API simulated error")
    def generate_structured_output(self, prompt: str, output_format: Dict, max_tokens: int =1, temperature: float=0, model:str=None) -> Dict:
        raise Exception("LLM API simulated error for structured")

        failing_synthesizer = LLMPolicyGenerator(llm_service=FailingLLM())
        s_input = PolicySynthesisInput("Test goal", "operational_rule")
        
        suggestion = failing_synthesizer.synthesize_policy(s_input)
        self.assertIsNone(suggestion, "Policy suggestion should be None if LLM service fails.")

    def test_synthesis_failure_if_llm_returns_empty_code(self):
        """Test behavior when LLM returns a response that parses to empty/None code."""
        class EmptyCodeLLM(MockLLMService):
            def generate_text(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.7, model:str=None) -> str:
                return ("POLICY_CODE_START\n\nPOLICY_CODE_END\n" # Empty code
                        "EXPLANATION_START\nExplanation for empty code.\nEXPLANATION_END\n")

        empty_code_synthesizer = LLMPolicyGenerator(llm_service=EmptyCodeLLM())
        s_input = PolicySynthesisInput("Test goal for empty code", "operational_rule")
        suggestion = empty_code_synthesizer.synthesize_policy(s_input)

        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.suggested_policy_code, "") # Code should be empty string
        self.assertIn("Explanation for empty code", suggestion.explanation)
        self.assertEqual(suggestion.confidence_score, 0.0) # Low confidence expected


if __name__ == '__main__':
    unittest.main(verbosity=2)
