from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime

from app.db import get_session
from app.models.event import Event, EventType
from app.schemas.analytics import AnalyticsSummary, CampaignPerformance, DailySending
from app.services.analytics import get_analytics_summary, get_campaign_performance, get_daily_sending

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/summary", response_model=AnalyticsSummary)
async def read_analytics_summary(
    session: AsyncSession = Depends(get_session)
):
    return await get_analytics_summary(session)

@router.get("/campaigns", response_model=List[CampaignPerformance])
async def read_campaign_performance(
    session: AsyncSession = Depends(get_session)
):
    return await get_campaign_performance(session)

@router.get("/daily", response_model=List[DailySending])
async def read_daily_sending(
    days: int = 7,
    session: AsyncSession = Depends(get_session)
):
    return await get_daily_sending(session, days)