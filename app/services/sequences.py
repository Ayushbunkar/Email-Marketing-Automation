"""Sequence engine for multi-step email campaigns."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact
from app.models.message import Message, MessageStatus
from app.models.sequence import Sequence, SequenceStatus, SequenceStep
from app.services.suppression import is_suppressed


async def get_next_sequence_step(
    session: AsyncSession,
    sequence: Sequence,
    contact: Contact,
) -> Optional[SequenceStep]:
    """Get the next step for a contact in a sequence.

    Args:
        session: Database session
        sequence: The sequence
        contact: The contact

    Returns:
        The next step or None if sequence is complete
    """
    # Get contact's current step index
    result = await session.execute(
        select(SequenceStep)
        .where(SequenceStep.sequence_id == sequence.id)
        .order_by(SequenceStep.step_index)
    )
    steps = list(result.scalars().all())

    if not steps:
        return None

    # Get contact's progress
    result = await session.execute(
        select(Message)
        .where(Message.contact_id == contact.id)
        .where(Message.campaign_id == sequence.campaign_id)
        .order_by(Message.scheduled_for.desc())
        .limit(1)
    )
    last_message = result.scalar_one_or_none()

    if not last_message:
        # First step
        return steps[0]

    # Find the next step based on last message
    current_step_index = last_message.step_index or 0
    next_index = current_step_index + 1

    if next_index >= len(steps):
        return None  # Sequence complete

    return steps[next_index]


async def should_skip_step(
    session: AsyncSession,
    sequence: Sequence,
    contact: Contact,
    step: SequenceStep,
) -> bool:
    """Check if a step should be skipped based on skip conditions.

    Args:
        session: Database session
        sequence: The sequence
        contact: The contact
        step: The step to check

    Returns:
        True if step should be skipped
    """
    if not step.skip_condition:
        return False

    # Evaluate skip condition
    condition = step.skip_condition

    # Check if contact has already completed this step
    result = await session.execute(
        select(Message)
        .where(Message.contact_id == contact.id)
        .where(Message.campaign_id == sequence.campaign_id)
        .where(Message.step_index == step.step_index)
        .where(Message.status.in_([MessageStatus.SENT, MessageStatus.DELIVERED]))
    )
    if result.scalar_one_or_none():
        return True

    # Check skip condition logic
    if condition.get("type") == "time_since_last_email":
        days = condition.get("days", 0)
        if contact.last_emailed_at:
            days_since = (datetime.utcnow() - contact.last_emailed_at).days
            if days_since < days:
                return True

    return False


async def calculate_delay(
    session: AsyncSession,
    sequence: Sequence,
    contact: Contact,
    step: SequenceStep,
) -> timedelta:
    """Calculate the delay before sending a step.

    Args:
        session: Database session
        sequence: The sequence
        contact: The contact
        step: The step

    Returns:
        The delay timedelta
    """
    # Base delay from step
    delay = timedelta(hours=step.delay_hours)

    # Apply contact-specific adjustments
    if contact.lifecycle_stage == "customer":
        # Customers get emails faster
        delay = delay / 2

    return delay


async def enroll_contact(
    session: AsyncSession,
    sequence_id: str,
    contact_id: str,
    triggered_by: Optional[str] = None,
) -> bool:
    """Enroll a contact in a sequence.

    Args:
        session: Database session
        sequence_id: Sequence ID
        contact_id: Contact ID
        triggered_by: Optional trigger event ID

    Returns:
        True if enrollment was successful
    """
    # Get sequence
    result = await session.execute(select(Sequence).where(Sequence.id == sequence_id))
    sequence = result.scalar_one_or_none()

    if not sequence:
        return False

    # Get contact
    result = await session.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()

    if not contact:
        return False

    # Check if already enrolled
    result = await session.execute(
        select(Message)
        .where(Message.contact_id == contact_id)
        .where(Message.campaign_id == sequence.campaign_id)
        .where(Message.status == MessageStatus.QUEUED)
    )
    if result.scalar_one_or_none():
        return False  # Already enrolled

    # Check if contact is suppressed
    if await is_suppressed(session, contact.email):
        return False

    # Get sequence steps
    result = await session.execute(
        select(SequenceStep)
        .where(SequenceStep.sequence_id == sequence_id)
        .order_by(SequenceStep.step_index)
    )
    steps = list(result.scalars().all())

    if not steps:
        return False

    # Create queued messages for all steps
    now = datetime.utcnow()
    current_time = now

    for step in steps:
        # Calculate delay
        delay = await calculate_delay(session, sequence, contact, step)
        current_time = current_time + delay

        # Check if should skip
        if await should_skip_step(session, sequence, contact, step):
            continue

        # Create message
        message = Message(
            campaign_id=sequence.campaign_id,
            step_index=step.step_index,
            contact_id=contact_id,
            template_id=step.template_id,
            status=MessageStatus.QUEUED,
            scheduled_for=current_time,
            triggered_by=triggered_by,
        )
        session.add(message)

    await session.commit()
    return True


async def complete_sequence(
    session: AsyncSession,
    sequence_id: str,
    contact_id: str,
) -> bool:
    """Mark a sequence as complete for a contact.

    Args:
        session: Database session
        sequence_id: Sequence ID
        contact_id: Contact ID

    Returns:
        True if sequence was completed
    """
    # Get sequence
    result = await session.execute(select(Sequence).where(Sequence.id == sequence_id))
    sequence = result.scalar_one_or_none()

    if not sequence:
        return False

    # Get contact's messages for this sequence
    result = await session.execute(
        select(Message)
        .where(Message.contact_id == contact_id)
        .where(Message.campaign_id == sequence.campaign_id)
    )
    messages = list(result.scalars().all())

    if not messages:
        return False

    # Mark all as completed
    for message in messages:
        if message.status == MessageStatus.QUEUED:
            message.status = MessageStatus.CANCELLED

    await session.commit()
    return True


async def get_sequence_progress(
    session: AsyncSession,
    sequence_id: str,
    contact_id: str,
) -> Dict[str, Any]:
    """Get the progress of a contact in a sequence.

    Args:
        session: Database session
        sequence_id: Sequence ID
        contact_id: Contact ID

    Returns:
        Progress dictionary
    """
    # Get sequence
    result = await session.execute(select(Sequence).where(Sequence.id == sequence_id))
    sequence = result.scalar_one_or_none()

    if not sequence:
        return {"error": "Sequence not found"}

    # Get steps
    result = await session.execute(
        select(SequenceStep)
        .where(SequenceStep.sequence_id == sequence_id)
        .order_by(SequenceStep.step_index)
    )
    steps = list(result.scalars().all())

    # Get contact's messages
    result = await session.execute(
        select(Message)
        .where(Message.contact_id == contact_id)
        .where(Message.campaign_id == sequence.campaign_id)
        .order_by(Message.scheduled_for)
    )
    messages = list(result.scalars().all())

    # Calculate progress
    total_steps = len(steps)
    completed = sum(1 for m in messages if m.status == MessageStatus.SENT)
    in_progress = sum(1 for m in messages if m.status == MessageStatus.QUEUED)

    return {
        "sequence_id": str(sequence.id),
        "contact_id": contact_id,
        "total_steps": total_steps,
        "completed_steps": completed,
        "in_progress_steps": in_progress,
        "status": SequenceStatus.COMPLETED
        if completed >= total_steps
        else SequenceStatus.IN_PROGRESS,
    }


async def create_sequence(
    session: AsyncSession,
    campaign_id: str,
    name: str,
    description: str,
    steps: List[Dict[str, Any]],
    created_by: str = "system",
) -> Sequence:
    """Create a new sequence.

    Args:
        session: Database session
        campaign_id: Campaign ID
        name: Sequence name
        description: Sequence description
        steps: List of step definitions
        created_by: User who created the sequence

    Returns:
        The created sequence
    """
    sequence = Sequence(
        campaign_id=campaign_id,
        name=name,
        description=description,
        status=SequenceStatus.DRAFT,
        created_by=created_by,
    )
    session.add(sequence)
    await session.commit()

    # Create steps
    for i, step_def in enumerate(steps):
        step = SequenceStep(
            sequence_id=sequence.id,
            step_index=i,
            delay_hours=step_def.get("delay_hours", 0),
            template_id=step_def.get("template_id"),
            skip_condition=step_def.get("skip_condition"),
        )
        session.add(step)

    await session.commit()
    return sequence


async def update_sequence_status(
    session: AsyncSession,
    sequence_id: str,
    status: SequenceStatus,
) -> Optional[Sequence]:
    """Update sequence status.

    Args:
        session: Database session
        sequence_id: Sequence ID
        status: New status

    Returns:
        The updated sequence
    """
    result = await session.execute(select(Sequence).where(Sequence.id == sequence_id))
    sequence = result.scalar_one_or_none()

    if not sequence:
        return None

    sequence.status = status
    await session.commit()
    return sequence


async def trigger_sequence(
    session: AsyncSession,
    sequence_id: str,
    contact_id: str,
    trigger_event: Optional[Dict[str, Any]] = None,
) -> bool:
    """Trigger a sequence for a contact.

    This is the main entry point for sequence execution.

    Args:
        session: Database session
        sequence_id: Sequence ID
        contact_id: Contact ID
        trigger_event: Optional trigger event data

    Returns:
        True if sequence was triggered
    """
    # Get sequence
    result = await session.execute(select(Sequence).where(Sequence.id == sequence_id))
    sequence = result.scalar_one_or_none()

    if not sequence:
        return False

    # Get contact
    result = await session.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()

    if not contact:
        return False

    # Check if contact is suppressed
    if await is_suppressed(session, contact.email):
        return False

    # Check if already enrolled
    result = await session.execute(
        select(Message)
        .where(Message.contact_id == contact_id)
        .where(Message.campaign_id == sequence.campaign_id)
        .where(Message.status == MessageStatus.QUEUED)
    )
    if result.scalar_one_or_none():
        return False

    # Get sequence steps
    result = await session.execute(
        select(SequenceStep)
        .where(SequenceStep.sequence_id == sequence_id)
        .order_by(SequenceStep.step_index)
    )
    steps = list(result.scalars().all())

    if not steps:
        return False

    # Create queued messages for all steps
    now = datetime.utcnow()
    current_time = now

    for step in steps:
        # Calculate delay
        delay = await calculate_delay(session, sequence, contact, step)
        current_time = current_time + delay

        # Check if should skip
        if await should_skip_step(session, sequence, contact, step):
            continue

        # Create message
        message = Message(
            campaign_id=sequence.campaign_id,
            step_index=step.step_index,
            contact_id=contact_id,
            template_id=step.template_id,
            status=MessageStatus.QUEUED,
            scheduled_for=current_time,
            triggered_by=trigger_event.get("id") if trigger_event else None,
        )
        session.add(message)

    await session.commit()
    return True
