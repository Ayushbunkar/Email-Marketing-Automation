"""Dispatcher service for sending emails with all guardrails."""

import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, List

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.campaign import Campaign, CampaignStatus
from app.models.campaign_step import CampaignStep
from app.models.contact import Contact, ContactStatus
from app.models.event import Event, EventType
from app.models.message import Message, MessageStatus
from app.providers.base import SendRequest
from app.providers.mock import MockProvider
from app.providers.resend import ResendProvider
from app.services.suppression import is_suppressed
from app.services.templates import render_template


def get_provider():
    """Get the configured email provider."""
    if settings.EMAIL_PROVIDER == "resend":
        return ResendProvider()
    return MockProvider()


async def check_global_circuit_breaker(session: AsyncSession) -> bool:
    """Check if global circuit breaker should pause all sending.

    Returns True if sending should be paused.
    """
    # Check bounce rate
    day_ago = datetime.utcnow() - timedelta(days=1)

    result = await session.execute(
        select(func.count(Message.id))
        .where(Message.status == MessageStatus.FAILED)
        .where(Message.created_at >= day_ago)
    )
    failed_count = result.scalar_one()

    result = await session.execute(
        select(func.count(Message.id)).where(Message.created_at >= day_ago)
    )
    total_count = result.scalar_one()

    if total_count > 0:
        bounce_rate = failed_count / total_count
        if bounce_rate > settings.AUTO_PAUSE_BOUNCE_RATE:
            return True

    # Check complaint rate
    result = await session.execute(
        select(func.count(Event.id))
        .where(Event.type == EventType.COMPLAINT)
        .where(Event.occurred_at >= day_ago)
    )
    complaint_count = result.scalar_one()

    if total_count > 0:
        complaint_rate = complaint_count / total_count
        if complaint_rate > settings.AUTO_PAUSE_COMPLAINT_RATE:
            return True

    return False


async def check_hourly_cap(session: AsyncSession) -> bool:
    """Check if hourly send cap is exceeded."""
    hour_ago = datetime.utcnow() - timedelta(hours=1)

    result = await session.execute(
        select(func.count(Message.id))
        .where(Message.status.in_([MessageStatus.SENT, MessageStatus.DELIVERED]))
        .where(Message.sent_at >= hour_ago)
    )
    count = result.scalar_one()

    return count >= settings.MAX_SENDS_PER_HOUR


async def check_daily_cap(session: AsyncSession) -> bool:
    """Check if daily send cap is exceeded."""
    day_ago = datetime.utcnow() - timedelta(days=1)

    result = await session.execute(
        select(func.count(Message.id))
        .where(Message.status.in_([MessageStatus.SENT, MessageStatus.DELIVERED]))
        .where(Message.sent_at >= day_ago)
    )
    count = result.scalar_one()

    return count >= settings.MAX_SENDS_PER_DAY


async def check_weekly_contact_cap(
    session: AsyncSession,
    contact_id: str,
) -> bool:
    """Check if contact has exceeded weekly send limit."""
    week_ago = datetime.utcnow() - timedelta(days=7)

    result = await session.execute(
        select(func.count(Message.id))
        .where(Message.contact_id == contact_id)
        .where(Message.status.in_([MessageStatus.SENT, MessageStatus.DELIVERED]))
        .where(Message.scheduled_for >= week_ago)
    )
    count = result.scalar_one()

    return count >= settings.MAX_EMAILS_PER_CONTACT_PER_WEEK


async def get_due_messages(session: AsyncSession, limit: int = 100) -> List[Message]:
    """Get messages that are due to send, respecting all guardrails.

    Returns messages sorted by scheduled_for, with contact and template loaded.
    """
    now = datetime.utcnow()

    # Build query with all filters
    query = (
        select(Message)
        .options(
            selectinload(Message.contact),
            selectinload(Message.template),
        )
        .where(Message.status == MessageStatus.APPROVED)
        .where(Message.scheduled_for <= now)
        .order_by(Message.scheduled_for)
        .limit(limit)
        .with_for_update(skip_locked=True)
    )

    result = await session.execute(query)
    messages = list(result.scalars().all())

    # Filter out suppressed contacts and check caps
    due_messages = []
    for message in messages:
        # Check if contact is suppressed
        if await is_suppressed(session, message.contact.email):
            message.status = MessageStatus.SUPPRESSED
            continue

        # Check contact weekly cap
        if await check_weekly_contact_cap(session, message.contact_id):
            # Reschedule for later
            message.scheduled_for = datetime.utcnow() + timedelta(days=7)
            continue

        due_messages.append(message)

    return due_messages


async def render_message_with_template(
    session: AsyncSession,
    message: Message,
) -> Dict[str, str]:
    """Render a message using its template.

    Returns dict with subject, html, text, and preheader.
    """
    template = message.template

    if not template:
        raise ValueError("Message has no template")

    # Get contact data
    contact = message.contact

    contact_data = {
        "first_name": contact.first_name or "",
        "last_name": contact.last_name or "",
        "email": contact.email,
        "company": contact.company or "",
        "lifecycle_stage": contact.lifecycle_stage,
        "attributes": contact.attributes or {},
    }

    return render_template(template, contact_data)


async def create_send_request(
    session: AsyncSession,
    message: Message,
    rendered: Dict[str, str],
) -> SendRequest:
    """Create a SendRequest for a message."""
    # Generate unsubscribe link
    unsubscribe_token = generate_unsubscribe_token(message.contact_id)

    # Build headers
    headers = {
        "List-Unsubscribe": f"<{settings.BASE_URL}/unsubscribe/{unsubscribe_token}>",
        "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
    }

    return SendRequest(
        to_email=message.contact.email,
        to_name=message.contact.first_name,
        from_email=settings.FROM_EMAIL,
        from_name=settings.FROM_NAME,
        reply_to=settings.REPLY_TO_EMAIL,
        subject=rendered["subject"],
        html=rendered["html"],
        text=rendered["text"],
        headers=headers,
        idempotency_key=str(message.id),
    )


def generate_unsubscribe_token(contact_id: str) -> str:
    """Generate a signed unsubscribe token."""
    # Simple HMAC-based token
    message = str(contact_id)
    signature = hmac.new(
        settings.SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"{contact_id}:{signature}"


def verify_unsubscribe_token(contact_id: str, token: str) -> bool:
    """Verify an unsubscribe token."""
    expected = generate_unsubscribe_token(contact_id)
    return hmac.compare_digest(token, expected)


async def send_message(
    session: AsyncSession,
    message: Message,
) -> bool:
    """Send a message via the configured provider.

    This is the ONLY function that should call provider.send().
    All guardrails are enforced before this is called.
    """
    # Final assertion: contact must not be suppressed
    if await is_suppressed(session, message.contact.email):
        message.status = MessageStatus.SUPPRESSED
        await session.commit()
        return False

    # Render message
    try:
        rendered = await render_message_with_template(session, message)
    except Exception as e:
        message.status = MessageStatus.FAILED
        message.error = str(e)
        await session.commit()
        return False

    # Create send request
    try:
        req = await create_send_request(session, message, rendered)
    except Exception as e:
        message.status = MessageStatus.FAILED
        message.error = str(e)
        await session.commit()
        return False

    # Send via provider
    provider = get_provider()
    result = await provider.send(req)

    if result.accepted:
        message.status = MessageStatus.SENT
        message.provider_message_id = result.provider_message_id
        message.sent_at = datetime.utcnow()

        # Record delivery event
        event = Event(
            message_id=message.id,
            contact_id=message.contact_id,
            type=EventType.DELIVERED,
            payload={"provider_message_id": result.provider_message_id},
            occurred_at=datetime.utcnow(),
        )
        session.add(event)

        # Update contact's last emailed at
        message.contact.last_emailed_at = datetime.utcnow()

        await session.commit()
        return True
    else:
        message.status = MessageStatus.FAILED
        message.error = result.error
        await session.commit()
        return False


async def process_scheduled_messages(session: AsyncSession) -> int:
    """Process all scheduled messages, respecting all guardrails.

    Returns the number of messages sent.
    """
    # Check global circuit breaker
    if await check_global_circuit_breaker(session):
        # Pause all campaigns
        await session.execute(
            select(Campaign).where(Campaign.status == CampaignStatus.RUNNING)
        )
        # TODO: Pause campaigns and create notification
        return 0

    # Check hourly cap
    if await check_hourly_cap(session):
        return 0

    # Check daily cap
    if await check_daily_cap(session):
        return 0

    # Get due messages
    messages = await get_due_messages(session)

    sent = 0
    for message in messages:
        if await send_message(session, message):
            sent += 1

    return sent


async def materialize_campaign(
    session: AsyncSession,
    campaign: Campaign,
    start_time: datetime,
) -> int:
    """Materialize a campaign by creating message records for all contacts.

    Returns the number of messages created.
    """
    from app.services.segments import evaluate_segment

    # Get segment contacts
    if campaign.segment_id:
        contacts = await evaluate_segment(session, campaign.segment_id)
    else:
        # All active contacts
        result = await session.execute(
            select(Contact).where(Contact.status == ContactStatus.ACTIVE)
        )
        contacts = list(result.scalars().all())

    # Get campaign steps
    result = await session.execute(
        select(CampaignStep)
        .where(CampaignStep.campaign_id == campaign.id)
        .order_by(CampaignStep.step_index)
    )
    steps = list(result.scalars().all())

    messages_created = 0

    for contact in contacts:
        # Skip suppressed contacts
        if await is_suppressed(session, contact.email):
            continue

        # Calculate send time for this contact (respecting timezone and quiet hours)
        send_time = calculate_send_time(contact, start_time)

        for step in steps:
            # Create message for this step
            message = Message(
                campaign_id=campaign.id,
                step_index=step.step_index,
                contact_id=contact.id,
                template_id=None,  # Will be set when template is created
                status=MessageStatus.QUEUED,
                scheduled_for=send_time,
            )
            session.add(message)
            messages_created += 1

            # Advance send time for next step
            send_time = send_time + timedelta(hours=step.delay_hours)

    await session.commit()
    return messages_created


def calculate_send_time(contact: Contact, base_time: datetime) -> datetime:
    """Calculate the send time for a contact, respecting timezone and quiet hours.

    Args:
        contact: The contact to schedule for
        base_time: The base time from campaign schedule

    Returns:
        The calculated send time
    """
    # TODO: Implement timezone conversion and quiet hours logic
    # For now, just return the base time
    return base_time


async def pause_campaign(session: AsyncSession, campaign_id: str) -> bool:
    """Pause a running campaign."""
    result = await session.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()

    if not campaign:
        return False

    if campaign.status not in (CampaignStatus.RUNNING, CampaignStatus.SCHEDULED):
        return False

    campaign.status = CampaignStatus.PAUSED

    # Cancel queued messages
    await session.execute(
        select(Message)
        .where(Message.campaign_id == campaign_id)
        .where(Message.status == MessageStatus.QUEUED)
    )
    # TODO: Update message status to CANCELLED

    await session.commit()
    return True


async def resume_campaign(session: AsyncSession, campaign_id: str) -> bool:
    """Resume a paused campaign."""
    result = await session.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()

    if not campaign:
        return False

    if campaign.status != CampaignStatus.PAUSED:
        return False

    campaign.status = CampaignStatus.RUNNING
    await session.commit()
    return True
