"""Celery tasks for Hermes."""

import asyncio
import os
from datetime import datetime, timedelta
from typing import List

from celery import shared_task
from sqlalchemy import select, delete

from app.db import AsyncSession, get_session
from app.models.message import Message, MessageStatus
from app.models.event import Event, EventType
from app.services.messages import send_message, record_event
from app.services.suppression import is_suppressed
from app.providers.mock import MockProvider


@shared_task
def send_scheduled_messages() -> int:
    """Send messages that are scheduled."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_send_scheduled_messages())
    finally:
        loop.close()


async def _send_scheduled_messages() -> int:
    """Send messages that are scheduled."""
    sent = 0
    async with get_session() as session:
        now = datetime.utcnow()
        result = await session.execute(
            select(Message)
            .where(Message.status == MessageStatus.APPROVED)
            .where(Message.scheduled_for <= now)
            .limit(100)
        )
        messages = list(result.scalars().all())

        for message in messages:
            if await send_message(session, message):
                sent += 1

    return sent


@shared_task
def poll_inbound_emails() -> int:
    """Poll IMAP for new inbound emails."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_poll_inbound_emails())
    finally:
        loop.close()


async def _poll_inbound_emails() -> int:
    """Poll IMAP for new inbound emails."""
    from app.providers.inbound_imap import InboundIMAPProvider

    provider = InboundIMAPProvider(
        host=os.getenv("IMAP_HOST", ""),
        port=int(os.getenv("IMAP_PORT", "993")),
        username=os.getenv("IMAP_USER", ""),
        password=os.getenv("IMAP_PASSWORD", ""),
        folder=os.getenv("IMAP_FOLDER", "INBOX"),
    )

    messages = await provider.poll()
    return len(messages)


@shared_task
def cleanup_old_events() -> int:
    """Clean up old events from the database."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_cleanup_old_events())
    finally:
        loop.close()


async def _cleanup_old_events() -> int:
    """Clean up old events from the database."""
    from sqlalchemy import func

    cutoff = datetime.utcnow() - timedelta(days=90)
    deleted = 0

    async with get_session() as session:
        result = await session.execute(
            select(Event.id).where(Event.occurred_at < cutoff).limit(1000)
        )
        event_ids = [row[0] for row in result.fetchall()]

        for event_id in event_ids:
            await session.execute(delete(Event).where(Event.id == event_id))
            deleted += 1

        await session.commit()

    return deleted