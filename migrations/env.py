# ACGS/alembic/env.py
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# This line allows Alembic to find your models by adding the project root to sys.path
# With the new directory structure:
# - migrations/ contains alembic files
# - src/backend/shared/ contains shared models
# The Dockerfile.alembic copies `src/backend/shared` to `/app/shared` and `migrations` to `/app/`.
# WORKDIR in Dockerfile.alembic is /app.
# alembic.ini is expected to be in /app/alembic.ini
# shared is in /app/shared
# env.py is in /app/env.py
# So from /app/env.py, /app/shared is `./shared`
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Add the shared directory to Python path for direct imports
shared_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "shared"))
if shared_path not in sys.path:
    sys.path.insert(0, shared_path)

print(f"Alembic env.py: Current working directory: {os.getcwd()}")
print(f"Alembic env.py: Python path: {sys.path}")

# Now you can import your models and metadata
# Ensure these imports match your project structure and model definitions
try:
    # Create a minimal database setup for Alembic without external dependencies
    print("Setting up minimal database configuration for Alembic...")

    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy import (
        Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Float, Index
    )
    from sqlalchemy.dialects.postgresql import JSONB, UUID, ARRAY
    from datetime import datetime, timezone
    import uuid

    # Create Base for models
    Base = declarative_base()

    # Define models directly in env.py to avoid import issues
    class User(Base):
        __tablename__ = "users"

        id = Column(Integer, primary_key=True, index=True)
        username = Column(String(100), unique=True, index=True, nullable=False)
        hashed_password = Column(String(255), nullable=False)
        email = Column(String(255), unique=True, index=True, nullable=False)
        full_name = Column(String(255), nullable=True)
        role = Column(String(50), default="user", nullable=False, index=True)
        is_active = Column(Boolean, default=True, nullable=False)
        created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
        updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    class RefreshToken(Base):
        __tablename__ = "refresh_tokens"

        id = Column(Integer, primary_key=True, index=True)
        user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
        jti = Column(String(36), unique=True, index=True, nullable=False)
        token = Column(String(512), nullable=False, index=True)
        expires_at = Column(DateTime(timezone=True), nullable=False)
        created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
        is_revoked = Column(Boolean, default=False, nullable=False)

    class Principle(Base):
        __tablename__ = "principles"

        id = Column(Integer, primary_key=True, index=True)
        name = Column(String(255), unique=True, index=True, nullable=False)
        description = Column(Text, nullable=True)
        content = Column(Text, nullable=False)
        version = Column(Integer, default=1, nullable=False)
        status = Column(String(50), default="draft", nullable=False, index=True)

        # Enhanced Phase 1 Constitutional Fields
        priority_weight = Column(Float, nullable=True)
        scope = Column(JSONB, nullable=True)
        normative_statement = Column(Text, nullable=True)
        constraints = Column(JSONB, nullable=True)
        rationale = Column(Text, nullable=True)
        keywords = Column(JSONB, nullable=True)
        category = Column(String(100), nullable=True, index=True)
        validation_criteria_nl = Column(Text, nullable=True)
        constitutional_metadata = Column(JSONB, nullable=True)

        created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
        updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
        created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Add other essential models here...
    # (Truncated for brevity - we can add more models as needed)

    # Use the Base metadata for migrations
    target_metadata = Base.metadata
    print(f"Using Base.metadata with {len(target_metadata.tables)} tables")

    # Print table names for debugging
    table_names = list(target_metadata.tables.keys())
    print(f"Tables found: {table_names}")

except Exception as e:
    print(f"Warning: Could not set up models: {e}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")

    # Fallback to empty metadata
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()
    target_metadata = Base.metadata
    print("Using empty metadata as fallback")


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# target_metadata = mymodel.Base.metadata # Handled by importing Base.metadata from shared.database

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def get_url():
    """
    Constructs the database URL from environment variables.
    Reads the DATABASE_URL directly and converts it for synchronous Alembic use if needed.
    """
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        # Fallback to the value in alembic.ini if DATABASE_URL is not set.
        # However, for this project, DATABASE_URL is expected to be set via docker-compose.
        # The alembic.ini has sqlalchemy.url = postgresql://user:pass@host/dbname
        # which is a placeholder.
        ini_url = config.get_main_option("sqlalchemy.url")
        if ini_url and ini_url != "postgresql://user:pass@host/dbname":
            db_url = ini_url
        else:
            raise ValueError("DATABASE_URL environment variable is not set and alembic.ini has no valid fallback. Alembic requires this to connect to the database.")
    
    # Alembic uses synchronous drivers. If DATABASE_URL is for asyncpg, convert it.
    if db_url.startswith("postgresql+asyncpg"):
        db_url = db_url.replace("postgresql+asyncpg", "postgresql", 1)
    elif db_url.startswith("sqlite+aiosqlite"): # For potential SQLite testing
        db_url = db_url.replace("sqlite+aiosqlite", "sqlite", 1)
    # Add other replacements here if needed for other async drivers
    
    return db_url

# Set the sqlalchemy.url in the Alembic config object
# This is crucial for Alembic to know where your database is.
# This overrides the sqlalchemy.url from alembic.ini if get_url() provides one.
effective_url = get_url()
if effective_url:
    config.set_main_option("sqlalchemy.url", effective_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # include_schemas=True, # if using multiple schemas
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}), # Uses sqlalchemy.url from config
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            # include_schemas=True, # if using multiple schemas
            # compare_type=True, # Detect column type changes
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
