from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession # Changed
from typing import List, Optional

from .. import crud, models, schemas # Adjusted relative import
from shared.database import get_async_db # Corrected import for async db session
from ..core.auth import require_internal_service, require_integrity_admin, User # Adjusted relative import

router = APIRouter()

@router.post("/", response_model=schemas.PolicyRule, status_code=status.HTTP_201_CREATED)
async def create_policy_rule_endpoint( # Changed to async def
    policy_rule: schemas.PolicyRuleCreate,
    db: AsyncSession = Depends(get_async_db), # Changed to AsyncSession and get_async_db
    current_user: User = Depends(require_internal_service)
):
    created_rule = await crud.create_policy_rule(db=db, policy_rule=policy_rule) # Added await
    return created_rule

@router.get("/{rule_id}", response_model=schemas.PolicyRule)
async def get_policy_rule_endpoint( # Changed to async def
    rule_id: int,
    db: AsyncSession = Depends(get_async_db), # Changed to AsyncSession and get_async_db
    current_user: User = Depends(require_internal_service)
):
    db_rule = await crud.get_policy_rule(db, rule_id=rule_id) # Added await
    if db_rule is None:
        raise HTTPException(status_code=404, detail="Policy Rule not found")
    return db_rule

@router.get("/", response_model=schemas.PolicyRuleList)
async def list_policy_rules_endpoint( # Changed to async def
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db), # Changed to AsyncSession and get_async_db
    current_user: User = Depends(require_internal_service)
):
    if status:
        rules = await crud.get_policy_rules_by_status(db, status=status, skip=skip, limit=limit) # Added await
        total_count = await crud.count_policy_rules(db, status=status) # Added await
    else:
        rules = await crud.get_policy_rules(db, skip=skip, limit=limit) # Added await
        total_count = await crud.count_policy_rules(db) # Added await
    return {"rules": rules, "total": total_count}

@router.put("/{rule_id}/status", response_model=schemas.PolicyRule)
async def update_policy_rule_status_endpoint( # Changed to async def
    rule_id: int,
    status_update: schemas.PolicyRuleUpdate,
    db: AsyncSession = Depends(get_async_db), # Changed to AsyncSession and get_async_db
    current_user: User = Depends(require_internal_service)
):
    if not status_update.verification_status:
        raise HTTPException(status_code=400, detail="Verification status must be provided in the request body.")

    updated_rule = await crud.update_policy_rule_status( # Added await
        db=db, 
        rule_id=rule_id, 
        status=status_update.verification_status
    )
    if updated_rule is None:
        raise HTTPException(status_code=404, detail="Policy Rule not found")
    return updated_rule

@router.put("/{rule_id}", response_model=schemas.PolicyRule)
async def update_policy_rule_content_endpoint( # Changed to async def
    rule_id: int,
    rule_update: schemas.PolicyRuleUpdate,
    db: AsyncSession = Depends(get_async_db), # Changed to AsyncSession and get_async_db
    current_user: User = Depends(require_integrity_admin)
):
    updated_rule = await crud.update_policy_rule_content(db=db, rule_id=rule_id, rule_update=rule_update) # Added await
    if updated_rule is None:
        raise HTTPException(status_code=404, detail="Policy Rule not found or update failed")
    return updated_rule

@router.delete("/{rule_id}", response_model=schemas.PolicyRule)
async def delete_policy_rule_endpoint( # Changed to async def
    rule_id: int,
    db: AsyncSession = Depends(get_async_db), # Changed to AsyncSession and get_async_db
    current_user: User = Depends(require_integrity_admin)
):
    deleted_rule = await crud.delete_policy_rule(db, rule_id=rule_id) # Added await
    if deleted_rule is None:
        raise HTTPException(status_code=404, detail="Policy Rule not found")
    return deleted_rule
