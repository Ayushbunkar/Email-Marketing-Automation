"""Suppression model and related types."""

from enum import Enum

from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, CITEXT, ENUM
from sqlalchemy.sql import func

from app.db import Base


class SuppressionReason(str, Enum):
    """Suppression reason."""

    UNSUBSCRIBE = "unsubscribe"
    HARD_BOUNCE = "hard_bounce"
    COMPLAINT = "complaint"
    MANUAL = "manual"
    LEGAL_REQUEST = "legal_request"


class Suppression(Base):
    """Suppression model for email suppression list."""

    __tablename__ = "suppressions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    email = Column(CITEXT, unique=True, nullable=False)
    reason = Column(
        ENUM(SuppressionReason),
        nullable=False,
    )
    source = Column(String(255), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Suppression(email={self.email}, reason={self.reason})>"