# backend/gs_service/app/api/v1/alphaevolve_integration.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
import uuid
import time
from datetime import datetime, timedelta

from src.backend.shared.database import get_async_db
from src.backend.gs_service.app import schemas as gs_schemas
from src.backend.gs_service.app.services.ac_client import ac_service_client as ac_client
from src.backend.gs_service.app.core.constitutional_prompting import constitutional_prompt_builder
from src.backend.gs_service.app.core.llm_integration import get_llm_client

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/constitutional-prompting", response_model=gs_schemas.ECConstitutionalPromptingOutput)
async def ec_constitutional_prompting(
    prompting_request: gs_schemas.ECConstitutionalPromptingInput,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Perform constitutional prompting for evolutionary computation systems.
    
    This endpoint:
    1. Analyzes the EC context and current population
    2. Retrieves relevant constitutional principles
    3. Generates constitutional guidance for EC operations
    4. Provides fitness function modifications and operator constraints
    """
    logger.info(f"EC constitutional prompting requested for context: {prompting_request.ec_context}")
    
    try:
        prompting_id = str(uuid.uuid4())
        
        # Step 1: Retrieve relevant constitutional principles
        principles = await ac_client.get_principles_by_context(prompting_request.ec_context)
        if not principles:
            logger.warning(f"No constitutional principles found for EC context: {prompting_request.ec_context}")
            principles = []
        
        # Step 2: Analyze current EC population for constitutional compliance
        population_analysis = _analyze_ec_population(prompting_request.current_population)
        
        # Step 3: Build constitutional context for EC
        constitutional_context = await _build_ec_constitutional_context(
            prompting_request.ec_context,
            principles,
            prompting_request.optimization_objective,
            prompting_request.constitutional_constraints
        )
        
        # Step 4: Generate constitutional guidance using LLM
        guidance_prompt = _construct_ec_constitutional_prompt(
            prompting_request,
            constitutional_context,
            population_analysis
        )
        
        llm_client = get_llm_client()
        # Use the available method for constitutional synthesis
        from src.backend.gs_service.app import schemas as gs_schemas
        synthesis_input = ConstitutionalSynthesisInput(
            context="evolutionary_computation_governance",
            synthesis_request=guidance_prompt,
            target_format="guidance",
            category=None,
            auth_token=None
        )
        llm_response = await llm_client.get_constitutional_synthesis(synthesis_input)
        
        # Step 5: Parse LLM response and extract structured guidance
        structured_guidance = _parse_ec_constitutional_guidance(llm_response.raw_llm_response)
        
        # Step 6: Generate fitness modifications and operator constraints
        fitness_modifications = _generate_fitness_modifications(
            structured_guidance,
            prompting_request.optimization_objective,
            principles
        )
        
        operator_constraints = _generate_operator_constraints(
            structured_guidance,
            prompting_request.constitutional_constraints
        )
        
        population_filters = _generate_population_filters(
            structured_guidance,
            population_analysis
        )
        
        # Step 7: Prepare response
        response = gs_schemas.ECConstitutionalPromptingOutput(
            prompting_id=prompting_id,
            constitutional_guidance=structured_guidance.get("guidance", ""),
            fitness_modifications=fitness_modifications,
            operator_constraints=operator_constraints,
            population_filters=population_filters,
            synthesis_metadata={
                "ec_context": prompting_request.ec_context,
                "principles_count": len(principles),
                "population_size": len(prompting_request.current_population),
                "optimization_objective": prompting_request.optimization_objective,
                "processing_time_ms": time.time() * 1000,
                "llm_model": getattr(llm_client, 'model_name', 'unknown'),
                "constitutional_constraints_count": len(prompting_request.constitutional_constraints)
            }
        )
        
        # Background task: Log constitutional prompting session
        background_tasks.add_task(
            _log_ec_constitutional_session,
            prompting_id,
            prompting_request,
            response
        )
        
        logger.info(f"EC constitutional prompting completed for session {prompting_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error during EC constitutional prompting: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"EC constitutional prompting failed: {str(e)}"
        )


@router.post("/governance-evaluation", response_model=gs_schemas.ECGovernanceResponse)
async def ec_governance_evaluation(
    governance_request: gs_schemas.ECGovernanceRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Evaluate EC proposals for constitutional compliance and governance decisions.
    
    This endpoint:
    1. Evaluates each EC proposal against constitutional principles
    2. Makes governance decisions (allow/deny/modify)
    3. Calculates governance penalties for fitness functions
    4. Provides enforcement actions and recommendations
    """
    logger.info(f"EC governance evaluation requested for {len(governance_request.proposals)} proposals")
    
    try:
        evaluation_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Step 1: Retrieve relevant constitutional principles for context
        principles = await ac_client.get_principles_by_context(governance_request.context)
        if not principles:
            logger.warning(f"No constitutional principles found for context: {governance_request.context}")
            principles = []
        
        # Step 2: Evaluate each proposal
        decisions = []
        total_compliance_score = 0.0
        
        for proposal in governance_request.proposals:
            decision = await _evaluate_ec_proposal(
                proposal,
                principles,
                governance_request.context
            )
            decisions.append(decision)
            
            # Calculate compliance score (1.0 - governance_penalty)
            compliance_score = max(0.0, 1.0 - decision.governance_penalty)
            total_compliance_score += compliance_score
        
        # Step 3: Calculate batch summary
        processing_time_ms = (time.time() - start_time) * 1000
        constitutional_compliance_rate = total_compliance_score / len(governance_request.proposals) if governance_request.proposals else 0.0
        
        batch_summary = {
            "total_proposals": len(governance_request.proposals),
            "allowed_proposals": len([d for d in decisions if d.decision == "allow"]),
            "denied_proposals": len([d for d in decisions if d.decision == "deny"]),
            "modified_proposals": len([d for d in decisions if d.decision == "modify"]),
            "average_confidence": sum(d.confidence for d in decisions) / len(decisions) if decisions else 0.0,
            "average_governance_penalty": sum(d.governance_penalty for d in decisions) / len(decisions) if decisions else 0.0,
            "violated_principles_count": len(set().union(*[d.violated_principles for d in decisions])),
            "processing_latency_ms": processing_time_ms
        }
        
        # Step 4: Generate recommendations
        recommendations = _generate_ec_recommendations(
            decisions,
            batch_summary,
            governance_request.context
        )
        
        # Step 5: Prepare response
        response = gs_schemas.ECGovernanceResponse(
            evaluation_id=evaluation_id,
            decisions=decisions,
            batch_summary=batch_summary,
            processing_time_ms=processing_time_ms,
            constitutional_compliance_rate=constitutional_compliance_rate,
            recommendations=recommendations
        )
        
        # Background task: Log governance evaluation
        background_tasks.add_task(
            _log_ec_governance_evaluation,
            evaluation_id,
            governance_request,
            response
        )
        
        logger.info(f"EC governance evaluation completed for {len(governance_request.proposals)} proposals in {processing_time_ms:.2f}ms")
        return response
        
    except Exception as e:
        logger.error(f"Error during EC governance evaluation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"EC governance evaluation failed: {str(e)}"
        )


# Helper functions

def _analyze_ec_population(population: List[gs_schemas.ECProposal]) -> Dict[str, Any]:
    """Analyze EC population for constitutional compliance patterns."""
    analysis = {
        "population_size": len(population),
        "generation_distribution": {},
        "fitness_contexts": [],
        "code_complexity_stats": {},
        "potential_issues": []
    }
    
    # Analyze generation distribution
    for proposal in population:
        gen = proposal.generation
        analysis["generation_distribution"][gen] = analysis["generation_distribution"].get(gen, 0) + 1
        analysis["fitness_contexts"].append(proposal.fitness_context)
    
    # Identify potential constitutional issues
    if len(population) > 100:
        analysis["potential_issues"].append("Large population size may require batch processing")
    
    return analysis


async def _build_ec_constitutional_context(
    ec_context: str,
    principles: List[Dict[str, Any]],
    optimization_objective: str,
    constitutional_constraints: List[str]
) -> Dict[str, Any]:
    """Build constitutional context for EC operations."""
    context = {
        "ec_context": ec_context,
        "applicable_principles": principles,
        "optimization_objective": optimization_objective,
        "constitutional_constraints": constitutional_constraints,
        "governance_priorities": [],
        "risk_factors": []
    }
    
    # Analyze principles for EC-specific governance priorities
    for principle in principles:
        if "safety" in principle.get("category", "").lower():
            context["governance_priorities"].append("safety_enforcement")
        if "fairness" in principle.get("category", "").lower():
            context["governance_priorities"].append("fairness_monitoring")
        if "privacy" in principle.get("category", "").lower():
            context["governance_priorities"].append("privacy_protection")
    
    return context


def _construct_ec_constitutional_prompt(
    prompting_request: gs_schemas.ECConstitutionalPromptingInput,
    constitutional_context: Dict[str, Any],
    population_analysis: Dict[str, Any]
) -> str:
    """Construct constitutional prompting prompt for EC systems."""
    
    prompt = f"""
You are a constitutional AI governance advisor for evolutionary computation systems. 
Your task is to provide constitutional guidance for an EC system operating in the context: {prompting_request.ec_context}

CONSTITUTIONAL CONTEXT:
- Optimization Objective: {prompting_request.optimization_objective}
- Constitutional Constraints: {', '.join(prompting_request.constitutional_constraints)}
- Applicable Principles: {len(constitutional_context['applicable_principles'])} principles
- Current Population Size: {population_analysis['population_size']}

CONSTITUTIONAL PRINCIPLES:
"""
    
    for principle in constitutional_context['applicable_principles']:
        prompt += f"- {principle.get('name', 'Unknown')}: {principle.get('description', 'No description')}\n"
    
    prompt += f"""

POPULATION ANALYSIS:
- Generation Distribution: {population_analysis['generation_distribution']}
- Potential Issues: {', '.join(population_analysis['potential_issues']) if population_analysis['potential_issues'] else 'None identified'}

Please provide:
1. Constitutional guidance for the EC system
2. Specific fitness function modifications to ensure constitutional compliance
3. Operator constraints to prevent constitutional violations
4. Population filtering rules to maintain constitutional standards

Format your response as structured guidance that can be parsed and implemented.
"""
    
    return prompt


def _parse_ec_constitutional_guidance(llm_response: str) -> Dict[str, Any]:
    """Parse LLM response into structured constitutional guidance."""
    # This is a simplified parser - in production, use more sophisticated parsing
    guidance = {
        "guidance": llm_response,
        "key_points": [],
        "constraints": [],
        "recommendations": []
    }
    
    # Extract key sections from LLM response
    lines = llm_response.split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        if "guidance" in line.lower():
            current_section = "guidance"
        elif "constraint" in line.lower():
            current_section = "constraints"
        elif "recommendation" in line.lower():
            current_section = "recommendations"
        elif line and current_section:
            if current_section == "constraints":
                guidance["constraints"].append(line)
            elif current_section == "recommendations":
                guidance["recommendations"].append(line)
    
    return guidance


def _generate_fitness_modifications(
    structured_guidance: Dict[str, Any],
    optimization_objective: str,
    principles: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Generate fitness function modifications based on constitutional guidance."""
    modifications = {
        "penalty_weights": {},
        "constraint_functions": [],
        "objective_adjustments": [],
        "monitoring_metrics": []
    }
    
    # Add penalty weights for constitutional violations
    for principle in principles:
        principle_name = principle.get("name", "unknown")
        priority_weight = principle.get("priority_weight", 0.5)
        modifications["penalty_weights"][principle_name] = priority_weight
    
    # Add constraint functions based on guidance
    for constraint in structured_guidance.get("constraints", []):
        modifications["constraint_functions"].append({
            "constraint": constraint,
            "enforcement_level": "strict"
        })
    
    return modifications


def _generate_operator_constraints(
    structured_guidance: Dict[str, Any],
    constitutional_constraints: List[str]
) -> List[str]:
    """Generate operator constraints for EC system."""
    constraints = []
    
    # Add constitutional constraints
    constraints.extend(constitutional_constraints)
    
    # Add constraints from guidance
    constraints.extend(structured_guidance.get("constraints", []))
    
    # Add default EC governance constraints
    constraints.extend([
        "No solution shall violate fundamental safety principles",
        "All mutations must preserve constitutional compliance",
        "Population diversity must be maintained within constitutional bounds"
    ])
    
    return constraints


def _generate_population_filters(
    structured_guidance: Dict[str, Any],
    population_analysis: Dict[str, Any]
) -> List[str]:
    """Generate population filtering rules."""
    filters = []
    
    # Add filters based on population analysis
    if population_analysis["population_size"] > 100:
        filters.append("Apply batch processing for large populations")
    
    # Add filters from guidance
    for recommendation in structured_guidance.get("recommendations", []):
        if "filter" in recommendation.lower():
            filters.append(recommendation)
    
    # Add default constitutional filters
    filters.extend([
        "Filter out solutions with constitutional violations",
        "Maintain minimum constitutional compliance threshold",
        "Preserve constitutional diversity in population"
    ])
    
    return filters


async def _evaluate_ec_proposal(
    proposal: gs_schemas.ECProposal,
    principles: List[Dict[str, Any]],
    context: str
) -> gs_schemas.ECGovernanceDecision:
    """Evaluate a single EC proposal for constitutional compliance."""
    
    # Simplified evaluation logic - in production, use more sophisticated analysis
    decision = "allow"
    confidence = 0.8
    violated_principles = []
    governance_penalty = 0.0
    explanation = f"Proposal {proposal.proposal_id} evaluated for constitutional compliance"
    enforcement_actions = []
    
    # Check for potential constitutional violations
    code_length = len(proposal.solution_code)
    if code_length > 1000:
        governance_penalty += 0.1
        explanation += ". Code complexity penalty applied"
    
    # Check against principles
    for principle in principles:
        if "safety" in principle.get("category", "").lower():
            if "unsafe" in proposal.solution_code.lower():
                violated_principles.append(str(principle.get("id", "unknown")))
                governance_penalty += 0.3
                decision = "deny"
                explanation += f". Safety violation detected in principle {principle.get('name', 'unknown')}"
    
    # Adjust confidence based on violations
    if violated_principles:
        confidence = max(0.1, confidence - len(violated_principles) * 0.2)
    
    # Generate enforcement actions
    if governance_penalty > 0.2:
        enforcement_actions.append("Apply governance penalty to fitness score")
    if violated_principles:
        enforcement_actions.append("Flag for human review")
    
    return gs_schemas.ECGovernanceDecision(
        proposal_id=proposal.proposal_id,
        decision=decision,
        confidence=confidence,
        violated_principles=violated_principles,
        governance_penalty=governance_penalty,
        explanation=explanation,
        enforcement_actions=enforcement_actions,
        timestamp=datetime.utcnow()
    )


def _generate_ec_recommendations(
    decisions: List[gs_schemas.ECGovernanceDecision],
    batch_summary: Dict[str, Any],
    context: str
) -> List[str]:
    """Generate recommendations for EC system based on governance evaluation."""
    recommendations = []
    
    # Analyze batch results
    denied_rate = batch_summary["denied_proposals"] / batch_summary["total_proposals"]
    avg_penalty = batch_summary["average_governance_penalty"]
    
    if denied_rate > 0.3:
        recommendations.append("High denial rate detected - consider adjusting EC operators")
    
    if avg_penalty > 0.2:
        recommendations.append("High governance penalties - review constitutional compliance")
    
    if batch_summary["violated_principles_count"] > 5:
        recommendations.append("Multiple principle violations - strengthen constitutional constraints")
    
    # Add context-specific recommendations
    if "healthcare" in context.lower():
        recommendations.append("Ensure HIPAA compliance in all generated solutions")
    elif "financial" in context.lower():
        recommendations.append("Maintain financial regulatory compliance")
    
    return recommendations


async def _log_ec_constitutional_session(
    prompting_id: str,
    request: gs_schemas.ECConstitutionalPromptingInput,
    response: gs_schemas.ECConstitutionalPromptingOutput
):
    """Log EC constitutional prompting session for audit purposes."""
    logger.info(f"EC Constitutional Session {prompting_id}: Context={request.ec_context}, Population={len(request.current_population)}")


async def _log_ec_governance_evaluation(
    evaluation_id: str,
    request: gs_schemas.ECGovernanceRequest,
    response: gs_schemas.ECGovernanceResponse
):
    """Log EC governance evaluation for audit purposes."""
    logger.info(f"EC Governance Evaluation {evaluation_id}: Proposals={len(request.proposals)}, Compliance={response.constitutional_compliance_rate:.2f}")
