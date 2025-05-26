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

logger = logging.getLogger(__name__)

# Configure basic logging if no configuration is set yet (e.g., for standalone testing)
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO)


class MockLLMClient:
    async def get_structured_interpretation(self, query: LLMInterpretationInput) -> LLMStructuredOutput:
        interpretations: List[LLMSuggestedRule] = []
        raw_llm_response = f"Mock interpretation for principle {query.principle_id}: {query.principle_content[:30]}..."
        logger.info(f"MockLLMClient: Processing query for principle ID {query.principle_id}")

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


# Global instances (or factory functions if preferred for more complex setup)
_mock_llm_client_instance = MockLLMClient()
_real_llm_client_instance = None # Initialize lazily

def get_llm_client():
    global _real_llm_client_instance
    llm_provider = os.getenv("LLM_PROVIDER", "mock").lower()

    if llm_provider == "real":
        if _real_llm_client_instance is None:
            _real_llm_client_instance = RealLLMClient()
        if not _real_llm_client_instance.api_key: # Check if API key was actually set
            logger.warning("LLM_PROVIDER is 'real' but OPENAI_API_KEY is not set. Falling back to MockLLMClient.")
            return _mock_llm_client_instance
        return _real_llm_client_instance
    elif llm_provider == "mock":
        return _mock_llm_client_instance
    else:
        logger.warning(f"Unknown LLM_PROVIDER '{llm_provider}'. Defaulting to MockLLMClient.")
        return _mock_llm_client_instance


async def query_llm_for_structured_output(input_data: LLMInterpretationInput) -> LLMStructuredOutput:
    """
    Helper function to query the chosen LLM for structured interpretation.
    """
    client = get_llm_client()
    logger.info(f"Using LLM client: {client.__class__.__name__}")
    try:
        return await client.get_structured_interpretation(input_data)
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
