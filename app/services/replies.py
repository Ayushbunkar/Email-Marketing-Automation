"""Reply service for managing inbound email replies."""

from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reply import Reply, ReplyStatus, ReplyClass


async def list_replies(
    session: AsyncSession,
    contact_id: Optional[str] = None,
    status: Optional[ReplyStatus] = None,
    classification: Optional[ReplyClass] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Reply]:
    """List replies with optional filters.
    
    Args:
        session: Database session
        contact_id: Optional contact ID filter
        status: Optional status filter
        classification: Optional classification filter
        limit: Maximum results
        offset: Offset for pagination
        
    Returns:
        List of replies
    """
    query = select(Reply)

    if contact_id:
        query = query.where(Reply.contact_id == contact_id)
    if status:
        query = query.where(Reply.status == status)
    if classification:
        query = query.where(Reply.classification == classification)

    query = query.order_by(Reply.received_at.desc()).limit(limit).offset(offset)

    result = await session.execute(query)
    return list(result.scalars().all())


async def get_reply(session: AsyncSession, reply_id: str) -> Optional[Reply]:
    """Get a specific reply.
    
    Args:
        session: Database session
        reply_id: Reply ID
        
    Returns:
        Reply or None
    """
    result = await session.execute(select(Reply).where(Reply.id == reply_id))
    return result.scalar_one_or_none()


async def create_reply(
    session: AsyncSession,
    contact_id: str,
    from_email: str,
    subject: Optional[str] = None,
    body_text: str = "",
    classification: Optional[ReplyClass] = None,
    confidence: Optional[float] = None,
    draft_response: Optional[str] = None,
    handled: bool = False,
    received_at: Optional[Any] = None,
) -> Reply:
    """Create a new reply.
    
    Args:
        session: Database session
        contact_id: Contact ID
        from_email: Sender email
        subject: Optional email subject
        body_text: Email body text
        classification: Optional classification
        confidence: Optional confidence score
        draft_response: Optional draft response
        handled: Whether the reply has been handled
        received_at: When the reply was received
        
    Returns:
        Created reply
    """
    reply = Reply(
        contact_id=contact_id,
        from_email=from_email,
        subject=subject,
        body_text=body_text,
        classification=classification,
        confidence=confidence,
        draft_response=draft_response,
        handled=handled,
        received_at=received_at,
    )
    session.add(reply)
    await session.commit()
    return reply


async def update_reply(
    session: AsyncSession,
    reply_id: str,
    reply_data: Dict[str, Any],
) -> Optional[Reply]:
    """Update a reply.
    
    Args:
        session: Database session
        reply_id: Reply ID
        reply_data: Update data
        
    Returns:
        Updated reply or None
    """
    result = await session.execute(select(Reply).where(Reply.id == reply_id))
    reply = result.scalar_one_or_none()
    
    if reply:
        for key, value in reply_data.items():
            if hasattr(reply, key):
                setattr(reply, key, value)
        await session.commit()
    return reply


async def delete_reply(
    session: AsyncSession,
    reply_id: str,
) -> Optional[Reply]:
    """Delete a reply.
    
    Args:
        session: Database session
        reply_id: Reply ID
        
    Returns:
        Deleted reply or None
    """
    result = await session.execute(select(Reply).where(Reply.id == reply_id))
    reply = result.scalar_one_or_none()
    
    if reply:
        await session.delete(reply)
        await session.commit()
    return reply


async def get_reply_count(
    session: AsyncSession,
    contact_id: Optional[str] = None,
    classification: Optional[ReplyClass] = None,
) -> int:
    """Get reply count with filters.
    
    Args:
        session: Database session
        contact_id: Optional contact ID filter
        classification: Optional classification filter
        
    Returns:
        Count of replies
    """
    query = select(func.count(Reply.id))

    if contact_id:
        query = query.where(Reply.contact_id == contact_id)
    if classification:
        query = query.where(Reply.classification == classification)

    result = await session.execute(query)
    return result.scalar_one()