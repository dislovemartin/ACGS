from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None
    user_id: Optional[int] = None
    roles: Optional[list[str]] = None
    type: Optional[str] = None
    jti: Optional[str] = None
