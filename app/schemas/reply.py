"""Reply schemas for Hermes."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from app.models.reply import ReplyStatus, ReplyClass


class ReplyBase(BaseModel):
    """Base schema for replies."""
    contact_id: str = Field(..., description="Contact ID")
    message_id: Optional[str] = Field(None, description="Message ID")
    from_email: str = Field(..., description="Sender email")
    subject: Optional[str] = Field(None, description="Email subject")
    body_text: str = Field(..., description="Email body text")
    classification: Optional[ReplyClass] = Field(None, description="Reply classification")
    confidence: Optional[float] = Field(None, description="Classification confidence")
    draft_response: Optional[str] = Field(None, description="Draft response")
    handled: bool = Field(False, description="Whether the reply has been handled")
    received_at: datetime = Field(..., description="When the reply was received")


class ReplyCreate(ReplyBase):
    """Schema for creating replies."""
    pass


class ReplyRead(ReplyBase):
    """Schema for reading replies."""
    id: str
    created_at: datetime
    updated_at: datetime
    brevo_message_id: Optional[str] = None

    class Config:
        from_attributes = True


class ReplyUpdate(BaseModel):
    """Schema for updating replies."""
    classification: Optional[ReplyClass] = None
    confidence: Optional[float] = None
    draft_response: Optional[str] = None
    handled: Optional[bool] = None


class ReplyListResponse(BaseModel):
    """Schema for reply list response."""
    total: int
    page: int
    per_page: int
    replies: List[ReplyRead]