"""Analytics schemas for Hermes."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any


class AnalyticsSummary(BaseModel):
    """Schema for analytics summary."""
    total_contacts: int = 0
    total_campaigns: int = 0
    emails_sent: int = 0
    emails_opened: int = 0
    emails_clicked: int = 0
    reply_count: int = 0
    bounce_count: int = 0
    complaint_count: int = 0
    unsubscribe_count: int = 0
    open_rate: float = 0.0
    click_rate: float = 0.0
    reply_rate: float = 0.0
    bounce_rate: float = 0.0


class CampaignPerformance(BaseModel):
    """Schema for campaign performance."""
    campaign_id: str
    name: str
    subject: str
    sent: int = 0
    opened: int = 0
    clicked: int = 0
    replied: int = 0
    bounced: int = 0
    complained: int = 0
    open_rate: float = 0.0
    click_rate: float = 0.0
    reply_rate: float = 0.0


class DailySending(BaseModel):
    """Schema for daily sending data."""
    date: str
    sent: int = 0
    opened: int = 0
    clicked: int = 0
    bounced: int = 0


class CampaignStats(BaseModel):
    """Schema for campaign statistics."""
    campaign_id: str
    sent: int = 0
    opened: int = 0
    clicked: int = 0
    replied: int = 0
    bounced: int = 0
    complained: int = 0
    unsubscribed: int = 0
    open_rate: float = 0.0
    click_rate: float = 0.0
    reply_rate: float = 0.0


class ContactAnalytics(BaseModel):
    """Schema for contact analytics."""
    contact_id: str
    email: str
    total_emails_sent: int = 0
    total_emails_opened: int = 0
    total_emails_clicked: int = 0
    last_contacted_at: Optional[datetime] = None
    most_recent_campaign: Optional[str] = None


class AnalyticsResponse(BaseModel):
    """Schema for analytics response."""
    summary: AnalyticsSummary
    campaign_performance: List[CampaignPerformance]
    daily_sending: List[DailySending]
    top_campaigns: List[CampaignPerformance]