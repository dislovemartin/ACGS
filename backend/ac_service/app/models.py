from sqlalchemy import Column, Integer, String, Text, DateTime, func, ForeignKey
from shared.database import Base # Assuming shared/database.py provides Base
from datetime import datetime

class Principle(Base):
    __tablename__ = "principles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=False) # Could be JSONB if using PostgreSQL and needing structured content
    version = Column(Integer, default=1, nullable=False)
    status = Column(String, default="draft", nullable=False) # e.g., "draft", "approved", "deprecated"
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Conceptual link to a user ID from an auth service.
    # For now, it's a simple integer. If using a separate users table within this service,
    # it would be a ForeignKey. Cross-service FKs are not directly feasible.
    created_by_user_id = Column(Integer, nullable=True) # Or False if user must always be known

    # If you were to have a direct FK to a local user table (not the case here for inter-service):
    # created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # creator = relationship("User")

    def __repr__(self):
        return f"<Principle(name='{self.name}', version={self.version}, status='{self.status}')>"
