"""Analytics service for email marketing metrics."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact
from app.models.event import Event, EventType
from app.models.message import Message, MessageStatus


async def get_campaign_metrics(
    session: AsyncSession,
    campaign_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Get metrics for a campaign.

    Args:
        session: Database session
        campaign_id: Campaign ID
        start_date: Optional start date filter
        end_date: Optional end date filter

    Returns:
        Dictionary with campaign metrics
    """
    # Build query filters
    filters = [Message.campaign_id == campaign_id]
    if start_date:
        filters.append(Message.scheduled_for >= start_date)
    if end_date:
        filters.append(Message.scheduled_for <= end_date)

    # Total messages
    result = await session.execute(select(func.count(Message.id)).where(and_(*filters)))
    total = result.scalar_one()

    # Sent messages
    result = await session.execute(
        select(func.count(Message.id)).where(
            and_(*filters, Message.status == MessageStatus.SENT)
        )
    )
    sent = result.scalar_one()

    # Delivered messages
    result = await session.execute(
        select(func.count(Event.id))
        .join(Message)
        .where(
            and_(
                Message.campaign_id == campaign_id,
                Event.type == EventType.DELIVERED,
                *([Message.scheduled_for >= start_date] if start_date else []),
                *([Message.scheduled_for <= end_date] if end_date else []),
            )
        )
    )
    delivered = result.scalar_one()

    # Opened messages
    result = await session.execute(
        select(func.count(Event.id))
        .join(Message)
        .where(
            and_(
                Message.campaign_id == campaign_id,
                Event.type == EventType.OPEN,
                *([Message.scheduled_for >= start_date] if start_date else []),
                *([Message.scheduled_for <= end_date] if end_date else []),
            )
        )
    )
    opened = result.scalar_one()

    # Clicked messages
    result = await session.execute(
        select(func.count(Event.id))
        .join(Message)
        .where(
            and_(
                Message.campaign_id == campaign_id,
                Event.type == EventType.CLICK,
                *([Message.scheduled_for >= start_date] if start_date else []),
                *([Message.scheduled_for <= end_date] if end_date else []),
            )
        )
    )
    clicked = result.scalar_one()

    # Bounced messages
    result = await session.execute(
        select(func.count(Message.id)).where(
            and_(*filters, Message.status == MessageStatus.FAILED)
        )
    )
    bounced = result.scalar_one()

    # Unsubscribed
    result = await session.execute(
        select(func.count(Event.id))
        .join(Message)
        .where(
            and_(
                Message.campaign_id == campaign_id,
                Event.type == EventType.UNSUBSCRIBE,
                *([Message.scheduled_for >= start_date] if start_date else []),
                *([Message.scheduled_for <= end_date] if end_date else []),
            )
        )
    )
    unsubscribed = result.scalar_one()

    # Complaints
    result = await session.execute(
        select(func.count(Event.id))
        .join(Message)
        .where(
            and_(
                Message.campaign_id == campaign_id,
                Event.type == EventType.COMPLAINT,
                *([Message.scheduled_for >= start_date] if start_date else []),
                *([Message.scheduled_for <= end_date] if end_date else []),
            )
        )
    )
    complaints = result.scalar_one()

    # Calculate rates
    delivery_rate = (delivered / sent * 100) if sent > 0 else 0
    open_rate = (opened / sent * 100) if sent > 0 else 0
    click_rate = (clicked / opened * 100) if opened > 0 else 0
    bounce_rate = (bounced / sent * 100) if sent > 0 else 0
    unsubscribe_rate = (unsubscribed / sent * 100) if sent > 0 else 0
    complaint_rate = (complaints / sent * 100) if sent > 0 else 0

    return {
        "campaign_id": campaign_id,
        "total": total,
        "sent": sent,
        "delivered": delivered,
        "opened": opened,
        "clicked": clicked,
        "bounced": bounced,
        "unsubscribed": unsubscribed,
        "complaints": complaints,
        "delivery_rate": round(delivery_rate, 2),
        "open_rate": round(open_rate, 2),
        "click_rate": round(click_rate, 2),
        "bounce_rate": round(bounce_rate, 2),
        "unsubscribe_rate": round(unsubscribe_rate, 2),
        "complaint_rate": round(complaint_rate, 2),
    }


async def get_account_metrics(
    session: AsyncSession,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Get account-wide metrics.

    Args:
        session: Database session
        start_date: Optional start date filter
        end_date: Optional end date filter

    Returns:
        Dictionary with account metrics
    """
    # Build date filters
    filters = []
    if start_date:
        filters.append(Event.occurred_at >= start_date)
    if end_date:
        filters.append(Event.occurred_at <= end_date)

    # Total sent
    result = await session.execute(
        select(func.count(Message.id)).where(
            and_(
                Message.status == MessageStatus.SENT,
                *filters,
            )
        )
    )
    total_sent = result.scalar_one()

    # Total delivered
    result = await session.execute(
        select(func.count(Event.id)).where(
            and_(
                Event.type == EventType.DELIVERED,
                *filters,
            )
        )
    )
    total_delivered = result.scalar_one()

    # Total opened
    result = await session.execute(
        select(func.count(Event.id)).where(
            and_(
                Event.type == EventType.OPEN,
                *filters,
            )
        )
    )
    total_opened = result.scalar_one()

    # Total clicked
    result = await session.execute(
        select(func.count(Event.id)).where(
            and_(
                Event.type == EventType.CLICK,
                *filters,
            )
        )
    )
    total_clicked = result.scalar_one()

    # Total bounced
    result = await session.execute(
        select(func.count(Message.id)).where(
            and_(
                Message.status == MessageStatus.FAILED,
                *filters,
            )
        )
    )
    total_bounced = result.scalar_one()

    # Total unsubscribed
    result = await session.execute(
        select(func.count(Event.id)).where(
            and_(
                Event.type == EventType.UNSUBSCRIBE,
                *filters,
            )
        )
    )
    total_unsubscribed = result.scalar_one()

    # Total complaints
    result = await session.execute(
        select(func.count(Event.id)).where(
            and_(
                Event.type == EventType.COMPLAINT,
                *filters,
            )
        )
    )
    total_complaints = result.scalar_one()

    # Calculate rates
    delivery_rate = (total_delivered / total_sent * 100) if total_sent > 0 else 0
    open_rate = (total_opened / total_sent * 100) if total_sent > 0 else 0
    click_rate = (total_clicked / total_opened * 100) if total_opened > 0 else 0
    bounce_rate = (total_bounced / total_sent * 100) if total_sent > 0 else 0
    unsubscribe_rate = (total_unsubscribed / total_sent * 100) if total_sent > 0 else 0
    complaint_rate = (total_complaints / total_sent * 100) if total_sent > 0 else 0

    return {
        "total_sent": total_sent,
        "total_delivered": total_delivered,
        "total_opened": total_opened,
        "total_clicked": total_clicked,
        "total_bounced": total_bounced,
        "total_unsubscribed": total_unsubscribed,
        "total_complaints": total_complaints,
        "delivery_rate": round(delivery_rate, 2),
        "open_rate": round(open_rate, 2),
        "click_rate": round(click_rate, 2),
        "bounce_rate": round(bounce_rate, 2),
        "unsubscribe_rate": round(unsubscribe_rate, 2),
        "complaint_rate": round(complaint_rate, 2),
    }


async def get_daily_rollups(
    session: AsyncSession,
    days: int = 30,
) -> List[Dict[str, Any]]:
    """Get daily rollup metrics.

    Args:
        session: Database session
        days: Number of days to include

    Returns:
        List of daily metrics
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Get all days in range
    days_list = []
    for i in range(days):
        day_start = start_date + timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        days_list.append((day_start, day_end))

    # Get metrics for each day
    rollups = []
    for day_start, day_end in days_list:
        # Sent
        result = await session.execute(
            select(func.count(Message.id)).where(
                and_(
                    Message.status == MessageStatus.SENT,
                    Message.scheduled_for >= day_start,
                    Message.scheduled_for < day_end,
                )
            )
        )
        sent = result.scalar_one()

        # Delivered
        result = await session.execute(
            select(func.count(Event.id)).where(
                and_(
                    Event.type == EventType.DELIVERED,
                    Event.occurred_at >= day_start,
                    Event.occurred_at < day_end,
                )
            )
        )
        delivered = result.scalar_one()

        # Opened
        result = await session.execute(
            select(func.count(Event.id)).where(
                and_(
                    Event.type == EventType.OPEN,
                    Event.occurred_at >= day_start,
                    Event.occurred_at < day_end,
                )
            )
        )
        opened = result.scalar_one()

        # Clicked
        result = await session.execute(
            select(func.count(Event.id)).where(
                and_(
                    Event.type == EventType.CLICK,
                    Event.occurred_at >= day_start,
                    Event.occurred_at < day_end,
                )
            )
        )
        clicked = result.scalar_one()

        rollups.append(
            {
                "date": day_start.strftime("%Y-%m-%d"),
                "sent": sent,
                "delivered": delivered,
                "opened": opened,
                "clicked": clicked,
                "delivery_rate": round((delivered / sent * 100) if sent > 0 else 0, 2),
                "open_rate": round((opened / sent * 100) if sent > 0 else 0, 2),
                "click_rate": round((clicked / opened * 100) if opened > 0 else 0, 2),
            }
        )

    return rollups


async def get_variant_metrics(
    session: AsyncSession,
    campaign_id: str,
) -> List[Dict[str, Any]]:
    """Get metrics for A/B test variants.

    Args:
        session: Database session
        campaign_id: Campaign ID

    Returns:
        List of variant metrics
    """
    # Get templates for campaign
    result = await session.execute(
        select(Message.template_id, func.count(Message.id).label("count"))
        .where(Message.campaign_id == campaign_id)
        .where(Message.status == MessageStatus.SENT)
        .group_by(Message.template_id)
    )
    variants = result.fetchall()

    variant_metrics = []
    for variant in variants:
        template_id = variant.template_id
        sent = variant.count

        # Get opens for this variant
        result = await session.execute(
            select(func.count(Event.id)).where(
                and_(
                    Event.message_id == Message.id,
                    Message.template_id == template_id,
                    Event.type == EventType.OPEN,
                )
            )
        )
        opened = result.scalar_one()

        # Get clicks for this variant
        result = await session.execute(
            select(func.count(Event.id)).where(
                and_(
                    Event.message_id == Message.id,
                    Message.template_id == template_id,
                    Event.type == EventType.CLICK,
                )
            )
        )
        clicked = result.scalar_one()

        variant_metrics.append(
            {
                "template_id": template_id,
                "sent": sent,
                "opened": opened,
                "clicked": clicked,
                "open_rate": round((opened / sent * 100) if sent > 0 else 0, 2),
                "click_rate": round((clicked / opened * 100) if opened > 0 else 0, 2),
            }
        )

    return variant_metrics


async def get_contact_metrics(
    session: AsyncSession,
    contact_id: str,
) -> Dict[str, Any]:
    """Get metrics for a specific contact.

    Args:
        session: Database session
        contact_id: Contact ID

    Returns:
        Dictionary with contact metrics
    """
    # Get contact
    result = await session.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()

    if not contact:
        return {"error": "Contact not found"}

    # Get message count
    result = await session.execute(
        select(func.count(Message.id)).where(Message.contact_id == contact_id)
    )
    total_messages = result.scalar_one()

    # Get sent count
    result = await session.execute(
        select(func.count(Message.id)).where(
            and_(
                Message.contact_id == contact_id,
                Message.status == MessageStatus.SENT,
            )
        )
    )
    sent_count = result.scalar_one()

    # Get delivered count
    result = await session.execute(
        select(func.count(Event.id)).where(
            and_(
                Event.contact_id == contact_id,
                Event.type == EventType.DELIVERED,
            )
        )
    )
    delivered_count = result.scalar_one()

    # Get open count
    result = await session.execute(
        select(func.count(Event.id)).where(
            and_(
                Event.contact_id == contact_id,
                Event.type == EventType.OPEN,
            )
        )
    )
    open_count = result.scalar_one()

    # Get click count
    result = await session.execute(
        select(func.count(Event.id)).where(
            and_(
                Event.contact_id == contact_id,
                Event.type == EventType.CLICK,
            )
        )
    )
    click_count = result.scalar_one()

    # Get bounce count
    result = await session.execute(
        select(func.count(Message.id)).where(
            and_(
                Message.contact_id == contact_id,
                Message.status == MessageStatus.FAILED,
            )
        )
    )
    bounce_count = result.scalar_one()

    return {
        "contact_id": contact_id,
        "email": contact.email,
        "total_messages": total_messages,
        "sent": sent_count,
        "delivered": delivered_count,
        "opened": open_count,
        "clicked": click_count,
        "bounced": bounce_count,
        "delivery_rate": round(
            (delivered_count / sent_count * 100) if sent_count > 0 else 0, 2
        ),
        "open_rate": round((open_count / sent_count * 100) if sent_count > 0 else 0, 2),
        "click_rate": round(
            (click_count / open_count * 100) if open_count > 0 else 0, 2
        ),
    }
