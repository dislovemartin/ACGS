"""
Local database configuration for integrity service to avoid shared module dependencies
"""
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Local database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://acgs_user:acgs_password@localhost:5434/acgs_db")
async_engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

async def get_async_db():
    """Local implementation of async database session dependency"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
