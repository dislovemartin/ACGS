"""
Conflict Resolution API endpoints for the AC Service.
Handles conflict detection, resolution strategies, and monitoring with QEC integration.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from datetime import datetime

from shared.database import get_async_db as get_db
from ...schemas import (
    ACConflictResolution,
    ACConflictResolutionCreate,
    ACConflictResolutionUpdate
)
from ... import crud
from shared.auth import get_current_active_user, require_admin, require_policy_manager, require_auditor
from shared.models import User

# Import QEC enhancement components and service
from ...services.qec_conflict_resolver import QECConflictResolver
from ...services.conflict_resolution_orchestrator import ConflictResolutionOrchestrator

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize conflict resolution systems
qec_resolver = QECConflictResolver()
orchestrator = ConflictResolutionOrchestrator()


@router.post("/", response_model=ACConflictResolution)
async def create_conflict_resolution(
    conflict: ACConflictResolutionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_policy_manager)
):
    """Create a new conflict resolution entry with QEC enhancement."""
    # Create the conflict resolution
    conflict_resolution = await crud.create_ac_conflict_resolution(db, conflict, current_user.id)

    # Apply QEC enhancements using the resolver service
    try:
        # Get involved principles
        principles = await crud.get_ac_principles_by_ids(db, conflict.principle_ids)

        # Perform QEC analysis
        analysis = await qec_resolver.analyze_conflict(conflict_resolution, principles)

        # Update conflict resolution with QEC analysis results
        conflict_resolution.resolution_details = conflict_resolution.resolution_details or {}
        conflict_resolution.resolution_details["qec_analysis"] = {
            "constitutional_distances": analysis.constitutional_distances,
            "average_distance": analysis.average_distance,
            "error_predictions": analysis.error_predictions,
            "recommended_strategy": analysis.recommended_strategy,
            "priority_score": analysis.priority_score,
            "validation_scenarios": analysis.validation_scenarios,
            "qec_metadata": analysis.qec_metadata
        }

        await crud.update_ac_conflict_resolution(
            db, conflict_resolution.id,
            ACConflictResolutionUpdate(resolution_details=conflict_resolution.resolution_details)
        )

    except Exception as e:
        logger.warning(f"QEC enhancement failed for conflict {conflict_resolution.id}: {e}")

    return conflict_resolution


@router.get("/{conflict_id}", response_model=ACConflictResolution)
async def get_conflict_resolution(
    conflict_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific conflict resolution by ID."""
    conflict = await crud.get_ac_conflict_resolution(db, conflict_id)
    if not conflict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conflict resolution not found"
        )
    return conflict


@router.get("/", response_model=List[ACConflictResolution])
async def list_conflict_resolutions(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = Query(None, description="Filter by status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    priority_order: Optional[str] = Query(None, description="Ordering: 'qec' for QEC-based prioritization"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all conflict resolutions with pagination and QEC-based prioritization."""
    conflicts = await crud.get_ac_conflict_resolutions(
        db, status=status, severity=severity, skip=skip, limit=limit
    )

    # Apply QEC-based prioritization if requested
    if priority_order == "qec":
        try:
            # Sort by QEC priority score (higher score = higher priority)
            def get_qec_priority(conflict):
                qec_analysis = conflict.resolution_details.get("qec_analysis", {}) if conflict.resolution_details else {}
                return qec_analysis.get("priority_score", 0.0)

            conflicts.sort(key=get_qec_priority, reverse=True)
        except Exception as e:
            logger.warning(f"QEC prioritization failed: {e}")

    return conflicts


@router.put("/{conflict_id}", response_model=ACConflictResolution)
async def update_conflict_resolution(
    conflict_id: int,
    conflict_update: ACConflictResolutionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_policy_manager)
):
    """Update a conflict resolution with QEC re-evaluation."""
    conflict = await crud.get_ac_conflict_resolution(db, conflict_id)
    if not conflict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conflict resolution not found"
        )
    
    # Update the conflict resolution
    updated_conflict = await crud.update_ac_conflict_resolution(
        db, conflict_id, conflict_update
    )
    
    # Re-evaluate with QEC if principles changed and QEC is available
    if QEC_AVAILABLE and conflict_update.principle_ids:
        try:
            # Recalculate QEC metrics for updated principles
            principles = await crud.get_ac_principles_by_ids(db, conflict_update.principle_ids)
            
            distance_scores = []
            for principle in principles:
                score = distance_calculator.calculate_distance(principle)
                distance_scores.append(score)
            
            # Update QEC metadata
            existing_qec = updated_conflict.resolution_details.get("qec_metadata", {}) if updated_conflict.resolution_details else {}
            existing_qec.update({
                "distance_scores": distance_scores,
                "average_distance": sum(distance_scores) / len(distance_scores) if distance_scores else 0,
                "last_updated": datetime.now().isoformat()
            })
            
            updated_conflict.resolution_details = updated_conflict.resolution_details or {}
            updated_conflict.resolution_details["qec_metadata"] = existing_qec
            
            await crud.update_ac_conflict_resolution(
                db, conflict_id,
                ACConflictResolutionUpdate(resolution_details=updated_conflict.resolution_details)
            )
            
        except Exception as e:
            logger.warning(f"QEC re-evaluation failed for conflict {conflict_id}: {e}")
    
    return updated_conflict


@router.delete("/{conflict_id}")
async def delete_conflict_resolution(
    conflict_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"]))
):
    """Delete a conflict resolution."""
    conflict = await crud.get_ac_conflict_resolution(db, conflict_id)
    if not conflict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conflict resolution not found"
        )
    
    await crud.delete_ac_conflict_resolution(db, conflict_id)
    return {"message": "Conflict resolution deleted successfully"}


@router.post("/{conflict_id}/generate-patch")
async def generate_conflict_patch(
    conflict_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_policy_manager)
):
    """Generate automated patch for conflict resolution using QEC components."""
    conflict = await crud.get_ac_conflict_resolution(db, conflict_id)
    if not conflict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conflict resolution not found"
        )

    try:
        # Get involved principles
        principles = await crud.get_ac_principles_by_ids(db, conflict.principle_ids)

        # Perform QEC analysis if not already done
        existing_analysis = conflict.resolution_details.get("qec_analysis") if conflict.resolution_details else None
        if existing_analysis:
            # Reconstruct analysis from stored data
            from ...services.qec_conflict_resolver import ConflictAnalysis
            analysis = ConflictAnalysis(
                conflict_id=conflict.id,
                constitutional_distances=existing_analysis["constitutional_distances"],
                average_distance=existing_analysis["average_distance"],
                error_predictions=existing_analysis["error_predictions"],
                recommended_strategy=existing_analysis["recommended_strategy"],
                validation_scenarios=existing_analysis["validation_scenarios"],
                priority_score=existing_analysis["priority_score"],
                qec_metadata=existing_analysis["qec_metadata"]
            )
        else:
            # Perform fresh analysis
            analysis = await qec_resolver.analyze_conflict(conflict, principles)

        # Generate patch using QEC resolver
        patch_result = await qec_resolver.generate_patch(conflict, principles, analysis)

        return {
            "conflict_id": conflict_id,
            "patch_generated": patch_result.success,
            "strategy_used": patch_result.strategy_used,
            "validation_tests": len(patch_result.validation_tests),
            "confidence_score": patch_result.confidence_score,
            "patch_content": patch_result.patch_content,
            "patch_details": patch_result.metadata,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Patch generation failed for conflict {conflict_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Patch generation failed: {str(e)}"
        )


@router.get("/{conflict_id}/qec-insights")
async def get_conflict_qec_insights(
    conflict_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get QEC insights for a specific conflict resolution."""
    conflict = await crud.get_ac_conflict_resolution(db, conflict_id)
    if not conflict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conflict resolution not found"
        )

    qec_analysis = conflict.resolution_details.get("qec_analysis", {}) if conflict.resolution_details else {}

    if not qec_analysis:
        return {
            "conflict_id": conflict_id,
            "qec_enhanced": False,
            "message": "No QEC analysis available for this conflict"
        }

    return {
        "conflict_id": conflict_id,
        "qec_enhanced": True,
        "constitutional_distances": qec_analysis.get("constitutional_distances", []),
        "average_distance": qec_analysis.get("average_distance", 0),
        "error_predictions": qec_analysis.get("error_predictions", []),
        "recommended_strategy": qec_analysis.get("recommended_strategy"),
        "priority_score": qec_analysis.get("priority_score", 0),
        "validation_scenarios": qec_analysis.get("validation_scenarios", []),
        "qec_metadata": qec_analysis.get("qec_metadata", {}),
        "analysis_timestamp": qec_analysis.get("qec_metadata", {}).get("analysis_timestamp")
    }


# New Intelligent Conflict Resolution Endpoints

@router.post("/detect-conflicts")
async def detect_conflicts(
    principle_ids: Optional[List[int]] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_policy_manager)
):
    """Run intelligent conflict detection scan."""
    try:
        detected_conflicts = await orchestrator.run_conflict_detection_scan(
            db, principle_ids, current_user.id
        )

        return {
            "scan_completed": True,
            "conflicts_detected": len(detected_conflicts),
            "conflicts": [
                {
                    "conflict_type": conflict.conflict_type.value,
                    "severity": conflict.severity.value,
                    "principle_ids": conflict.principle_ids,
                    "confidence_score": conflict.confidence_score,
                    "priority_score": conflict.priority_score,
                    "description": conflict.description,
                    "recommended_strategy": conflict.recommended_strategy
                }
                for conflict in detected_conflicts
            ],
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Conflict detection scan failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Conflict detection failed: {str(e)}"
        )


@router.post("/{conflict_id}/resolve-automatically")
async def resolve_conflict_automatically(
    conflict_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_policy_manager)
):
    """Attempt automatic resolution of a conflict."""
    try:
        success, resolution_result, escalation_request = await orchestrator.resolve_conflict_automatically(
            db, conflict_id, None, current_user.id
        )

        response = {
            "conflict_id": conflict_id,
            "resolution_attempted": True,
            "success": success,
            "timestamp": datetime.now().isoformat()
        }

        if resolution_result:
            response["resolution_details"] = {
                "strategy_used": resolution_result.strategy_used.value,
                "confidence_score": resolution_result.confidence_score,
                "validation_passed": resolution_result.validation_passed,
                "processing_time": resolution_result.processing_time,
                "generated_patch": resolution_result.generated_patch is not None
            }

        if escalation_request:
            response["escalation"] = {
                "escalated": True,
                "escalation_level": escalation_request.escalation_level.value,
                "escalation_reason": escalation_request.escalation_reason.value,
                "urgency_score": escalation_request.urgency_score,
                "timeout_deadline": escalation_request.timeout_deadline.isoformat()
            }

        return response

    except Exception as e:
        logger.error(f"Automatic resolution failed for conflict {conflict_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Automatic resolution failed: {str(e)}"
        )


@router.post("/{conflict_id}/human-intervention")
async def handle_human_intervention(
    conflict_id: int,
    intervention_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_policy_manager)
):
    """Handle human intervention in conflict resolution."""
    try:
        success = await orchestrator.handle_human_intervention(
            db, conflict_id, intervention_data, current_user.id
        )

        return {
            "conflict_id": conflict_id,
            "intervention_processed": success,
            "decision": intervention_data.get("decision"),
            "processed_by": current_user.id,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Human intervention failed for conflict {conflict_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Human intervention failed: {str(e)}"
        )


@router.get("/performance-report")
async def get_performance_report(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auditor)
):
    """Get comprehensive system performance report."""
    try:
        report = await orchestrator.get_system_performance_report(db)
        return report

    except Exception as e:
        logger.error(f"Performance report generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Performance report generation failed: {str(e)}"
        )


@router.get("/{conflict_id}/audit-trace")
async def get_conflict_audit_trace(
    conflict_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auditor)
):
    """Get complete audit trace for a conflict resolution process."""
    try:
        trace = await orchestrator.auditor.generate_conflict_trace(db, conflict_id)

        return {
            "conflict_id": conflict_id,
            "trace": {
                "detection_trace": trace.detection_trace,
                "resolution_attempts": trace.resolution_attempts,
                "escalation_trace": trace.escalation_trace,
                "final_outcome": trace.final_outcome,
                "total_processing_time": trace.total_processing_time,
                "integrity_verified": trace.integrity_verified,
                "audit_entries_count": len(trace.audit_entries)
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Audit trace generation failed for conflict {conflict_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audit trace generation failed: {str(e)}"
        )
