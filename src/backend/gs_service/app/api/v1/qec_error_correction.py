"""
qec_error_correction.py

API endpoints for QEC-Inspired Error Correction Service.
Provides endpoints for error correction workflows, conflict resolution,
and performance monitoring.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from shared.database import get_async_db
from shared.models import ConstitutionalPrinciple, Policy, User
from shared.auth import get_current_active_user

# Import QEC error correction services
from app.services.qec_error_correction_service import (
    QECErrorCorrectionService,
    ConflictDetectionEngine,
    AutomaticResolutionWorkflow,
    SemanticValidationEngine,
    PolicyRefinementSuggester,
    ConflictComplexityScorer,
    ParallelConflictProcessor,
    ConflictType,
    ResolutionStrategy,
    ErrorCorrectionStatus,
    ConflictDetectionResult,
    ErrorCorrectionResult,
    PolicyRefinementSuggestion
)

# Import Pydantic models for request/response
from pydantic import BaseModel, Field
from enum import Enum

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/qec-error-correction", tags=["QEC Error Correction"])

# Global service instance
qec_service = QECErrorCorrectionService()


# Pydantic models for API
class ErrorCorrectionRequest(BaseModel):
    """Request model for error correction workflow."""
    principle_ids: Optional[List[str]] = Field(default=None, description="Constitutional principle IDs to analyze")
    policy_ids: Optional[List[str]] = Field(default=None, description="Policy IDs to analyze")
    context_data: Optional[Dict[str, Any]] = Field(default=None, description="Additional context for correction")
    enable_parallel_processing: bool = Field(default=True, description="Enable parallel conflict processing")
    max_response_time_seconds: int = Field(default=30, description="Maximum response time target")


class ConflictDetectionRequest(BaseModel):
    """Request model for conflict detection."""
    principle_ids: List[str] = Field(..., description="Constitutional principle IDs")
    policy_ids: List[str] = Field(..., description="Policy IDs")
    context_data: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


class SemanticValidationRequest(BaseModel):
    """Request model for semantic validation."""
    principle_id: str = Field(..., description="Constitutional principle ID")
    policy_id: str = Field(..., description="Policy ID")
    context_data: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


class PolicyRefinementRequest(BaseModel):
    """Request model for policy refinement suggestions."""
    policy_id: str = Field(..., description="Policy ID to refine")
    principle_ids: List[str] = Field(..., description="Constitutional principle IDs to align with")
    context_data: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


@router.post("/workflow/execute")
async def execute_error_correction_workflow(
    request: ErrorCorrectionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Execute complete QEC error correction workflow.
    
    Performs conflict detection, automatic resolution, semantic validation,
    and human escalation as needed. Targets <30 second response times
    and 80% automatic resolution rate.
    """
    try:
        # Fetch principles and policies
        principles = []
        if request.principle_ids:
            principle_query = select(ConstitutionalPrinciple).where(
                ConstitutionalPrinciple.id.in_(request.principle_ids)
            )
            principle_result = await db.execute(principle_query)
            principles = principle_result.scalars().all()
        
        policies = []
        if request.policy_ids:
            policy_query = select(Policy).where(
                Policy.id.in_(request.policy_ids)
            )
            policy_result = await db.execute(policy_query)
            policies = policy_result.scalars().all()
        
        if not principles and not policies:
            # Fetch all active principles and policies
            all_principles_query = select(ConstitutionalPrinciple).where(
                ConstitutionalPrinciple.status == "active"
            )
            all_principles_result = await db.execute(all_principles_query)
            principles = all_principles_result.scalars().all()
            
            all_policies_query = select(Policy).where(
                Policy.status == "active"
            )
            all_policies_result = await db.execute(all_policies_query)
            policies = all_policies_result.scalars().all()
        
        # Execute error correction workflow
        workflow_results = await qec_service.process_error_correction_workflow(
            principles=principles,
            policies=policies,
            context_data=request.context_data,
            db=db
        )
        
        # Log workflow execution
        logger.info(f"Error correction workflow executed by user {current_user.id}: "
                   f"{workflow_results['conflicts_detected']} conflicts, "
                   f"{workflow_results['automatic_resolutions']} auto-resolved, "
                   f"{workflow_results['escalations_required']} escalated")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Error correction workflow completed successfully",
                "workflow_results": workflow_results,
                "execution_metadata": {
                    "executed_by": str(current_user.id),
                    "execution_time": datetime.utcnow().isoformat(),
                    "principles_analyzed": len(principles),
                    "policies_analyzed": len(policies)
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error in error correction workflow: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error correction workflow failed: {str(e)}"
        )


@router.post("/conflicts/detect")
async def detect_conflicts(
    request: ConflictDetectionRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Detect conflicts between constitutional principles and policies.
    
    Analyzes specified principles and policies for conflicts using
    constitutional distance scoring and semantic analysis.
    """
    try:
        # Fetch principles
        principle_query = select(ConstitutionalPrinciple).where(
            ConstitutionalPrinciple.id.in_(request.principle_ids)
        )
        principle_result = await db.execute(principle_query)
        principles = principle_result.scalars().all()
        
        # Fetch policies
        policy_query = select(Policy).where(
            Policy.id.in_(request.policy_ids)
        )
        policy_result = await db.execute(policy_query)
        policies = policy_result.scalars().all()
        
        if not principles or not policies:
            raise HTTPException(
                status_code=400,
                detail="Both principles and policies must be provided and exist"
            )
        
        # Detect conflicts
        conflicts = await qec_service.conflict_detector.detect_conflicts(
            principles=principles,
            policies=policies,
            context_data=request.context_data
        )
        
        # Format conflicts for response
        conflict_data = []
        for conflict in conflicts:
            conflict_data.append({
                "conflict_detected": conflict.conflict_detected,
                "conflict_type": conflict.conflict_type.value if conflict.conflict_type else None,
                "severity": conflict.severity.value if conflict.severity else None,
                "conflicting_principles": conflict.conflicting_principles,
                "conflicting_policies": conflict.conflicting_policies,
                "conflict_description": conflict.conflict_description,
                "confidence_score": conflict.confidence_score,
                "recommended_strategy": conflict.recommended_strategy.value if conflict.recommended_strategy else None,
                "detection_metadata": conflict.detection_metadata
            })
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Conflict detection completed - {len(conflicts)} conflicts found",
                "conflicts": conflict_data,
                "detection_metadata": {
                    "principles_analyzed": len(principles),
                    "policies_analyzed": len(policies),
                    "detection_time": datetime.utcnow().isoformat(),
                    "detected_by": str(current_user.id)
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error in conflict detection: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Conflict detection failed: {str(e)}"
        )


@router.post("/validation/semantic")
async def validate_semantic_consistency(
    request: SemanticValidationRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Validate semantic consistency between a principle and policy.
    
    Uses constitutional distance calculation and semantic analysis
    to validate alignment and suggest corrections if needed.
    """
    try:
        # Fetch principle
        principle_query = select(ConstitutionalPrinciple).where(
            ConstitutionalPrinciple.id == request.principle_id
        )
        principle_result = await db.execute(principle_query)
        principle = principle_result.scalar_one_or_none()
        
        if not principle:
            raise HTTPException(
                status_code=404,
                detail=f"Constitutional principle {request.principle_id} not found"
            )
        
        # Fetch policy
        policy_query = select(Policy).where(
            Policy.id == request.policy_id
        )
        policy_result = await db.execute(policy_query)
        policy = policy_result.scalar_one_or_none()
        
        if not policy:
            raise HTTPException(
                status_code=404,
                detail=f"Policy {request.policy_id} not found"
            )
        
        # Perform semantic validation
        validation_result = await qec_service.semantic_validator.validate_and_correct(
            principle=principle,
            policy=policy,
            context_data=request.context_data
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Semantic validation completed",
                "validation_result": {
                    "correction_id": validation_result.correction_id,
                    "status": validation_result.status.value,
                    "correction_applied": validation_result.correction_applied,
                    "fidelity_improvement": validation_result.fidelity_improvement,
                    "response_time_seconds": validation_result.response_time_seconds,
                    "correction_description": validation_result.correction_description,
                    "recommended_actions": validation_result.recommended_actions,
                    "escalation_required": validation_result.escalation_required,
                    "correction_metadata": validation_result.correction_metadata
                },
                "validation_metadata": {
                    "principle_id": str(principle.id),
                    "policy_id": str(policy.id),
                    "validated_by": str(current_user.id),
                    "validation_time": datetime.utcnow().isoformat()
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error in semantic validation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Semantic validation failed: {str(e)}"
        )


@router.get("/performance/summary")
async def get_performance_summary(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current performance summary for the QEC error correction service.
    
    Returns metrics on automatic resolution rates, response times,
    accuracy rates, and target achievement.
    """
    try:
        performance_summary = qec_service.get_performance_summary()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Performance summary retrieved successfully",
                "performance_summary": performance_summary,
                "summary_metadata": {
                    "retrieved_by": str(current_user.id),
                    "retrieval_time": datetime.utcnow().isoformat(),
                    "service_uptime": "active"  # Could be calculated from service start time
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving performance summary: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve performance summary: {str(e)}"
        )


@router.post("/refinement/suggestions")
async def generate_policy_refinement_suggestions(
    request: PolicyRefinementRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate policy refinement suggestions based on constitutional principles.

    Analyzes a policy against specified constitutional principles and
    provides specific suggestions for improving constitutional alignment.
    """
    try:
        # Fetch policy
        policy_query = select(Policy).where(
            Policy.id == request.policy_id
        )
        policy_result = await db.execute(policy_query)
        policy = policy_result.scalar_one_or_none()

        if not policy:
            raise HTTPException(
                status_code=404,
                detail=f"Policy {request.policy_id} not found"
            )

        # Fetch principles
        principle_query = select(ConstitutionalPrinciple).where(
            ConstitutionalPrinciple.id.in_(request.principle_ids)
        )
        principle_result = await db.execute(principle_query)
        principles = principle_result.scalars().all()

        if not principles:
            raise HTTPException(
                status_code=400,
                detail="At least one valid constitutional principle must be provided"
            )

        # Generate refinement suggestions
        suggestions = await qec_service.refinement_suggester.generate_refinement_suggestions(
            policy=policy,
            principles=principles,
            context_data=request.context_data
        )

        # Format suggestions for response
        suggestion_data = []
        for suggestion in suggestions:
            suggestion_data.append({
                "suggestion_id": suggestion.suggestion_id,
                "policy_id": suggestion.policy_id,
                "principle_id": suggestion.principle_id,
                "refinement_type": suggestion.refinement_type,
                "original_text": suggestion.original_text,
                "suggested_text": suggestion.suggested_text,
                "justification": suggestion.justification,
                "constitutional_basis": suggestion.constitutional_basis,
                "confidence_score": suggestion.confidence_score,
                "impact_assessment": suggestion.impact_assessment
            })

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Generated {len(suggestions)} refinement suggestions",
                "suggestions": suggestion_data,
                "suggestion_metadata": {
                    "policy_id": str(policy.id),
                    "principles_analyzed": len(principles),
                    "generated_by": str(current_user.id),
                    "generation_time": datetime.utcnow().isoformat()
                }
            }
        )

    except Exception as e:
        logger.error(f"Error generating refinement suggestions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate refinement suggestions: {str(e)}"
        )


@router.post("/conflicts/resolve")
async def resolve_conflict_automatically(
    conflict_data: Dict[str, Any],
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Attempt automatic resolution of a specific conflict.

    Takes conflict detection data and attempts to resolve it using
    the automatic resolution workflow with fallback to escalation.
    """
    try:
        # Create ConflictDetectionResult from input data
        conflict = ConflictDetectionResult(
            conflict_detected=conflict_data.get("conflict_detected", True),
            conflict_type=ConflictType(conflict_data.get("conflict_type", "policy_inconsistency")),
            severity=ViolationSeverity(conflict_data.get("severity", "medium")),
            conflicting_principles=conflict_data.get("conflicting_principles", []),
            conflicting_policies=conflict_data.get("conflicting_policies", []),
            conflict_description=conflict_data.get("conflict_description", ""),
            confidence_score=conflict_data.get("confidence_score", 0.5),
            detection_metadata=conflict_data.get("detection_metadata", {}),
            recommended_strategy=ResolutionStrategy(conflict_data.get("recommended_strategy", "automatic_merge")) if conflict_data.get("recommended_strategy") else None
        )

        # Attempt automatic resolution
        resolution_result = await qec_service.resolution_workflow.resolve_conflict(
            conflict=conflict,
            db=db
        )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Conflict resolution attempted",
                "resolution_result": {
                    "correction_id": resolution_result.correction_id,
                    "status": resolution_result.status.value,
                    "conflict_type": resolution_result.conflict_type.value if resolution_result.conflict_type else None,
                    "resolution_strategy": resolution_result.resolution_strategy.value if resolution_result.resolution_strategy else None,
                    "correction_applied": resolution_result.correction_applied,
                    "fidelity_improvement": resolution_result.fidelity_improvement,
                    "response_time_seconds": resolution_result.response_time_seconds,
                    "correction_description": resolution_result.correction_description,
                    "recommended_actions": resolution_result.recommended_actions,
                    "escalation_required": resolution_result.escalation_required,
                    "escalation_reason": resolution_result.escalation_reason,
                    "correction_metadata": resolution_result.correction_metadata
                },
                "resolution_metadata": {
                    "resolved_by": str(current_user.id),
                    "resolution_time": datetime.utcnow().isoformat()
                }
            }
        )

    except Exception as e:
        logger.error(f"Error in conflict resolution: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Conflict resolution failed: {str(e)}"
        )


@router.get("/conflicts/complexity/{conflict_id}")
async def analyze_conflict_complexity(
    conflict_id: str,
    conflict_data: Dict[str, Any] = None,
    current_user: User = Depends(get_current_active_user)
):
    """
    Analyze the complexity of a conflict to determine escalation necessity.

    Scores conflict complexity based on multiple factors and determines
    if human escalation is required.
    """
    try:
        if not conflict_data:
            raise HTTPException(
                status_code=400,
                detail="Conflict data must be provided for complexity analysis"
            )

        # Create ConflictDetectionResult from input data
        conflict = ConflictDetectionResult(
            conflict_detected=conflict_data.get("conflict_detected", True),
            conflict_type=ConflictType(conflict_data.get("conflict_type", "policy_inconsistency")),
            severity=ViolationSeverity(conflict_data.get("severity", "medium")),
            conflicting_principles=conflict_data.get("conflicting_principles", []),
            conflicting_policies=conflict_data.get("conflicting_policies", []),
            conflict_description=conflict_data.get("conflict_description", ""),
            confidence_score=conflict_data.get("confidence_score", 0.5),
            detection_metadata=conflict_data.get("detection_metadata", {})
        )

        # Analyze complexity
        complexity_score, requires_escalation = await qec_service.complexity_scorer.score_complexity(
            conflict=conflict,
            context_data=conflict_data.get("context_data", {})
        )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Conflict complexity analysis completed",
                "complexity_analysis": {
                    "conflict_id": conflict_id,
                    "complexity_score": complexity_score,
                    "requires_escalation": requires_escalation,
                    "escalation_recommendation": (
                        "Human escalation recommended" if requires_escalation
                        else "Automatic resolution suitable"
                    ),
                    "complexity_factors": {
                        "stakeholder_impact": len(conflict.conflicting_principles) + len(conflict.conflicting_policies),
                        "severity_level": conflict.severity.value if conflict.severity else "unknown",
                        "confidence_score": conflict.confidence_score,
                        "conflict_type": conflict.conflict_type.value if conflict.conflict_type else "unknown"
                    }
                },
                "analysis_metadata": {
                    "analyzed_by": str(current_user.id),
                    "analysis_time": datetime.utcnow().isoformat()
                }
            }
        )

    except Exception as e:
        logger.error(f"Error in complexity analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Complexity analysis failed: {str(e)}"
        )
