from typing import Optional

from app.core.config import settings
from app.db.base_class import Base  # Import Base for metadata
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Determine which database URL to use
db_url_to_use: Optional[str] = settings.SQLALCHEMY_DATABASE_URI

# Create an async engine instance
# SQLALCHEMY_DATABASE_URI will point to test DB if TEST_ASYNC_DATABASE_URL is set.
async_engine = create_async_engine(
    db_url_to_use if db_url_to_use else "",  # Handle None for create_async_engine
    echo=getattr(settings, "DB_ECHO_LOG", False),  # Safely access DB_ECHO_LOG
    pool_pre_ping=True,
)

# Create an async session factory
AsyncSessionFactory = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_db():
    """Initializes the database. If using SQLite, creates all tables."""
    if db_url_to_use and "sqlite" in str(db_url_to_use):
        async with async_engine.begin() as conn:
            # For SQLite, metadata.create_all() is sync; run_sync is needed.
            await conn.run_sync(Base.metadata.create_all)


async def get_async_db() -> AsyncSession:
    """FastAPI dependency that provides an async database session."""
    # Initialize DB (creates tables if SQLite and they don't exist).
    # Simplified for testing; in prod, this is usually done at app/suite start.
    if db_url_to_use and "sqlite" in str(db_url_to_use):
        await init_db()

    async with AsyncSessionFactory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Alembic async migrations might need a sync engine or async-supporting libs.
# Focusing on async session for the app for now.
