from fastapi import APIRouter, Depends, HTTPException, status, Request # Added Request
from typing import List, Optional

from ....app import schemas # Relative imports for app directory
from ....app.core.policy_manager import policy_manager # Global policy manager instance
from ....app.core.datalog_engine import datalog_engine # Global Datalog engine instance
from ....app.core.secure_execution import apply_pet_transformation, execute_in_mock_tee # Mock PET/TEE
from ....app.core.auth import require_policy_evaluation_triggerer, User # Placeholder auth
from ....app.core.limiter import limiter # Import the limiter

router = APIRouter()

@router.post("/evaluate", response_model=schemas.PolicyQueryResponse, status_code=status.HTTP_200_OK)
@limiter.limit("30/minute") # Apply rate limit
async def evaluate_policy_query(
    fastapi_request: Request, # Added Request for limiter
    policy_query_payload: schemas.PolicyQueryRequest, # Renamed original 'request'
    current_user: User = Depends(require_policy_evaluation_triggerer) # Protect this endpoint
):
    """
    Evaluates a policy query against the currently active Datalog policies.
    """
    # 1. Ensure policies are loaded (PolicyManager handles caching and refreshing)
    # The policy_manager already loads rules into the datalog_engine when refreshed.
    # We might force a refresh if needed, or rely on its internal schedule.
    # For an evaluation endpoint, typically we want the most up-to-date rules,
    # but frequent forced refreshes on every call could be inefficient.
    # For now, let's ensure rules are loaded once before evaluation if not already.
    # The current_user is now available in fastapi_request.scope['current_user'] for the limiter
    if not policy_manager._last_refresh_time: # Check if initial load has happened
        print("PGC Endpoint: Initial policy load triggered by first evaluation request.")
        await policy_manager.get_active_rules(force_refresh=True)
    
    active_rules_content = policy_manager.get_active_rule_strings()
    if not active_rules_content:
        # This might happen if Integrity Service has no verified rules or failed to load
        return schemas.PolicyQueryResponse(
            decision="error",
            reason="No active policies loaded or available for evaluation.",
            error_message="Policy set is empty or could not be loaded."
        )

    # 2. Prepare Datalog engine: Load rules (done by PolicyManager) and add facts from context
    # Datalog engine rules are managed by PolicyManager.
    # We need to clear any facts from previous queries and add current context facts.
    datalog_engine.clear_rules_and_facts() # Clear previous facts (rules are reloaded by PolicyManager)
    
    # Reload rules to ensure the engine instance for this request is clean and has the latest rules
    # (PolicyManager's load_rules clears before loading)
    datalog_engine.load_rules(active_rules_content) 

    context_facts = datalog_engine.build_facts_from_context(policy_query_payload.context.model_dump())
    datalog_engine.add_facts(context_facts)
    
    # --- Placeholder for PETs/TEEs ---
    # Example: If context indicates a need for PET/TEE processing before evaluation
    # This is highly conceptual and depends on specific policy requirements.
    # if policy_query_payload.context.user.get("requires_pet_processing"):
    #     pet_input = schemas.PETContextInput(data=policy_query_payload.context.user, transformation="differential_privacy")
    #     pet_output = await apply_pet_transformation(pet_input)
    #     if pet_output.status == "success":
    #          # Update context_facts with processed data or add new facts
    #          # e.g., datalog_engine.add_facts([f"+processed_user_attribute('some_attr', '{pet_output.processed_data}')"])
    #          pass
    #     else:
    #         return schemas.PolicyQueryResponse(decision="error", reason="PET processing failed.", error_message=str(pet_output.processed_data))

    # if policy_query_payload.context.action.get("requires_tee_execution"):
    #     tee_input = schemas.TEEContextInput(data=policy_query_payload.context.action, code_to_execute="some_sensitive_check")
    #     tee_output = await execute_in_mock_tee(tee_input)
    #     if tee_output.status == "success" and tee_output.result.get("decision") == "permit_tee":
    #         # Add facts based on TEE outcome
    #         # e.g., datalog_engine.add_facts(["+tee_approved_action(policy_query_payload.context.action.type)"])
    #         pass
    #     else:
    #         return schemas.PolicyQueryResponse(decision="deny", reason=f"TEE execution denied or failed. Details: {tee_output.result}", error_message=str(tee_output.status))


    # 3. Formulate and execute the Datalog query
    # The query needs to be constructed based on the request context.
    # Example: Check for a predicate like 'allow(User, Action, Resource)'.
    # For simplicity, let's assume a generic 'allow' predicate that takes context IDs.
    # A more robust system would derive the query target from the request or policy structure.
    
    user_id = policy_query_payload.context.user.get("id", "_") # Use actual ID or wildcard if not present
    resource_id = policy_query_payload.context.resource.get("id", "_")
    action_type = policy_query_payload.context.action.get("type", "_")

    # Example target query: is 'allow(user_id, action_type, resource_id)' derivable?
    # This query structure must align with how your Datalog rules are written.
    # E.g., a rule might be: allow(U, A, R) <= user_role(U, 'admin') & action_requires_admin(A) & resource_type(R, 'sensitive').
    target_query = f"allow('{user_id}', '{action_type}', '{resource_id}')"
    
    print(f"PGC Endpoint: Executing Datalog query: {target_query}")
    query_results = datalog_engine.query(target_query)

    # 4. Interpret results and form response
    decision = "deny" # Default to deny
    reason = "No specific policy grants permission for the given context."
    matching_rules_info = None # Future: trace which rules fired

    if query_results: # If the query returns any results (e.g., [()] for a ground query)
        decision = "permit"
        reason = f"Action '{action_type}' on resource '{resource_id}' by user '{user_id}' is permitted by policy."
        # In a real system with rule tracing, identify matching rules here.
        # matching_rules_info = [{"id": "rule_xyz", "content": "allow(...)"}] 
    
    # Clear facts for the next request (rules are managed by PolicyManager's refresh cycle)
    # datalog_engine.clear_rules_and_facts() # Reconsidering this: facts should be cleared at start of next request.
                                          # Rules are cleared/reloaded by PolicyManager.

    return schemas.PolicyQueryResponse(
        decision=decision,
        reason=reason,
        matching_rules=matching_rules_info
    )
