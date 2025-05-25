# backend/gs_service/app/core/llm_integration.py
from typing import List, Optional, Dict # Ensure Dict is imported
from ..schemas import (
    LLMInterpretationInput, 
    LLMStructuredOutput, 
    LLMSuggestedRule, 
    LLMSuggestedAtom
)

class MockLLMClient:
    async def get_structured_interpretation(self, query: LLMInterpretationInput) -> LLMStructuredOutput:
        interpretations: List[LLMSuggestedRule] = []
        raw_llm_response = f"Mock interpretation for principle {query.principle_id}: {query.principle_content[:30]}..."
        
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
            # Fallback generic rule
            head_predicate_name = f"generic_compliance_fact_for_p{query.principle_id}"
            # Ensure arguments are not empty if the predicate expects them, or make it a 0-arity predicate
            # For this example, let's assume it can take a context or be a fact.
            # If it must have arguments based on a schema from datalog_predicate_schema, this needs to be smarter.
            # For now, creating a simple fact if no specific arguments are obvious.
            head = LLMSuggestedAtom(predicate_name=head_predicate_name, arguments=["DefaultContext"]) # Making it a fact with one argument
            interpretations.append(LLMSuggestedRule(head=head, body=[], explanation="Generic rule based on principle content.", confidence=0.5))

        return LLMStructuredOutput(interpretations=interpretations, raw_llm_response=raw_llm_response)

# Global instance of the client to be used by other modules
mock_llm_client = MockLLMClient()

async def query_llm_for_structured_output(input_data: LLMInterpretationInput) -> LLMStructuredOutput:
    """
    Helper function to query the LLM for structured interpretation using the new schemas.
    """
    return await mock_llm_client.get_structured_interpretation(input_data)

# Example Usage (can be run directly for testing this file)
if __name__ == "__main__":
    import asyncio

    async def test_llm_structured_mock():
        # Example of datalog_predicate_schema (optional, for more advanced LLM guidance)
        predicate_schema_example = {
            "allow_action": "allow_action(User, Action, Resource)",
            "user_has_role": "user_has_role(User, Role)",
            "role_has_permission_for_action": "role_has_permission_for_action(Role, Action, Resource)",
            "event_logged": "event_logged(EventID, Timestamp, Actor, Action, Details)",
            "event_occurred": "event_occurred(EventID, Timestamp, Actor, Action, Details)"
        }

        test_principles = [
            LLMInterpretationInput(principle_id=1, principle_content="Users must have appropriate roles for access control.", datalog_predicate_schema=predicate_schema_example),
            LLMInterpretationInput(principle_id=2, principle_content="Access to sensitive data is strictly controlled and logged."),
            LLMInterpretationInput(principle_id=3, principle_content="All system events must be logged with details."),
            LLMInterpretationInput(principle_id=4, principle_content="A very generic principle about operational integrity.")
        ]

        for i, principle_input in enumerate(test_principles):
            print(f"Testing Principle ID {principle_input.principle_id}: '{principle_input.principle_content}'")
            response = await query_llm_for_structured_output(principle_input)
            print(f"Response {i+1}:")
            # Pydantic's model_dump_json is useful for printing
            print(response.model_dump_json(indent=2))
            print("-" * 30)

    asyncio.run(test_llm_structured_mock())
