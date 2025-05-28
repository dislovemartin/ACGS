# ACGS/shared/database.py
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base # Updated import for declarative_base

# Use a single DATABASE_URL environment variable with the async driver
# Default value is for Docker Compose setup.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://acgs_user:acgs_password@postgres_db:5432/acgs_pgp_db",
)

# Create async engine
# echo=True can be noisy in production, consider making it configurable via ENV
DB_ECHO = os.getenv("DB_ECHO_LOG", "False").lower() == "true"
async_engine = create_async_engine(DATABASE_URL, echo=DB_ECHO, pool_pre_ping=True)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    bind=async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False, 
    autocommit=False, # Default for AsyncSession
    autoflush=False   # Default for AsyncSession
)

# Base for declarative models
Base = declarative_base()
metadata = Base.metadata # Expose metadata for Alembic and table creation

# Async dependency to get DB session for FastAPI
async def get_async_db() -> AsyncSession: # Changed to yield AsyncGenerator
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # Removed await session.commit() here.
            # Commits should be handled at the router/CRUD operation level
            # to allow for more control over transactions.
            # If an operation completes successfully, it commits. If it raises an error,
            # the calling code or an exception handler should ensure rollback.
        except Exception:
            await session.rollback() # Rollback on error within the session's scope
            raise
        # finally:
            # await session.close() # session is closed automatically by context manager

async def create_db_and_tables():
    """
    Creates all tables defined by models inheriting from Base.
    This is typically called once at application startup or by migrations.
    Alembic is the preferred way to manage schema, but this can be useful for initial setup
    or in test environments if not using Alembic for tests.
    Make sure all models are imported before calling this.
    """
    async with async_engine.begin() as conn:
        # Import all models here so Base knows about them before creating tables
        # This dynamic import can be tricky. It's often better to ensure models
        # are imported in shared/models/__init__.py and then `from . import models`
        # is called somewhere before this function (e.g. in shared/__init__.py or service main.py)
        # For now, assuming models are loaded.
        # from . import models # noqa
        await conn.run_sync(Base.metadata.create_all)
    print(f"Database tables checked/created for {DATABASE_URL}")

# Note: For Alembic, env.py handles table creation/migration.
# create_db_and_tables() might be called by individual service main.py on startup
# for non-Alembic managed tables or for ensuring DB exists, though migrations handle schema.
# It's generally recommended to rely on Alembic for all schema management in production.
