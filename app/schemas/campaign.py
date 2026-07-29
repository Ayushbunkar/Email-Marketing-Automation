"""Campaign schemas for Hermes."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from uuid import UUID


class CampaignStatus(str, Enum):
    """Campaign status enum."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    SENDING = "sending"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class CampaignType(str, Enum):
    """Campaign type enum."""
    BROADCAST = "broadcast"
    AUTOMATED = "automated"
    REPLY = "reply"


class CampaignCreate(BaseModel):
    """Schema for creating a campaign."""
    name: str = Field(..., min_length=1, max_length=255)
    subject: str = Field(..., min_length=1, max_length=255)
    from_email: str = Field(..., max_length=255)
    from_name: str = Field(..., max_length=255)
    content: str = Field(..., min_length=1)
    segment_id: Optional[str] = None
    contact_ids: Optional[List[str]] = None
    schedule_at: Optional[datetime] = None
    max_sends: Optional[int] = None
    type: CampaignType = CampaignType.BROADCAST


class CampaignRead(BaseModel):
    """Schema for reading a campaign."""
    model_config = {"from_attributes": True}
    
    id: UUID
    name: str
    subject: str
    from_email: str
    from_name: str
    content: str
    segment_id: Optional[UUID]
    contact_ids: List[str]
    status: CampaignStatus
    type: CampaignType
    schedule_at: Optional[datetime]
    max_sends: Optional[int]
    sent_count: int = 0
    open_count: int = 0
    click_count: int = 0
    bounce_count: int = 0
    complaint_count: int = 0
    reply_count: int = 0
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None


class CampaignUpdate(BaseModel):
    """Schema for updating a campaign."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    subject: Optional[str] = Field(None, min_length=1, max_length=255)
    from_email: Optional[str] = Field(None, max_length=255)
    from_name: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    segment_id: Optional[str] = None
    contact_ids: Optional[List[str]] = None
    schedule_at: Optional[datetime] = None
    max_sends: Optional[int] = None
    status: Optional[CampaignStatus] = None
    type: Optional[CampaignType] = None


class CampaignStats(BaseModel):
    """Schema for campaign statistics."""
    total: int = 0
    sent: int = 0
    opened: int = 0
    clicked: int = 0
    bounced: int = 0
    complained: int = 0
    replied: int = 0
    unsubscribed: int = 0


class CampaignAnalytics(BaseModel):
    """Schema for campaign analytics."""
    campaign_id: str
    stats: CampaignStats
    top_locations: List[Dict[str, Any]] = []
    top_devices: List[Dict[str, Any]] = []
    top_referrers: List[Dict[str, Any]] = []
    daily_stats: List[Dict[str, Any]] = []