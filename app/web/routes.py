"""Web dashboard and API routes."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models.agent import Approval, ApprovalStatus, ApprovalSubject
from app.models.campaign import Campaign, CampaignStatus, CampaignType
from app.models.contact import ContactStatus, LifecycleStage
from app.models.message import Message, MessageStatus
from app.services.campaigns import create_campaign, list_campaigns
from app.services.contacts import get_contact_by_email, search_contacts, upsert_contact
from app.services.suppression import suppress_contact_from_event

router = APIRouter(prefix="/api/v1", tags=["api"])


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@router.get("/campaigns", response_model=None)
async def list_campaigns_endpoint(
    status: Optional[CampaignStatus] = None,
    session: AsyncSession = Depends(get_session),
):
    """List campaigns."""
    return await list_campaigns(session, status)


@router.post("/campaigns", response_model=None)
async def create_campaign_endpoint(
    name: str,
    goal: str,
    campaign_type: CampaignType,
    segment_id: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
):
    """Create a new campaign."""
    return await create_campaign(session, name, goal, campaign_type, segment_id)


@router.get("/contacts", response_model=None)
async def search_contacts_endpoint(
    stage: Optional[LifecycleStage] = None,
    status: Optional[ContactStatus] = None,
    text: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
):
    """Search contacts."""
    return await search_contacts(session, stage, status, text)


@router.get("/contacts/{email}", response_model=None)
async def get_contact_endpoint(
    email: str,
    session: AsyncSession = Depends(get_session),
):
    """Get a contact by email."""
    contact = await get_contact_by_email(session, email)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.post("/contacts", response_model=None)
async def upsert_contact_endpoint(
    email: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    company: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
):
    """Upsert a contact."""
    return await upsert_contact(session, email, first_name, last_name, company)


@router.get("/messages", response_model=None)
async def get_messages_endpoint(
    status: Optional[MessageStatus] = None,
    session: AsyncSession = Depends(get_session),
):
    """Get messages."""
    if status:
        result = await session.execute(select(Message).where(Message.status == status))
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

    result = await session.execute(select(Message).where(Message.id == contact_id))
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    success = await send_message(session, message)
    if success:
        return JSONResponse({"status": "sent"})
    else:
        raise HTTPException(status_code=500, detail="Failed to send message")


# --- Webhook Routes ---


@router.post("/webhooks/email")
async def email_webhook_endpoint(
    event_type: str,
    message_id: Optional[str] = None,
    contact_email: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
) -> JSONResponse:
    """Handle email provider webhooks for events like bounce, complaint, unsubscribe."""
    # Suppress contact based on event type
    if contact_email:
        await suppress_contact_from_event(session, contact_email, event_type)

    return JSONResponse({"status": "received"})


@router.get("/unsubscribe/{token}")
async def unsubscribe_get_endpoint(
    token: str,
    session: AsyncSession = Depends(get_session),
) -> JSONResponse:
    """Display unsubscribe confirmation page."""
    return JSONResponse(
        {
            "status": "confirm",
            "message": "Click POST to confirm unsubscribe",
            "token": token,
        }
    )


@router.post("/unsubscribe/{token}")
async def unsubscribe_post_endpoint(
    token: str,
    session: AsyncSession = Depends(get_session),
) -> JSONResponse:
    """Process unsubscribe confirmation."""
    # In a real implementation, verify the token and suppress the contact
    return JSONResponse(
        {
            "status": "unsubscribed",
            "message": "You have been unsubscribed",
        }
    )


# --- Approval Routes ---


@router.get("/approvals", response_model=None)
async def list_approvals_endpoint(
    status: Optional[ApprovalStatus] = None,
    session: AsyncSession = Depends(get_session),
):
    """List approvals with optional status filter."""
    query = select(Approval)

    if status:
        query = query.where(Approval.status == status)

    result = await session.execute(query)
    return list(result.scalars().all())


@router.post("/approvals/{approval_id}/approve")
async def approve_endpoint(
    approval_id: str,
    notes: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
) -> JSONResponse:
    """Approve an item."""
    result = await session.execute(select(Approval).where(Approval.id == approval_id))
    approval = result.scalar_one_or_none()

    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    approval.status = ApprovalStatus.APPROVED
    approval.decided_by = "operator"
    approval.decided_at = datetime.utcnow()
    approval.notes = notes
    await session.commit()

    return JSONResponse(
        {
            "status": "approved",
            "approval_id": approval_id,
        }
    )


@router.post("/approvals/{approval_id}/reject")
async def reject_endpoint(
    approval_id: str,
    notes: str,
    session: AsyncSession = Depends(get_session),
) -> JSONResponse:
    """Reject an item."""
    result = await session.execute(select(Approval).where(Approval.id == approval_id))
    approval = result.scalar_one_or_none()

    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    approval.status = ApprovalStatus.REJECTED
    approval.decided_by = "operator"
    approval.decided_at = datetime.utcnow()
    approval.notes = notes
    await session.commit()

    return JSONResponse(
        {
            "status": "rejected",
            "approval_id": approval_id,
        }
    )


@router.post("/approvals/campaign/{campaign_id}/create")
async def create_campaign_approval_endpoint(
    campaign_id: str,
    summary: str,
    session: AsyncSession = Depends(get_session),
) -> JSONResponse:
    """Create an approval for a campaign."""
    from uuid import uuid4

    # Check if campaign exists
    result = await session.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Check if approval already exists
    result = await session.execute(
        select(Approval).where(
            Approval.subject_type == ApprovalSubject.CAMPAIGN,
            Approval.subject_id == campaign_id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        return JSONResponse(
            {
                "status": "existing",
                "approval_id": str(existing.id),
            }
        )

    # Create approval
    approval = Approval(
        id=uuid4(),
        subject_type=ApprovalSubject.CAMPAIGN,
        subject_id=campaign_id,
        status=ApprovalStatus.PENDING,
        summary=summary,
    )
    session.add(approval)
    await session.commit()

    return JSONResponse(
        {
            "status": "created",
            "approval_id": str(approval.id),
        }
    )
