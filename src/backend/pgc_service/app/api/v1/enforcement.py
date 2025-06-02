from fastapi import APIRouter, Depends, HTTPException, status, Request # Added Request
from typing import List, Optional
from datetime import datetime

from ... import schemas # Relative imports for app directory
from ...core.policy_manager import policy_manager # Global policy manager instance
from ...core.datalog_engine import datalog_engine # Global Datalog engine instance
from ...core.secure_execution import apply_pet_transformation, execute_in_mock_tee # Mock PET/TEE
from ...core.auth import require_policy_evaluation_triggerer, User # Placeholder auth
from ...core.limiter import limiter # Import the limiter
from ...core.wina_enforcement_optimizer import (
    get_wina_enforcement_optimizer,
    EnforcementContext,
    WINAEnforcementOptimizer
)
from ...core.opa_client import get_opa_client
from ...core.wina_policy_compiler import WINAPolicyCompiler

router = APIRouter()

@router.post("/evaluate", response_model=schemas.PolicyQueryResponse, status_code=status.HTTP_200_OK)
@limiter.limit("30/minute") # Apply rate limit
async def evaluate_policy_query(
    request: Request, # Added Request for limiter (must be named 'request')
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
    # The current_user is now available in request.scope['current_user'] for the limiter
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


@router.post("/evaluate-wina", response_model=schemas.PolicyQueryResponse, status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
async def evaluate_policy_query_with_wina(
    request: Request,
    policy_query_payload: schemas.PolicyQueryRequest,
    current_user: User = Depends(require_policy_evaluation_triggerer)
):
    """
    Evaluates a policy query using WINA-optimized enforcement for enhanced performance.

    This endpoint leverages WINA (Weight Informed Neuron Activation) optimization
    to provide more efficient policy enforcement while maintaining constitutional compliance.
    """
    try:
        # Get WINA enforcement optimizer
        wina_optimizer = await get_wina_enforcement_optimizer()

        # Initialize WINA components if not already done
        if not wina_optimizer.opa_client:
            opa_client = await get_opa_client()
            wina_policy_compiler = WINAPolicyCompiler(enable_wina=True)
            await wina_optimizer.initialize(opa_client, wina_policy_compiler)

        # Get active policies
        active_rules = await policy_manager.get_active_rules()

        # Create enforcement context
        context = EnforcementContext(
            user_id=policy_query_payload.context.user.get("id", "unknown"),
            action_type=policy_query_payload.context.action.get("type", "unknown"),
            resource_id=policy_query_payload.context.resource.get("id", "unknown"),
            environment_factors=policy_query_payload.context.environment or {},
            priority_level=policy_query_payload.context.get("priority", "normal"),
            constitutional_requirements=policy_query_payload.context.get("constitutional_requirements", []),
            performance_constraints=policy_query_payload.context.get("performance_constraints", {})
        )

        # Perform WINA-optimized enforcement
        wina_result = await wina_optimizer.optimize_enforcement(
            context=context,
            policies=active_rules,
            optimization_hints=policy_query_payload.context.get("optimization_hints")
        )

        # Convert WINA result to standard response format
        matching_rules_info = None
        if wina_result.matching_rules:
            matching_rules_info = [
                {
                    "id": f"rule_{i}",
                    "content": str(rule.get("node", {})),
                    "location": rule.get("location", {})
                }
                for i, rule in enumerate(wina_result.matching_rules)
            ]

        # Add WINA-specific information to the reason
        enhanced_reason = wina_result.reason
        if wina_result.optimization_applied:
            enhanced_reason += f" (WINA-optimized: {wina_result.enforcement_metrics.strategy_used.value})"
        if wina_result.constitutional_compliance:
            enhanced_reason += " [Constitutional compliance verified]"

        return schemas.PolicyQueryResponse(
            decision=wina_result.decision,
            reason=enhanced_reason,
            matching_rules=matching_rules_info,
            # Add WINA-specific metadata if the schema supports it
            metadata={
                "wina_optimization_applied": wina_result.optimization_applied,
                "enforcement_time_ms": wina_result.enforcement_metrics.enforcement_time_ms,
                "strategy_used": wina_result.enforcement_metrics.strategy_used.value,
                "constitutional_compliance": wina_result.constitutional_compliance,
                "confidence_score": wina_result.confidence_score,
                "performance_improvement": wina_result.enforcement_metrics.performance_improvement,
                "wina_insights": wina_result.wina_insights
            } if hasattr(schemas.PolicyQueryResponse, 'metadata') else None
        )

    except Exception as e:
        # Fallback to standard enforcement if WINA fails
        print(f"WINA enforcement failed, falling back to standard: {e}")

        # Fallback to original implementation
        await policy_manager.get_active_rules()

        user_id = policy_query_payload.context.user.get("id", "_")
        resource_id = policy_query_payload.context.resource.get("id", "_")
        action_type = policy_query_payload.context.action.get("type", "_")

        target_query = f"allow('{user_id}', '{action_type}', '{resource_id}')"
        query_results = datalog_engine.query(target_query)

        decision = "permit" if query_results else "deny"
        reason = f"Action '{action_type}' on resource '{resource_id}' by user '{user_id}' is {'permitted' if query_results else 'denied'} by policy (fallback enforcement)"

        return schemas.PolicyQueryResponse(
            decision=decision,
            reason=reason,
            matching_rules=None
        )


@router.get("/wina-performance", status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def get_wina_performance_metrics(
    request: Request,
    current_user: User = Depends(require_policy_evaluation_triggerer)
):
    """
    Get WINA enforcement performance metrics and statistics.

    Returns comprehensive performance data including enforcement times,
    strategy distribution, constitutional compliance rates, and optimization effectiveness.
    """
    try:
        # Get WINA enforcement optimizer
        wina_optimizer = await get_wina_enforcement_optimizer()

        # Get performance summary
        performance_summary = wina_optimizer.get_performance_summary()

        return {
            "status": "success",
            "wina_performance_metrics": performance_summary,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve WINA performance metrics: {str(e)}"
        )
