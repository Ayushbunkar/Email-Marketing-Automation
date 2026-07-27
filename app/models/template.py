"""Template model."""

from sqlalchemy import JSON, Column, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db import Base


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
        nullable=False,
    )
    step_id = Column(
        UUID(as_uuid=True),
        ForeignKey("campaign_steps.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(String(255))
    subject = Column(Text, nullable=False)
    preheader = Column(Text)
    body_markdown = Column(Text, nullable=False)
    variant_label = Column(String(10), nullable=False, default="A")
    variables = Column(JSON, nullable=False, server_default="[]")

    def __repr__(self) -> str:
        return f"<Template(id={self.id}, subject={self.subject})>"
