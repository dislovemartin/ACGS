from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List, Optional

from . import models, schemas

# Principle CRUD operations

async def create_principle(db: AsyncSession, principle: schemas.PrincipleCreate, user_id: Optional[int] = None) -> models.Principle:
    db_principle = models.Principle(
        **principle.model_dump(),  # Use model_dump() for Pydantic v2+
        created_by_user_id=user_id,
        version=1, # Initial version
        status="draft" # Initial status
    )
    db.add(db_principle)
    await db.commit()
    await db.refresh(db_principle)
    return db_principle

async def get_principle(db: AsyncSession, principle_id: int) -> Optional[models.Principle]:
    result = await db.execute(select(models.Principle).filter(models.Principle.id == principle_id))
    return result.scalars().first()

async def get_principle_by_name(db: AsyncSession, name: str) -> Optional[models.Principle]:
    # This simple version gets the first principle with this name.
    # For versioning, you might want the latest version or a specific one.
    result = await db.execute(select(models.Principle).filter(models.Principle.name == name).order_by(models.Principle.version.desc()))
    return result.scalars().first()

async def get_principles(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[models.Principle]:
    result = await db.execute(select(models.Principle).offset(skip).limit(limit))
    return result.scalars().all()

async def update_principle(db: AsyncSession, principle_id: int, principle_update: schemas.PrincipleUpdate) -> Optional[models.Principle]:
    db_principle = await get_principle(db, principle_id)
    if db_principle:
        update_data = principle_update.model_dump(exclude_unset=True) # Pydantic v2+
        
        # Simple version increment if content changes, or could be more complex
        if "content" in update_data and update_data["content"] != db_principle.content:
            # Using models.Principle.version + 1 for potential ORM-level handling or complex scenarios,
            # though db_principle.version += 1 would often suffice for simple increments.
            db_principle.version = models.Principle.version + 1 
            # Optionally, reset status to 'draft' or handle as per business logic
            # db_principle.status = "draft"

        for key, value in update_data.items():
            setattr(db_principle, key, value)
        
        await db.commit()
        await db.refresh(db_principle)
    return db_principle

async def delete_principle(db: AsyncSession, principle_id: int) -> Optional[models.Principle]:
    db_principle = await get_principle(db, principle_id)
    if db_principle:
        # Instead of deleting, we can mark as "deprecated" or "deleted"
        # db_principle.status = "deleted" 
        # await db.commit()
        # await db.refresh(db_principle)
        # For actual deletion:
        await db.delete(db_principle)
        await db.commit()
    return db_principle

async def count_principles(db: AsyncSession) -> int:
    result = await db.execute(select(func.count()).select_from(models.Principle))
    return result.scalar_one()
