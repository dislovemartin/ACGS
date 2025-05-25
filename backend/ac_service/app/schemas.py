from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Base schema for Principle attributes
class PrincipleBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100, description="Unique name of the principle")
    description: Optional[str] = Field(None, max_length=500, description="Detailed description of the principle")
    content: str = Field(..., description="The full content of the principle (e.g., text, JSON string)")

# Schema for creating a new principle
class PrincipleCreate(PrincipleBase):
    # version and status will have default values in the model
    # created_by_user_id will be passed from the request context (e.g., authenticated user)
    pass

# Schema for updating an existing principle
# All fields are optional for updates
class PrincipleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = None
    status: Optional[str] = Field(None, description="e.g., 'draft', 'approved', 'deprecated'")
    # version might be handled automatically or via a specific versioning endpoint
    # version: Optional[int] = Field(None, gt=0) 

# Schema for representing a Principle in API responses
class Principle(PrincipleBase):
    id: int
    version: int
    status: str
    created_at: datetime
    updated_at: datetime
    created_by_user_id: Optional[int] = None # Made optional if user can be anonymous or system-created

    class Config:
        orm_mode = True # For SQLAlchemy model compatibility

# Optional: Schema for a list of principles for responses
class PrincipleList(BaseModel):
    principles: List[Principle]
    total: int

# Placeholder for user information, to be refined with actual auth integration
class User(BaseModel):
    id: int
    username: str
    roles: List[str] = [] # e.g., ["user", "ac_admin"]
