from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession # Changed
from typing import List, Optional
from datetime import datetime

from app import crud, models, schemas # Fixed import
from shared.database import get_async_db # Corrected import for async db session
from app.core.auth import require_internal_service, require_auditor, User # Fixed import

router = APIRouter()

@router.post("/", response_model=schemas.AuditLog, status_code=status.HTTP_201_CREATED)
async def create_audit_log_endpoint( # Changed to async def
    log_entry: schemas.AuditLogCreate,
    db: AsyncSession = Depends(get_async_db), # Changed to AsyncSession and get_async_db
    current_user: User = Depends(require_internal_service) 
):
    created_log = await crud.create_audit_log(db=db, log_entry=log_entry) # Added await
    return created_log

@router.get("/", response_model=schemas.AuditLogList)
async def list_audit_logs_endpoint( # Changed to async def
    skip: int = 0,
    limit: int = Query(default=100, lte=1000),
    service_name: Optional[str] = Query(None, description="Filter by service name"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    start_time: Optional[datetime] = Query(None, description="Filter logs after this timestamp (ISO format)"),
    end_time: Optional[datetime] = Query(None, description="Filter logs before this timestamp (ISO format)"),
    db: AsyncSession = Depends(get_async_db), # Changed to AsyncSession and get_async_db
    current_user: User = Depends(require_auditor)
):
    logs = await crud.get_audit_logs( # Added await
        db, 
        skip=skip, 
        limit=limit, 
        service_name=service_name, 
        user_id=user_id, 
        action=action,
        start_time=start_time,
        end_time=end_time
    )
    total_count = await crud.count_audit_logs( # Added await
        db,
        service_name=service_name,
        user_id=user_id,
        action=action,
        start_time=start_time,
        end_time=end_time
    )
    return {"logs": logs, "total": total_count}

@router.get("/{log_id}", response_model=schemas.AuditLog)
async def get_audit_log_endpoint( # Changed to async def
    log_id: int,
    db: AsyncSession = Depends(get_async_db), # Changed to AsyncSession and get_async_db
    current_user: User = Depends(require_auditor)
):
    db_log = await crud.get_audit_log(db, log_id=log_id) # Added await
    if db_log is None:
        raise HTTPException(status_code=404, detail="Audit Log not found")
    return db_log
