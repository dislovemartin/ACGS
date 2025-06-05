"""
API endpoints for Collective Constitutional AI (CCAI) functionality.

This module provides REST API endpoints for democratic principle sourcing,
bias evaluation, and collective input aggregation using the CCAI methodology.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.auth import get_current_user_id
from ...services.collective_constitutional_ai import (
    get_collective_constitutional_ai,
    BiasCategory,
    DemocraticLegitimacyLevel,
    PolisConversation,
    BiasEvaluationResult,
    CollectiveInput,
    DemocraticPrinciple
)

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class CreatePolisConversationRequest(BaseModel):
    """Request model for creating a Polis conversation."""
    topic: str = Field(..., description="Conversation topic")
    description: str = Field(..., description="Detailed description")
    target_participants: int = Field(default=100, description="Target number of participants")


class BiasEvaluationRequest(BaseModel):
    """Request model for bias evaluation."""
    principle_text: str = Field(..., description="Constitutional principle text to evaluate")
    categories: Optional[List[BiasCategory]] = Field(
        default=None, 
        description="Specific bias categories to evaluate"
    )


class SynthesizePrincipleRequest(BaseModel):
    """Request model for synthesizing democratic principles."""
    topic: str = Field(..., description="Principle topic")
    conversation_id: str = Field(..., description="Polis conversation ID")
    min_consensus: float = Field(default=0.6, description="Minimum consensus threshold")


class PolisConversationResponse(BaseModel):
    """Response model for Polis conversation."""
    conversation_id: str
    topic: str
    description: str
    created_at: str
    participant_count: int
    statement_count: int
    status: str


class BiasEvaluationResponse(BaseModel):
    """Response model for bias evaluation."""
    category: str
    bias_score: float
    confidence: float
    examples: List[str]
    recommendations: List[str]
    baseline_comparison: Optional[float] = None


class DemocraticPrincipleResponse(BaseModel):
    """Response model for democratic principle."""
    principle_id: str
    title: str
    description: str
    legitimacy_level: str
    stakeholder_agreement: float
    bias_evaluation_summary: Dict[str, Any]
    input_count: int
    created_at: str


@router.post("/conversations", response_model=PolisConversationResponse)
async def create_polis_conversation(
    request: CreatePolisConversationRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new Polis conversation for democratic deliberation.
    
    This endpoint creates a conversation on the Polis platform for collecting
    stakeholder input on constitutional principles.
    """
    try:
        ccai = get_collective_constitutional_ai()
        
        conversation = await ccai.create_polis_conversation(
            topic=request.topic,
            description=request.description,
            target_participants=request.target_participants
        )
        
        return PolisConversationResponse(
            conversation_id=conversation.conversation_id,
            topic=conversation.topic,
            description=conversation.description,
            created_at=conversation.created_at.isoformat(),
            participant_count=conversation.participant_count,
            statement_count=conversation.statement_count,
            status=conversation.status
        )
        
    except Exception as e:
        logger.error(f"Error creating Polis conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create Polis conversation: {str(e)}"
        )


@router.post("/bias-evaluation", response_model=List[BiasEvaluationResponse])
async def evaluate_bias(
    request: BiasEvaluationRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Evaluate bias in constitutional principle text using BBQ framework.
    
    This endpoint analyzes the provided text across nine social dimensions
    to detect potential bias and provide recommendations for improvement.
    """
    try:
        ccai = get_collective_constitutional_ai()
        
        bias_results = await ccai.evaluate_bias_bbq(
            principle_text=request.principle_text,
            categories=request.categories
        )
        
        return [
            BiasEvaluationResponse(
                category=result.category.value,
                bias_score=result.bias_score,
                confidence=result.confidence,
                examples=result.examples,
                recommendations=result.recommendations,
                baseline_comparison=result.baseline_comparison
            )
            for result in bias_results
        ]
        
    except Exception as e:
        logger.error(f"Error evaluating bias: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate bias: {str(e)}"
        )


@router.post("/synthesize-principle", response_model=DemocraticPrincipleResponse)
async def synthesize_democratic_principle(
    request: SynthesizePrincipleRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Synthesize a democratic constitutional principle from collective input.
    
    This endpoint aggregates input from a Polis conversation and synthesizes
    it into a constitutional principle with democratic legitimacy scoring.
    """
    try:
        ccai = get_collective_constitutional_ai()
        
        # Aggregate collective input from conversation
        collective_inputs = await ccai.aggregate_collective_input(
            conversation_id=request.conversation_id,
            min_consensus=request.min_consensus
        )
        
        if not collective_inputs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No collective input found meeting consensus threshold"
            )
        
        # Synthesize democratic principle
        democratic_principle = await ccai.synthesize_democratic_principle(
            topic=request.topic,
            collective_inputs=collective_inputs
        )
        
        # Create bias evaluation summary
        bias_summary = {}
        for result in democratic_principle.bias_evaluation:
            bias_summary[result.category.value] = {
                "bias_score": result.bias_score,
                "confidence": result.confidence,
                "recommendations_count": len(result.recommendations)
            }
        
        return DemocraticPrincipleResponse(
            principle_id=democratic_principle.principle_id,
            title=democratic_principle.title,
            description=democratic_principle.description,
            legitimacy_level=democratic_principle.legitimacy_level.value,
            stakeholder_agreement=democratic_principle.stakeholder_agreement,
            bias_evaluation_summary=bias_summary,
            input_count=len(democratic_principle.collective_inputs),
            created_at=democratic_principle.created_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error synthesizing democratic principle: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to synthesize democratic principle: {str(e)}"
        )


@router.get("/conversations/{conversation_id}", response_model=PolisConversationResponse)
async def get_polis_conversation(
    conversation_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get details of a specific Polis conversation."""
    try:
        ccai = get_collective_constitutional_ai()
        
        if conversation_id not in ccai.active_conversations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )
        
        conversation = ccai.active_conversations[conversation_id]
        
        return PolisConversationResponse(
            conversation_id=conversation.conversation_id,
            topic=conversation.topic,
            description=conversation.description,
            created_at=conversation.created_at.isoformat(),
            participant_count=conversation.participant_count,
            statement_count=conversation.statement_count,
            status=conversation.status
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve conversation: {str(e)}"
        )


@router.get("/monitoring/legitimacy")
async def monitor_democratic_legitimacy(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Monitor democratic legitimacy metrics across all principles.
    
    Returns comprehensive metrics on democratic legitimacy, bias reduction,
    and stakeholder engagement for all constitutional principles.
    """
    try:
        ccai = get_collective_constitutional_ai()
        
        metrics = await ccai.monitor_democratic_legitimacy()
        
        return {
            "message": "Democratic legitimacy monitoring data retrieved successfully",
            "metrics": metrics,
            "ccai_status": {
                "target_bias_reduction": "40%",
                "methodology": "Anthropic Collective Constitutional AI",
                "evaluation_framework": "BBQ (Bias Benchmark for QA)"
            }
        }
        
    except Exception as e:
        logger.error(f"Error monitoring democratic legitimacy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to monitor democratic legitimacy: {str(e)}"
        )


@router.get("/conversations")
async def list_active_conversations(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """List all active Polis conversations."""
    try:
        ccai = get_collective_constitutional_ai()
        
        conversations = [
            PolisConversationResponse(
                conversation_id=conv.conversation_id,
                topic=conv.topic,
                description=conv.description,
                created_at=conv.created_at.isoformat(),
                participant_count=conv.participant_count,
                statement_count=conv.statement_count,
                status=conv.status
            )
            for conv in ccai.active_conversations.values()
        ]
        
        return {
            "message": f"Retrieved {len(conversations)} active conversations",
            "conversations": conversations,
            "total_count": len(conversations)
        }
        
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list conversations: {str(e)}"
        )
