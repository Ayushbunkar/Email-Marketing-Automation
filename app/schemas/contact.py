"""Contact schemas for Hermes."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from uuid import UUID


class ContactStatus(str, Enum):
    """Contact status enum."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNSUBSCRIBED = "unsubscribed"
    BOUNCED = "bounced"
    COMPLAINED = "complained"


class ContactCreate(BaseModel):
    """Schema for creating a contact."""
    email: str
    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    company: Optional[str] = Field(None, max_length=255)
    job_title: Optional[str] = Field(None, max_length=255)
    status: ContactStatus = ContactStatus.ACTIVE
    custom_fields: Optional[Dict[str, Any]] = None
    segment_ids: Optional[List[str]] = None


class ContactRead(BaseModel):
    """Schema for reading a contact."""
    model_config = {"from_attributes": True}
    
    id: UUID
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    phone: Optional[str]
    company: Optional[str]
    job_title: Optional[str]
    status: ContactStatus
    custom_fields: Optional[Dict[str, Any]]
    segment_ids: List[str]
    created_at: datetime
    updated_at: datetime
    last_contacted_at: Optional[datetime] = None
    total_emails_sent: int = 0
    total_emails_opened: int = 0
    total_emails_clicked: int = 0


class ContactUpdate(BaseModel):
    """Schema for updating a contact."""
    email: Optional[str] = None
    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    company: Optional[str] = Field(None, max_length=255)
    job_title: Optional[str] = Field(None, max_length=255)
    status: Optional[ContactStatus] = None
    custom_fields: Optional[Dict[str, Any]] = None
    segment_ids: Optional[List[str]] = None


class ContactStats(BaseModel):
    """Schema for contact statistics."""
    total: int = 0
    active: int = 0
    unsubscribed: int = 0
    bounced: int = 0
    complained: int = 0


class ContactListResponse(BaseModel):
    """Schema for contact list response."""
    contacts: List[ContactRead]
    total: int
    page: int
    page_size: int
    total_pages: int