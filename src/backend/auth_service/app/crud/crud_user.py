from typing import Any, Dict, List, Optional, Union

from app.core.password import get_password_hash, verify_password # Import from password module to avoid circular imports
from shared.models import User
from shared.schemas.user import UserCreate, UserUpdate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_user(db: AsyncSession, user_id: int) -> Optional[User]:
    """Retrieve a user by their ID."""
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalars().first()


async def get_user_by_username(db: AsyncSession, *, username: str) -> Optional[User]:
    """Retrieve a user by their username."""
    result = await db.execute(select(User).filter(User.username == username))
    return result.scalars().first()


async def get_user_by_email(db: AsyncSession, *, email: str) -> Optional[User]:
    """Retrieve a user by their email address."""
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()


async def get_users(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> List[
    User
]:
    """Retrieve a list of users with pagination."""
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()


async def create_user(db: AsyncSession, *, obj_in: UserCreate) -> User:
    """Create a new user in the database."""
    db_obj = User(
        email=obj_in.email,
        hashed_password=get_password_hash(obj_in.password),
        full_name=getattr(obj_in, 'full_name', None), # Handle optional fields
        username=obj_in.username,
        is_active=True  # New users active by default
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def update_user(
    db: AsyncSession, *, db_obj: User, obj_in: UserUpdate
) -> User:
    """Update an existing user's information."""
    update_data = obj_in.model_dump(exclude_unset=True) # Use model_dump for Pydantic V2

    if "password" in update_data and update_data["password"]:
        hashed_password = get_password_hash(update_data["password"])
        db_obj.hashed_password = hashed_password
        del update_data["password"]

    for field_name, value in update_data.items():
        if hasattr(db_obj, field_name):
            setattr(db_obj, field_name, value)

    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def delete_user(db: AsyncSession, *, user_id: int) -> Optional[User]:
    """Delete a user from the database by their ID."""
    db_obj = await db.get(User, user_id)
    if db_obj:
        await db.delete(db_obj)
        await db.commit()
    return db_obj
