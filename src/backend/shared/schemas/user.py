from typing import Optional
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    username: str
    is_active: Optional[bool] = True
    role: Optional[str] = "user"
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(UserBase):
    password: Optional[str] = None


class UserInDBBase(UserBase):
    id: int

    class Config:
        from_attributes = True


# Properties to return to client
class UserInDB(UserInDBBase):
    pass
