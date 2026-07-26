"""Campaign step model."""

from sqlalchemy import Column, Integer, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db import Base


class CampaignStep(Base):
    """Campaign step model for multi-step campaigns."""

    __tablename__ = "campaign_steps"

    campaign_id = Column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    step_index = Column(Integer, primary_key=True, nullable=False)
    delay_hours = Column(Integer, nullable=False, default=0)
    send_condition = Column(JSON, nullable=False, server_default="{}")

    __table_args__ = (
        UniqueConstraint("campaign_id", "step_index"),
    )

    def __repr__(self) -> str:
        return f"<CampaignStep(campaign_id={self.campaign_id}, step_index={self.step_index})>"