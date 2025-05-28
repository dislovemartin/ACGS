from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

# User Schemas
class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    # Add any other fields that should be returned when reading a user

    class Config:
        from_attributes = True # Pydantic V2

# Principle Schemas
class PrincipleBase(BaseModel):
    name: str
    description: Optional[str] = None

class PrincipleCreate(PrincipleBase):
    pass

class Principle(PrincipleBase):
    id: int
    # guidelines: List["Guideline"] = [] # Avoid circular dependency if Guideline schema also refers back

    class Config:
        from_attributes = True

# Guideline Schemas
class GuidelineBase(BaseModel):
    content: str
    principle_id: int

class GuidelineCreate(GuidelineBase):
    pass

class Guideline(GuidelineBase):
    id: int
    # principle: Principle # If Principle schema is defined to include guidelines, this creates circular dep.

    class Config:
        from_attributes = True

# For relationship loading, you might need to use Pydantic's Postponed Annotations (ForwardRefs)
# For example, in Principle schema:
# guidelines: List["GuidelineSchema"] = [] 
# And then update_forward_refs() after all models are defined if they are in the same file.
# If in different files, careful import management is needed.
# For now, keeping them simple.

# AuditLog Schemas (already created in integrity_service/app/schemas/audit_log.py, 
# but good to have a shared reference if other services might read them directly,
# or if integrity_service is the sole writer but logs are centrally queried)

class AuditLogBaseShared(BaseModel): # Renamed to avoid conflict if directly imported
    service_name: str
    event_type: str
    details: Optional[str] = None

class AuditLogShared(AuditLogBaseShared):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

# Token Schemas (for Auth service, but can be shared if other services need to validate tokens)
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# If you decide to use the commented out relationship fields (e.g. Principle.guidelines),
# you'll need to handle circular dependencies. One way is:
#
# from pydantic import validator
#
# class GuidelineForPrinciple(GuidelineBase): # A version of Guideline for nesting, without back-refs
#     id: int
#     class Config:
#         from_attributes = True
#
# class Principle(PrincipleBase):
#     id: int
#     guidelines: List[GuidelineForPrinciple] = []
#
#     class Config:
#         from_attributes = True
#
# # And similarly for Guideline if it needs to show Principle info without guidelines list.
# # Or use ForwardRefs as mentioned in Pydantic docs.
