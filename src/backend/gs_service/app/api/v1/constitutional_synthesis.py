"""
Constitutional Synthesis API endpoints for ACGS-PGP Phase 1

This module provides API endpoints for constitutional synthesis using
the constitutional prompting methodology.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.llm_integration import query_llm_for_constitutional_synthesis
from ...core.contextual_analyzer import contextual_analyzer, EnvironmentalFactor
from src.backend.shared.database import get_async_db
from ...schemas import (
    ConstitutionalSynthesisInput,
    ConstitutionalSynthesisOutput,
    ConstitutionallyCompliantRule
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/synthesize", response_model=ConstitutionalSynthesisOutput)
async def constitutional_synthesis_endpoint(
    synthesis_request: ConstitutionalSynthesisInput,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Perform constitutional synthesis using constitutional prompting methodology.
    
    This endpoint:
    1. Builds constitutional context from AC principles
    2. Applies constitutional prompting to LLM
    3. Generates constitutionally compliant policies
    4. Returns detailed compliance information
    """
    logger.info(f"Constitutional synthesis requested for context: {synthesis_request.context}")
    
    try:
        # Perform constitutional synthesis
        synthesis_result = await query_llm_for_constitutional_synthesis(synthesis_request)
        
        # Add contextual analysis in background
        background_tasks.add_task(
            _analyze_synthesis_context,
            synthesis_request.context,
            synthesis_result.constitutional_context
        )
        
        logger.info(f"Constitutional synthesis completed for context '{synthesis_request.context}' with {len(synthesis_result.generated_rules)} rules")
        return synthesis_result
        
    except Exception as e:
        logger.error(f"Error during constitutional synthesis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Constitutional synthesis failed: {str(e)}"
        )


@router.post("/analyze-context")
async def analyze_constitutional_context_endpoint(
    context: str,
    category: Optional[str] = None,
    auth_token: Optional[str] = None
):
    """
    Analyze constitutional context for a given target context.
    
    Returns constitutional context information without performing synthesis.
    """
    logger.info(f"Constitutional context analysis requested for: {context}")
    
    try:
        from ...core.constitutional_prompting import constitutional_prompt_builder
        
        constitutional_context = await constitutional_prompt_builder.build_constitutional_context(
            context=context,
            category=category,
            auth_token=auth_token
        )
        
        if "error" in constitutional_context:
            return {
                "context": context,
                "constitutional_context": None,
                "error": constitutional_context["error"]
            }
        return {
            "context": context,
            "constitutional_context": constitutional_context,
            "analysis_timestamp": constitutional_context.get("timestamp"),
            "applicable_principles": constitutional_context.get("principle_count", 0)
        }
        
    except Exception as e:
        logger.error(f"Error during constitutional context analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Constitutional context analysis failed: {str(e)}"
        )


@router.get("/constitutional-context/{context}")
async def get_constitutional_context_endpoint(
    context: str,
    category: Optional[str] = None
):
    """
    Get constitutional context information for a specific context.
    
    This is a simplified version that returns cached or quickly computed context.
    """
    try:
        # Perform contextual analysis
        contextual_analysis = contextual_analyzer.analyze_context(context)
        
        return {
            "context": context,
            "category": category,
            "contextual_analysis": contextual_analysis,
            "environmental_factors": len(contextual_analysis["relevant_factors"]),
            "similar_contexts": len(contextual_analysis["similar_contexts"]),
            "recommendations": contextual_analysis["recommendations"]
        }
        
    except Exception as e:
        logger.error(f"Error getting constitutional context: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get constitutional context: {str(e)}"
        )


@router.post("/environmental-factors")
async def add_environmental_factor_endpoint(
    factor_id: str,
    factor_type: str,
    value: str,
    source: Optional[str] = None,
    confidence: float = 1.0
):
    """
    Add an environmental factor for contextual analysis.
    
    Environmental factors influence policy generation and adaptation.
    """
    try:
        if not (0.0 <= confidence <= 1.0):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Confidence must be between 0.0 and 1.0"
            )
        
        factor = EnvironmentalFactor(
            factor_id=factor_id,
            factor_type=factor_type,
            value=value,
            source=source,
            confidence=confidence
        )
        
        contextual_analyzer.add_environmental_factor(factor)
        
        return {
            "message": f"Environmental factor '{factor_id}' added successfully",
            "factor": factor.to_dict()
        }
        
    except Exception as e:
        logger.error(f"Error adding environmental factor: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add environmental factor: {str(e)}"
        )


@router.get("/environmental-factors/{factor_type}")
async def get_environmental_factors_endpoint(factor_type: str):
    """Get all environmental factors of a specific type."""
    try:
        factors = contextual_analyzer.get_environmental_factors_by_type(factor_type)
        
        return {
            "factor_type": factor_type,
            "factors": [factor.to_dict() for factor in factors],
            "count": len(factors)
        }
        
    except Exception as e:
        logger.error(f"Error getting environmental factors: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get environmental factors: {str(e)}"
        )


@router.get("/adaptation-triggers/{context}")
async def get_adaptation_triggers_endpoint(context: str):
    """
    Get adaptation triggers for a specific context.
    
    Returns triggers that indicate when policies should be adapted.
    """
    try:
        triggers = contextual_analyzer.get_context_adaptation_triggers(context)
        
        return {
            "context": context,
            "triggers": triggers,
            "immediate_count": len(triggers["immediate_triggers"]),
            "scheduled_count": len(triggers["scheduled_triggers"]),
            "conditional_count": len(triggers["conditional_triggers"])
        }
        
    except Exception as e:
        logger.error(f"Error getting adaptation triggers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get adaptation triggers: {str(e)}"
        )


async def _analyze_synthesis_context(context: str, constitutional_context: dict):
    """
    Background task to analyze synthesis context and update environmental factors.
    """
    try:
        logger.info(f"Analyzing synthesis context in background: {context}")
        
        # Add constitutional context as environmental factors
        if constitutional_context.get("principles"):
            for principle in constitutional_context["principles"]:
                factor = EnvironmentalFactor(
                    factor_id=f"constitutional_principle_{principle['id']}",
                    factor_type="constitutional",
                    value=f"Principle: {principle['name']} (Priority: {principle.get('priority_weight', 'N/A')})",
                    source="constitutional_synthesis",
                    confidence=principle.get('priority_weight', 0.5)
                )
                contextual_analyzer.add_environmental_factor(factor)
        
        # Perform contextual analysis
        contextual_analyzer.analyze_context(context, constitutional_context)
        
        logger.info(f"Background context analysis completed for: {context}")
        
    except Exception as e:
        logger.error(f"Error in background context analysis: {e}")


@router.get("/health")
async def constitutional_synthesis_health():
    """Health check endpoint for constitutional synthesis service."""
    return {
        "status": "healthy",
        "service": "constitutional_synthesis",
        "version": "1.0.0",
        "environmental_factors": len(contextual_analyzer.environmental_factors),
        "context_history": len(contextual_analyzer.context_history)
    }
