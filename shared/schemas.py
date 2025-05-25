# Pydantic schemas 
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


# User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    role: Optional[str] = "user"

class UserInDB(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


from typing import List, Dict, Any # Add Any if not present

# PolicyTemplate Schemas
class PolicyTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    default_content: str
    parameters_schema: Optional[Dict[str, Any]] = None # JSON schema for parameters

class PolicyTemplateCreate(PolicyTemplateBase):
    pass

class PolicyTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    default_content: Optional[str] = None
    parameters_schema: Optional[Dict[str, Any]] = None
    version: Optional[int] = None

class PolicyTemplateInDBBase(PolicyTemplateBase):
    id: int
    version: int
    created_at: datetime
    updated_at: datetime
    created_by_user_id: Optional[int] = None

    class Config:
        from_attributes = True

class PolicyTemplate(PolicyTemplateInDBBase):
    pass

# Policy Schemas
class PolicyBase(BaseModel):
    name: str
    description: Optional[str] = None
    content: str
    status: Optional[str] = "draft"
    template_id: Optional[int] = None
    customization_parameters: Optional[Dict[str, Any]] = None

class PolicyCreate(PolicyBase):
    pass

class PolicyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None
    customization_parameters: Optional[Dict[str, Any]] = None
    version: Optional[int] = None

class PolicyInDBBase(PolicyBase):
    id: int
    version: int
    created_at: datetime
    updated_at: datetime
    created_by_user_id: Optional[int] = None
    # template: Optional[PolicyTemplate] = None # Could be added if needed for responses

    class Config:
        from_attributes = True

class Policy(PolicyInDBBase):
    pass

# For displaying Policy with its template details
class PolicyWithTemplate(Policy):
   template: Optional[PolicyTemplate] = None

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel): # This is typically for username from an older form of token, can be removed if not used
    username: Optional[str] = None

class TokenPayload(BaseModel): # Payload within the JWT
    sub: str # Subject (username)
    user_id: int
    roles: List[str] = []
    # exp: Optional[int] = None # Expiration time, handled by JWT library; jose handles this internally

# Principle Schemas
class PrincipleBase(BaseModel):
    name: str
    description: str
    content: str

class PrincipleCreate(PrincipleBase):
    pass

class PrincipleUpdate(BaseModel):
    description: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None

class Principle(PrincipleBase):
    id: int
    version: int
    status: str
    created_at: datetime
    updated_at: datetime
    created_by_user_id: Optional[int]

    class Config:
        from_attributes = True

# Policy Rule Schemas
class PolicyRuleBase(BaseModel):
    # principle_id: int # Replaced by source_principle_ids
    source_principle_ids: Optional[List[int]] = None
    rule_name: str
    datalog_content: str

class PolicyRuleCreate(PolicyRuleBase):
    pass

class PolicyRuleUpdate(BaseModel):
    datalog_content: Optional[str] = None
    status: Optional[str] = None
    verification_status: Optional[str] = None

class PolicyRule(PolicyRuleBase):
    id: int
    version: int
    status: str
    verification_status: str
    created_at: datetime
    updated_at: datetime
    synthesized_by_gs_engine_id: Optional[str]
    verified_by_fv_service_id: Optional[str]

    class Config:
        from_attributes = True

# Audit Log Schemas
class AuditLogBase(BaseModel):
    event_type: str
    entity_type: str
    entity_id: Optional[int] = None
    description: Optional[str] = None
    actor_id: Optional[int] = None
    metadata_json: Optional[str] = None

class AuditLogCreate(AuditLogBase):
    pass

class AuditLog(AuditLogBase):
    id: int
    timestamp: datetime
    previous_hash: Optional[str]
    current_hash: str

    class Config:
        from_attributes = True