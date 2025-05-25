# ACGS/backend/ac_service/app/crud.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete # func is sqlalchemy.sql.func
from typing import List, Optional

# Models and Schemas from shared directory
try:
    from shared.models import Principle as PrincipleModel
    from shared.schemas import PrincipleCreate, PrincipleUpdate 
except ImportError:
    # Fallback for local dev
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
    from shared.models import Principle as PrincipleModel
    from shared.schemas import PrincipleCreate, PrincipleUpdate


async def create_principle(db: AsyncSession, principle: PrincipleCreate, user_id: Optional[int] = None) -> PrincipleModel:
    db_principle = PrincipleModel(
        **principle.model_dump(), # Use model_dump() for Pydantic v2
        created_by_user_id=user_id,
        version=1 # Initial version
        # status is defaulted in model or schema
    )
    db.add(db_principle)
    await db.commit()
    await db.refresh(db_principle)
    return db_principle

async def get_principle(db: AsyncSession, principle_id: int) -> Optional[PrincipleModel]:
    result = await db.execute(select(PrincipleModel).filter(PrincipleModel.id == principle_id))
    return result.scalars().first()

async def get_principle_by_name(db: AsyncSession, name: str) -> Optional[PrincipleModel]:
    result = await db.execute(select(PrincipleModel).filter(PrincipleModel.name == name))
    return result.scalars().first()

async def get_principles(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[PrincipleModel]:
    result = await db.execute(select(PrincipleModel).offset(skip).limit(limit).order_by(PrincipleModel.id))
    return result.scalars().all()

async def count_principles(db: AsyncSession) -> int:
    result = await db.execute(select(func.count(PrincipleModel.id))) # Pass column to count
    return result.scalar_one()

async def update_principle(
    db: AsyncSession,
    principle_id: int,
    principle_update: PrincipleUpdate
) -> Optional[PrincipleModel]:
    db_principle = await get_principle(db, principle_id)
    if not db_principle:
        return None

    update_data = principle_update.model_dump(exclude_unset=True)

    version_incremented = False
    if "content" in update_data and update_data["content"] != db_principle.content:
        db_principle.version = PrincipleModel.version + 1 # type: ignore
        version_incremented = True
        # Optionally reset status to 'draft' or similar if content changes significantly
        # db_principle.status = "draft"

    for key, value in update_data.items():
        setattr(db_principle, key, value)
    
    # updated_at is handled by SQLAlchemy onupdate in shared.models.Principle
    await db.commit()
    await db.refresh(db_principle)
    return db_principle

async def delete_principle(db: AsyncSession, principle_id: int) -> Optional[PrincipleModel]:
    db_principle = await get_principle(db, principle_id)
    if db_principle:
        await db.delete(db_principle)
        await db.commit()
        return db_principle
    return None
