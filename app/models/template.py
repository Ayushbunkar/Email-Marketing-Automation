"""Template model."""

from enum import Enum

from sqlalchemy import JSON, Column, ForeignKey, String, Text, DateTime, Integer, ForeignKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db import Base


class TemplateStatus(str, Enum):
    """Template status."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    DELETED = "deleted"


class Template(Base):
    """Template model for email templates."""

    __tablename__ = "templates"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    campaign_id = Column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=True,
    )
    step_index = Column(
        Integer,
        nullable=True,
    )
    name = Column(String(255))
    subject = Column(Text, nullable=False)
    preheader = Column(Text)
    body_markdown = Column(Text, nullable=False)
    variant_label = Column(String(10), nullable=False, default="A")
    variables = Column(JSON, nullable=False, server_default="[]")
    
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
    )

    def __repr__(self) -> str:
        return f"<Template(id={self.id}, subject={self.subject})>"
