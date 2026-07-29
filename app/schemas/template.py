"""Template schemas for Hermes."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from uuid import UUID

from app.models.template import TemplateStatus


class TemplateBase(BaseModel):
    """Base schema for templates."""
    campaign_id: Optional[UUID] = Field(None, description="Campaign ID")
    step_index: Optional[int] = Field(None, description="Campaign step index")
    name: Optional[str] = Field(None, description="Template name")
    subject: str = Field(..., description="Email subject")
    preheader: Optional[str] = Field(None, description="Email preheader")
    body_markdown: str = Field(..., description="Email body in markdown")
    variant_label: str = Field("A", description="Template variant label")
    variables: List[str] = Field(default_factory=list, description="Template variables")


class TemplateCreate(TemplateBase):
    """Schema for creating templates."""
    pass


class TemplateRead(TemplateBase):
    """Schema for reading templates."""
    model_config = {"from_attributes": True}
    
    id: UUID
    created_at: datetime
    updated_at: datetime
    status: Optional[TemplateStatus] = None


class TemplateUpdate(BaseModel):
    """Schema for updating templates."""
    name: Optional[str] = None
    subject: Optional[str] = None
    preheader: Optional[str] = None
    body_markdown: Optional[str] = None
    variant_label: Optional[str] = None
    variables: Optional[List[str]] = None
    status: Optional[TemplateStatus] = None


class TemplateListResponse(BaseModel):
    """Schema for template list response."""
    total: int
    page: int
    per_page: int
    templates: List[TemplateRead]