"""Segment model."""

from datetime import datetime

from sqlalchemy import Column, String, Text, JSON, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db import Base


class Segment(Base):
    """Segment model for audience segmentation."""

    __tablename__ = "segments"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    name = Column(String(255), nullable=False)
    description = Column(Text)
    definition = Column(JSON, nullable=False, server_default="{}")
    is_dynamic = Column(JSON, nullable=False, server_default="true")
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
        return f"<Segment(id={self.id}, name={self.name})>"