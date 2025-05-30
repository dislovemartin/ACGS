from app.db.base_class import Base  # We'll create this base class soon
from sqlalchemy import Boolean, Column, Integer, String


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=False)

    # If you have relationships, define them here. For example:
    # from sqlalchemy.orm import relationship
    # items = relationship("Item", back_populates="owner")
