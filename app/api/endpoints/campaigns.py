from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime

from app.db import get_session
from app.models.campaign import Campaign, CampaignStatus, CampaignType
from app.schemas.campaign import CampaignCreate, CampaignRead, CampaignUpdate
from app.services.campaigns import create_campaign, list_campaigns, get_campaign, update_campaign, delete_campaign

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

@router.post("/", response_model=CampaignRead)
async def create_new_campaign(
    campaign: CampaignCreate,
    session: AsyncSession = Depends(get_session)
):
    settings = {
        "subject": campaign.subject,
        "from_email": campaign.from_email,
        "from_name": campaign.from_name,
        "content": campaign.content,
        "contact_ids": campaign.contact_ids or [],
    }
    return await create_campaign(
        session=session,
        name=campaign.name,
        goal="General",
        campaign_type=campaign.type,
        segment_id=campaign.segment_id,
        settings=settings,
    )

@router.get("/", response_model=List[CampaignRead])
async def read_campaigns(
    status: Optional[CampaignStatus] = None,
    session: AsyncSession = Depends(get_session)
):
    return await list_campaigns(session, status)

@router.get("/{campaign_id}", response_model=CampaignRead)
async def read_campaign(
    campaign_id: str,
    session: AsyncSession = Depends(get_session)
):
    campaign = await get_campaign(session, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign

@router.put("/{campaign_id}", response_model=CampaignRead)
async def update_existing_campaign(
    campaign_id: str,
    campaign: CampaignUpdate,
    session: AsyncSession = Depends(get_session)
):
    updated_campaign = await update_campaign(session, campaign_id, campaign)
    if not updated_campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return updated_campaign

@router.delete("/{campaign_id}", response_model=CampaignRead)
async def delete_existing_campaign(
    campaign_id: str,
    session: AsyncSession = Depends(get_session)
):
    deleted_campaign = await delete_campaign(session, campaign_id)
    if not deleted_campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return deleted_campaign