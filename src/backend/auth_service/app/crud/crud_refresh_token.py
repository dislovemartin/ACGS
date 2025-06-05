# acgspcp-main/auth_service/app/crud/crud_refresh_token.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from shared.models import RefreshToken # Ensure shared.models has RefreshToken
from datetime import datetime, timezone
from typing import Optional

async def create_refresh_token(db: AsyncSession, user_id: int, token: str, jti: str, expires_at: datetime) -> RefreshToken:
    db_refresh_token = RefreshToken(
        user_id=user_id,
        token=token,
        jti=jti,
        expires_at=expires_at,
        created_at=datetime.now(timezone.utc),
        is_revoked=False
    )
    db.add(db_refresh_token)
    await db.commit()
    await db.refresh(db_refresh_token)
    return db_refresh_token

async def get_refresh_token_by_jti(db: AsyncSession, jti: str) -> Optional[RefreshToken]:
    result = await db.execute(select(RefreshToken).filter(RefreshToken.jti == jti))
    return result.scalars().first()

async def is_valid_refresh_token(db: AsyncSession, user_id: int, jti: str) -> bool:
    token = await get_refresh_token_by_jti(db, jti)
    if not token:
        return False
    if token.user_id != user_id:
        return False
    if token.is_revoked:
        return False
    # Ensure both datetimes are timezone-aware for comparison
    expires_at = token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        return False
    return True

async def revoke_refresh_token(db: AsyncSession, jti: str, user_id: Optional[int] = None):
    stmt = update(RefreshToken).where(RefreshToken.jti == jti)
    if user_id is not None:
        stmt = stmt.where(RefreshToken.user_id == user_id)
    stmt = stmt.values(is_revoked=True)
    await db.execute(stmt)
    await db.commit()

async def revoke_all_refresh_tokens_for_user(db: AsyncSession, user_id: int):
    stmt = update(RefreshToken).where(RefreshToken.user_id == user_id).values(is_revoked=True)
    await db.execute(stmt)
    await db.commit()

# Alias for backward compatibility with backend endpoints
async def create_user_refresh_token(db: AsyncSession, user_id: int, token: str, jti: str, expires_at: datetime) -> RefreshToken:
    """Alias for create_refresh_token to maintain backward compatibility."""
    return await create_refresh_token(db, user_id, token, jti, expires_at)

async def revoke_refresh_token_by_jti(db: AsyncSession, jti: str):
    """Revoke a refresh token by its JTI."""
    stmt = update(RefreshToken).where(RefreshToken.jti == jti).values(is_revoked=True)
    await db.execute(stmt)
    await db.commit()

async def get_active_refresh_token_by_jti(db: AsyncSession, jti: str) -> Optional[RefreshToken]:
    """Get an active (non-revoked) refresh token by its JTI."""
    result = await db.execute(
        select(RefreshToken).filter(
            RefreshToken.jti == jti,
            RefreshToken.is_revoked == False
        )
    )
    return result.scalars().first()
