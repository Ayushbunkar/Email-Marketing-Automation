"""Contact model and related types."""

from enum import Enum

from sqlalchemy import ARRAY, JSON, Column, DateTime, Float, Index, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import CITEXT, UUID
from sqlalchemy.sql import func

from app.db import Base


class LifecycleStage(str, Enum):
    """Contact lifecycle stage."""

    LEAD = "lead"
    SUBSCRIBER = "subscriber"
    ENGAGED = "engaged"
    CUSTOMER = "customer"
    CHURNED = "churned"


class ContactStatus(str, Enum):
    """Contact status."""

    ACTIVE = "active"
    UNSUBSCRIBED = "unsubscribed"
    BOUNCED = "bounced"
    COMPLAINED = "complained"
    SUPPRESSED = "suppressed"


class Contact(Base):
    """Contact model representing a person in the CRM."""

    __tablename__ = "contacts"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    email = Column(CITEXT, unique=True, nullable=False)
    first_name = Column(Text)
    last_name = Column(Text)
    company = Column(Text)
    attributes = Column(
        JSON,
        nullable=False,
        server_default="{}",
    )
    lifecycle_stage = Column(
        SQLEnum(LifecycleStage),
        nullable=False,
        server_default="lead",
    )
    status = Column(
        SQLEnum(ContactStatus),
        nullable=False,
        server_default="active",
    )
    consent_source = Column(Text)
    consent_at = Column(DateTime(timezone=True))
    timezone = Column(Text, nullable=False, server_default="Asia/Kolkata")
    last_emailed_at = Column(DateTime(timezone=True))
    embedding = Column(ARRAY(Float))

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
        Index("ix_contacts_status", "status"),
        Index("ix_contacts_lifecycle_stage", "lifecycle_stage"),
    )

    def __repr__(self) -> str:
        return f"<Contact(id={self.id}, email={self.email})>"
