"""
Database configuration for Research Infrastructure Service
"""

import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    poolclass=NullPool,  # Use NullPool for async
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_database():
    """Initialize database tables."""
    try:
        from ..models.experiment import Base as ExperimentBase
        from ..models.research_data import Base as ResearchDataBase
        
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(ExperimentBase.metadata.create_all)
            await conn.run_sync(ResearchDataBase.metadata.create_all)
        
        logger.info("Database tables created successfully")
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


async def close_database():
    """Close database connections."""
    try:
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")
        raise
