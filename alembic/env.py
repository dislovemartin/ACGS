# ACGS/alembic/env.py
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# This line allows Alembic to find your models by adding the project root to sys.path
# Assuming alembic commands are run from the ACGS project root,
# or that the Docker context for alembic-runner places 'shared' correctly.
# The Dockerfile.alembic copies `shared` to `/app/shared` and `alembic` to `/app/alembic`.
# WORKDIR in Dockerfile.alembic is /app.
# alembic.ini is expected to be in /app/alembic/alembic.ini
# shared is in /app/shared
# env.py is in /app/alembic/env.py
# So from /app/alembic/env.py, /app/shared is `../shared`
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# Now you can import your models and metadata
# Ensure these imports match your project structure and model definitions
try:
    # Import only the essential models without the full application
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy import MetaData

    # Create a simple Base for migrations
    Base = declarative_base()

    # For now, use empty metadata - we'll run existing migrations
    target_metadata = Base.metadata

    # Try to import models if possible, but don't fail if dependencies are missing
    try:
        from shared.database import Base as SharedBase
        from shared import models
        target_metadata = SharedBase.metadata
    except ImportError:
        print("Warning: Could not import shared models, using empty metadata")
        pass

except ImportError as e:
    sys.exit(f"Error importing models or metadata for Alembic: {e}. Check PYTHONPATH and alembic/env.py structure. Current sys.path: {sys.path}")


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
