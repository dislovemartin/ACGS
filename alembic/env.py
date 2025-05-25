import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# This line allows Alembic to find your models by adding the project root to sys.path
# Adjust the path if your project structure is different
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now you can import your models and metadata
# Ensure these imports match your project structure and model definitions
try:
    from shared.models import (User, Principle, PolicyRule, AuditLog,
                               PolicyTemplate, Policy, RefreshToken) # Add all your models here
    from shared.database import metadata # Assuming your Base.metadata is accessible here
except ImportError as e:
    sys.exit(f"Error importing models or metadata: {e}. Check PYTHONPATH and alembic/env.py.")


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = metadata # Use the imported metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_url():
    """
    Constructs the database URL from environment variables.
    Reads the DATABASE_URL directly and converts it for synchronous Alembic use.
    """
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is not set.")
    
    # Replace known async drivers with their synchronous counterparts or base scheme
    if "postgresql+asyncpg" in db_url:
        db_url = db_url.replace("postgresql+asyncpg", "postgresql")
    elif "sqlite+aiosqlite" in db_url:
        db_url = db_url.replace("sqlite+aiosqlite", "sqlite")
    # Add other replacements here if needed for other async drivers
    
    return db_url

# Set the sqlalchemy.url in the Alembic config object
# This is crucial for Alembic to know where your database is.
config.set_main_option("sqlalchemy.url", get_url())


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
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
