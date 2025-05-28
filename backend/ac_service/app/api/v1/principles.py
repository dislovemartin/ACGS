from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession # Changed
from typing import List, Optional

from app import crud, models, schemas # Import from app directory
from shared.database import get_async_db # Corrected import for async db session
from app.core.auth import get_current_active_user_placeholder, require_admin_role, User # Import from app directory

router = APIRouter()

@router.post("/", response_model=schemas.Principle, status_code=status.HTTP_201_CREATED)
async def create_principle_endpoint( # Changed to async def
    principle: schemas.PrincipleCreate, 
    db: AsyncSession = Depends(get_async_db), # Changed to AsyncSession and get_async_db
    current_user: Optional[User] = Depends(require_admin_role)
):
    user_id = current_user.id if current_user else None
    
    db_principle_by_name = await crud.get_principle_by_name(db, name=principle.name) # Added await
    if db_principle_by_name:
        raise HTTPException(status_code=400, detail=f"Principle with name '{principle.name}' already exists.")
    
    created_principle = await crud.create_principle(db=db, principle=principle, user_id=user_id) # Added await
    return created_principle

@router.get("/", response_model=schemas.PrincipleList)
async def list_principles_endpoint( # Changed to async def
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_async_db) # Changed to AsyncSession and get_async_db
):
    principles = await crud.get_principles(db, skip=skip, limit=limit) # Added await
    total_count = await crud.count_principles(db) # Added await
    return {"principles": principles, "total": total_count}

@router.get("/{principle_id}", response_model=schemas.Principle)
async def get_principle_endpoint( # Changed to async def
    principle_id: int, 
    db: AsyncSession = Depends(get_async_db) # Changed to AsyncSession and get_async_db
):
    db_principle = await crud.get_principle(db, principle_id=principle_id) # Added await
    if db_principle is None:
        raise HTTPException(status_code=404, detail="Principle not found")
    return db_principle

@router.put("/{principle_id}", response_model=schemas.Principle)
async def update_principle_endpoint( # Changed to async def
    principle_id: int, 
    principle_update: schemas.PrincipleUpdate, 
    db: AsyncSession = Depends(get_async_db), # Changed to AsyncSession and get_async_db
    current_user: User = Depends(require_admin_role)
):
    db_principle = await crud.get_principle(db, principle_id=principle_id) # Added await
    if db_principle is None:
        raise HTTPException(status_code=404, detail="Principle not found")
    
    if principle_update.name and principle_update.name != db_principle.name:
        existing_principle_with_new_name = await crud.get_principle_by_name(db, name=principle_update.name) # Added await
        if existing_principle_with_new_name and existing_principle_with_new_name.id != principle_id:
            raise HTTPException(status_code=400, detail=f"Principle name '{principle_update.name}' already in use by another principle.")

    updated_principle = await crud.update_principle(db=db, principle_id=principle_id, principle_update=principle_update) # Added await
    if updated_principle is None:
        raise HTTPException(status_code=404, detail="Principle not found after update attempt")
    return updated_principle

@router.delete("/{principle_id}", response_model=schemas.Principle)
async def delete_principle_endpoint( # Changed to async def
    principle_id: int,
    db: AsyncSession = Depends(get_async_db), # Changed to AsyncSession and get_async_db
    current_user: User = Depends(require_admin_role)
):
    db_principle = await crud.delete_principle(db, principle_id=principle_id) # Added await
    if db_principle is None:
        raise HTTPException(status_code=404, detail="Principle not found or already deleted")
    return db_principle

# Enhanced Phase 1 Constitutional Principle Endpoints

@router.get("/category/{category}", response_model=schemas.PrincipleList)
async def get_principles_by_category_endpoint(
    category: str,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db)
):
    """Get principles filtered by category."""
    principles = await crud.get_principles_by_category(db, category=category, skip=skip, limit=limit)
    total_count = await crud.count_principles(db)  # Could be optimized to count only by category
    return {"principles": principles, "total": total_count}

@router.get("/scope/{scope_context}", response_model=schemas.PrincipleList)
async def get_principles_by_scope_endpoint(
    scope_context: str,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db)
):
    """Get principles that apply to a specific scope context."""
    principles = await crud.get_principles_by_scope(db, scope_context=scope_context, skip=skip, limit=limit)
    total_count = await crud.count_principles(db)
    return {"principles": principles, "total": total_count}

@router.get("/priority-range", response_model=schemas.PrincipleList)
async def get_principles_by_priority_range_endpoint(
    min_priority: float = 0.0,
    max_priority: float = 1.0,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db)
):
    """Get principles within a specific priority weight range."""
    if min_priority < 0.0 or max_priority > 1.0 or min_priority > max_priority:
        raise HTTPException(status_code=400, detail="Invalid priority range. Must be between 0.0 and 1.0, with min <= max")

    principles = await crud.get_principles_by_priority_range(
        db, min_priority=min_priority, max_priority=max_priority, skip=skip, limit=limit
    )
    total_count = await crud.count_principles(db)
    return {"principles": principles, "total": total_count}

@router.post("/search/keywords", response_model=schemas.PrincipleList)
async def search_principles_by_keywords_endpoint(
    keywords: List[str],
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db)
):
    """Search principles by keywords."""
    if not keywords:
        raise HTTPException(status_code=400, detail="At least one keyword must be provided")

    principles = await crud.search_principles_by_keywords(db, keywords=keywords, skip=skip, limit=limit)
    total_count = await crud.count_principles(db)
    return {"principles": principles, "total": total_count}

@router.get("/active/context/{context}", response_model=schemas.PrincipleList)
async def get_active_principles_for_context_endpoint(
    context: str,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db)
):
    """Get active principles applicable to a specific context, optionally filtered by category."""
    principles = await crud.get_active_principles_for_context(db, context=context, category=category)
    return {"principles": principles, "total": len(principles)}
