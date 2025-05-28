from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime

# --- PolicyRule Schemas ---

class PolicyRuleBase(BaseModel):
    rule_content: str = Field(..., description="Datalog rule content")
    source_principle_ids: Optional[List[int]] = Field(None, description="List of AC principle IDs it's derived from")

class PolicyRuleCreate(PolicyRuleBase):
    # version will be defaulted in CRUD or model
    # verification_status will be defaulted
    pass

class PolicyRuleUpdate(BaseModel):
    rule_content: Optional[str] = None
    source_principle_ids: Optional[List[int]] = None
    verification_status: Optional[str] = Field(None, description="e.g., 'pending', 'verified', 'failed'")
    # version might be incremented automatically on content change in CRUD

class PolicyRule(PolicyRuleBase): # For API responses
    id: int
    version: int
    verification_status: str
    verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class PolicyRuleList(BaseModel):
    rules: List[PolicyRule]
    total: int

# --- AuditLog Schemas ---

class AuditLogBase(BaseModel):
    service_name: str = Field(..., description="Name of the service generating the log (e.g., 'ac_service')")
    action: str = Field(..., description="Action performed (e.g., 'CREATE_PRINCIPLE')")
    user_id: Optional[str] = Field(None, description="Identifier of the user performing the action")
    details: Optional[Dict[str, Any]] = Field(None, description="Event-specific data")

class AuditLogCreate(AuditLogBase):
    # timestamp will be defaulted in model or CRUD
    pass

class AuditLog(AuditLogBase): # For API responses
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True

class AuditLogList(BaseModel):
    logs: List[AuditLog]
    total: int

# Placeholder for user information, similar to other services if needed for auth context
class User(BaseModel):
    id: str # Assuming user ID is a string from JWT sub
    roles: List[str] = [] # e.g., ["integrity_admin", "auditor"]
