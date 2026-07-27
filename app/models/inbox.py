"""Inbox models for inbound email processing."""

from enum import Enum

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.sql import func

from app.db import Base


class InboxStatus(str, Enum):
    """Inbox message status."""

    UNREAD = "unread"
    READ = "read"
    REPLIED = "replied"
    ARCHIVED = "archived"


class InboxThread(Base):
    """Inbox thread model."""

    __tablename__ = "inbox_threads"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    contact_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id"),
        nullable=False,
    )
    subject = Column(String(255), nullable=False)
    status = Column(
        ENUM(InboxStatus),
        nullable=False,
        server_default="unread",
    )
    last_message_at = Column(DateTime(timezone=True))

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
        return (
            f"<InboxThread(id={self.id}, subject={self.subject}, status={self.status})>"
        )


class InboxMessage(Base):
    """Inbox message model."""

    __tablename__ = "inbox_messages"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    thread_id = Column(
        UUID(as_uuid=True),
        ForeignKey("inbox_threads.id"),
        nullable=False,
    )
    contact_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id"),
        nullable=False,
    )
    message_id = Column(String(255))  # Email Message-ID header
    subject = Column(String(255))
    body = Column(Text)
    html = Column(Text)
    from_email = Column(String(255), nullable=False)
    from_name = Column(String(255))
    to_emails = Column(JSON)
    date = Column(String(255))
    headers = Column(JSON)
    attachments = Column(JSON)
    status = Column(
        ENUM(InboxStatus),
        nullable=False,
        server_default="unread",
    )

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
        return f"<InboxMessage(id={self.id}, subject={self.subject}, status={self.status})>"
