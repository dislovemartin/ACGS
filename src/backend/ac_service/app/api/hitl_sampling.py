"""
Human-in-the-Loop Sampling API Endpoints

This module provides REST API endpoints for the HITL sampling system,
enabling uncertainty assessment, human oversight triggering, and feedback processing.
"""

import logging
import time
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_async_db as get_db
from ..schemas import (
    HITLSamplingRequest, HITLSamplingResult, HITLFeedbackRequest, 
    HITLPerformanceMetrics, UncertaintyMetrics
)
from ..services.human_in_the_loop_sampler import HumanInTheLoopSampler, UncertaintyAssessment
from ..services.hitl_cross_service_integration import HITLCrossServiceIntegrator, CrossServiceConfidenceMetrics
from shared.auth import get_current_active_user as get_current_user, require_admin, require_policy_manager
from shared.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hitl-sampling", tags=["Human-in-the-Loop Sampling"])

# Global HITL sampler instance and cross-service integrator
hitl_sampler = HumanInTheLoopSampler()
cross_service_integrator = HITLCrossServiceIntegrator(hitl_sampler)


@router.post("/assess", response_model=HITLSamplingResult)
async def assess_uncertainty(
    request: HITLSamplingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Assess uncertainty for a constitutional decision and determine if human oversight is required.
    
    This endpoint performs comprehensive uncertainty analysis across multiple dimensions
    and determines whether human intervention is needed based on configurable thresholds.
    """
    try:
        start_time = time.time()
        
        # Convert request to decision context
        decision_context = dict(request.decision_context)
        decision_context.update({
            "user_id": current_user.id,
            "decision_scope": request.decision_scope,
            "time_pressure": request.time_pressure,
            "reversibility": request.reversibility,
            "impact_magnitude": request.impact_magnitude,
            "safety_critical": request.safety_critical,
            "stakeholder_count": request.stakeholder_count,
            "stakeholder_diversity": request.stakeholder_diversity,
            "stakeholder_conflicts": request.stakeholder_conflicts,
            "requires_public_consultation": request.requires_public_consultation,
            "multi_service": request.multi_service,
            "database_changes": request.database_changes,
            "external_apis": request.external_apis,
            "real_time_processing": request.real_time_processing,
            "security_implications": request.security_implications,
            "performance_critical": request.performance_critical,
            "novel_technology": request.novel_technology,
            "novel_scenario": request.novel_scenario,
            "has_training_data": request.has_training_data,
            "domain_expertise_available": request.domain_expertise_available,
            "clear_requirements": request.clear_requirements,
            "has_implementation_precedent": request.has_implementation_precedent,
            "has_stakeholder_feedback": request.has_stakeholder_feedback,
            "escalation_required": request.escalation_required
        })
        
        # Perform uncertainty assessment
        assessment = await hitl_sampler.assess_uncertainty(
            db=db,
            decision_context=decision_context,
            ai_confidence=request.ai_confidence,
            principle_ids=request.principle_ids
        )
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Convert assessment to response format
        result = HITLSamplingResult(
            decision_id=assessment.decision_id,
            overall_uncertainty=assessment.overall_uncertainty,
            dimensional_uncertainties=UncertaintyMetrics(
                constitutional=assessment.dimensional_uncertainties.get("constitutional", 0.0),
                technical=assessment.dimensional_uncertainties.get("technical", 0.0),
                stakeholder=assessment.dimensional_uncertainties.get("stakeholder", 0.0),
                precedent=assessment.dimensional_uncertainties.get("precedent", 0.0),
                complexity=assessment.dimensional_uncertainties.get("complexity", 0.0)
            ),
            confidence_score=assessment.confidence_score,
            requires_human_oversight=assessment.requires_human_oversight,
            recommended_oversight_level=assessment.recommended_oversight_level.value,
            triggers_activated=[trigger.value for trigger in assessment.triggers_activated],
            assessment_timestamp=assessment.timestamp,
            assessment_metadata=assessment.assessment_metadata,
            processing_time_ms=processing_time
        )
        
        logger.info(f"HITL assessment completed for {request.decision_id}: "
                   f"oversight_required={assessment.requires_human_oversight}, "
                   f"processing_time={processing_time:.2f}ms")
        
        return result
        
    except Exception as e:
        logger.error(f"HITL uncertainty assessment failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Uncertainty assessment failed: {str(e)}"
        )


@router.post("/trigger-oversight")
async def trigger_human_oversight(
    request: HITLSamplingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Trigger human oversight based on uncertainty assessment.
    
    This endpoint performs uncertainty assessment and automatically triggers
    human oversight if required, integrating with the existing escalation system.
    """
    try:
        # First perform assessment
        decision_context = dict(request.decision_context)
        decision_context.update({
            "user_id": current_user.id,
            "decision_scope": request.decision_scope,
            "safety_critical": request.safety_critical,
            "stakeholder_conflicts": request.stakeholder_conflicts,
            "escalation_required": request.escalation_required
        })
        
        assessment = await hitl_sampler.assess_uncertainty(
            db=db,
            decision_context=decision_context,
            ai_confidence=request.ai_confidence,
            principle_ids=request.principle_ids
        )
        
        # Trigger oversight if required
        escalation_request = None
        if assessment.requires_human_oversight:
            escalation_request = await hitl_sampler.trigger_human_oversight(
                db=db,
                assessment=assessment,
                user_id=current_user.id
            )
        
        return {
            "decision_id": assessment.decision_id,
            "oversight_triggered": assessment.requires_human_oversight,
            "oversight_level": assessment.recommended_oversight_level.value,
            "escalation_request_id": escalation_request.request_id if escalation_request else None,
            "triggers_activated": [trigger.value for trigger in assessment.triggers_activated],
            "overall_uncertainty": assessment.overall_uncertainty,
            "confidence_score": assessment.confidence_score
        }
        
    except Exception as e:
        logger.error(f"HITL oversight trigger failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Oversight trigger failed: {str(e)}"
        )


@router.post("/feedback")
async def submit_human_feedback(
    feedback: HITLFeedbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_policy_manager)
):
    """
    Submit human feedback on HITL sampling decisions for adaptive learning.
    
    This endpoint allows authorized users to provide feedback on the accuracy
    of HITL sampling decisions, enabling the system to learn and improve over time.
    """
    try:
        # Add user context to feedback metadata
        feedback_metadata = feedback.feedback_metadata or {}
        feedback_metadata.update({
            "feedback_user_id": current_user.id,
            "feedback_user_roles": current_user.roles,
            "feedback_timestamp": time.time(),
            "was_oversight_triggered": feedback.human_decision.get("oversight_needed", False)
        })
        
        # Process feedback
        success = await hitl_sampler.process_human_feedback(
            db=db,
            assessment_id=feedback.assessment_id,
            human_decision=feedback.human_decision,
            feedback_metadata=feedback_metadata
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process human feedback"
            )
        
        logger.info(f"Human feedback processed for assessment {feedback.assessment_id} "
                   f"by user {current_user.id}")
        
        return {
            "success": True,
            "assessment_id": feedback.assessment_id,
            "feedback_processed": True,
            "learning_enabled": hitl_sampler.config.learning_enabled
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Human feedback processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Feedback processing failed: {str(e)}"
        )


@router.get("/metrics", response_model=HITLPerformanceMetrics)
async def get_performance_metrics(
    current_user: User = Depends(require_policy_manager)
):
    """
    Get current performance metrics for the HITL sampling system.
    
    This endpoint provides comprehensive performance metrics including accuracy rates,
    false positive rates, and adaptive learning statistics.
    """
    try:
        metrics = await hitl_sampler.get_performance_metrics()
        
        if "error" in metrics:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Metrics calculation failed: {metrics['error']}"
            )
        
        return HITLPerformanceMetrics(**metrics)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Performance metrics retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Metrics retrieval failed: {str(e)}"
        )


@router.get("/config")
async def get_hitl_config(
    current_user: User = Depends(require_admin)
):
    """
    Get current HITL sampling configuration.
    
    This endpoint returns the current configuration including thresholds,
    weights, and learning parameters.
    """
    try:
        config = {
            "uncertainty_threshold": hitl_sampler.config.uncertainty_threshold,
            "confidence_threshold": hitl_sampler.config.confidence_threshold,
            "false_positive_target": hitl_sampler.config.false_positive_target,
            "accuracy_target": hitl_sampler.config.accuracy_target,
            "dimensional_weights": {
                dim.value: weight for dim, weight in hitl_sampler.config.dimensional_weights.items()
            },
            "learning_enabled": hitl_sampler.config.learning_enabled,
            "adaptation_rate": hitl_sampler.config.adaptation_rate,
            "feedback_window_hours": hitl_sampler.config.feedback_window_hours,
            "min_feedback_samples": hitl_sampler.config.min_feedback_samples,
            "monitoring_enabled": hitl_sampler.config.monitoring_enabled
        }
        
        return config
        
    except Exception as e:
        logger.error(f"HITL config retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Config retrieval failed: {str(e)}"
        )


@router.put("/config")
async def update_hitl_config(
    config_updates: Dict[str, Any],
    current_user: User = Depends(require_admin)
):
    """
    Update HITL sampling configuration.
    
    This endpoint allows administrators to update configuration parameters
    such as thresholds, weights, and learning settings.
    """
    try:
        # Validate and apply configuration updates
        if "uncertainty_threshold" in config_updates:
            threshold = float(config_updates["uncertainty_threshold"])
            if 0.0 <= threshold <= 1.0:
                hitl_sampler.config.uncertainty_threshold = threshold
            else:
                raise ValueError("uncertainty_threshold must be between 0.0 and 1.0")
        
        if "confidence_threshold" in config_updates:
            threshold = float(config_updates["confidence_threshold"])
            if 0.0 <= threshold <= 1.0:
                hitl_sampler.config.confidence_threshold = threshold
            else:
                raise ValueError("confidence_threshold must be between 0.0 and 1.0")
        
        if "learning_enabled" in config_updates:
            hitl_sampler.config.learning_enabled = bool(config_updates["learning_enabled"])
        
        if "adaptation_rate" in config_updates:
            rate = float(config_updates["adaptation_rate"])
            if 0.0 <= rate <= 1.0:
                hitl_sampler.config.adaptation_rate = rate
            else:
                raise ValueError("adaptation_rate must be between 0.0 and 1.0")
        
        logger.info(f"HITL config updated by user {current_user.id}: {config_updates}")
        
        return {
            "success": True,
            "updated_fields": list(config_updates.keys()),
            "current_config": {
                "uncertainty_threshold": hitl_sampler.config.uncertainty_threshold,
                "confidence_threshold": hitl_sampler.config.confidence_threshold,
                "learning_enabled": hitl_sampler.config.learning_enabled,
                "adaptation_rate": hitl_sampler.config.adaptation_rate
            }
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"HITL config update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Config update failed: {str(e)}"
        )


@router.post("/assess-cross-service", response_model=HITLSamplingResult)
async def assess_cross_service_uncertainty(
    request: HITLSamplingRequest,
    include_services: Optional[List[str]] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Assess uncertainty across all ACGS-PGP services for comprehensive oversight.

    This endpoint performs uncertainty analysis by gathering confidence metrics
    from all relevant microservices and provides enhanced oversight recommendations.
    """
    try:
        start_time = time.time()

        # Convert request to decision context
        decision_context = dict(request.decision_context)
        decision_context.update({
            "user_id": current_user.id,
            "decision_scope": request.decision_scope,
            "safety_critical": request.safety_critical,
            "stakeholder_conflicts": request.stakeholder_conflicts,
            "escalation_required": request.escalation_required
        })

        # Perform cross-service uncertainty assessment
        assessment, confidence_metrics = await cross_service_integrator.assess_cross_service_uncertainty(
            db=db,
            decision_context=decision_context,
            principle_ids=request.principle_ids,
            include_services=include_services
        )

        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000

        # Convert assessment to response format with enhanced metadata
        enhanced_metadata = dict(assessment.assessment_metadata)
        enhanced_metadata.update({
            "cross_service_confidence": confidence_metrics.get_average_confidence(),
            "gs_llm_confidence": confidence_metrics.gs_llm_confidence,
            "gs_synthesis_confidence": confidence_metrics.gs_synthesis_confidence,
            "fv_bias_confidence": confidence_metrics.fv_bias_confidence,
            "fv_fairness_confidence": confidence_metrics.fv_fairness_confidence,
            "pgc_enforcement_confidence": confidence_metrics.pgc_enforcement_confidence,
            "pgc_compilation_confidence": confidence_metrics.pgc_compilation_confidence,
            "integrity_verification_confidence": confidence_metrics.integrity_verification_confidence,
            "integrity_cryptographic_confidence": confidence_metrics.integrity_cryptographic_confidence,
            "services_included": include_services or ["gs_service", "fv_service", "pgc_service", "integrity_service"]
        })

        result = HITLSamplingResult(
            decision_id=assessment.decision_id,
            overall_uncertainty=assessment.overall_uncertainty,
            dimensional_uncertainties=UncertaintyMetrics(
                constitutional=assessment.dimensional_uncertainties.get("constitutional", 0.0),
                technical=assessment.dimensional_uncertainties.get("technical", 0.0),
                stakeholder=assessment.dimensional_uncertainties.get("stakeholder", 0.0),
                precedent=assessment.dimensional_uncertainties.get("precedent", 0.0),
                complexity=assessment.dimensional_uncertainties.get("complexity", 0.0)
            ),
            confidence_score=assessment.confidence_score,
            requires_human_oversight=assessment.requires_human_oversight,
            recommended_oversight_level=assessment.recommended_oversight_level.value,
            triggers_activated=[trigger.value for trigger in assessment.triggers_activated],
            assessment_timestamp=assessment.timestamp,
            assessment_metadata=enhanced_metadata,
            processing_time_ms=processing_time
        )

        logger.info(f"Cross-service HITL assessment completed for {request.decision_id}: "
                   f"oversight_required={assessment.requires_human_oversight}, "
                   f"cross_service_confidence={confidence_metrics.get_average_confidence():.3f}, "
                   f"processing_time={processing_time:.2f}ms")

        return result

    except Exception as e:
        logger.error(f"Cross-service HITL assessment failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cross-service assessment failed: {str(e)}"
        )


@router.post("/coordinate-oversight")
async def coordinate_cross_service_oversight(
    request: HITLSamplingRequest,
    include_services: Optional[List[str]] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_policy_manager)
):
    """
    Coordinate human oversight across all ACGS-PGP services.

    This endpoint performs cross-service assessment and automatically coordinates
    oversight activities across all relevant microservices.
    """
    try:
        # First perform cross-service assessment
        decision_context = dict(request.decision_context)
        decision_context.update({
            "user_id": current_user.id,
            "decision_scope": request.decision_scope,
            "safety_critical": request.safety_critical,
            "stakeholder_conflicts": request.stakeholder_conflicts
        })

        assessment, confidence_metrics = await cross_service_integrator.assess_cross_service_uncertainty(
            db=db,
            decision_context=decision_context,
            principle_ids=request.principle_ids,
            include_services=include_services
        )

        # Coordinate oversight if required
        coordination_result = await cross_service_integrator.coordinate_cross_service_oversight(
            assessment=assessment,
            confidence_metrics=confidence_metrics,
            user_id=current_user.id
        )

        return {
            "decision_id": assessment.decision_id,
            "assessment_summary": {
                "oversight_required": assessment.requires_human_oversight,
                "oversight_level": assessment.recommended_oversight_level.value,
                "overall_uncertainty": assessment.overall_uncertainty,
                "cross_service_confidence": confidence_metrics.get_average_confidence(),
                "triggers_activated": [trigger.value for trigger in assessment.triggers_activated]
            },
            "coordination_result": coordination_result,
            "service_confidence_breakdown": {
                "gs_service": {
                    "llm_confidence": confidence_metrics.gs_llm_confidence,
                    "synthesis_confidence": confidence_metrics.gs_synthesis_confidence
                },
                "fv_service": {
                    "bias_confidence": confidence_metrics.fv_bias_confidence,
                    "fairness_confidence": confidence_metrics.fv_fairness_confidence
                },
                "pgc_service": {
                    "enforcement_confidence": confidence_metrics.pgc_enforcement_confidence,
                    "compilation_confidence": confidence_metrics.pgc_compilation_confidence
                },
                "integrity_service": {
                    "verification_confidence": confidence_metrics.integrity_verification_confidence,
                    "cryptographic_confidence": confidence_metrics.integrity_cryptographic_confidence
                }
            }
        }

    except Exception as e:
        logger.error(f"Cross-service oversight coordination failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Oversight coordination failed: {str(e)}"
        )


@router.get("/integration-metrics")
async def get_integration_metrics(
    current_user: User = Depends(require_policy_manager)
):
    """
    Get cross-service integration metrics for the HITL sampling system.

    This endpoint provides comprehensive metrics about cross-service integration
    performance, service availability, and coordination effectiveness.
    """
    try:
        integration_metrics = await cross_service_integrator.get_integration_metrics()
        hitl_metrics = await hitl_sampler.get_performance_metrics()

        return {
            "hitl_performance": hitl_metrics,
            "cross_service_integration": integration_metrics,
            "combined_metrics": {
                "total_assessments": hitl_metrics.get("total_assessments", 0),
                "cross_service_assessments": integration_metrics.get("total_cross_service_assessments", 0),
                "cross_service_usage_rate": (
                    integration_metrics.get("total_cross_service_assessments", 0) /
                    max(1, hitl_metrics.get("total_assessments", 1))
                ),
                "overall_success_rate": (
                    (hitl_metrics.get("accuracy_rate", 0) + integration_metrics.get("success_rate", 0)) / 2
                ),
                "avg_processing_time_ms": integration_metrics.get("avg_integration_time_ms", 0)
            }
        }

    except Exception as e:
        logger.error(f"Integration metrics retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Integration metrics retrieval failed: {str(e)}"
        )
