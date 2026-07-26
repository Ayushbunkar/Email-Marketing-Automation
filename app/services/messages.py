"""Message service for sending and tracking emails."""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.config import settings
from app.models.message import Message, MessageStatus
from app.models.campaign import Campaign, CampaignStatus
from app.models.contact import Contact, ContactStatus
from app.models.suppression import Suppression, SuppressionReason
from app.models.event import Event, EventType
from app.providers.base import SendRequest
from app.providers.mock import MockProvider
from app.providers.resend import ResendProvider


async def can_send_to_contact(
    session: AsyncSession,
    contact_id: str,
    contact_email: str,
) -> bool:
    """Check if we can send to a contact based on guardrails."""
    # Check if contact is suppressed
    result = await session.execute(
        select(Suppression).where(Suppression.email == contact_email)
    )
    if result.scalar_one_or_none():
        return False

    # Check if contact is active
    result = await session.execute(
        select(Contact).where(Contact.id == contact_id)
    )
    contact = result.scalar_one_or_none()
    if not contact or contact.status != ContactStatus.ACTIVE:
        return False

    # Check weekly send limit
    week_ago = datetime.utcnow() - timedelta(days=7)
    result = await session.execute(
        select(func.count(Message.id))
        .where(Message.contact_id == contact_id)
        .where(Message.status.in_([MessageStatus.SENT, MessageStatus.DELIVERED]))
        .where(Message.scheduled_for >= week_ago)
    )
    if result.scalar_one() >= settings.MAX_EMAILS_PER_CONTACT_PER_WEEK:
        return False

    return True


async def create_message(
    session: AsyncSession,
    campaign_id: Optional[str],
    step_id: Optional[str],
    contact_id: str,
    template_id: Optional[str],
    scheduled_for: datetime,
    status: MessageStatus = MessageStatus.QUEUED,
) -> Message:
    """Create a message record."""
    message = Message(
        campaign_id=campaign_id,
        step_id=step_id,
        contact_id=contact_id,
        template_id=template_id,
        status=status,
        scheduled_for=scheduled_for,
    )
    session.add(message)
    await session.commit()
    return message


async def get_messages_to_send(
    session: AsyncSession,
    limit: int = 100,
) -> List[Message]:
    """Get messages ready to send."""
    now = datetime.utcnow()
    result = await session.execute(
        select(Message)
        .where(Message.status == MessageStatus.APPROVED)
        .where(Message.scheduled_for <= now)
        .order_by(Message.scheduled_for)
        .limit(limit)
    )
    return list(result.scalars().all())


async def update_message_status(
    session: AsyncSession,
    message_id: str,
    status: MessageStatus,
    error: Optional[str] = None,
) -> Optional[Message]:
    """Update message status."""
    result = await session.execute(
        select(Message).where(Message.id == message_id)
    )
    message = result.scalar_one_or_none()
    if message:
        message.status = status
        if error:
            message.error = error
        await session.commit()
    return message


async def record_event(
    session: AsyncSession,
    message_id: Optional[str],
    contact_id: Optional[str],
    event_type: EventType,
    payload: Optional[Dict[str, Any]] = None,
) -> Event:
    """Record an email event."""
    event = Event(
        message_id=message_id,
        contact_id=contact_id,
        type=event_type,
        payload=payload or {},
        occurred_at=datetime.utcnow(),
    )
    session.add(event)
    await session.commit()
    return event


async def send_message(
    session: AsyncSession,
    message: Message,
) -> bool:
    """Send a message via the configured provider."""
    # Get contact
    result = await session.execute(
        select(Contact).where(Contact.id == message.contact_id)
    )
    contact = result.scalar_one_or_none()
    if not contact:
        await update_message_status(session, message.id, MessageStatus.FAILED, "Contact not found")
        return False

    # Get template
    result = await session.execute(
        select(Message).where(Message.id == message.id)
    )
    msg = result.scalar_one_or_none()
    if not msg or not msg.template_id:
        await update_message_status(session, message.id, MessageStatus.FAILED, "Template not found")
        return False

    # Get provider
    provider = get_provider()

    # Create send request
    req = SendRequest(
        to_email=contact.email,
        to_name=contact.first_name,
        from_email=settings.FROM_EMAIL,
        from_name=settings.FROM_NAME,
        reply_to=settings.REPLY_TO_EMAIL,
        subject="Test Subject",
        html="<p>Test HTML</p>",
        text="Test text",
        headers={},
        idempotency_key=str(message.id),
    )

    # Send
    result = await provider.send(req)

    if result.accepted:
        await update_message_status(session, message.id, MessageStatus.SENT)
        await record_event(
            session,
            message.id,
            contact.id,
            EventType.DELIVERED,
            {"provider_message_id": result.provider_message_id},
        )
        return True
    else:
        await update_message_status(session, message.id, MessageStatus.FAILED, result.error)
        return False


def get_provider():
    """Get the configured email provider."""
    if settings.EMAIL_PROVIDER == "resend":
        return ResendProvider()
    return MockProvider()