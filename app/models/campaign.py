"""Campaign model and related types."""

from enum import Enum
from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Column, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.sql import func

from app.db import Base


class CampaignStatus(str, Enum):
    """Campaign status."""

    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class CampaignType(str, Enum):
    """Campaign type."""

    ONE_SHOT = "one_shot"
    SEQUENCE = "sequence"
    TRIGGER = "trigger"


class Campaign(Base):
    """Campaign model for email campaigns."""

    __tablename__ = "campaigns"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    name = Column(String(255), nullable=False)
    goal = Column(Text, nullable=False)
    type = Column(
        String(50),
        nullable=False,
    )
    status = Column(
        String(50),
        nullable=False,
        server_default="DRAFT",
    )
    segment_id = Column(UUID(as_uuid=True))
    settings = Column(JSON, nullable=False, server_default="{}")
    scheduled_at = Column(DateTime(timezone=True))
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_by = Column(String(50), nullable=False)
    approved_by = Column(String(50))
    approved_at = Column(DateTime(timezone=True))

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Campaign(id={self.id}, name={self.name}, status={self.status})>"

    @property
    def subject(self) -> str:
        return self.settings.get("subject", "") if self.settings else ""

    @property
    def from_email(self) -> str:
        return self.settings.get("from_email", "") if self.settings else ""

    @property
    def from_name(self) -> str:
        return self.settings.get("from_name", "") if self.settings else ""

    @property
    def content(self) -> str:
        return self.settings.get("content", "") if self.settings else ""

    @property
    def contact_ids(self) -> list:
        return self.settings.get("contact_ids", []) if self.settings else []

    @property
    def schedule_at(self) -> Optional[datetime]:
        return self.scheduled_at

    @property
    def max_sends(self) -> Optional[int]:
        return self.settings.get("max_sends") if self.settings else None
