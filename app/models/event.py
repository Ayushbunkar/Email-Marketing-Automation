"""Event model and related types."""

from enum import Enum

from sqlalchemy import Column, String, JSON, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.sql import func

from app.db import Base


class EventType(str, Enum):
    """Event type."""

    DELIVERED = "delivered"
    OPEN = "open"
    CLICK = "click"
    BOUNCE_HARD = "bounce_hard"
    BOUNCE_SOFT = "bounce_soft"
    COMPLAINT = "complaint"
    UNSUBSCRIBE = "unsubscribe"
    REPLY = "reply"


class Event(Base):
    """Event model for tracking email events."""

    __tablename__ = "events"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"))
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id"))
    type = Column(
        ENUM(EventType),
        nullable=False,
    )
    payload = Column(JSON, nullable=False, server_default="{}")
    provider_event_id = Column(String(255), unique=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_events_contact_type_occurred", "contact_id", "type", "occurred_at"),
    )

    def __repr__(self) -> str:
        return f"<Event(id={self.id}, type={self.type})>"