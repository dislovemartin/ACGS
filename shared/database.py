# backend/shared/database.py
import os

# SQLAlchemy async imports
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Use a single DATABASE_URL environment variable with the async driver
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://user:password@localhost:5432/acgs_pgp_db",
)


# Create async engine
async_engine = create_async_engine(DATABASE_URL, echo=True)

# Create async session local
AsyncSessionLocal = sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()
metadata = Base.metadata # Expose metadata directly


# Async dependency to get DB session
async def get_async_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            pass
