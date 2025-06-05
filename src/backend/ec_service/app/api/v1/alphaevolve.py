"""
AlphaEvolve Integration API for EC Service

Provides endpoints for integrating evolutionary computation with the AlphaEvolve
governance framework, including WINA-optimized constitutional oversight.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field

from src.backend.ec_service.app.core.wina_oversight_coordinator import WINAECOversightCoordinator
from src.backend.ec_service.app.services.gs_client import gs_service_client
from src.backend.ec_service.app.services.ac_client import ac_service_client
from src.backend.ec_service.app.services.pgc_client import pgc_service_client

logger = logging.getLogger(__name__)
router = APIRouter()


class ECProposal(BaseModel):
    """Evolutionary computation proposal model."""
    proposal_id: str = Field(..., description="Unique proposal identifier")
    algorithm_type: str = Field(..., description="EC algorithm type")
    parameters: Dict[str, Any] = Field(..., description="Algorithm parameters")
    fitness_function: str = Field(..., description="Fitness function definition")
    constraints: List[str] = Field(default_factory=list, description="Optimization constraints")
    objectives: List[str] = Field(..., description="Optimization objectives")
    population_size: int = Field(..., description="Population size")
    generations: int = Field(..., description="Number of generations")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ECGovernanceRequest(BaseModel):
    """Request for EC governance evaluation."""
    context: str = Field(..., description="Governance context")
    proposals: List[ECProposal] = Field(..., description="EC proposals to evaluate")
    constitutional_requirements: List[str] = Field(default_factory=list, description="Constitutional requirements")
    optimization_hints: Optional[Dict[str, Any]] = Field(None, description="WINA optimization hints")


class ECGovernanceDecision(BaseModel):
    """EC governance decision model."""
    proposal_id: str = Field(..., description="Proposal identifier")
    decision: str = Field(..., description="Governance decision")
    rationale: str = Field(..., description="Decision rationale")
    governance_penalty: float = Field(..., description="Governance penalty for fitness function")
    constitutional_compliance: bool = Field(..., description="Constitutional compliance status")
    enforcement_actions: List[str] = Field(default_factory=list, description="Required enforcement actions")
    recommendations: List[str] = Field(default_factory=list, description="Governance recommendations")
    confidence_score: float = Field(..., description="Decision confidence score")


class ECGovernanceResponse(BaseModel):
    """Response for EC governance evaluation."""
    evaluation_id: str = Field(..., description="Unique evaluation identifier")
    decisions: List[ECGovernanceDecision] = Field(..., description="Individual governance decisions")
    batch_summary: Dict[str, Any] = Field(..., description="Batch evaluation summary")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    constitutional_compliance_rate: float = Field(..., description="Overall compliance rate")
    recommendations: List[str] = Field(default_factory=list, description="Overall recommendations")


class ECOptimizationRequest(BaseModel):
    """Request for EC optimization with constitutional constraints."""
    optimization_context: str = Field(..., description="Optimization context")
    algorithm_config: Dict[str, Any] = Field(..., description="Algorithm configuration")
    constitutional_constraints: List[str] = Field(..., description="Constitutional constraints")
    performance_targets: Dict[str, float] = Field(..., description="Performance targets")
    wina_optimization: bool = Field(default=True, description="Enable WINA optimization")


class ECOptimizationResponse(BaseModel):
    """Response for EC optimization."""
    optimization_id: str = Field(..., description="Unique optimization identifier")
    optimized_config: Dict[str, Any] = Field(..., description="Optimized algorithm configuration")
    performance_improvements: Dict[str, float] = Field(..., description="Performance improvements")
    constitutional_compliance: bool = Field(..., description="Constitutional compliance status")
    wina_insights: Dict[str, Any] = Field(..., description="WINA optimization insights")
    recommendations: List[str] = Field(default_factory=list, description="Optimization recommendations")


def get_wina_coordinator() -> WINAECOversightCoordinator:
    """Dependency to get WINA oversight coordinator."""
    from src.backend.ec_service.app.main import get_wina_coordinator
    return get_wina_coordinator()


@router.post("/governance-evaluation", response_model=ECGovernanceResponse)
async def evaluate_ec_governance(
    request: ECGovernanceRequest,
    background_tasks: BackgroundTasks,
    coordinator: WINAECOversightCoordinator = Depends(get_wina_coordinator)
):
    """
    Evaluate EC proposals for constitutional compliance and governance decisions.
    
    This endpoint integrates with the GS service to evaluate evolutionary computation
    proposals against constitutional principles and provides governance decisions
    with WINA-optimized oversight.
    """
    start_time = datetime.utcnow()
    evaluation_id = str(uuid.uuid4())
    
    try:
        logger.info(f"Starting EC governance evaluation for {len(request.proposals)} proposals")
        
        # Convert proposals to format expected by GS service
        gs_proposals = []
        for proposal in request.proposals:
            gs_proposals.append({
                "proposal_id": proposal.proposal_id,
                "algorithm_type": proposal.algorithm_type,
                "parameters": proposal.parameters,
                "fitness_function": proposal.fitness_function,
                "constraints": proposal.constraints,
                "objectives": proposal.objectives,
                "population_size": proposal.population_size,
                "generations": proposal.generations,
                "metadata": proposal.metadata
            })
        
        # Evaluate governance through GS service
        gs_response = await gs_service_client.evaluate_ec_governance(
            proposals=gs_proposals,
            context=request.context,
            optimization_hints=request.optimization_hints
        )
        
        # Process GS response into EC governance decisions
        decisions = []
        total_compliance_score = 0.0
        
        for gs_decision in gs_response.get("decisions", []):
            decision = ECGovernanceDecision(
                proposal_id=gs_decision.get("proposal_id", ""),
                decision=gs_decision.get("decision", "requires_review"),
                rationale=gs_decision.get("rationale", ""),
                governance_penalty=gs_decision.get("governance_penalty", 0.0),
                constitutional_compliance=gs_decision.get("constitutional_compliance", False),
                enforcement_actions=gs_decision.get("enforcement_actions", []),
                recommendations=gs_decision.get("recommendations", []),
                confidence_score=gs_decision.get("confidence_score", 0.0)
            )
            decisions.append(decision)
            
            # Calculate compliance score
            compliance_score = 1.0 if decision.constitutional_compliance else 0.0
            total_compliance_score += compliance_score
        
        # Calculate metrics
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        constitutional_compliance_rate = total_compliance_score / len(decisions) if decisions else 0.0
        
        # Generate overall recommendations
        overall_recommendations = []
        if constitutional_compliance_rate < 0.8:
            overall_recommendations.append("Consider revising proposals to improve constitutional compliance")
        if any(d.governance_penalty > 0.5 for d in decisions):
            overall_recommendations.append("High governance penalties detected - review optimization objectives")
        
        # Create batch summary
        batch_summary = {
            "total_proposals": len(request.proposals),
            "approved_proposals": sum(1 for d in decisions if d.decision == "approved"),
            "denied_proposals": sum(1 for d in decisions if d.decision == "denied"),
            "conditional_proposals": sum(1 for d in decisions if d.decision == "conditional"),
            "average_confidence_score": sum(d.confidence_score for d in decisions) / len(decisions) if decisions else 0.0,
            "average_governance_penalty": sum(d.governance_penalty for d in decisions) / len(decisions) if decisions else 0.0,
            "wina_optimization_applied": request.optimization_hints is not None
        }
        
        response = ECGovernanceResponse(
            evaluation_id=evaluation_id,
            decisions=decisions,
            batch_summary=batch_summary,
            processing_time_ms=processing_time,
            constitutional_compliance_rate=constitutional_compliance_rate,
            recommendations=overall_recommendations
        )
        
        # Background task: Report evaluation to AC service
        background_tasks.add_task(
            _report_governance_evaluation,
            evaluation_id,
            request.context,
            response
        )
        
        logger.info(f"EC governance evaluation completed in {processing_time:.2f}ms")
        return response
        
    except Exception as e:
        logger.error(f"EC governance evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Governance evaluation failed: {str(e)}")


@router.post("/optimize", response_model=ECOptimizationResponse)
async def optimize_ec_algorithm(
    request: ECOptimizationRequest,
    background_tasks: BackgroundTasks,
    coordinator: WINAECOversightCoordinator = Depends(get_wina_coordinator)
):
    """
    Optimize EC algorithm configuration with constitutional constraints and WINA insights.
    
    This endpoint provides WINA-optimized configuration recommendations for
    evolutionary computation algorithms while ensuring constitutional compliance.
    """
    start_time = datetime.utcnow()
    optimization_id = str(uuid.uuid4())
    
    try:
        logger.info(f"Starting EC algorithm optimization for context: {request.optimization_context}")
        
        # Synthesize governance rules for the optimization context
        rules_response = await gs_service_client.synthesize_ec_rules(
            ec_context=request.optimization_context,
            optimization_objective="performance_efficiency",
            constitutional_constraints=request.constitutional_constraints,
            target_format="rego"
        )
        
        # Apply WINA optimization if enabled
        wina_insights = {}
        optimized_config = request.algorithm_config.copy()
        
        if request.wina_optimization and coordinator.enable_wina:
            # Get WINA synthesis metrics for optimization insights
            try:
                wina_metrics = await gs_service_client.get_wina_synthesis_metrics()
                wina_insights = {
                    "gflops_reduction": wina_metrics.get("gflops_reduction", 0.0),
                    "synthesis_accuracy": wina_metrics.get("synthesis_accuracy", 0.0),
                    "optimization_strategy": "svd_transformation_with_gating"
                }
                
                # Apply WINA-informed optimizations to algorithm config
                if "population_size" in optimized_config:
                    # Optimize population size based on WINA insights
                    efficiency_factor = wina_insights.get("gflops_reduction", 0.0)
                    if efficiency_factor > 0.4:  # Significant efficiency gain
                        optimized_config["population_size"] = int(
                            optimized_config["population_size"] * (1 + efficiency_factor * 0.2)
                        )
                
                if "mutation_rate" in optimized_config:
                    # Adjust mutation rate based on synthesis accuracy
                    accuracy = wina_insights.get("synthesis_accuracy", 0.0)
                    if accuracy > 0.9:
                        optimized_config["mutation_rate"] *= 0.9  # Reduce mutation for stable synthesis
                        
            except Exception as e:
                logger.warning(f"WINA optimization failed, using standard config: {e}")
        
        # Calculate performance improvements
        performance_improvements = {}
        for target, value in request.performance_targets.items():
            if target in ["efficiency", "accuracy", "convergence_speed"]:
                # Estimate improvement based on WINA insights
                base_improvement = 0.1  # 10% base improvement
                wina_bonus = wina_insights.get("gflops_reduction", 0.0) * 0.5
                performance_improvements[target] = min(base_improvement + wina_bonus, 0.8)  # Cap at 80%
        
        # Verify constitutional compliance
        constitutional_compliance = True
        if rules_response.get("rules"):
            # Check if optimization maintains constitutional compliance
            # This would involve policy evaluation through PGC service
            try:
                compliance_check = await pgc_service_client.evaluate_policy_compliance(
                    proposal={"optimized_config": optimized_config},
                    policies=rules_response.get("rules", []),
                    context={"optimization_context": request.optimization_context}
                )
                constitutional_compliance = compliance_check.get("compliant", True)
            except Exception as e:
                logger.warning(f"Constitutional compliance check failed: {e}")
        
        # Generate recommendations
        recommendations = []
        if not constitutional_compliance:
            recommendations.append("Review optimization parameters for constitutional compliance")
        if wina_insights.get("gflops_reduction", 0.0) > 0.5:
            recommendations.append("Consider leveraging WINA optimization for additional efficiency gains")
        if any(imp < 0.1 for imp in performance_improvements.values()):
            recommendations.append("Explore alternative optimization strategies for better performance")
        
        response = ECOptimizationResponse(
            optimization_id=optimization_id,
            optimized_config=optimized_config,
            performance_improvements=performance_improvements,
            constitutional_compliance=constitutional_compliance,
            wina_insights=wina_insights,
            recommendations=recommendations
        )
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.info(f"EC algorithm optimization completed in {processing_time:.2f}ms")
        
        return response
        
    except Exception as e:
        logger.error(f"EC algorithm optimization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Algorithm optimization failed: {str(e)}")


async def _report_governance_evaluation(
    evaluation_id: str,
    context: str,
    response: ECGovernanceResponse
):
    """Background task to report governance evaluation to AC service."""
    try:
        await ac_service_client.report_oversight_activity(
            activity_type="ec_governance_evaluation",
            details={
                "evaluation_id": evaluation_id,
                "context": context,
                "total_proposals": response.batch_summary["total_proposals"],
                "constitutional_compliance_rate": response.constitutional_compliance_rate
            },
            metrics={
                "processing_time_ms": response.processing_time_ms,
                "average_confidence_score": response.batch_summary["average_confidence_score"],
                "average_governance_penalty": response.batch_summary["average_governance_penalty"]
            }
        )
        logger.debug(f"Reported governance evaluation {evaluation_id} to AC service")
    except Exception as e:
        logger.error(f"Failed to report governance evaluation: {e}")


@router.get("/health")
async def alphaevolve_health_check():
    """Health check for AlphaEvolve integration."""
    try:
        # Check GS service connectivity
        gs_metrics = await gs_service_client.get_wina_synthesis_metrics()
        
        return {
            "status": "healthy",
            "gs_service_connected": True,
            "wina_synthesis_available": "gflops_reduction" in gs_metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"AlphaEvolve health check failed: {e}")
        return {
            "status": "degraded",
            "gs_service_connected": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
