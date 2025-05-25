import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables from .env file (especially for local development)
# In a containerized environment, these might be set directly.
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://youruser:yourpassword@postgres:5432/yourdatabase_auth")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_db_tables():
    # This is where you would import your models and call Base.metadata.create_all(engine)
    # For now, it's a placeholder. We'll call it from main.py
    # from auth_service.app.models import Base # This will be the actual import
    # from shared.database import Base # Or if Base is truly shared and models are separate
    # Base.metadata.create_all(bind=engine)
    print(f"Database tables creation would be triggered here for {DATABASE_URL}")
    # Actual table creation will be linked once models are fully in place and Base is confirmed.
    # For now, we are just setting up the structure.
    # We need to ensure all models that use a Base are imported before calling create_all.
    # For example, if User model is in auth_service.app.models
    from auth_service.app.models import Base as UserBase # Assuming User model uses its own Base or a shared one
    from shared.database import Base as SharedBase # If there's another Base in shared

    # If models are defined using the Base from shared.database, then:
    from shared.database import Base
    # Import all models here that should be created
    from auth_service.app.models import User, RefreshToken # noqa
    Base.metadata.create_all(bind=engine)
    print("Tables created (if they didn't exist already, including refresh_tokens).")
