"""Suppression service for managing email suppression list."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.contact import Contact, ContactStatus
from app.models.suppression import Suppression, SuppressionReason


async def is_suppressed(session: AsyncSession, email: str) -> bool:
    """Check if an email is suppressed."""
    result = await session.execute(
        select(Suppression).where(Suppression.email == email)
    )
    return result.scalar_one_or_none() is not None


async def add_suppression(
    session: AsyncSession,
    email: str,
    reason: SuppressionReason,
    source: str,
) -> Suppression:
    """Add an email to the suppression list."""
    suppression = Suppression(
        email=email,
        reason=reason,
        source=source,
    )
    session.add(suppression)
    await session.commit()
    return suppression


async def remove_suppression(session: AsyncSession, email: str) -> bool:
    """Remove an email from the suppression list."""
    result = await session.execute(
        select(Suppression).where(Suppression.email == email)
    )
    suppression = result.scalar_one_or_none()
    if suppression:
        await session.delete(suppression)
        await session.commit()
        return True
    return False


async def suppress_contact_from_event(
    session: AsyncSession,
    email: str,
    event_type: str,
) -> None:
    """Suppress a contact based on event type."""
    reason_map = {
        "bounce_hard": SuppressionReason.HARD_BOUNCE,
        "bounce_soft": SuppressionReason.HARD_BOUNCE,
        "complaint": SuppressionReason.COMPLAINT,
        "unsubscribe": SuppressionReason.UNSUBSCRIBE,
    }

    reason = reason_map.get(event_type, SuppressionReason.MANUAL)
    await add_suppression(session, email, reason, "webhook")
    await update_contact_status(session, email, reason)


async def update_contact_status(
    session: AsyncSession,
    email: str,
    reason: SuppressionReason,
) -> None:
    """Update contact status based on suppression reason."""
    result = await session.execute(select(Contact).where(Contact.email == email))
    contact = result.scalar_one_or_none()
    if contact:
        status_map = {
            SuppressionReason.UNSUBSCRIBE: ContactStatus.UNSUBSCRIBED,
            SuppressionReason.HARD_BOUNCE: ContactStatus.BOUNCED,
            SuppressionReason.COMPLAINT: ContactStatus.COMPLAINED,
            SuppressionReason.MANUAL: ContactStatus.SUPPRESSED,
            SuppressionReason.LEGAL_REQUEST: ContactStatus.SUPPRESSED,
        }
        contact.status = status_map.get(reason, ContactStatus.SUPPRESSED)
        await session.commit()
