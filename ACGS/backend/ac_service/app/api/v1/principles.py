# ACGS/backend/ac_service/app/api/v1/principles.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

# Adjust relative imports to point to service's app level, then shared
try:
    from ....app import crud  # From backend.ac_service.app.crud
    from ....app import schemas as local_schemas # From backend.ac_service.app.schemas (contains placeholder User)
    from ....app.core import auth as service_auth # From backend.ac_service.app.core.auth
    from shared.database import get_async_db
    # Principle schemas are directly used from shared.schemas in this endpoint file for clarity
    from shared.schemas import PrincipleCreate, PrincipleUpdate, PrincipleResponse, PrincipleListResponse
except ImportError:
    # Fallback for local dev - ensure ACGS root is in PYTHONPATH
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))) # To ACGS root
    from backend.ac_service.app import crud
    from backend.ac_service.app import schemas as local_schemas
    from backend.ac_service.app.core import auth as service_auth
    from shared.database import get_async_db
    from shared.schemas import PrincipleCreate, PrincipleUpdate, PrincipleResponse, PrincipleListResponse


router = APIRouter()

@router.post("/", response_model=PrincipleResponse, status_code=status.HTTP_201_CREATED)
async def create_principle_endpoint(
    principle: PrincipleCreate, # Uses shared.schemas.PrincipleCreate
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[local_schemas.User] = Depends(service_auth.require_admin_role) # Uses local_schemas.User
):
    user_id_to_pass = current_user.id if current_user else None

    db_principle_by_name = await crud.get_principle_by_name(db, name=principle.name)
    if db_principle_by_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Principle with name '{principle.name}' already exists.")
    
    created_principle = await crud.create_principle(db=db, principle=principle, user_id=user_id_to_pass)
    return created_principle # Automatically mapped to shared.schemas.PrincipleResponse

@router.get("/", response_model=PrincipleListResponse) # Uses shared.schemas.PrincipleListResponse
async def list_principles_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_async_db)
    # current_user: Optional[local_schemas.User] = Depends(service_auth.get_current_active_user_placeholder) # Publicly readable for now
):
    principles = await crud.get_principles(db, skip=skip, limit=limit)
    total_count = await crud.count_principles(db)
    # Ensure the response is wrapped in PrincipleListResponse
    return PrincipleListResponse(principles=[PrincipleResponse.model_validate(p) for p in principles], total=total_count)


@router.get("/{principle_id}", response_model=PrincipleResponse) # Uses shared.schemas.PrincipleResponse
async def get_principle_endpoint(
    principle_id: int,
    db: AsyncSession = Depends(get_async_db)
    # current_user: Optional[local_schemas.User] = Depends(service_auth.get_current_active_user_placeholder)
):
    db_principle = await crud.get_principle(db, principle_id=principle_id)
    if db_principle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Principle not found")
    return db_principle

@router.put("/{principle_id}", response_model=PrincipleResponse) # Uses shared.schemas.PrincipleResponse
async def update_principle_endpoint(
    principle_id: int,
    principle_update: PrincipleUpdate, # Uses shared.schemas.PrincipleUpdate
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[local_schemas.User] = Depends(service_auth.require_admin_role)
):
    db_principle = await crud.get_principle(db, principle_id=principle_id)
    if db_principle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Principle not found")
    
    if principle_update.name and principle_update.name != db_principle.name:
        existing_principle_with_new_name = await crud.get_principle_by_name(db, name=principle_update.name)
        if existing_principle_with_new_name and existing_principle_with_new_name.id != principle_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Principle name '{principle_update.name}' already in use by another principle.")

    updated_principle = await crud.update_principle(db=db, principle_id=principle_id, principle_update=principle_update)
    # crud.update_principle should return the updated model instance or None
    if updated_principle is None: 
        # This condition might be redundant if get_principle check already passed and update logic is sound
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Principle not found after update attempt or update failed")
    return updated_principle

@router.delete("/{principle_id}", response_model=PrincipleResponse) # Uses shared.schemas.PrincipleResponse
async def delete_principle_endpoint(
    principle_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[local_schemas.User] = Depends(service_auth.require_admin_role)
):
    deleted_principle = await crud.delete_principle(db, principle_id=principle_id)
    if deleted_principle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Principle not found or already deleted")
    return deleted_principle
