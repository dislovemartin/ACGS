from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# Schema for token response
class Token(BaseModel):
    access_token: str
    refresh_token: str # Added refresh_token
    token_type: str

# Schema for data embedded in the token
class TokenData(BaseModel):
    username: Optional[str] = None
    jti: Optional[str] = None # JWT ID claim
    # Add 'type' to distinguish access vs refresh if needed, but often handled by different expiries and usage
    # token_type: Optional[str] = "access" 

# Schema for creating a refresh token in DB (minimal)
class RefreshTokenCreate(BaseModel):
    user_id: int
    token: str # The refresh token string itself
    expires_at: datetime

# Schema for RefreshToken in DB (includes ID, etc.)
class RefreshToken(RefreshTokenCreate):
    id: int
    created_at: datetime
    revoked: bool

    class Config:
        orm_mode = True

# Base User schema for common attributes
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr

# Schema for user creation (request)
class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

# Schema for user response (excluding sensitive data like password)
class UserResponse(UserBase):
    id: int
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True # For SQLAlchemy model compatibility

# Schema for user in database (internal, includes hashed_password)
class UserInDB(UserBase):
    id: int
    hashed_password: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
