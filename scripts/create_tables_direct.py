#!/usr/bin/env python3
"""
Direct table creation script for ACGS-PGP
This bypasses alembic import issues and creates tables directly
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src" / "backend"))

# Import database components
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func, JSON, Float, Index, Enum, Numeric
)
from sqlalchemy.dialects.postgresql import JSONB, UUID, ARRAY
from datetime import datetime, timezone
import uuid
import enum

# Create Base
Base = declarative_base()

# Define essential models directly (simplified versions)
class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
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
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
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
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

async def create_tables():
    """Create all tables in the database"""
    
    # Database URL
    DATABASE_URL = "postgresql+asyncpg://acgs_user:acgs_password@localhost:5433/acgs_pgp_db"
    
    # Create engine
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    try:
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Database tables created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False
    finally:
        await engine.dispose()

async def main():
    """Main function"""
    print("🔄 Creating ACGS-PGP database tables...")
    success = await create_tables()
    
    if success:
        print("🎉 Database initialization completed!")
        return 0
    else:
        print("💥 Database initialization failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
