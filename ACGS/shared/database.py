# ACGS/shared/database.py
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base # Updated import for declarative_base
from typing import AsyncGenerator

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/acgs_pgp_db")

async_engine = create_async_engine(DATABASE_URL, echo=False) # Set echo=True for SQL logging

AsyncSessionFactory = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False, # Good for FastAPI dependencies
    autocommit=False, # Should be False for sessionmaker
    autoflush=False,  # Should be False for sessionmaker
)

# Base for declarative models
Base = declarative_base()

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionFactory() as session:
        try:
            yield session
            # Removed await session.commit() - commit should be explicit in CRUD operations
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Function to create tables (optional, Alembic is preferred for migrations)
# This might be useful for initial setup or tests if Alembic isn't used.
async def create_db_and_tables():
    async with async_engine.begin() as conn:
        # Import all models here before calling create_all
        # This ensures they are registered with Base.metadata
        import shared.models # noqa
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created (if they didn't exist).")
