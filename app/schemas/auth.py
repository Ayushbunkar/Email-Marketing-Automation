from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    name: str
    is_active: bool
    is_superuser: bool

    class Config:
        from_attributes = True