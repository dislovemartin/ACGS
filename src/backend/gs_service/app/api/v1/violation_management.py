"""
violation_management.py

API endpoints for constitutional violation management.
Provides REST API for violation detection, escalation, audit trail access,
and threshold configuration management.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload

from shared.database import get_async_db
from shared.models import (
    ConstitutionalViolation, ViolationAlert, ViolationEscalation,
    ViolationThreshold, User, ConstitutionalPrinciple, Policy
)
from shared.auth import get_current_active_user

# Import violation services
from app.services.violation_detection_service import (
    ViolationDetectionService,
    ViolationType,
    ViolationSeverity,
    ViolationDetectionResult,
    BatchViolationResult
)
from app.services.violation_escalation_service import (
    ViolationEscalationService,
    EscalationLevel,
    EscalationResult
)
from app.services.violation_audit_service import (
    ViolationAuditService,
    AuditEventType,
    AnalyticsPeriod,
    ViolationAnalytics,
    ComplianceReport
)
from app.core.violation_config import (
    ViolationConfigManager,
    ThresholdConfig,
    get_violation_config_manager
)

# Import WebSocket broadcasting
from app.api.v1.fidelity_monitoring_websocket import (
    monitoring_manager,
    ViolationAlert as WSViolationAlert
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
violation_detection_service = ViolationDetectionService()
violation_escalation_service = ViolationEscalationService()
violation_audit_service = ViolationAuditService()


@router.get("/violations", response_model=Dict[str, Any])
async def get_violations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    violation_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    escalated: Optional[bool] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get constitutional violations with filtering and pagination.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        violation_type: Filter by violation type
        severity: Filter by severity level
        status: Filter by status
        escalated: Filter by escalation status
        start_date: Filter violations after this date
        end_date: Filter violations before this date
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Paginated list of violations with metadata
    """
    try:
        # Build query filters
        filters = []
        
        if violation_type:
            filters.append(ConstitutionalViolation.violation_type == violation_type)
        if severity:
            filters.append(ConstitutionalViolation.severity == severity)
        if status:
            filters.append(ConstitutionalViolation.status == status)
        if escalated is not None:
            filters.append(ConstitutionalViolation.escalated == escalated)
        if start_date:
            filters.append(ConstitutionalViolation.detected_at >= start_date)
        if end_date:
            filters.append(ConstitutionalViolation.detected_at <= end_date)
        
        # Get total count
        count_query = select(func.count(ConstitutionalViolation.id))
        if filters:
            count_query = count_query.where(and_(*filters))
        
        total_result = await db.execute(count_query)
        total_count = total_result.scalar()
        
        # Get violations
        query = select(ConstitutionalViolation).options(
            selectinload(ConstitutionalViolation.principle),
            selectinload(ConstitutionalViolation.policy)
        )
        
        if filters:
            query = query.where(and_(*filters))
        
        query = query.order_by(desc(ConstitutionalViolation.detected_at)).offset(skip).limit(limit)
        
        result = await db.execute(query)
        violations = result.scalars().all()
        
        # Format response
        violations_data = []
        for violation in violations:
            violation_data = {
                "id": str(violation.id),
                "violation_type": violation.violation_type,
                "severity": violation.severity,
                "description": violation.violation_description,
                "detection_method": violation.detection_method,
                "fidelity_score": float(violation.fidelity_score) if violation.fidelity_score else None,
                "distance_score": float(violation.distance_score) if violation.distance_score else None,
                "status": violation.status,
                "escalated": violation.escalated,
                "escalation_level": violation.escalation_level,
                "detected_at": violation.detected_at.isoformat(),
                "resolved_at": violation.resolved_at.isoformat() if violation.resolved_at else None,
                "context_data": violation.context_data,
                "detection_metadata": violation.detection_metadata
            }
            violations_data.append(violation_data)
        
        return {
            "violations": violations_data,
            "pagination": {
                "total": total_count,
                "skip": skip,
                "limit": limit,
                "has_more": skip + limit < total_count
            },
            "filters_applied": {
                "violation_type": violation_type,
                "severity": severity,
                "status": status,
                "escalated": escalated,
                "date_range": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting violations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get violations: {str(e)}")


@router.get("/violations/{violation_id}", response_model=Dict[str, Any])
async def get_violation(
    violation_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get detailed information about a specific violation.
    
    Args:
        violation_id: Violation ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Detailed violation information with audit history
    """
    try:
        # Get violation
        result = await db.execute(
            select(ConstitutionalViolation).options(
                selectinload(ConstitutionalViolation.principle),
                selectinload(ConstitutionalViolation.policy)
            ).where(ConstitutionalViolation.id == violation_id)
        )
        
        violation = result.scalar_one_or_none()
        if not violation:
            raise HTTPException(status_code=404, detail="Violation not found")
        
        # Get audit history
        audit_history = await violation_audit_service.get_violation_history(str(violation_id), db)
        
        # Get escalation history
        escalations_result = await db.execute(
            select(ViolationEscalation).where(
                ViolationEscalation.violation_id == violation_id
            ).order_by(desc(ViolationEscalation.escalated_at))
        )
        escalations = escalations_result.scalars().all()
        
        escalation_history = []
        for escalation in escalations:
            escalation_data = {
                "id": str(escalation.id),
                "escalation_type": escalation.escalation_type,
                "escalation_level": escalation.escalation_level,
                "escalation_reason": escalation.escalation_reason,
                "status": escalation.status,
                "assigned_to": str(escalation.assigned_to) if escalation.assigned_to else None,
                "escalated_at": escalation.escalated_at.isoformat(),
                "resolved_at": escalation.resolved_at.isoformat() if escalation.resolved_at else None,
                "response_time_seconds": escalation.response_time_seconds,
                "resolution_time_seconds": escalation.resolution_time_seconds
            }
            escalation_history.append(escalation_data)
        
        return {
            "violation": {
                "id": str(violation.id),
                "violation_type": violation.violation_type,
                "severity": violation.severity,
                "description": violation.violation_description,
                "detection_method": violation.detection_method,
                "fidelity_score": float(violation.fidelity_score) if violation.fidelity_score else None,
                "distance_score": float(violation.distance_score) if violation.distance_score else None,
                "status": violation.status,
                "resolution_status": violation.resolution_status,
                "resolution_description": violation.resolution_description,
                "escalated": violation.escalated,
                "escalation_level": violation.escalation_level,
                "detected_at": violation.detected_at.isoformat(),
                "resolved_at": violation.resolved_at.isoformat() if violation.resolved_at else None,
                "context_data": violation.context_data,
                "detection_metadata": violation.detection_metadata,
                "principle_id": str(violation.principle_id) if violation.principle_id else None,
                "policy_id": str(violation.policy_id) if violation.policy_id else None
            },
            "audit_history": audit_history,
            "escalation_history": escalation_history
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting violation {violation_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get violation: {str(e)}")


@router.post("/violations/scan", response_model=Dict[str, Any])
async def trigger_violation_scan(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Trigger manual violation scan.
    
    Args:
        background_tasks: FastAPI background tasks
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Scan initiation confirmation
    """
    try:
        # Add background task for violation scanning
        background_tasks.add_task(perform_violation_scan, db)
        
        return {
            "scan_initiated": True,
            "message": "Violation scan initiated in background",
            "initiated_by": current_user.username,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error triggering violation scan: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger scan: {str(e)}")


async def perform_violation_scan(db: AsyncSession):
    """Perform violation scan in background."""
    try:
        # Perform batch violation scan
        scan_result = await violation_detection_service.scan_for_violations(db)
        
        # Process detected violations
        for detection_result in scan_result.detection_results:
            if detection_result.violation_detected:
                # Create violation record
                violation = ConstitutionalViolation(
                    violation_type=detection_result.violation_type.value,
                    severity=detection_result.severity.value,
                    violation_description=detection_result.description,
                    detection_method="automated_scan",
                    fidelity_score=detection_result.fidelity_score,
                    distance_score=detection_result.distance_score,
                    context_data=detection_result.context_data,
                    detection_metadata=detection_result.detection_metadata
                )
                
                db.add(violation)
                await db.flush()
                
                # Log audit event
                await violation_audit_service.log_violation_event(
                    AuditEventType.VIOLATION_DETECTED,
                    violation,
                    additional_data={"scan_type": "manual_trigger"},
                    db=db
                )
                
                # Check for escalation
                escalation_result = await violation_escalation_service.evaluate_escalation(violation, db)
                if escalation_result and escalation_result.escalated:
                    # Broadcast escalation notification
                    await monitoring_manager.broadcast_escalation_notification(
                        escalation_result, str(violation.id)
                    )
                
                # Create WebSocket violation alert
                ws_alert = WSViolationAlert(
                    alert_id=f"violation_{violation.id}",
                    violation_id=str(violation.id),
                    violation_type=detection_result.violation_type.value,
                    severity=detection_result.severity.value,
                    title=f"{detection_result.violation_type.value.replace('_', ' ').title()} Detected",
                    description=detection_result.description,
                    fidelity_score=detection_result.fidelity_score,
                    distance_score=detection_result.distance_score,
                    recommended_actions=detection_result.recommended_actions,
                    escalated=violation.escalated,
                    escalation_level=violation.escalation_level,
                    timestamp=datetime.now(timezone.utc)
                )
                
                # Broadcast violation alert
                await monitoring_manager.broadcast_violation_alert(ws_alert)
        
        await db.commit()
        logger.info(f"Violation scan completed: {scan_result.violations_detected} violations detected")
        
    except Exception as e:
        logger.error(f"Error in violation scan: {e}")
        await db.rollback()


@router.post("/violations/{violation_id}/escalate", response_model=Dict[str, Any])
async def escalate_violation(
    violation_id: UUID,
    escalation_level: EscalationLevel,
    reason: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Manually escalate a violation.

    Args:
        violation_id: Violation ID
        escalation_level: Target escalation level
        reason: Reason for escalation
        db: Database session
        current_user: Current authenticated user

    Returns:
        Escalation result
    """
    try:
        # Get violation
        result = await db.execute(
            select(ConstitutionalViolation).where(ConstitutionalViolation.id == violation_id)
        )
        violation = result.scalar_one_or_none()

        if not violation:
            raise HTTPException(status_code=404, detail="Violation not found")

        # Perform escalation
        escalation_result = await violation_escalation_service.escalate_violation(
            violation, escalation_level, reason, current_user, db
        )

        if escalation_result.escalated:
            # Log audit event
            await violation_audit_service.log_violation_event(
                AuditEventType.VIOLATION_ESCALATED,
                violation,
                current_user,
                additional_data={
                    "escalation_level": escalation_level.value,
                    "reason": reason,
                    "escalation_id": escalation_result.escalation_id
                },
                db=db
            )

            # Broadcast escalation notification
            await monitoring_manager.broadcast_escalation_notification(
                escalation_result, str(violation_id)
            )

        return {
            "escalation_result": {
                "escalation_id": escalation_result.escalation_id,
                "escalated": escalation_result.escalated,
                "escalation_level": escalation_result.escalation_level.value,
                "assigned_to": escalation_result.assigned_to,
                "notification_sent": escalation_result.notification_sent,
                "response_time_target": escalation_result.response_time_target,
                "error_message": escalation_result.error_message
            },
            "escalated_by": current_user.username,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error escalating violation {violation_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to escalate violation: {str(e)}")


@router.put("/violations/{violation_id}/resolve", response_model=Dict[str, Any])
async def resolve_violation(
    violation_id: UUID,
    resolution_description: str,
    resolution_status: str = "manual_resolved",
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Resolve a violation.

    Args:
        violation_id: Violation ID
        resolution_description: Description of resolution
        resolution_status: Resolution status
        db: Database session
        current_user: Current authenticated user

    Returns:
        Resolution confirmation
    """
    try:
        # Get violation
        result = await db.execute(
            select(ConstitutionalViolation).where(ConstitutionalViolation.id == violation_id)
        )
        violation = result.scalar_one_or_none()

        if not violation:
            raise HTTPException(status_code=404, detail="Violation not found")

        # Update violation
        violation.status = "resolved"
        violation.resolution_status = resolution_status
        violation.resolution_description = resolution_description
        violation.resolved_at = datetime.now(timezone.utc)
        violation.resolved_by = current_user.id

        await db.commit()

        # Log audit event
        await violation_audit_service.log_violation_event(
            AuditEventType.VIOLATION_RESOLVED,
            violation,
            current_user,
            additional_data={
                "resolution_status": resolution_status,
                "resolution_description": resolution_description
            },
            db=db
        )

        return {
            "resolved": True,
            "violation_id": str(violation_id),
            "resolution_status": resolution_status,
            "resolution_description": resolution_description,
            "resolved_by": current_user.username,
            "resolved_at": violation.resolved_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving violation {violation_id}: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to resolve violation: {str(e)}")


@router.get("/analytics", response_model=Dict[str, Any])
async def get_violation_analytics(
    period: AnalyticsPeriod = Query(AnalyticsPeriod.DAY),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get violation analytics for specified period.

    Args:
        period: Analytics period
        start_time: Start time (optional)
        end_time: End time (optional)
        db: Database session
        current_user: Current authenticated user

    Returns:
        Violation analytics data
    """
    try:
        analytics = await violation_audit_service.generate_analytics(
            period, start_time, end_time, db
        )

        return {
            "analytics": {
                "period": analytics.period.value,
                "start_time": analytics.start_time.isoformat(),
                "end_time": analytics.end_time.isoformat(),
                "total_violations": analytics.total_violations,
                "violations_by_type": analytics.violations_by_type,
                "violations_by_severity": analytics.violations_by_severity,
                "escalations_count": analytics.escalations_count,
                "resolution_rate": analytics.resolution_rate,
                "average_resolution_time_minutes": analytics.average_resolution_time_minutes,
                "top_violation_sources": analytics.top_violation_sources,
                "trend_analysis": analytics.trend_analysis
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generated_by": current_user.username
        }

    except Exception as e:
        logger.error(f"Error getting violation analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


@router.get("/compliance-report", response_model=Dict[str, Any])
async def get_compliance_report(
    start_time: datetime = Query(...),
    end_time: datetime = Query(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate compliance report for specified period.

    Args:
        start_time: Report start time
        end_time: Report end time
        db: Database session
        current_user: Current authenticated user

    Returns:
        Compliance report
    """
    try:
        report = await violation_audit_service.generate_compliance_report(
            start_time, end_time, db
        )

        return {
            "compliance_report": {
                "report_id": report.report_id,
                "generated_at": report.generated_at.isoformat(),
                "period_start": report.period_start.isoformat(),
                "period_end": report.period_end.isoformat(),
                "total_violations": report.total_violations,
                "critical_violations": report.critical_violations,
                "unresolved_violations": report.unresolved_violations,
                "compliance_score": report.compliance_score,
                "policy_adherence_rate": report.policy_adherence_rate,
                "escalation_effectiveness": report.escalation_effectiveness,
                "recommendations": report.recommendations,
                "detailed_metrics": report.detailed_metrics
            },
            "generated_by": current_user.username
        }

    except Exception as e:
        logger.error(f"Error generating compliance report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.get("/thresholds", response_model=Dict[str, Any])
async def get_violation_thresholds(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all violation thresholds.

    Args:
        db: Database session
        current_user: Current authenticated user

    Returns:
        All configured violation thresholds
    """
    try:
        config_manager = get_violation_config_manager()
        thresholds = await config_manager.get_all_threshold_configs(db)

        thresholds_data = {}
        for name, config in thresholds.items():
            thresholds_data[name] = {
                "name": config.name,
                "threshold_type": config.threshold_type.value,
                "green_threshold": config.green_threshold,
                "amber_threshold": config.amber_threshold,
                "red_threshold": config.red_threshold,
                "enabled": config.enabled,
                "description": config.description,
                "configuration": config.configuration,
                "source": config.source.value
            }

        return {
            "thresholds": thresholds_data,
            "retrieved_at": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting violation thresholds: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get thresholds: {str(e)}")


@router.put("/thresholds/{threshold_name}", response_model=Dict[str, Any])
async def update_violation_threshold(
    threshold_name: str,
    threshold_config: Dict[str, Any],
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update violation threshold configuration.

    Args:
        threshold_name: Name of threshold to update
        threshold_config: New threshold configuration
        db: Database session
        current_user: Current authenticated user

    Returns:
        Update confirmation
    """
    try:
        # Validate user permissions (admin or policy_manager)
        if current_user.role not in ["admin", "policy_manager"]:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to update thresholds"
            )

        config_manager = get_violation_config_manager()

        # Create ThresholdConfig object
        from app.core.violation_config import ThresholdConfig, ThresholdType

        config = ThresholdConfig(
            name=threshold_name,
            threshold_type=ThresholdType(threshold_config["threshold_type"]),
            green_threshold=float(threshold_config["green_threshold"]),
            amber_threshold=float(threshold_config["amber_threshold"]),
            red_threshold=float(threshold_config["red_threshold"]),
            enabled=threshold_config.get("enabled", True),
            description=threshold_config.get("description", ""),
            configuration=threshold_config.get("configuration", {})
        )

        # Update threshold
        success = await config_manager.update_threshold_config(
            threshold_name, config, current_user, db
        )

        if not success:
            raise HTTPException(status_code=400, detail="Failed to update threshold")

        return {
            "updated": True,
            "threshold_name": threshold_name,
            "updated_by": current_user.username,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating threshold {threshold_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update threshold: {str(e)}")
