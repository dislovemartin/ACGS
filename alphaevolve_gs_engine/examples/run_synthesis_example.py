"""
run_synthesis_example.py

This script demonstrates a basic example of using the PolicySynthesizer
to generate a new policy based on a defined goal.

It showcases:
1. Setting up a mock LLM service.
2. Initializing the LLMPolicyGenerator.
3. Defining a policy synthesis input.
4. Running the synthesis process.
5. Displaying the suggested policy.
"""

import os
import sys

# Adjust path to import from the src directory if running from examples folder
# This is a common pattern for examples that are not part of an installed package.
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(os.path.dirname(os.path.dirname(current_dir)), "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from alphaevolve_gs_engine.services.llm_service import get_llm_service, MockLLMService
from alphaevolve_gs_engine.services.policy_synthesizer import LLMPolicyGenerator, PolicySynthesisInput
from alphaevolve_gs_engine.utils.logging_utils import setup_logger
from alphaevolve_gs_engine.core.constitutional_principle import ConstitutionalPrinciple

# Setup logger for the example
logger = setup_logger("PolicySynthesisExample", level="INFO") # Use "DEBUG" for more verbosity

def run_example():
    """
    Runs the policy synthesis example.
    """
    logger.info("Starting policy synthesis example...")

    # 1. Setup LLM Service (using Mock for this example)
    # To use OpenAI, ensure OPENAI_API_KEY is set in your environment or .env file
    # and change "mock" to "openai".
    # llm_service_type = "openai" if os.getenv("OPENAI_API_KEY") else "mock"
    llm_service_type = "mock" # Force mock for this example to ensure it runs without API key
    
    if llm_service_type == "mock":
        logger.info("Using MockLLMService for policy synthesis.")
        # Customize mock LLM behavior if needed for more specific example outputs
        # For instance, make the mock LLM actually generate some valid Rego-like code
        class CustomMockLLM(MockLLMService):
            def generate_text(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.7, model:str=None) -> str:
                # Simple mock Rego generation based on keywords in prompt
                if "operational_rule" in prompt.lower() and "rego" in prompt.lower():
                    package_name = "company.access_control" # Default
                    if "package name" in prompt:
                        try:
                            # Attempt to extract package name from prompt (very basic)
                            import re
                            match = re.search(r"package named '([^']*)'", prompt)
                            if match:
                                package_name = match.group(1)
                        except Exception:
                            pass  # Ignore if regex fails

                    mock_rego_code = f"""
POLICY_CODE_START
package {package_name}

default allow = false

# Rule: Deny access if resource is confidential and domain is external.
allow {{
    not (input.resource.tag == "confidential" and ends_with(input.user.email, "@external_domain.com"))
}}
# This is a mock generated Rego policy.
POLICY_CODE_END
EXPLANATION_START
This Rego policy implements the denial for users from 'external_domain.com' accessing 'confidential' resources.
It defaults to 'allow = false' and then sets 'allow = true' only if the condition (confidential resource AND external user) is NOT met.
This effectively means if the condition IS met, 'allow' remains false.
The package name '{package_name}' has been used as requested.
EXPLANATION_END
"""
                    return mock_rego_code
                elif "constitutional_principle" in prompt.lower():
                    return """
POLICY_CODE_START
# Principle Title: AI Prioritization of Human Well-being

**Core Statement:** All AI systems developed or deployed under this governance framework must prioritize human well-being, safety, and fundamental rights above purely operational goals or efficiency gains.

**Clauses:**
1.  **Risk Assessment:** AI systems must undergo rigorous risk assessment for potential harm to humans.
2.  **Benefit Maximization:** Where choices exist, AI actions should favor outcomes that maximize human benefit and minimize negative impacts.
3.  **Human Oversight:** Critical decisions with significant impact on human well-being must involve meaningful human oversight.
POLICY_CODE_END
EXPLANATION_START
This constitutional principle establishes a clear hierarchy where human well-being is paramount. It is articulated in structured natural language with a title and actionable clauses to guide AI development and operation.
EXPLANATION_END
"""
                return super().generate_text(prompt, max_tokens, temperature)

        llm_service = CustomMockLLM(delay=0) # No delay for faster example
    else: # "openai"
        logger.info("Attempting to use OpenAILLMService. Ensure API key is available.")
        try:
            llm_service = get_llm_service("openai")
            # Test with a simple call to ensure it's working
            llm_service.generate_text("Test: What is 1+1?", max_tokens=10)
            logger.info("OpenAILLMService seems to be working.")
        except Exception as e:
            logger.error(f"Failed to initialize or use OpenAILLMService: {e}. Falling back to MockLLMService.")
            llm_service = CustomMockLLM(delay=0)


    # 2. Initialize Policy Synthesizer
    policy_synthesizer = LLMPolicyGenerator(llm_service=llm_service)

    # 3. Define Policy Synthesis Input
    # Example: Create an operational rule for data access based on user roles.
    synthesis_goal_op_rule = (
        "Generate an operational rule in Rego format. "
        "This rule should allow users with the 'researcher' role to access datasets tagged as 'anonymized_data'. "
        "Users with the 'auditor' role should be allowed to access any dataset if the access purpose is 'compliance_check'. "
        "All other access requests should be denied by default. The package should be 'data_access_policy'."
    )
    
    # Define an existing constitutional principle for context
    existing_cp = ConstitutionalPrinciple(
        principle_id="CP001",
        name="Data Minimization",
        description="AI systems should only access data essential for their current task.",
        category="DataPrivacy",
        policy_code="# Conceptual: data_access_scope == 'minimal'" # Not Rego, just text
    )

    operational_rule_input = PolicySynthesisInput(
        synthesis_goal=synthesis_goal_op_rule,
        policy_type="operational_rule",
        desired_format="rego",
        existing_policies=[existing_cp], # Provide context
        constraints=[
            "The rule must explicitly default to deny.",
            "Package name must be 'data_access_policy'.",
            "Consider the 'Data Minimization' principle (CP001)."
        ],
        context_data={"available_roles": ["researcher", "auditor", "analyst"],
                      "dataset_tags": ["anonymized_data", "pii_data", "research_data"]}
    )
    logger.info(f"Synthesizing new operational rule with goal: '{operational_rule_input.synthesis_goal[:100]}...'")

    # 4. Run Synthesis for the Operational Rule
    suggestion_op_rule = policy_synthesizer.synthesize_policy(operational_rule_input)

    # 5. Display Suggestion for Operational Rule
    if suggestion_op_rule:
        logger.info("Successfully synthesized an operational rule suggestion:")
        print("\n--- Suggested Operational Rule ---")
        print(f"Source: {suggestion_op_rule.source_synthesizer}")
        print(f"Confidence: {suggestion_op_rule.confidence_score if suggestion_op_rule.confidence_score is not None else 'N/A'}")
        print("Policy Code (Rego):")
        print(suggestion_op_rule.suggested_policy_code)
        print("\nExplanation:")
        print(suggestion_op_rule.explanation)
    else:
        logger.error("Failed to synthesize an operational rule suggestion.")

    # --- Example 2: Synthesize a Constitutional Principle ---
    synthesis_goal_cp = (
        "Draft a new constitutional principle focused on 'AI Explainability'. "
        "This principle should state that decisions made by AI systems, especially critical ones, "
        "must be explainable to affected parties in an understandable manner."
    )
    
    cp_input = PolicySynthesisInput(
        synthesis_goal=synthesis_goal_cp,
        policy_type="constitutional_principle",
        desired_format="structured_natural_language", # Requesting natural language
        constraints=["The principle should be concise, impactful, and include at least two sub-clauses detailing aspects of explainability."]
    )
    logger.info(f"\nSynthesizing new constitutional principle with goal: '{cp_input.synthesis_goal[:100]}...'")
    
    suggestion_cp = policy_synthesizer.synthesize_policy(cp_input)

    if suggestion_cp:
        logger.info("Successfully synthesized a constitutional principle suggestion:")
        print("\n--- Suggested Constitutional Principle ---")
        print(f"Source: {suggestion_cp.source_synthesizer}")
        print(f"Confidence: {suggestion_cp.confidence_score if suggestion_cp.confidence_score is not None else 'N/A'}")
        print("Principle Text:")
        print(suggestion_cp.suggested_policy_code) # This should be natural language
        print("\nExplanation:")
        print(suggestion_cp.explanation)
    else:
        logger.error("Failed to synthesize a constitutional principle suggestion.")


    logger.info("\nPolicy synthesis example completed.")

if __name__ == "__main__":
    run_example()
