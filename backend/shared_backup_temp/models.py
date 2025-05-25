from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base # Ensure this import works with the shared directory structure
import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
    # Add relationships if needed, e.g., roles, activity logs

class Principle(Base):
    __tablename__ = "principles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    guidelines = relationship("Guideline", back_populates="principle")

class Guideline(Base):
    __tablename__ = "guidelines"
    id = Column(Integer, primary_key=True, index=True)
    principle_id = Column(Integer, ForeignKey("principles.id"), nullable=False)
    content = Column(Text, nullable=False)
    principle = relationship("Principle", back_populates="guidelines")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    service_name = Column(String(100), nullable=False)
    event_type = Column(String(100), nullable=False)
    details = Column(Text, nullable=True)

# Add other shared models here if necessary as the project evolves
# e.g., Policy, GovernanceRule, VerificationResult etc.
