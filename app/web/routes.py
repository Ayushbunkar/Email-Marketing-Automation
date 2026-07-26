"""Web dashboard and API routes."""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.db import get_session
from app.models.campaign import Campaign, CampaignStatus, CampaignType
from app.models.contact import Contact, LifecycleStage, ContactStatus
from app.models.message import Message, MessageStatus
from app.services.campaigns import create_campaign, get_campaign, list_campaigns
from app.services.contacts import search_contacts, get_contact_by_email, upsert_contact
from app.services.messages import create_message, get_messages_to_send

router = APIRouter(prefix="/api/v1", tags=["api"])


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@router.get("/campaigns")
async def list_campaigns_endpoint(
    status: Optional[CampaignStatus] = None,
    session: AsyncSession = Depends(get_session),
) -> List[Campaign]:
    """List campaigns."""
    return await list_campaigns(session, status)


@router.post("/campaigns")
async def create_campaign_endpoint(
    name: str,
    goal: str,
    campaign_type: CampaignType,
    segment_id: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
) -> Campaign:
    """Create a new campaign."""
    return await create_campaign(session, name, goal, campaign_type, segment_id)


@router.get("/contacts")
async def search_contacts_endpoint(
    stage: Optional[LifecycleStage] = None,
    status: Optional[ContactStatus] = None,
    text: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
) -> List[Contact]:
    """Search contacts."""
    return await search_contacts(session, stage, status, text)


@router.get("/contacts/{email}")
async def get_contact_endpoint(
    email: str,
    session: AsyncSession = Depends(get_session),
) -> Contact:
    """Get a contact by email."""
    contact = await get_contact_by_email(session, email)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.post("/contacts")
async def upsert_contact_endpoint(
    email: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    company: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
) -> Contact:
    """Upsert a contact."""
    return await upsert_contact(session, email, first_name, last_name, company)


@router.get("/messages")
async def get_messages_endpoint(
    status: Optional[MessageStatus] = None,
    session: AsyncSession = Depends(get_session),
) -> List[Message]:
    """Get messages."""
    if status:
        result = await session.execute(
            select(Message).where(Message.status == status)
        )
    else:
        result = await session.execute(select(Message))
    return list(result.scalars().all())


@router.post("/messages/send")
async def send_message_endpoint(
    contact_id: str,
    campaign_id: Optional[str] = None,
    background_tasks: BackgroundTasks = None,
    session: AsyncSession = Depends(get_session),
) -> JSONResponse:
    """Send a message to a contact."""
    from sqlalchemy import select
    from app.services.messages import send_message

    result = await session.execute(
        select(Message).where(Message.id == contact_id)
    )
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    success = await send_message(session, message)
    if success:
        return JSONResponse({"status": "sent"})
    else:
        raise HTTPException(status_code=500, detail="Failed to send message")