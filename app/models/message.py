"""Message model and related types."""

from enum import Enum

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    Integer,
    ForeignKeyConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db import Base


class MessageStatus(str, Enum):
    """Message status."""

    QUEUED = "queued"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    BOUNCED = "bounced"
    FAILED = "failed"
    SUPPRESSED = "suppressed"
    CANCELED = "canceled"


class Message(Base):
    """Message model for email messages."""

    __tablename__ = "messages"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"))
    step_index = Column(Integer)
    contact_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id"),
        nullable=False,
    )
    template_id = Column(UUID(as_uuid=True), ForeignKey("templates.id"))
    status = Column(
        String(50),
        nullable=False,
        server_default="QUEUED",
    )
    provider_message_id = Column(String(255), unique=True)
    scheduled_for = Column(DateTime(timezone=True), nullable=False)
    sent_at = Column(DateTime(timezone=True))
    error = Column(Text)
    provider_event_id = Column(String(255))
    
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

    __table_args__ = (
        ForeignKeyConstraint(
            ["campaign_id", "step_index"],
            ["campaign_steps.campaign_id", "campaign_steps.step_index"],
            ondelete="CASCADE",
        ),
        UniqueConstraint("campaign_id", "step_index", "contact_id"),
        Index("ix_messages_status_scheduled_for", "status", "scheduled_for"),
    )

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, status={self.status})>"
