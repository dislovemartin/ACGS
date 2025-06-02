# backend/gs_service/app/core/llm_integration.py
import json
import logging
import os
from typing import Dict, List, Optional

# Third-party libraries for retry logic and LLM interaction
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError
import openai # Placeholder for actual OpenAI client library

from ..schemas import (LLMInterpretationInput, LLMSuggestedAtom,
                       LLMSuggestedRule, LLMStructuredOutput)
from .constitutional_prompting import constitutional_prompt_builder

logger = logging.getLogger(__name__)

# Configure basic logging if no configuration is set yet (e.g., for standalone testing)
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO)


class MockLLMClient:
    async def get_structured_interpretation(self, query: LLMInterpretationInput, wina_gating_mask: Optional[Dict[str, bool]] = None) -> LLMStructuredOutput:
        interpretations: List[LLMSuggestedRule] = []
        raw_llm_response = f"Mock interpretation for principle {query.principle_id}: {query.principle_content[:30]}..."
        logger.info(f"MockLLMClient: Processing query for principle ID {query.principle_id}")
        if wina_gating_mask:
            logger.info(f"MockLLMClient: Received WINA gating mask: {wina_gating_mask}")
            # In a real scenario, this mask would influence the mock response generation.
            # For example, if a key concept related to a neuron in the mask is 'off',
            # the mock might avoid generating rules related to that concept.
            # For now, just logging its presence.
            raw_llm_response += f" (WINA Gating Applied: {len(wina_gating_mask)} rules)"


        # Example: If principle mentions "user access control based on roles"
        if "user" in query.principle_content.lower() and "role" in query.principle_content.lower():
            head = LLMSuggestedAtom(predicate_name="allow_action", arguments=["User", "Action", "Resource"])
            body = [
                LLMSuggestedAtom(predicate_name="user_has_role", arguments=["User", "Role"]),
                LLMSuggestedAtom(predicate_name="role_has_permission_for_action", arguments=["Role", "Action", "Resource"])
            ]
            interpretations.append(LLMSuggestedRule(head=head, body=body, explanation="Standard RBAC check.", confidence=0.9))
        elif "data" in query.principle_content.lower() and "access" in query.principle_content.lower() and "sensitive" in query.principle_content.lower():
            head = LLMSuggestedAtom(predicate_name="may_access_sensitive_data", arguments=["User", "Data"])
            body = [
                LLMSuggestedAtom(predicate_name="user_is_authorized_for_sensitive", arguments=["User"]),
                LLMSuggestedAtom(predicate_name="data_is_classified_sensitive", arguments=["Data"])
            ]
            interpretations.append(LLMSuggestedRule(head=head, body=body, explanation="Access to sensitive data.", confidence=0.85))
        elif "log" in query.principle_content.lower() and ("action" in query.principle_content.lower() or "event" in query.principle_content.lower()):
            head = LLMSuggestedAtom(predicate_name="event_logged", arguments=["EventID", "Timestamp", "Actor", "Action", "Details"])
            body = [
                LLMSuggestedAtom(predicate_name="event_occurred", arguments=["EventID", "Timestamp", "Actor", "Action", "Details"])
            ]
            interpretations.append(LLMSuggestedRule(head=head, body=body, explanation="Logging of actions/events.", confidence=0.92))
        else:
            head_predicate_name = f"generic_compliance_fact_for_p{query.principle_id}"
            head = LLMSuggestedAtom(predicate_name=head_predicate_name, arguments=["DefaultContext"])
            interpretations.append(LLMSuggestedRule(head=head, body=[], explanation="Generic rule based on principle content.", confidence=0.5))

        logger.info(f"MockLLMClient: Generated {len(interpretations)} interpretation(s).")
        return LLMStructuredOutput(interpretations=interpretations, raw_llm_response=raw_llm_response)

    async def get_constitutional_synthesis(self, synthesis_input, wina_gating_mask: Optional[Dict[str, bool]] = None) -> 'ConstitutionalSynthesisOutput':
        """Mock implementation of constitutional synthesis."""
        from ..schemas import ConstitutionalSynthesisOutput, ConstitutionallyCompliantRule, ConstitutionalComplianceInfo

        logger.info(f"MockLLMClient: Performing mock constitutional synthesis for context '{synthesis_input.context}'")
        raw_response_addition = ""
        if wina_gating_mask:
            logger.info(f"MockLLMClient: Received WINA gating mask for CS: {wina_gating_mask}")
            raw_response_addition = f" (WINA Gating Applied to CS: {len(wina_gating_mask)} rules)"


        # Mock constitutional context
        mock_constitutional_context = {
            "context": synthesis_input.context,
            "category": synthesis_input.category,
            "principles": [
                {
                    "id": 1,
                    "name": "Mock Safety Principle",
                    "priority_weight": 0.9,
                    "category": "Safety",
                    "content": "AI systems must prioritize user safety"
                },
                {
                    "id": 2,
                    "name": "Mock Privacy Principle",
                    "priority_weight": 0.8,
                    "category": "Privacy",
                    "content": "User data must be protected"
                }
            ],
            "principle_count": 2
        }

        # Generate mock rules
        mock_rules = []
        for i, principle in enumerate(mock_constitutional_context["principles"]):
            rule_content = f"mock_constitutional_rule_{principle['id']}(X) :- {synthesis_input.context}_context(X), mock_principle_{principle['id']}_satisfied(X)."

            compliance_info = ConstitutionalComplianceInfo(
                principle_id=principle['id'],
                principle_name=principle['name'],
                priority_weight=principle['priority_weight'],
                influence_level="HIGH" if principle['priority_weight'] > 0.7 else "MEDIUM",
                compliance_score=0.9 - (i * 0.1)
            )

            mock_rule = ConstitutionallyCompliantRule(
                rule_content=rule_content,
                rule_format=synthesis_input.target_format,
                constitutional_compliance=[compliance_info],
                explanation=f"Mock rule for principle '{principle['name']}' in context '{synthesis_input.context}'",
                confidence=0.85 - (i * 0.05)
            )
            mock_rules.append(mock_rule)

        return ConstitutionalSynthesisOutput(
            context=synthesis_input.context,
            generated_rules=mock_rules,
            constitutional_context=mock_constitutional_context,
            synthesis_metadata={
                "principle_count": 2,
                "synthesis_method": "mock_constitutional_prompting",
                "target_format": synthesis_input.target_format
            },
            raw_llm_response=f"Mock constitutional synthesis for context '{synthesis_input.context}'{raw_response_addition}"
        )


class RealLLMClient:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo")
        if not self.api_key:
            logger.warning("OPENAI_API_KEY environment variable not set. RealLLMClient will not be able to make API calls.")
            # You might raise an error here or allow it to fail on first call depending on desired behavior
            # raise ValueError("OPENAI_API_KEY must be set to use RealLLMClient")

        # Initialize the OpenAI client if the API key is available
        # Note: The actual initialization might vary based on the version of the openai library
        # For example, older versions used `openai.api_key = self.api_key` globally.
        # Newer versions might use `self.client = openai.OpenAI(api_key=self.api_key)`
        try:
            self.client = openai.OpenAI(api_key=self.api_key) if self.api_key else None
            logger.info(f"RealLLMClient initialized with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.client = None


class GroqLLMClient:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model_name = os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")
        if not self.api_key:
            logger.warning("GROQ_API_KEY environment variable not set. GroqLLMClient will not be able to make API calls.")

        # Initialize the OpenAI client with Groq's endpoint if the API key is available
        try:
            self.client = openai.OpenAI(
                api_key=self.api_key,
                base_url="https://api.groq.com/openai/v1"
            ) if self.api_key else None
            logger.info(f"GroqLLMClient initialized with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
            self.client = None

    def _construct_prompt(self, query: LLMInterpretationInput, wina_gating_mask: Optional[Dict[str, bool]] = None) -> str:
        # Similar prompt construction as RealLLMClient but optimized for Llama models
        wina_directive = ""
        if wina_gating_mask:
            active_neurons = [nid for nid, active in wina_gating_mask.items() if active]
            inactive_neurons = [nid for nid, active in wina_gating_mask.items() if not active]
            wina_directive = f"\nWINA Gating Instructions:\n"
            if active_neurons:
                wina_directive += f"- Prioritize concepts related to: {', '.join(active_neurons)}\n"
            if inactive_neurons:
                wina_directive += f"- De-emphasize concepts related to: {', '.join(inactive_neurons)}\n"
            wina_directive += "Adjust your interpretation based on these WINA directives to optimize for computational efficiency while maintaining accuracy.\n"

        prompt = f"""
You are an AI assistant specialized in constitutional AI governance. Your task is to interpret constitutional principles and convert them into structured logical rules.
{wina_directive}
Constitutional Principle (ID: {query.principle_id}):
{query.principle_content}

Please analyze this principle and provide a structured interpretation in JSON format with the following structure:
{{
    "interpretations": [
        {{
            "head": {{
                "predicate_name": "string",
                "arguments": ["arg1", "arg2"]
            }},
            "body": [
                {{
                    "predicate_name": "string",
                    "arguments": ["arg1", "arg2"]
                }}
            ],
            "explanation": "string",
            "confidence": 0.0-1.0
        }}
    ],
    "raw_llm_response": "string"
}}

Focus on creating logical rules that capture the essence of the constitutional principle.
"""
        return prompt

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_structured_interpretation(self, query: LLMInterpretationInput, wina_gating_mask: Optional[Dict[str, bool]] = None) -> LLMStructuredOutput:
        if not self.client:
            logger.error("GroqLLMClient is not configured with an API key. Cannot make API calls.")
            return LLMStructuredOutput(interpretations=[], raw_llm_response="GroqLLMClient not configured.")

        prompt = self._construct_prompt(query, wina_gating_mask)
        logger.info(f"GroqLLMClient: Sending request to Groq for principle ID {query.principle_id}. Prompt length: {len(prompt)}")
        logger.debug(f"GroqLLMClient: Prompt for P{query.principle_id}:\n{prompt}")

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2048,
                temperature=0.3
            )

            raw_response_content = response.choices[0].message.content
            logger.info(f"GroqLLMClient: Received raw response for principle ID {query.principle_id}.")
            logger.debug(f"GroqLLMClient: Raw response content for P{query.principle_id}: {raw_response_content}")

            # Attempt to parse the LLM's JSON response
            try:
                parsed_data = json.loads(raw_response_content)
            except json.JSONDecodeError:
                # Try to extract JSON from the response if it's wrapped in text
                import re
                json_match = re.search(r'\{.*\}', raw_response_content, re.DOTALL)
                if json_match:
                    try:
                        parsed_data = json.loads(json_match.group())
                    except json.JSONDecodeError:
                        # Fallback to mock structure if JSON parsing fails
                        parsed_data = {
                            "interpretations": [{
                                "head": {"predicate_name": f"groq_interpreted_p{query.principle_id}", "arguments": ["Context"]},
                                "body": [{"predicate_name": "groq_condition", "arguments": ["Context"]}],
                                "explanation": f"Groq interpretation of principle {query.principle_id} (JSON parsing failed)",
                                "confidence": 0.6
                            }],
                            "raw_llm_response": raw_response_content
                        }
                else:
                    # Complete fallback
                    parsed_data = {
                        "interpretations": [{
                            "head": {"predicate_name": f"groq_interpreted_p{query.principle_id}", "arguments": ["Context"]},
                            "body": [{"predicate_name": "groq_condition", "arguments": ["Context"]}],
                            "explanation": f"Groq interpretation of principle {query.principle_id} (no JSON found)",
                            "confidence": 0.5
                        }],
                        "raw_llm_response": raw_response_content
                    }

            # Validate and structure the output using Pydantic models
            structured_output = LLMStructuredOutput(**parsed_data)
            logger.info(f"GroqLLMClient: Successfully parsed structured output for principle ID {query.principle_id}.")
            return structured_output

        except json.JSONDecodeError as e:
            logger.error(f"GroqLLMClient: JSONDecodeError for principle ID {query.principle_id}. Error: {e}")
            return LLMStructuredOutput(interpretations=[], raw_llm_response=f"Error decoding Groq JSON: {e}")
        except Exception as e:
            logger.error(f"GroqLLMClient: Unexpected error for principle ID {query.principle_id}. Error: {e}")
            raise


    def _construct_prompt(self, query: LLMInterpretationInput) -> str:
        # This is a placeholder for actual prompt engineering.
        # A real implementation would carefully craft a prompt to guide the LLM
        # to produce JSON output matching the LLMStructuredOutput schema.
        # It might include examples (few-shot prompting), specific instructions about
        # the desired JSON structure, and details from query.datalog_predicate_schema.
        
        schema_description = """
        The output should be a JSON object matching the following Pydantic schema:
        LLMStructuredOutput = {
            "interpretations": [
                {
                    "head": {"predicate_name": "string", "arguments": ["string", ...]},
                    "body": [{"predicate_name": "string", "arguments": ["string", ...]}, ...],
                    "explanation": "string",
                    "confidence": float (0.0 to 1.0)
                },
                ...
            ],
            "raw_llm_response": "string" // This will be the original full text from you.
        }
        Each rule should have a 'head' atom and a 'body' as a list of atoms.
        Arguments should be abstract placeholders (e.g., "User", "Resource", "Action")
        unless the principle implies specific values.
        """

        prompt = (
            f"Interpret the following principle into structured Datalog-like rules.\n"
            f"Principle ID: {query.principle_id}\n"
            f"Principle Content: \"{query.principle_content}\"\n"
            f"Relevant Datalog Predicate Schemas (if any, use these as guidance for predicate names and arguments):\n"
            f"{json.dumps(query.datalog_predicate_schema, indent=2) if query.datalog_predicate_schema else 'N/A'}\n\n"
            f"{schema_description}\n\n"
            f"Provide your interpretation as a JSON object as described above:"
        )
        return prompt

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=60), # Exponential backoff: 2s, 4s, 8s, ... up to 60s
        stop=stop_after_attempt(5), # Retry up to 5 times
        reraise=True, # Reraise the last exception if all retries fail
        before_sleep=lambda retry_state: logger.info(f"Retrying LLM call for principle {retry_state.args[0].principle_id if retry_state.args else 'unknown'} after {retry_state.attempt_number} attempt(s) due to {retry_state.outcome.exception()}...")
    )
    async def get_structured_interpretation(self, query: LLMInterpretationInput) -> LLMStructuredOutput:
        if not self.client:
            logger.error("RealLLMClient is not configured with an API key. Cannot make API calls.")
            # Fallback to a default error response or raise an exception
            return LLMStructuredOutput(interpretations=[], raw_llm_response="RealLLMClient not configured.")

        prompt = self._construct_prompt(query)
        logger.info(f"RealLLMClient: Sending request to LLM for principle ID {query.principle_id}. Prompt length: {len(prompt)}")
        logger.debug(f"RealLLMClient: Prompt for P{query.principle_id}:\n{prompt}")

        try:
            # Example using OpenAI's chat completions API (adjust based on actual library usage)
            # This is a synchronous call in the example; ensure your openai client setup is async or run this in a thread.
            # For an async library, it would be `await self.client.chat.completions.create(...)`
            # For simplicity, let's assume a hypothetical async call or that the library handles it.
            # If using a sync library in an async method, it should be wrapped with `asyncio.to_thread`.
            # For now, we'll simulate an async-compatible call structure.
            
            # This is a conceptual representation. Actual API call will vary.
            # response = await asyncio.to_thread(
            #     self.client.chat.completions.create,
            #     model=self.model_name,
            #     messages=[{"role": "user", "content": prompt}],
            #     response_format={"type": "json_object"} # If supported for structured output
            # )
            # raw_response_content = response.choices[0].message.content

            # MOCKING THE ACTUAL API CALL FOR NOW TO AVOID EXTERNAL DEPENDENCY DURING TEST
            # In a real scenario, the above lines would make the actual API call.
            # For this task, we'll simulate a response structure.
            logger.warning("RealLLMClient: Using MOCKED API call for get_structured_interpretation.")
            mock_json_response_content = {
                "interpretations": [
                    {
                        "head": {"predicate_name": f"interpreted_p{query.principle_id}", "arguments": ["Arg1", "Arg2"]},
                        "body": [{"predicate_name": "condition_for_p1", "arguments": ["Arg1"]}],
                        "explanation": f"Successfully interpreted principle {query.principle_id} by real LLM (mocked).",
                        "confidence": 0.75
                    }
                ],
                "raw_llm_response": f"This is a mocked raw response from RealLLMClient for principle {query.principle_id}."
            }
            raw_response_content = json.dumps(mock_json_response_content)
            # END OF MOCKED API CALL

            logger.info(f"RealLLMClient: Received raw response for principle ID {query.principle_id}.")
            logger.debug(f"RealLLMClient: Raw response content for P{query.principle_id}: {raw_response_content}")

            # Attempt to parse the LLM's JSON response
            parsed_data = json.loads(raw_response_content)
            
            # Validate and structure the output using Pydantic models
            # The LLM is asked to return the full LLMStructuredOutput structure.
            structured_output = LLMStructuredOutput(**parsed_data)
            
            # If the LLM only returns the 'interpretations' part, you'd do:
            # interpretations_data = parsed_data.get("interpretations", [])
            # interpretations = [LLMSuggestedRule(**rule_data) for rule_data in interpretations_data]
            # structured_output = LLMStructuredOutput(interpretations=interpretations, raw_llm_response=raw_response_content)
            
            logger.info(f"RealLLMClient: Successfully parsed response for principle ID {query.principle_id}. Found {len(structured_output.interpretations)} rule(s).")
            return structured_output

        except json.JSONDecodeError as e:
            logger.error(f"RealLLMClient: JSONDecodeError for principle ID {query.principle_id}. Raw response: {raw_response_content}. Error: {e}")
            # Return an empty/error structure or raise a specific exception
            return LLMStructuredOutput(interpretations=[], raw_llm_response=f"Error decoding LLM JSON: {e}. Original response: {raw_response_content}")
        except openai.APIError as e: # Catch specific OpenAI errors
            logger.error(f"RealLLMClient: OpenAI APIError for principle ID {query.principle_id}. Error: {e}")
            raise # Reraise to trigger tenacity retry
        except Exception as e:
            logger.error(f"RealLLMClient: Unexpected error for principle ID {query.principle_id}. Raw response: {raw_response_content}. Error: {e}")
            # Depending on policy, either reraise or return an error structure
            # For tenacity to work, reraising is often preferred for transient errors.
            # If it's a permanent error (e.g. bad prompt, unparseable response), might not want to retry.
            raise # Reraise to potentially trigger tenacity if it's a type of error covered by retry policy

    async def get_constitutional_synthesis(self, synthesis_input, wina_gating_mask: Optional[Dict[str, bool]] = None) -> 'ConstitutionalSynthesisOutput':
        """
        Perform constitutional synthesis using constitutional prompting methodology.

        Args:
            synthesis_input: ConstitutionalSynthesisInput containing synthesis parameters
            wina_gating_mask: Optional WINA gating mask to influence prompt generation

        Returns:
            ConstitutionalSynthesisOutput with constitutionally compliant rules
        """
        from ..schemas import ConstitutionalSynthesisOutput, ConstitutionallyCompliantRule, ConstitutionalComplianceInfo

        if not self.client:
            logger.error("RealLLMClient is not configured with an API key. Cannot make API calls.")
            return ConstitutionalSynthesisOutput(
                context=synthesis_input.context,
                generated_rules=[],
                constitutional_context={},
                synthesis_metadata={"error": "RealLLMClient not configured"},
                raw_llm_response="RealLLMClient not configured."
            )

        try:
            # Build constitutional context
            # The constitutional_prompt_builder might also need to be WINA-aware if principles themselves are modified by WINA
            # For now, assuming it provides standard context, and gating is applied at LLM call.
            constitutional_context = await constitutional_prompt_builder.build_constitutional_context(
                context=synthesis_input.context,
                category=synthesis_input.category,
                auth_token=synthesis_input.auth_token
            )

            # Build constitutional prompt - this is where wina_gating_mask can be integrated
            # by modifying how constitutional_prompt_builder.build_constitutional_prompt works,
            # or by augmenting the prompt string afterwards.
            # For simplicity, we'll augment the prompt string here if mask is present.
            
            base_constitutional_prompt = constitutional_prompt_builder.build_constitutional_prompt(
                constitutional_context=constitutional_context,
                synthesis_request=synthesis_input.synthesis_request,
                target_format=synthesis_input.target_format
            )

            wina_directive_cs = ""
            if wina_gating_mask:
                active_neurons = [nid for nid, active in wina_gating_mask.items() if active]
                inactive_neurons = [nid for nid, active in wina_gating_mask.items() if not active]
                wina_directive_cs = f"\nWINA Gating Instructions for Constitutional Synthesis:\n"
                if active_neurons:
                    wina_directive_cs += f"- Prioritize synthesis aspects related to: {', '.join(active_neurons)}\n"
                if inactive_neurons:
                    wina_directive_cs += f"- De-emphasize synthesis aspects related to: {', '.join(inactive_neurons)}\n"
                wina_directive_cs += "Adjust your synthesis based on these WINA directives.\n"
            
            constitutional_prompt = base_constitutional_prompt + wina_directive_cs


            logger.info(f"RealLLMClient: Performing constitutional synthesis for context '{synthesis_input.context}'. Prompt length: {len(constitutional_prompt)}")
            logger.debug(f"RealLLMClient: Constitutional prompt:\n{constitutional_prompt}")

            # MOCKED API CALL FOR NOW - Replace with actual OpenAI call
            logger.warning("RealLLMClient: Using MOCKED API call for constitutional synthesis.")

            # Simulate constitutional synthesis response
            principles = constitutional_context.get('principles', [])
            mock_rules = []

            for i, principle in enumerate(principles[:3]):  # Limit to top 3 principles
                rule_content = f"constitutional_rule_{principle['id']}(X) :- {synthesis_input.context}_context(X), principle_{principle['id']}_satisfied(X)."

                compliance_info = ConstitutionalComplianceInfo(
                    principle_id=principle['id'],
                    principle_name=principle['name'],
                    priority_weight=principle.get('priority_weight', 0.5),
                    influence_level="HIGH" if principle.get('priority_weight', 0.5) > 0.7 else "MEDIUM",
                    compliance_score=0.85 + (i * 0.05)  # Simulate varying compliance scores
                )

                mock_rule = ConstitutionallyCompliantRule(
                    rule_content=rule_content,
                    rule_format=synthesis_input.target_format,
                    constitutional_compliance=[compliance_info],
                    explanation=f"Rule generated to satisfy principle '{principle['name']}' in context '{synthesis_input.context}'",
                    confidence=0.8 + (i * 0.05)
                )
                mock_rules.append(mock_rule)

            raw_response = f"Constitutional synthesis completed for context '{synthesis_input.context}' with {len(principles)} applicable principles."

            synthesis_metadata = {
                "principle_count": len(principles),
                "synthesis_method": "constitutional_prompting",
                "target_format": synthesis_input.target_format,
                "llm_model": self.model_name,
                "prompt_length": len(constitutional_prompt)
            }

            result = ConstitutionalSynthesisOutput(
                context=synthesis_input.context,
                generated_rules=mock_rules,
                constitutional_context=constitutional_context,
                synthesis_metadata=synthesis_metadata,
                raw_llm_response=raw_response
            )

            logger.info(f"RealLLMClient: Constitutional synthesis completed. Generated {len(mock_rules)} rules.")
            return result

        except Exception as e:
            logger.error(f"RealLLMClient: Error during constitutional synthesis: {e}")
            return ConstitutionalSynthesisOutput(
                context=synthesis_input.context,
                generated_rules=[],
                constitutional_context={},
                synthesis_metadata={"error": str(e)},
                raw_llm_response=f"Error during constitutional synthesis: {e}"
            )


# Global instances (or factory functions if preferred for more complex setup)
_mock_llm_client_instance = MockLLMClient()
_real_llm_client_instance = None # Initialize lazily

# Global instances for different LLM clients
_groq_llm_client_instance = None

def get_llm_client():
    global _real_llm_client_instance, _groq_llm_client_instance
    llm_provider = os.getenv("LLM_PROVIDER", "mock").lower()

    if llm_provider == "real":
        if _real_llm_client_instance is None:
            _real_llm_client_instance = RealLLMClient()
        if not _real_llm_client_instance.api_key: # Check if API key was actually set
            logger.warning("LLM_PROVIDER is 'real' but OPENAI_API_KEY is not set. Falling back to MockLLMClient.")
            return _mock_llm_client_instance
        return _real_llm_client_instance
    elif llm_provider == "groq":
        if _groq_llm_client_instance is None:
            _groq_llm_client_instance = GroqLLMClient()
        if not _groq_llm_client_instance.api_key: # Check if API key was actually set
            logger.warning("LLM_PROVIDER is 'groq' but GROQ_API_KEY is not set. Falling back to MockLLMClient.")
            return _mock_llm_client_instance
        return _groq_llm_client_instance
    elif llm_provider == "mock":
        return _mock_llm_client_instance
    else:
        logger.warning(f"Unknown LLM_PROVIDER '{llm_provider}'. Defaulting to MockLLMClient.")
        return _mock_llm_client_instance


async def query_llm_for_structured_output(input_data: LLMInterpretationInput, wina_gating_mask: Optional[Dict[str, bool]] = None) -> LLMStructuredOutput:
    """
    Helper function to query the chosen LLM for structured interpretation.
    Accepts an optional WINA gating mask.
    """
    client = get_llm_client()
    logger.info(f"Using LLM client: {client.__class__.__name__}")
    try:
        # Pass the gating mask to the client's method
        return await client.get_structured_interpretation(input_data, wina_gating_mask=wina_gating_mask)
    except RetryError as e: # Catch tenacity's RetryError after all attempts fail
        logger.error(f"LLM query failed after multiple retries for principle {input_data.principle_id}: {e}")
        # Return a default error response or re-raise a custom application exception
        return LLMStructuredOutput(
            interpretations=[],
            raw_llm_response=f"LLM query failed after multiple retries: {e}"
        )
    except Exception as e:
        logger.error(f"An unexpected error occurred during LLM query for principle {input_data.principle_id}: {e}")
        return LLMStructuredOutput(
            interpretations=[],
            raw_llm_response=f"Unexpected error during LLM query: {e}"
        )

async def query_llm_for_constitutional_synthesis(synthesis_input, wina_gating_mask: Optional[Dict[str, bool]] = None) -> 'ConstitutionalSynthesisOutput':
    """
    Helper function to query the chosen LLM for constitutional synthesis.
    Accepts an optional WINA gating mask.
    """
    from ..schemas import ConstitutionalSynthesisOutput

    client = get_llm_client()
    logger.info(f"Using LLM client for constitutional synthesis: {client.__class__.__name__}")
    try:
        # Pass the gating mask to the client's method
        return await client.get_constitutional_synthesis(synthesis_input, wina_gating_mask=wina_gating_mask)
    except Exception as e:
        logger.error(f"An unexpected error occurred during constitutional synthesis for context {synthesis_input.context}: {e}")
        return ConstitutionalSynthesisOutput(
            context=synthesis_input.context,
            generated_rules=[],
            constitutional_context={},
            synthesis_metadata={"error": str(e)},
            raw_llm_response=f"Unexpected error during constitutional synthesis: {e}"
        )

if __name__ == "__main__":
    import asyncio

    async def main_test():
        # Example: Test with Mock Client (default if OPENAI_API_KEY is not set or LLM_PROVIDER=mock)
        print("--- Testing with MockLLMClient ---")
        test_principles_mock = [
            LLMInterpretationInput(principle_id=1, principle_content="Users must have appropriate roles for access control."),
            LLMInterpretationInput(principle_id=4, principle_content="A very generic principle about operational integrity.")
        ]
        for principle_input in test_principles_mock:
            print(f"\nTesting Mock Principle ID {principle_input.principle_id}: '{principle_input.principle_content}'")
            response = await query_llm_for_structured_output(principle_input)
            print(response.model_dump_json(indent=2))

        # To test RealLLMClient, ensure OPENAI_API_KEY is set in your environment
        # and set LLM_PROVIDER="real" (or comment out the os.getenv default for LLM_PROVIDER for testing)
        # For example, you might run: LLM_PROVIDER="real" OPENAI_API_KEY="your_key" python -m app.core.llm_integration
        print("\n--- Testing with RealLLMClient (will be mocked if API key is missing) ---")
        # Temporarily set provider to real for this test, assuming API key might be available
        os.environ["LLM_PROVIDER"] = "real" 
        # You might need to clear the cached client instance if you change env vars at runtime for testing
        global _real_llm_client_instance
        _real_llm_client_instance = None # Force re-initialization

        test_principles_real = [
            LLMInterpretationInput(principle_id=101, principle_content="Ensure all financial transactions are auditable."),
            LLMInterpretationInput(principle_id=102, principle_content="Data privacy must be maintained according to GDPR.", 
                                   datalog_predicate_schema={"gdpr_compliant_processing": "gdpr_compliant_processing(Data, Purpose, Consent)"})
        ]
        for principle_input in test_principles_real:
            print(f"\nTesting Real Principle ID {principle_input.principle_id}: '{principle_input.principle_content}'")
            response = await query_llm_for_structured_output(principle_input)
            print(response.model_dump_json(indent=2))
        
        # Reset LLM_PROVIDER if you changed it for the test
        os.environ["LLM_PROVIDER"] = "mock"


    asyncio.run(main_test())
