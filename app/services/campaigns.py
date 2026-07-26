"""Campaign service for managing email campaigns."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.models.campaign import Campaign, CampaignStatus, CampaignType
from app.models.campaign_step import CampaignStep
from app.models.template import Template
from app.models.message import Message, MessageStatus


async def create_campaign(
    session: AsyncSession,
    name: str,
    goal: str,
    campaign_type: CampaignType,
    segment_id: Optional[str] = None,
    settings: Optional[Dict[str, Any]] = None,
    created_by: str = "system",
) -> Campaign:
    """Create a new campaign."""
    campaign = Campaign(
        name=name,
        goal=goal,
        type=campaign_type,
        status=CampaignStatus.DRAFT,
        segment_id=segment_id,
        settings=settings or {},
        created_by=created_by,
    )
    session.add(campaign)
    await session.commit()
    return campaign


async def get_campaign(session: AsyncSession, campaign_id: str) -> Optional[Campaign]:
    """Get a campaign by ID."""
    result = await session.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    return result.scalar_one_or_none()


async def get_campaign_with_steps(session: AsyncSession, campaign_id: str) -> Optional[Campaign]:
    """Get a campaign with its steps."""
    result = await session.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()
    if campaign:
        result = await session.execute(
            select(CampaignStep)
            .where(CampaignStep.campaign_id == campaign_id)
            .order_by(CampaignStep.step_index)
        )
        campaign.steps = list(result.scalars().all())
    return campaign


async def list_campaigns(
    session: AsyncSession,
    status: Optional[CampaignStatus] = None,
    limit: int = 50,
) -> List[Campaign]:
    """List campaigns with optional status filter."""
    query = select(Campaign)

    if status:
        query = query.where(Campaign.status == status)

    query = query.order_by(Campaign.created_at.desc()).limit(limit)
    result = await session.execute(query)
    return list(result.scalars().all())


async def update_campaign_status(
    session: AsyncSession,
    campaign_id: str,
    status: CampaignStatus,
    approved_by: Optional[str] = None,
) -> Optional[Campaign]:
    """Update campaign status."""
    result = await session.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()
    if campaign:
        campaign.status = status
        if status in (CampaignStatus.APPROVED, CampaignStatus.RUNNING):
            campaign.approved_by = approved_by
            campaign.approved_at = datetime.utcnow()
        await session.commit()
    return campaign


async def add_campaign_step(
    session: AsyncSession,
    campaign_id: str,
    step_index: int,
    delay_hours: int = 0,
    send_condition: Optional[Dict[str, Any]] = None,
) -> CampaignStep:
    """Add a step to a campaign."""
    step = CampaignStep(
        campaign_id=campaign_id,
        step_index=step_index,
        delay_hours=delay_hours,
        send_condition=send_condition or {},
    )
    session.add(step)
    await session.commit()
    return step


async def create_template(
    session: AsyncSession,
    campaign_id: str,
    step_id: str,
    subject: str,
    body_markdown: str,
    preheader: Optional[str] = None,
    name: Optional[str] = None,
    variant_label: str = "A",
    variables: Optional[List[str]] = None,
) -> Template:
    """Create a template for a campaign step."""
    template = Template(
        campaign_id=campaign_id,
        step_id=step_id,
        name=name,
        subject=subject,
        preheader=preheader,
        body_markdown=body_markdown,
        variant_label=variant_label,
        variables=variables or [],
    )
    session.add(template)
    await session.commit()
    return template


async def get_campaign_message_count(
    session: AsyncSession,
    campaign_id: str,
    status: Optional[MessageStatus] = None,
) -> int:
    """Get message count for a campaign."""
    query = select(func.count(Message.id)).where(Message.campaign_id == campaign_id)

    if status:
        query = query.where(Message.status == status)

    result = await session.execute(query)
    return result.scalar_one()