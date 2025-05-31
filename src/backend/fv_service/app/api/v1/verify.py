from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict

from ... import schemas # Relative imports for app directory
from ...core.verification_logic import verify_policy_rules
from ...services.ac_client import ac_service_client, ACPrinciple
from ...services.integrity_client import integrity_service_client, PolicyRule
from ...core.auth import require_verification_triggerer, User # Placeholder auth
# Phase 3 imports
from ...core.tiered_validation import tiered_validation_pipeline
from ...core.safety_conflict_checker import safety_property_checker, conflict_detector
from ...core.bias_detector import bias_detector

router = APIRouter()

# Import service authentication
from shared.auth import get_service_token

@router.post("/", response_model=schemas.VerificationResponse, status_code=status.HTTP_200_OK)
async def verify_policies(
    request_data: schemas.VerificationRequest,
    current_user: User = Depends(require_verification_triggerer) # Protect this endpoint
):
    """
    Orchestrates the formal verification of Datalog policy rules against AC principles.
    """
    if not request_data.policy_rule_refs:
        raise HTTPException(status_code=400, detail="No policy rule references provided for verification.")

    # 1. Fetch Policy Rules from Integrity Service
    policy_rules_to_verify: List[PolicyRule] = []
    rule_ids_to_fetch = [ref.id for ref in request_data.policy_rule_refs]
    
    fetched_rules_from_integrity = await integrity_service_client.get_policy_rules_by_ids(
        rule_ids=rule_ids_to_fetch,
        auth_token=INTEGRITY_SERVICE_MOCK_TOKEN
    )
    if len(fetched_rules_from_integrity) != len(rule_ids_to_fetch):
        # Handle case where some rules couldn't be fetched
        # For now, raising an error. Could also proceed with found rules.
        found_ids = {r.id for r in fetched_rules_from_integrity}
        missing_ids = set(rule_ids_to_fetch) - found_ids
        raise HTTPException(status_code=404, detail=f"Could not fetch policy rules with IDs: {list(missing_ids)} from Integrity Service.")
    policy_rules_to_verify = fetched_rules_from_integrity
    

    # 2. Determine and Fetch AC Principles
    # Principles can be directly referenced in the request or derived from the policy rules.
    ac_principles_for_obligations: List[ACPrinciple] = []
    principle_ids_to_fetch = set()

    if request_data.ac_principle_refs:
        for ref in request_data.ac_principle_refs:
            principle_ids_to_fetch.add(ref.id)
    else:
        # If not specified, use source_principle_ids from the fetched policy rules
        for rule in policy_rules_to_verify:
            if rule.source_principle_ids:
                for pid in rule.source_principle_ids:
                    principle_ids_to_fetch.add(pid)
    
    if not principle_ids_to_fetch:
        # If no principles are identified, verification cannot proceed meaningfully against custom obligations
        # Or, it could mean verification against a "default" set of obligations, if applicable.
        # For now, let's assume principles are required.
        results = [
            schemas.VerificationResult(policy_rule_id=rule.id, status="error", message="No AC principles identified for deriving proof obligations.")
            for rule in policy_rules_to_verify
        ]
        return schemas.VerificationResponse(results=results, overall_status="error", summary_message="Missing AC principle context.")

    service_token = await get_service_token()
    fetched_ac_principles = await ac_service_client.list_principles_by_ids(
        principle_ids=list(principle_ids_to_fetch),
        auth_token=service_token
    )
    if len(fetched_ac_principles) != len(principle_ids_to_fetch):
        found_pids = {p.id for p in fetched_ac_principles}
        missing_pids = principle_ids_to_fetch - found_pids
        # Decide: error out, or proceed with found principles?
        # For now, proceed with found principles, but a real system might log/error.
        print(f"Warning: Could not fetch AC principles with IDs: {list(missing_pids)}")
        if not fetched_ac_principles:
             results = [
                schemas.VerificationResult(policy_rule_id=rule.id, status="error", message=f"Could not fetch any of the specified AC principles: {list(missing_pids)}.")
                for rule in policy_rules_to_verify
            ]
             return schemas.VerificationResponse(results=results, overall_status="error", summary_message="AC principle fetching failed.")

    ac_principles_for_obligations = fetched_ac_principles

    # 3. Perform Verification using Verification Logic
    verification_results: List[schemas.VerificationResult] = await verify_policy_rules(
        policy_rules=policy_rules_to_verify,
        ac_principles=ac_principles_for_obligations
    )

    # 4. Update verification status in Integrity Service for each rule
    for result in verification_results:
        # Only update if status is not "error" (error might be due to FV service itself)
        if result.status in ["verified", "failed"]:
            updated_rule = await integrity_service_client.update_policy_rule_status(
                rule_id=result.policy_rule_id,
                status=result.status, # "verified" or "failed"
                auth_token=INTEGRITY_SERVICE_MOCK_TOKEN
            )
            if not updated_rule:
                result.message = (result.message or "") + f" | Failed to update status in Integrity Service."
                # Potentially change result.status to "error_updating_status" here if needed

    # 5. Determine overall status and return response
    overall_status = "all_verified"
    if any(r.status == "failed" for r in verification_results):
        overall_status = "some_failed"
    if any(r.status == "error" for r in verification_results):
        overall_status = "error" # Or more granular if mixed results

    summary = f"Verification process completed. {len(verification_results)} rules processed."
    if overall_status == "error":
        summary += " Errors occurred during verification."
        
    return schemas.VerificationResponse(
        results=verification_results,
        overall_status=overall_status,
        summary_message=summary
    )


# --- Phase 3: Advanced Verification Endpoints ---

@router.post("/tiered", response_model=schemas.TieredVerificationResponse, status_code=status.HTTP_200_OK)
async def tiered_verification(
    request_data: schemas.TieredVerificationRequest,
    current_user: User = Depends(require_verification_triggerer)
):
    """
    Phase 3: Tiered formal verification with Automated, HITL, and Rigorous validation levels.
    """
    if not request_data.policy_rule_refs:
        raise HTTPException(status_code=400, detail="No policy rule references provided for tiered verification.")

    # Fetch Policy Rules from Integrity Service
    rule_ids_to_fetch = [ref.id for ref in request_data.policy_rule_refs]

    fetched_rules = await integrity_service_client.get_policy_rules_by_ids(
        rule_ids=rule_ids_to_fetch,
        auth_token=INTEGRITY_SERVICE_MOCK_TOKEN
    )

    if len(fetched_rules) != len(rule_ids_to_fetch):
        found_ids = {r.id for r in fetched_rules}
        missing_ids = set(rule_ids_to_fetch) - found_ids
        raise HTTPException(
            status_code=404,
            detail=f"Could not fetch policy rules with IDs: {list(missing_ids)} from Integrity Service."
        )

    # Fetch AC Principles for context
    principle_ids_to_fetch = set()
    for rule in fetched_rules:
        if rule.source_principle_ids:
            for pid in rule.source_principle_ids:
                principle_ids_to_fetch.add(pid)

    ac_principles = []
    if principle_ids_to_fetch:
        service_token = await get_service_token()
        ac_principles = await ac_service_client.list_principles_by_ids(
            principle_ids=list(principle_ids_to_fetch),
            auth_token=service_token
        )

    # Perform tiered validation
    response = await tiered_validation_pipeline.validate_tiered(
        request=request_data,
        policy_rules=fetched_rules,
        ac_principles=ac_principles
    )

    return response


@router.post("/safety-check", response_model=schemas.SafetyCheckResponse, status_code=status.HTTP_200_OK)
async def safety_property_check(
    request_data: schemas.SafetyCheckRequest,
    current_user: User = Depends(require_verification_triggerer)
):
    """
    Phase 3: Safety property verification for policy rules.
    """
    if not request_data.safety_properties:
        raise HTTPException(status_code=400, detail="No safety properties provided for verification.")

    # For this endpoint, we'll check safety properties against all active policy rules
    # In a real implementation, you might want to specify which rules to check
    all_rules = await integrity_service_client.get_all_policy_rules(
        auth_token=INTEGRITY_SERVICE_MOCK_TOKEN
    )

    # Perform safety property checking
    response = await safety_property_checker.check_safety_properties(
        request=request_data,
        policy_rules=all_rules
    )

    return response


@router.post("/conflict-check", response_model=schemas.ConflictCheckResponse, status_code=status.HTTP_200_OK)
async def conflict_detection(
    request_data: schemas.ConflictCheckRequest,
    current_user: User = Depends(require_verification_triggerer)
):
    """
    Phase 3: Conflict detection between policy rule sets.
    """
    if not request_data.rule_sets:
        raise HTTPException(status_code=400, detail="No rule sets provided for conflict detection.")

    # Fetch rules for each rule set
    # In this simplified implementation, we'll treat rule_sets as categories or tags
    # In a real implementation, you'd have a more sophisticated rule set management system
    all_rules_by_set: Dict[str, List[PolicyRule]] = {}

    for rule_set_name in request_data.rule_sets:
        # For demonstration, we'll fetch all rules and filter by a hypothetical category
        # In practice, you'd have proper rule set management
        all_rules = await integrity_service_client.get_all_policy_rules(
            auth_token=INTEGRITY_SERVICE_MOCK_TOKEN
        )

        # Simple filtering - in practice, you'd have proper rule set categorization
        filtered_rules = [rule for rule in all_rules if rule_set_name.lower() in rule.rule_content.lower()]
        all_rules_by_set[rule_set_name] = filtered_rules

    # Perform conflict detection
    response = await conflict_detector.detect_conflicts(
        request=request_data,
        all_policy_rules=all_rules_by_set
    )

    return response


@router.get("/validation-status/{rule_id}", response_model=Dict, status_code=status.HTTP_200_OK)
async def get_validation_status(
    rule_id: int,
    current_user: User = Depends(require_verification_triggerer)
):
    """
    Phase 3: Get comprehensive validation status for a specific rule.
    """
    # Fetch the rule
    try:
        rules = await integrity_service_client.get_policy_rules_by_ids(
            rule_ids=[rule_id],
            auth_token=INTEGRITY_SERVICE_MOCK_TOKEN
        )

        if not rules:
            raise HTTPException(status_code=404, detail=f"Policy rule {rule_id} not found.")

        rule = rules[0]

        # Return comprehensive status information
        # In a real implementation, this would query validation history, cache results, etc.
        return {
            "rule_id": rule_id,
            "rule_content": rule.rule_content,
            "verification_status": rule.verification_status,
            "last_verified": rule.verified_at,
            "available_validation_tiers": ["automated", "human_in_the_loop", "rigorous"],
            "safety_check_status": "not_checked",  # Would be populated from actual checks
            "conflict_status": "not_checked",      # Would be populated from actual checks
            "recommendations": [
                "Consider running tiered validation for comprehensive verification",
                "Safety property checking recommended for critical rules",
                "Conflict detection recommended when multiple rule sets are active"
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving validation status: {str(e)}")


# --- Phase 3: Algorithmic Fairness Endpoints ---

@router.post("/bias-detection", response_model=schemas.BiasDetectionResponse, status_code=status.HTTP_200_OK)
async def bias_detection_analysis(
    request_data: schemas.BiasDetectionRequest,
    current_user: User = Depends(require_verification_triggerer)
):
    """
    Phase 3: Comprehensive bias detection analysis for policy rules.
    """
    if not request_data.policy_rule_ids:
        raise HTTPException(status_code=400, detail="No policy rule IDs provided for bias detection.")

    if not request_data.bias_metrics:
        raise HTTPException(status_code=400, detail="No bias metrics specified for analysis.")

    # Fetch Policy Rules from Integrity Service
    fetched_rules = await integrity_service_client.get_policy_rules_by_ids(
        rule_ids=request_data.policy_rule_ids,
        auth_token=INTEGRITY_SERVICE_MOCK_TOKEN
    )

    if len(fetched_rules) != len(request_data.policy_rule_ids):
        found_ids = {r.id for r in fetched_rules}
        missing_ids = set(request_data.policy_rule_ids) - found_ids
        raise HTTPException(
            status_code=404,
            detail=f"Could not fetch policy rules with IDs: {list(missing_ids)} from Integrity Service."
        )

    # Perform bias detection analysis
    response = await bias_detector.detect_bias(
        request=request_data,
        policy_rules=fetched_rules
    )

    return response


@router.post("/fairness-validation", response_model=schemas.FairnessValidationResponse, status_code=status.HTTP_200_OK)
async def fairness_validation_analysis(
    request_data: schemas.FairnessValidationRequest,
    current_user: User = Depends(require_verification_triggerer)
):
    """
    Phase 3: Fairness property validation for policy rules.
    """
    if not request_data.policy_rule_ids:
        raise HTTPException(status_code=400, detail="No policy rule IDs provided for fairness validation.")

    if not request_data.fairness_properties:
        raise HTTPException(status_code=400, detail="No fairness properties specified for validation.")

    # Fetch Policy Rules from Integrity Service
    fetched_rules = await integrity_service_client.get_policy_rules_by_ids(
        rule_ids=request_data.policy_rule_ids,
        auth_token=INTEGRITY_SERVICE_MOCK_TOKEN
    )

    if len(fetched_rules) != len(request_data.policy_rule_ids):
        found_ids = {r.id for r in fetched_rules}
        missing_ids = set(request_data.policy_rule_ids) - found_ids
        raise HTTPException(
            status_code=404,
            detail=f"Could not fetch policy rules with IDs: {list(missing_ids)} from Integrity Service."
        )

    # Perform fairness validation
    response = await bias_detector.validate_fairness(
        request=request_data,
        policy_rules=fetched_rules
    )

    return response


@router.get("/bias-metrics", response_model=List[Dict], status_code=status.HTTP_200_OK)
async def get_available_bias_metrics(
    current_user: User = Depends(require_verification_triggerer)
):
    """
    Phase 3: Get available bias detection metrics and their configurations.
    """
    # Return predefined bias metrics
    bias_metrics = [
        {
            "metric_id": "demographic_parity",
            "metric_type": "statistical",
            "metric_name": "Demographic Parity",
            "description": "Ensures equal positive outcome rates across protected groups",
            "threshold": 0.1,
            "parameters": {"requires_dataset": True}
        },
        {
            "metric_id": "counterfactual_fairness",
            "metric_type": "counterfactual",
            "metric_name": "Counterfactual Fairness",
            "description": "Detects differential treatment based on protected attributes",
            "threshold": 0.2,
            "parameters": {"protected_attributes_required": True}
        },
        {
            "metric_id": "semantic_bias",
            "metric_type": "embedding",
            "metric_name": "Semantic Bias Detection",
            "description": "Analyzes semantic embeddings for bias-associated patterns",
            "threshold": 0.15,
            "parameters": {"embedding_model": "default"}
        },
        {
            "metric_id": "llm_bias_review",
            "metric_type": "llm_review",
            "metric_name": "LLM Bias Review",
            "description": "Expert-level bias review using large language models",
            "threshold": 0.3,
            "parameters": {"model": "gpt-4", "review_depth": "comprehensive"}
        }
    ]

    return bias_metrics


@router.get("/fairness-properties", response_model=List[Dict], status_code=status.HTTP_200_OK)
async def get_available_fairness_properties(
    current_user: User = Depends(require_verification_triggerer)
):
    """
    Phase 3: Get available fairness properties and their definitions.
    """
    # Return predefined fairness properties
    fairness_properties = [
        {
            "property_id": "demographic_parity",
            "property_type": "demographic_parity",
            "property_name": "Demographic Parity",
            "description": "P(Ŷ = 1|A = 0) = P(Ŷ = 1|A = 1) - Equal positive outcome rates",
            "threshold": 0.1,
            "criticality_level": "high"
        },
        {
            "property_id": "equalized_odds",
            "property_type": "equalized_odds",
            "property_name": "Equalized Odds",
            "description": "P(Ŷ = 1|Y = y, A = a) independent of A - Equal true/false positive rates",
            "threshold": 0.1,
            "criticality_level": "high"
        },
        {
            "property_id": "calibration",
            "property_type": "calibration",
            "property_name": "Calibration",
            "description": "P(Y = 1|Ŷ = s, A = a) independent of A - Consistent prediction accuracy",
            "threshold": 0.05,
            "criticality_level": "medium"
        },
        {
            "property_id": "individual_fairness",
            "property_type": "individual_fairness",
            "property_name": "Individual Fairness",
            "description": "Similar individuals receive similar treatment",
            "threshold": 0.2,
            "criticality_level": "medium"
        }
    ]

    return fairness_properties
