"""Campaign model and related types."""

from enum import Enum

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
        ENUM(CampaignType),
        nullable=False,
    )
    status = Column(
        ENUM(CampaignStatus),
        nullable=False,
        server_default="draft",
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
