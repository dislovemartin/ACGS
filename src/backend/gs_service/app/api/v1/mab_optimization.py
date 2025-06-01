"""
Multi-Armed Bandit Optimization API Endpoints

REST API endpoints for managing MAB prompt optimization,
viewing performance metrics, and configuring optimization parameters.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Optional, Any
import logging

from shared.database import get_async_db
from shared.auth import get_current_user_from_token, get_current_active_user
from ..core.mab_integration import MABIntegratedGSService
from ..core.mab_prompt_optimizer import MABConfig, MABAlgorithm, PromptTemplate
from ..schemas import ConstitutionalSynthesisInput, ConstitutionalSynthesisOutput
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# Global MAB service instance (would be dependency injected in production)
_mab_service: Optional[MABIntegratedGSService] = None


def get_mab_service() -> MABIntegratedGSService:
    """Get or create MAB service instance."""
    global _mab_service
    if _mab_service is None:
        _mab_service = MABIntegratedGSService()
    return _mab_service


# Pydantic models for API
class MABConfigRequest(BaseModel):
    algorithm: str = "thompson_sampling"
    exploration_rate: float = 0.1
    confidence_level: float = 0.95
    alpha_prior: float = 1.0
    beta_prior: float = 1.0
    semantic_similarity_weight: float = 0.4
    policy_quality_weight: float = 0.3
    constitutional_compliance_weight: float = 0.2
    bias_mitigation_weight: float = 0.1
    reward_threshold: float = 0.8


class PromptTemplateRequest(BaseModel):
    name: str
    template_content: str
    category: str
    version: str = "1.0"
    metadata: Dict[str, Any] = {}


class SynthesisRequest(BaseModel):
    context: str
    target_format: str = "rego"
    category: str = "constitutional"
    safety_level: str = "standard"
    additional_context: Dict[str, Any] = {}


class MABMetricsResponse(BaseModel):
    algorithm: str
    total_optimizations: int
    total_template_uses: int
    overall_success_rate: float
    template_count: int
    template_metrics: Dict[str, Any]
    recent_history: List[Dict[str, Any]]


class IntegrationStatusResponse(BaseModel):
    integration_metrics: Dict[str, Any]
    mab_optimization: Dict[str, Any]
    best_templates: List[Dict[str, Any]]
    reliability_config: Dict[str, Any]
    system_status: str


@router.get("/status", response_model=IntegrationStatusResponse)
async def get_mab_status():
    """Get comprehensive MAB integration status and metrics."""
    try:
        mab_service = get_mab_service()
        status_data = await mab_service.get_integration_status()
        return IntegrationStatusResponse(**status_data)
    except Exception as e:
        logger.error(f"Failed to get MAB status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve MAB status: {str(e)}"
        )


@router.get("/metrics", response_model=MABMetricsResponse)
async def get_mab_metrics():
    """Get detailed MAB optimization metrics."""
    try:
        mab_service = get_mab_service()
        metrics = mab_service.mab_optimizer.get_optimization_metrics()
        return MABMetricsResponse(**metrics)
    except Exception as e:
        logger.error(f"Failed to get MAB metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve MAB metrics: {str(e)}"
        )


@router.get("/templates/best")
async def get_best_templates(top_k: int = Query(5, ge=1, le=20)):
    """Get top-performing prompt templates."""
    try:
        mab_service = get_mab_service()
        best_templates = mab_service.mab_optimizer.get_best_performing_templates(top_k)
        return {"best_templates": best_templates}
    except Exception as e:
        logger.error(f"Failed to get best templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve best templates: {str(e)}"
        )


@router.post("/templates/register")
async def register_prompt_template(
    template_request: PromptTemplateRequest,
    # current_user = Depends(require_admin)  # Require admin access
):
    """Register a new prompt template for MAB optimization."""
    try:
        mab_service = get_mab_service()
        
        # Create template ID from name
        template_id = template_request.name.lower().replace(" ", "_").replace("-", "_")
        
        # Create PromptTemplate object
        template = PromptTemplate(
            template_id=template_id,
            name=template_request.name,
            template_content=template_request.template_content,
            category=template_request.category,
            version=template_request.version,
            metadata=template_request.metadata
        )
        
        # Register with MAB optimizer
        mab_service.mab_optimizer.register_prompt_template(template)
        
        return {
            "message": "Template registered successfully",
            "template_id": template_id,
            "template_name": template_request.name,
            "category": template_request.category
        }
    except Exception as e:
        logger.error(f"Failed to register template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register template: {str(e)}"
        )


@router.post("/synthesize")
async def synthesize_with_mab(
    synthesis_request: SynthesisRequest,
    # current_user = Depends(get_current_user)  # Require authentication
):
    """Synthesize constitutional policies using MAB-optimized prompts."""
    try:
        mab_service = get_mab_service()
        
        # Create synthesis input
        synthesis_input = ConstitutionalSynthesisInput(
            context=synthesis_request.context,
            target_format=synthesis_request.target_format,
            requirements=[],  # Would be populated from request
            constraints=[]    # Would be populated from request
        )
        
        # Prepare context
        context = {
            "category": synthesis_request.category,
            "safety_level": synthesis_request.safety_level,
            **synthesis_request.additional_context
        }
        
        # Execute MAB-optimized synthesis
        synthesis_output, integration_metadata = await mab_service.synthesize_with_mab_optimization(
            synthesis_input, context
        )
        
        return {
            "synthesis_result": {
                "context": synthesis_output.context,
                "generated_rules": synthesis_output.generated_rules,
                "constitutional_context": synthesis_output.constitutional_context,
                "synthesis_metadata": synthesis_output.synthesis_metadata,
                "raw_llm_response": synthesis_output.raw_llm_response
            },
            "integration_metadata": integration_metadata
        }
    except Exception as e:
        logger.error(f"MAB synthesis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MAB synthesis failed: {str(e)}"
        )


@router.put("/config")
async def update_mab_config(
    config_request: MABConfigRequest,
    # current_user = Depends(require_admin)  # Require admin access
):
    """Update MAB optimization configuration."""
    try:
        # Validate algorithm
        try:
            algorithm = MABAlgorithm(config_request.algorithm)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid algorithm: {config_request.algorithm}"
            )
        
        # Create new config
        new_config = MABConfig(
            algorithm=algorithm,
            exploration_rate=config_request.exploration_rate,
            confidence_level=config_request.confidence_level,
            alpha_prior=config_request.alpha_prior,
            beta_prior=config_request.beta_prior,
            semantic_similarity_weight=config_request.semantic_similarity_weight,
            policy_quality_weight=config_request.policy_quality_weight,
            constitutional_compliance_weight=config_request.constitutional_compliance_weight,
            bias_mitigation_weight=config_request.bias_mitigation_weight,
            reward_threshold=config_request.reward_threshold
        )
        
        # Reinitialize MAB service with new config
        global _mab_service
        _mab_service = MABIntegratedGSService(mab_config=new_config)
        
        return {
            "message": "MAB configuration updated successfully",
            "new_config": {
                "algorithm": new_config.algorithm.value,
                "exploration_rate": new_config.exploration_rate,
                "reward_threshold": new_config.reward_threshold
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update MAB config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update MAB config: {str(e)}"
        )


@router.get("/templates")
async def list_prompt_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    active_only: bool = Query(True, description="Show only active templates")
):
    """List all registered prompt templates."""
    try:
        mab_service = get_mab_service()
        templates = mab_service.mab_optimizer.prompt_templates
        
        template_list = []
        for template_id, template in templates.items():
            if category and template.category != category:
                continue
                
            template_info = {
                "template_id": template.template_id,
                "name": template.name,
                "category": template.category,
                "version": template.version,
                "total_uses": template.total_uses,
                "success_count": template.success_count,
                "average_reward": template.average_reward,
                "confidence_interval": template.confidence_interval,
                "created_at": template.created_at.isoformat()
            }
            template_list.append(template_info)
        
        return {
            "templates": template_list,
            "total_count": len(template_list),
            "categories": list(set(t.category for t in templates.values()))
        }
    except Exception as e:
        logger.error(f"Failed to list templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list templates: {str(e)}"
        )


@router.get("/algorithms")
async def list_available_algorithms():
    """List available MAB algorithms and their descriptions."""
    algorithms = [
        {
            "name": "thompson_sampling",
            "display_name": "Thompson Sampling",
            "description": "Bayesian approach using Beta-Bernoulli conjugate priors for exploration-exploitation balance",
            "best_for": "Dynamic environments with changing reward distributions",
            "parameters": ["alpha_prior", "beta_prior"]
        },
        {
            "name": "upper_confidence_bound",
            "display_name": "Upper Confidence Bound (UCB1)",
            "description": "Optimistic approach using confidence intervals for arm selection",
            "best_for": "Stable environments with consistent reward patterns",
            "parameters": ["confidence_level"]
        },
        {
            "name": "epsilon_greedy",
            "display_name": "Epsilon-Greedy",
            "description": "Simple exploration strategy with fixed exploration rate",
            "best_for": "Baseline comparison and simple scenarios",
            "parameters": ["exploration_rate"]
        }
    ]
    
    return {"algorithms": algorithms}
