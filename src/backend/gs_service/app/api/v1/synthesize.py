# backend/gs_service/app/api/v1/synthesize.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional

from shared.database import get_async_db # Added

# Import schemas and CRUD functions using relative paths
from ... import schemas as gs_schemas # Goes up 3 levels from v1 to app.
from ...crud_gs import get_policy # Goes up 3 levels from v1 to app for crud_gs
from ...services import ac_client, integrity_client, fv_client # Goes up 3 levels for services

router = APIRouter()

# Placeholder for actual synthesis logic
async def perform_actual_synthesis(
    principles_content: List[Dict[str, Any]], 
    target_context: Optional[str] = None
) -> List[gs_schemas.GeneratedRuleInfo]:
    """
    Simulates the core synthesis logic based on principle content.
    In a real scenario, this would involve complex NLP, logic processing, etc.
    """
    generated_rules = []
    for i, principle in enumerate(principles_content):
        # Simulate rule generation - this would be the core AI/ML part
        rule_content = f"rule_for_principle_{principle.get('id', i+1)}_{principle.get('name', 'unknown').replace(' ', '_')}(X) :- condition(X)."
        if target_context:
            rule_content += f" AND context_is_{target_context}(X)."
        
        # Ensure source_principle_ids is a list of integers
        source_ids = [principle.get('id')] if principle.get('id') is not None else []
        # If principle IDs are not available (e.g., content-only synthesis), source_ids might be empty or use a placeholder
        if not source_ids and 'name' in principle : # Fallback if id is missing but name is there
             # This is a placeholder, real scenario needs robust ID management or content hashing for traceability
             # source_ids = [hash(principle['name']) % 10000] # Example, not production ready
             pass


        generated_rules.append(
            gs_schemas.GeneratedRuleInfo(
                rule_content=rule_content,
                source_principle_ids=source_ids # Pass the list of source IDs
            )
        )
    return generated_rules

@router.post("/", response_model=gs_schemas.SynthesisResponse, status_code=status.HTTP_202_ACCEPTED)
async def synthesize_rules(
    request_body: gs_schemas.SynthesisRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db)
    # current_user: User = Depends(get_current_active_user) # Add authentication if needed
):
    """
    Endpoint to synthesize governance rules from constitutional principles or a GSPolicy.
    Accepts either a policy_id or a list of principles.
    """
    principles_for_synthesis: List[Dict[str, Any]] = []
    policy_id_for_logging: Optional[int] = None

    if request_body.policy_id:
        policy_id_for_logging = request_body.policy_id
        policy = await get_policy(db, policy_id=request_body.policy_id)
        if not policy:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Policy with ID {request_body.policy_id} not found.")
        
        # Use policy content for synthesis. This might involve parsing the policy content
        # if it's structured, or treating it as a single block of text/rules.
        # For now, assume it's a single piece of content that acts like one principle.
        # Or, if policy.source_principle_ids are set, fetch those.
        if policy.source_principle_ids:
            try:
                fetched_principles = await ac_client.ac_service_client.fetch_principles_by_ids(policy.source_principle_ids)
                # Convert ACPrinciple (Pydantic model from client) to dict for internal processing
                principles_for_synthesis = [fp.model_dump() for fp in fetched_principles]
            except Exception as e:
                 raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Failed to fetch principles from AC Service: {e}")
        else:
            # Fallback: use policy content itself as a "principle"
            principles_for_synthesis = [{
                "id": policy.id, # Or a special marker
                "name": policy.name,
                "content": policy.content, # The actual policy text/rules
                "category": "policy_derived" 
            }]

    elif request_body.principles:
        # Direct principles provided in the request.
        # These might be minimal (e.g., just IDs) or full content.
        # If only IDs, fetch full content from AC Service.
        principle_ids_to_fetch = [p['id'] for p in request_body.principles if 'id' in p and p.get('content') is None]
        
        # Add principles that already have content directly
        for p_data in request_body.principles:
            if p_data.get('content'):
                 # Ensure it's a dict, not a Pydantic model if it comes from client
                principles_for_synthesis.append(dict(p_data))

        if principle_ids_to_fetch:
            try:
                fetched_principles = await ac_client.ac_service_client.fetch_principles_by_ids(principle_ids_to_fetch)
                principles_for_synthesis.extend([fp.model_dump() for fp in fetched_principles])
            except Exception as e:
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Failed to fetch principles from AC Service: {e}")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either policy_id or a list of principles must be provided."
        )

    if not principles_for_synthesis:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No principles found or provided for synthesis.")

    # --- Perform Synthesis (Core Logic) ---
    # This is a simplified placeholder. Real synthesis is complex.
    generated_rules_info = await perform_actual_synthesis(
        principles_content=principles_for_synthesis,
        target_context=request_body.target_context
    )
    
    # --- Post-synthesis actions (background tasks) ---
    # 1. Record synthesis event with Integrity Service
    # This should be done in the background.
    # Assuming current_user.id is available if auth is implemented.
    user_id_placeholder = 1 # Replace with actual user ID from auth
    
    # Prepare details for integrity logging
    synthesis_event_details = {
        "policy_id_synthesized_from": policy_id_for_logging,
        "principles_used_ids": [p.get('id') for p in principles_for_synthesis if p.get('id')],
        "num_rules_generated": len(generated_rules_info),
        "target_context": request_body.target_context,
        # Add a hash or summary of generated rules if possible/needed
        # "rules_summary_hash": hashlib.sha256(str(generated_rules_info).encode()).hexdigest()
    }
    background_tasks.add_task(
        integrity_client.integrity_service_client.record_synthesis_event,
        user_id=user_id_placeholder,
        details=synthesis_event_details,
        status="success" # Or based on actual synthesis outcome
    )

    # 2. (Optional) Request verification of generated rules from FV Service
    # This also can be a background task.
    if generated_rules_info: # Only if rules were generated
        # Assuming FV service can take a list of rule contents
        rules_to_verify = [rule.rule_content for rule in generated_rules_info]
        background_tasks.add_task(
            fv_client.fv_service_client.request_verification_of_rules,
            rules=rules_to_verify,
            metadata={"source": "gs_synthesis", "policy_id": policy_id_for_logging}
        )
        
    return gs_schemas.SynthesisResponse(
        generated_rules=generated_rules_info,
        message="Synthesis process initiated. Results (if any) are being processed.",
        overall_synthesis_status="pending_verification" # Or "completed" if no FV step
    )

# Note: If using Pydantic V2, model_dump() is preferred over dict().
# Ensure ACPrinciple from ac_client and other models are V2 compatible if so.
