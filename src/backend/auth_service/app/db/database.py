import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables from .env file (especially for local development)
# In a containerized environment, these might be set directly.
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://youruser:yourpassword@postgres:5432/yourdatabase_auth")

engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session

async def create_db_tables():
    # This is where you would import your models and call Base.metadata.create_all(engine)
    # For now, it's a placeholder. We'll call it from main.py
    print(f"Database tables creation would be triggered here for {DATABASE_URL}")
    # Actual table creation will be linked once models are fully in place and Base is confirmed.
    # For now, we are just setting up the structure.
    # We need to ensure all models that use a Base are imported before calling create_all.
    try:
        # If models are defined using the Base from shared.database, then:
        from shared.database import Base
        # Import all models here that should be created
        from shared.models import User, RefreshToken # noqa
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Tables created (if they didn't exist already, including refresh_tokens).")
    except Exception as e:
        print(f"Error creating tables: {e}")
        # For now, just continue without creating tables
