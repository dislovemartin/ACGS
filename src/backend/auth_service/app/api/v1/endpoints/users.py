from typing import Any, List

from app.api.v1 import deps
from app.crud import crud_user
from fastapi import APIRouter, Depends, HTTPException
from shared.models import user as user_model
from shared.schemas import user as user_schema
from shared.schemas.user import UserCreate
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/", response_model=List[user_schema.User])
async def read_users(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: user_model.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve users.
    Requires active user. Superuser check also re-enabled.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    users = await crud_user.get_users(db, skip=skip, limit=limit)
    return users


@router.post("/", response_model=user_schema.User)
async def create_user(
    *,
    db: AsyncSession = Depends(deps.get_db),
    user_in: UserCreate,
    current_user: user_model.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Create new user. Requires active superuser.
    """
    user = await crud_user.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )

    new_user = await crud_user.create_user(db=db, obj_in=user_in)
    return new_user
