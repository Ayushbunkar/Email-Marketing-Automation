"""Sequence model and related types."""

from enum import Enum

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.sql import func

from app.db import Base


class SequenceStatus(str, Enum):
    """Sequence status."""

    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Sequence(Base):
    """Sequence model for multi-step email campaigns."""

    __tablename__ = "sequences"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    campaign_id = Column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id"),
        nullable=False,
    )
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(
        ENUM(SequenceStatus),
        nullable=False,
        server_default="draft",
    )
    created_by = Column(String(50), nullable=False)

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
        return f"<Sequence(id={self.id}, name={self.name}, status={self.status})>"


class SequenceStep(Base):
    """Sequence step model."""

    __tablename__ = "sequence_steps"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    sequence_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sequences.id"),
        nullable=False,
    )
    step_index = Column(Integer, nullable=False)
    delay_hours = Column(Integer, nullable=False, default=0)
    template_id = Column(UUID(as_uuid=True))
    skip_condition = Column(JSON)

    def __repr__(self) -> str:
        return f"<SequenceStep(id={self.id}, sequence_id={self.sequence_id}, step_index={self.step_index})>"
