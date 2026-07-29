from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserRead(BaseModel):
    id: str
    email: EmailStr
    name: str
    is_active: bool
    is_superuser: bool

    class Config:
        from_attributes = True