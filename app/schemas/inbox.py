"""Inbox schemas for Hermes."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class InboxStatus(str, Enum):
    """Status of an inbox message."""
    UNREAD = "unread"
    READ = "read"
    REPLIED = "replied"
    ARCHIVED = "archived"


class InboxThreadBase(BaseModel):
    contact_id: str
    subject: str
    status: InboxStatus = InboxStatus.UNREAD
    last_message_at: Optional[datetime] = None


class InboxThreadRead(InboxThreadBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InboxMessageBase(BaseModel):
    """Base schema for inbox messages."""
    thread_id: str
    contact_id: str
    message_id: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    html: Optional[str] = None
    from_email: str
    from_name: Optional[str] = None
    to_emails: Optional[List[str]] = None
    date: Optional[str] = None
    headers: Optional[Dict[str, Any]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    status: InboxStatus = InboxStatus.UNREAD


class InboxMessageCreate(InboxMessageBase):
    """Schema for creating inbox messages."""
    pass


class InboxMessageRead(InboxMessageBase):
    """Schema for reading inbox messages."""
    id: str
    created_at: datetime
    updated_at: datetime
    
    # We map 'body' to 'body_text' for the frontend based on the frontend component
    @property
    def body_text(self) -> str:
        return self.body or ""

    class Config:
        from_attributes = True


class InboxMessageUpdate(BaseModel):
    """Schema for updating inbox messages."""
    status: Optional[InboxStatus] = None


class InboxListResponse(BaseModel):
    """Schema for inbox list response."""
    total: int
    page: int
    per_page: int
    messages: List[InboxMessageRead]