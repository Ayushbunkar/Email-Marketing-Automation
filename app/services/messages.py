"""Message service for sending and tracking emails."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config import settings
from app.models.contact import Contact, ContactStatus
from app.models.event import Event, EventType
from app.models.message import Message, MessageStatus
from app.models.suppression import Suppression
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
    result = await session.execute(select(Contact).where(Contact.id == contact_id))
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
    step_index: Optional[int],
    contact_id: str,
    template_id: Optional[str],
    scheduled_for: datetime,
    status: MessageStatus = MessageStatus.QUEUED,
) -> Message:
    """Create a message record."""
    message = Message(
        campaign_id=campaign_id,
        step_index=step_index,
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
    result = await session.execute(select(Message).where(Message.id == message_id))
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
        await update_message_status(
            session, message.id, MessageStatus.FAILED, "Contact not found"
        )
        return False

    # Get template
    from app.models.template import Template
    result = await session.execute(select(Template).where(Template.id == message.template_id))
    msg = result.scalar_one_or_none()
    if not msg:
        await update_message_status(
            session, message.id, MessageStatus.FAILED, "Template not found"
        )
        return False

    # Get provider
    provider = get_provider()

    # Fetch the campaign to get the from_email
    from app.models.campaign import Campaign
    camp_result = await session.execute(select(Campaign).where(Campaign.id == message.campaign_id))
    campaign = camp_result.scalar_one_or_none()
    
    # Use campaign's from_email if set, otherwise fallback to settings.
    # Note: Brevo requires the from_email to be authenticated.
    from_email = campaign.from_email if campaign and campaign.from_email else settings.FROM_EMAIL
    
    # Create send request
    import markdown
    raw_html = markdown.markdown(msg.body_markdown) if msg.body_markdown else ""
    
    unsubscribe_url = f"{settings.BASE_URL}/unsubscribe?email={contact.email}"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #eaeaea; font-size: 12px; color: #666; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            {raw_html}
            <div class="footer">
                <p>This email was sent to <strong>{contact.email}</strong></p>
                <p>{settings.COMPANY_POSTAL_ADDRESS}</p>
                <p>If you no longer wish to receive these emails, you can <a href="{unsubscribe_url}">unsubscribe here</a>.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_body = msg.body_markdown or ""
    text_body += f"\n\n---\nThis email was sent to {contact.email}\n{settings.COMPANY_POSTAL_ADDRESS}\nUnsubscribe: {unsubscribe_url}"
    
    req = SendRequest(
        to_email=contact.email,
        to_name=contact.first_name,
        from_email=from_email,
        from_name="Pixel Punch",
        reply_to=from_email,
        subject=msg.subject or "Notification from Pixel Punch",
        html=html_body,
        text=text_body,
        headers={
            "List-Unsubscribe": f"<{unsubscribe_url}>",
            "List-Unsubscribe-Post": "List-Unsubscribe=One-Click"
        },
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
        await update_message_status(
            session, message.id, MessageStatus.FAILED, result.error
        )
        return False


def get_provider():
    """Get the configured email provider."""
    if settings.EMAIL_PROVIDER == "resend":
        return ResendProvider()
    elif settings.EMAIL_PROVIDER == "brevo":
        from app.providers.brevo import BrevoProvider
        return BrevoProvider()
    return MockProvider()
