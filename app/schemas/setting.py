"""Pydantic schemas for settings."""

from pydantic import BaseModel
from typing import Optional


class SettingRead(BaseModel):
    id: str
    key: str
    value: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True


class SettingUpdate(BaseModel):
    value: Optional[str] = None
    description: Optional[str] = None
