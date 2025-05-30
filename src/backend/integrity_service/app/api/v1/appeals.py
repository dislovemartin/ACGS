"""
Phase 3: Appeal and Dispute Resolution API endpoints for ACGS-PGP
Provides democratic governance mechanisms for challenging algorithmic decisions
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from shared.database import get_async_db
from app.core.auth import get_current_user_placeholder as get_current_user, require_integrity_admin, require_auditor
from app import schemas, crud
from app.core.explainability import explainability_engine

router = APIRouter()

# --- Appeal Management Endpoints ---

@router.post("/appeals", response_model=schemas.Appeal, status_code=status.HTTP_201_CREATED)
async def create_appeal(
    appeal_data: schemas.AppealCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user = Depends(get_current_user)
):
    """
    Create a new appeal for a policy decision.
    Available to all authenticated users.
    """
    try:
        # Create appeal with current user as appellant
        appeal = await crud.create_appeal(db, appeal_data, current_user.id)
        
        # Log the appeal creation
        await crud.create_audit_log(db, schemas.AuditLogCreate(
            service_name="integrity_service",
            user_id=current_user.id,
            action="appeal_created",
            details={
                "appeal_id": appeal.id,
                "decision_id": appeal.decision_id,
                "escalation_level": appeal.escalation_level
            }
        ))
        
        return appeal
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating appeal: {str(e)}")


@router.get("/appeals", response_model=schemas.AppealList, status_code=status.HTTP_200_OK)
async def get_appeals(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[str] = Query(None, alias="status"),
    decision_id: Optional[str] = Query(None),
    escalation_level: Optional[int] = Query(None, ge=1, le=4),
    db: AsyncSession = Depends(get_async_db),
    current_user = Depends(get_current_user)
):
    """
    Get appeals with optional filtering.
    Regular users see only their appeals, admins see all.
    """
    try:
        # Determine access level
        assigned_reviewer_id = None
        if "integrity_admin" not in current_user.roles and "auditor" not in current_user.roles:
            # Regular users see only their appeals
            assigned_reviewer_id = current_user.id
        
        appeals = await crud.get_appeals(
            db=db,
            skip=skip,
            limit=limit,
            status=status_filter,
            decision_id=decision_id,
            escalation_level=escalation_level,
            assigned_reviewer_id=assigned_reviewer_id
        )
        
        total = await crud.count_appeals(
            db=db,
            status=status_filter,
            decision_id=decision_id,
            escalation_level=escalation_level
        )
        
        return schemas.AppealList(appeals=appeals, total=total)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving appeals: {str(e)}")


@router.get("/appeals/{appeal_id}", response_model=schemas.Appeal, status_code=status.HTTP_200_OK)
async def get_appeal(
    appeal_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user = Depends(get_current_user)
):
    """
    Get a specific appeal by ID.
    """
    try:
        appeal = await crud.get_appeal(db, appeal_id)
        if not appeal:
            raise HTTPException(status_code=404, detail="Appeal not found")
        
        # Check access permissions
        if ("integrity_admin" not in current_user.roles and 
            "auditor" not in current_user.roles and 
            appeal.assigned_reviewer_id != current_user.id):
            raise HTTPException(status_code=403, detail="Access denied to this appeal")
        
        return appeal
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving appeal: {str(e)}")


@router.patch("/appeals/{appeal_id}", response_model=schemas.Appeal, status_code=status.HTTP_200_OK)
async def update_appeal(
    appeal_id: int,
    appeal_update: schemas.AppealUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user = Depends(require_auditor)
):
    """
    Update an appeal (admin/auditor only).
    """
    try:
        appeal = await crud.update_appeal(db, appeal_id, appeal_update)
        if not appeal:
            raise HTTPException(status_code=404, detail="Appeal not found")
        
        # Log the update
        await crud.create_audit_log(db, schemas.AuditLogCreate(
            service_name="integrity_service",
            user_id=current_user.id,
            action="appeal_updated",
            details={
                "appeal_id": appeal_id,
                "updates": appeal_update.model_dump(exclude_unset=True)
            }
        ))
        
        return appeal
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating appeal: {str(e)}")


@router.post("/appeals/{appeal_id}/escalate", response_model=schemas.Appeal, status_code=status.HTTP_200_OK)
async def escalate_appeal(
    appeal_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user = Depends(require_auditor)
):
    """
    Escalate an appeal to the next level (admin/auditor only).
    """
    try:
        appeal = await crud.escalate_appeal(db, appeal_id)
        if not appeal:
            raise HTTPException(status_code=404, detail="Appeal not found or cannot be escalated")
        
        # Log the escalation
        await crud.create_audit_log(db, schemas.AuditLogCreate(
            service_name="integrity_service",
            user_id=current_user.id,
            action="appeal_escalated",
            details={
                "appeal_id": appeal_id,
                "new_escalation_level": appeal.escalation_level
            }
        ))
        
        return appeal
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error escalating appeal: {str(e)}")


# --- Dispute Resolution Endpoints ---

@router.post("/dispute-resolutions", response_model=schemas.DisputeResolution, status_code=status.HTTP_201_CREATED)
async def create_dispute_resolution(
    dispute_data: schemas.DisputeResolutionCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user = Depends(require_auditor)
):
    """
    Create a new dispute resolution process (admin/auditor only).
    """
    try:
        # Verify the appeal exists
        appeal = await crud.get_appeal(db, dispute_data.appeal_id)
        if not appeal:
            raise HTTPException(status_code=404, detail="Appeal not found")
        
        dispute = await crud.create_dispute_resolution(db, dispute_data)
        
        # Log the dispute resolution creation
        await crud.create_audit_log(db, schemas.AuditLogCreate(
            service_name="integrity_service",
            user_id=current_user.id,
            action="dispute_resolution_created",
            details={
                "dispute_id": dispute.id,
                "appeal_id": dispute.appeal_id,
                "resolution_method": dispute.resolution_method
            }
        ))
        
        return dispute
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating dispute resolution: {str(e)}")


@router.get("/dispute-resolutions", response_model=schemas.DisputeResolutionList, status_code=status.HTTP_200_OK)
async def get_dispute_resolutions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[str] = Query(None, alias="status"),
    resolution_method: Optional[str] = Query(None),
    appeal_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_async_db),
    current_user = Depends(require_auditor)
):
    """
    Get dispute resolutions with optional filtering (admin/auditor only).
    """
    try:
        resolutions = await crud.get_dispute_resolutions(
            db=db,
            skip=skip,
            limit=limit,
            status=status_filter,
            resolution_method=resolution_method,
            appeal_id=appeal_id
        )
        
        total = await crud.count_dispute_resolutions(
            db=db,
            status=status_filter,
            resolution_method=resolution_method,
            appeal_id=appeal_id
        )
        
        return schemas.DisputeResolutionList(resolutions=resolutions, total=total)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving dispute resolutions: {str(e)}")


@router.get("/dispute-resolutions/{dispute_id}", response_model=schemas.DisputeResolution, status_code=status.HTTP_200_OK)
async def get_dispute_resolution(
    dispute_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user = Depends(require_auditor)
):
    """
    Get a specific dispute resolution by ID (admin/auditor only).
    """
    try:
        dispute = await crud.get_dispute_resolution(db, dispute_id)
        if not dispute:
            raise HTTPException(status_code=404, detail="Dispute resolution not found")
        
        return dispute
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving dispute resolution: {str(e)}")


@router.patch("/dispute-resolutions/{dispute_id}", response_model=schemas.DisputeResolution, status_code=status.HTTP_200_OK)
async def update_dispute_resolution(
    dispute_id: int,
    dispute_update: schemas.DisputeResolutionUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user = Depends(require_auditor)
):
    """
    Update a dispute resolution (admin/auditor only).
    """
    try:
        dispute = await crud.update_dispute_resolution(db, dispute_id, dispute_update)
        if not dispute:
            raise HTTPException(status_code=404, detail="Dispute resolution not found")
        
        # Log the update
        await crud.create_audit_log(db, schemas.AuditLogCreate(
            service_name="integrity_service",
            user_id=current_user.id,
            action="dispute_resolution_updated",
            details={
                "dispute_id": dispute_id,
                "updates": dispute_update.model_dump(exclude_unset=True)
            }
        ))
        
        return dispute
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating dispute resolution: {str(e)}")


# --- Explainability Endpoints ---

@router.post("/explain", response_model=schemas.ExplainabilityResponse, status_code=status.HTTP_200_OK)
async def explain_decision(
    request_data: schemas.ExplainabilityRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user = Depends(get_current_user)
):
    """
    Generate explanation for a policy decision.
    Available to all authenticated users.
    """
    try:
        explanation = await explainability_engine.generate_explanation(request_data, db)
        
        # Log the explanation request
        await crud.create_audit_log(db, schemas.AuditLogCreate(
            service_name="integrity_service",
            user_id=current_user.id,
            action="explanation_requested",
            details={
                "decision_id": request_data.decision_id,
                "explanation_level": request_data.explanation_level,
                "target_audience": request_data.target_audience
            }
        ))
        
        return explanation
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating explanation: {str(e)}")


@router.get("/provenance/{rule_id}", response_model=schemas.RuleProvenanceResponse, status_code=status.HTTP_200_OK)
async def get_rule_provenance(
    rule_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user = Depends(get_current_user)
):
    """
    Get detailed provenance information for a specific rule.
    Available to all authenticated users.
    """
    try:
        provenance = await explainability_engine.get_rule_provenance(rule_id, db)
        
        # Log the provenance request
        await crud.create_audit_log(db, schemas.AuditLogCreate(
            service_name="integrity_service",
            user_id=current_user.id,
            action="rule_provenance_requested",
            details={"rule_id": rule_id}
        ))
        
        return provenance
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving rule provenance: {str(e)}")
