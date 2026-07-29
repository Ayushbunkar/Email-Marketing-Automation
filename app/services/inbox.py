"""Inbox pipeline for processing inbound emails."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agent.loop import run_agent
from app.config import settings
from app.models.agent import Approval, ApprovalStatus, ApprovalSubject
from app.models.contact import Contact, ContactStatus
from app.models.event import Event, EventType
from app.models.inbox import InboxMessage, InboxStatus, InboxThread
from app.models.reply import Reply, ReplyClass


async def process_brevo_inbound_email(
    session: AsyncSession,
    inbound_data: Dict[str, Any],
) -> None:
    """Process an inbound email from Brevo webhook.

    Args:
        session: Database session
        inbound_data: Parsed Brevo inbound email data

    Returns:
        None
    """
    import uuid

    from app.models.message import Message
    from app.services.contacts import find_or_create_contact

    # Find or create contact
    contact = await find_or_create_contact(
        session,
        inbound_data["from_email"],
        inbound_data.get("from_name"),
    )

    # Find the original message if this is a reply
    original_message = None
    if inbound_data.get("thread_id"):
        result = await session.execute(
            select(Message).where(Message.provider_message_id == inbound_data["thread_id"])
        )
        original_message = result.scalar_one_or_none()

    # Create reply record
    reply = Reply(
        contact_id=contact.id,
        message_id=original_message.id if original_message else None,
        from_email=inbound_data["from_email"],
        subject=inbound_data.get("subject", ""),
        body_text=inbound_data.get("text_body", ""),
        classification=ReplyClass.OTHER,  # Will be classified by AI later
        confidence=0.0,
        draft_response="",
        handled=False,
        received_at=datetime.fromisoformat(inbound_data["received_at"]) if inbound_data.get("received_at") else datetime.utcnow(),
    )
    session.add(reply)

    # Create inbox message and thread
    # Find or create thread
    result = await session.execute(
        select(InboxThread)
        .where(InboxThread.contact_id == contact.id)
        .where(InboxThread.subject == inbound_data.get("subject", ""))
    )
    thread = result.scalar_one_or_none()

    if not thread:
        thread = InboxThread(
            contact_id=contact.id,
            subject=inbound_data.get("subject", ""),
            status=InboxStatus.UNREAD,
        )
        session.add(thread)

    # Create inbox message
    message = InboxMessage(
        thread_id=thread.id,
        contact_id=contact.id,
        message_id=inbound_data.get("message_id", str(uuid.uuid4())),
        subject=inbound_data.get("subject", ""),
        body=inbound_data.get("text_body", ""),
        html=inbound_data.get("html_body", ""),
        from_email=inbound_data["from_email"],
        from_name=inbound_data.get("from_name", ""),
        to_emails=[inbound_data.get("to_email", "")],
        date=inbound_data.get("received_at", ""),
        headers=inbound_data.get("headers", {}),
        attachments=inbound_data.get("attachments", []),
        status=InboxStatus.UNREAD,
    )
    session.add(message)

    # Record reply event
    event = Event(
        contact_id=contact.id,
        type=EventType.REPLY,
        payload={
            "reply_id": str(reply.id),
            "subject": inbound_data.get("subject", ""),
            "message_id": inbound_data.get("message_id", ""),
        },
        occurred_at=datetime.utcnow(),
    )
    session.add(event)

    # Update contact engagement
    contact.attributes = contact.attributes or {}
    contact.attributes["last_reply_at"] = datetime.utcnow().isoformat()
    contact.lifecycle_stage = "engaged"  # Mark as engaged when they reply

    await session.commit()

    # Trigger AI classification for the reply
    await classify_reply_with_ai(session, reply.id)
    await generate_draft_response_if_needed(session, reply.id)

async def find_or_create_contact(
    session: AsyncSession,
    email: str,
    name: Optional[str] = None,
) -> Contact:
    """Find or create a contact from an inbound email.

    Args:
        session: Database session
        email: Email address
        name: Optional name from email

    Returns:
        Contact object
    """
    result = await session.execute(select(Contact).where(Contact.email == email))
    contact = result.scalar_one_or_none()

    if not contact:
        contact = Contact(
            email=email,
            first_name=name.split()[0] if name else None,
            last_name=" ".join(name.split()[1:]) if name and " " in name else None,
            lifecycle_stage="lead",
            status=ContactStatus.ACTIVE,
        )
        session.add(contact)
        await session.commit()

    return contact

async def mark_as_read(
    session: AsyncSession,
    message_id: str,
) -> bool:
    """Mark an inbox message as read.

    Args:
        session: Database session
        message_id: Message ID

    Returns:
        True if successful
    """
    result = await session.execute(
        select(InboxMessage).where(InboxMessage.id == message_id)
    )
    message = result.scalar_one_or_none()

    if not message:
        return False

    message.status = InboxStatus.READ
    await session.commit()
    return True

async def mark_thread_as_read(
    session: AsyncSession,
    thread_id: str,
) -> bool:
    """Mark all messages in a thread as read.

    Args:
        session: Database session
        thread_id: Thread ID

    Returns:
        True if successful
    """
    result = await session.execute(
        select(InboxMessage).where(InboxMessage.thread_id == thread_id)
    )
    messages = list(result.scalars().all())

    for message in messages:
        message.status = InboxStatus.READ

    await session.commit()
    return True

async def get_unread_count(
    session: AsyncSession,
) -> int:
    """Get count of unread inbox messages.

    Args:
        session: Database session

    Returns:
        Count of unread messages
    """
    result = await session.execute(
        select(func.count(InboxMessage.id)).where(
            InboxMessage.status == InboxStatus.UNREAD
        )
    )
    return result.scalar_one()

async def get_inbox_messages(
    session: AsyncSession,
    contact_id: Optional[str] = None,
    status: Optional[InboxStatus] = None,
    limit: int = 50,
) -> List[InboxMessage]:
    """Get inbox messages with optional filters.

    Args:
        session: Database session
        contact_id: Optional contact ID filter
        status: Optional status filter
        limit: Maximum results

    Returns:
        List of inbox messages
    """
    query = select(InboxMessage).options(
        selectinload(InboxMessage.thread),
    )

    if contact_id:
        query = query.where(InboxMessage.contact_id == contact_id)
    if status:
        query = query.where(InboxMessage.status == status)

    query = query.order_by(InboxMessage.date.desc()).limit(limit)

    result = await session.execute(query)
    return list(result.scalars().all())

async def get_inbox_threads(
    session: AsyncSession,
    contact_id: Optional[str] = None,
    status: Optional[InboxStatus] = None,
    limit: int = 50,
) -> List[InboxThread]:
    """Get inbox threads with optional filters.

    Args:
        session: Database session
        contact_id: Optional contact ID filter
        status: Optional status filter
        limit: Maximum results

    Returns:
        List of inbox threads
    """
    query = select(InboxThread)

    if contact_id:
        query = query.where(InboxThread.contact_id == contact_id)
    if status:
        query = query.where(InboxThread.status == status)

    query = query.order_by(InboxThread.last_message_at.desc()).limit(limit)

    result = await session.execute(query)
    return list(result.scalars().all())

async def classify_reply_with_ai(
    session: AsyncSession,
    reply_id: str,
) -> None:
    """Classify a reply using AI and update the reply record.

    Args:
        session: Database session
        reply_id: Reply ID to classify
    """
    # Get the reply
    result = await session.execute(
        select(Reply).where(Reply.id == reply_id)
    )
    reply = result.scalar_one_or_none()

    if not reply:
        return

    # Get the contact for context
    result = await session.execute(
        select(Contact).where(Contact.id == reply.contact_id)
    )
    contact = result.scalar_one_or_none()

    if not contact:
        return

    # Prepare context for AI classification
    context = {
        "reply_text": reply.body_text,
        "subject": reply.subject,
        "contact_name": f"{contact.first_name} {contact.last_name}".strip(),
        "contact_email": contact.email,
        "contact_company": contact.company or "",
        "contact_lifecycle_stage": contact.lifecycle_stage,
    }

    # Use AI to classify the reply
    try:
        # Create an agent run for classification
        from uuid import uuid4
        run_id = str(uuid4())

        # Define the system prompt for classification
        system_prompt = """You are an email classification assistant. Your task is to analyze incoming email replies and classify them into one of the following categories:

1. INTERESTED - The contact is expressing interest in our product/service
2. QUESTION - The contact is asking a question that requires a response
3. NOT_INTERESTED - The contact is not interested or wants to be removed
4. UNSUBSCRIBE_REQUEST - The contact explicitly requests to unsubscribe
5. OUT_OF_OFFICE - This is an automatic out-of-office reply
6. AUTO_REPLY - This is an automatic email response
7. OTHER - Doesn't fit any of the above categories

Analyze the email content carefully and choose the most appropriate category. Provide a confidence score (0.0-1.0) and a brief reasoning for your classification.

Respond with JSON in this format:
{
  "classification": "CATEGORY",
  "confidence": 0.95,
  "reasoning": "Brief explanation of why you chose this category"
}"""

        # Run the agent to classify the reply
        user_message = f"Classify this email reply:\n\nSubject: {context['subject']}\nFrom: {context['contact_name']} <{context['contact_email']}>\n\n{context['reply_text']}"

        # Use the worker model for classification
        result = await run_agent(
            session,
            run_id=run_id,
            kind="inbox",
            system_prompt=system_prompt,
            user_message=user_message,
            model=settings.WORKER_MODEL,
        )

        # Parse the AI response
        if result and "content" in result:
            try:
                classification_data = json.loads(result["content"])

                # Update the reply with classification
                reply.classification = classification_data.get("classification", "OTHER")
                reply.confidence = classification_data.get("confidence", 0.0)

                # Handle unsubscribe requests immediately
                if reply.classification == "UNSUBSCRIBE_REQUEST":
                    from app.services.suppression import suppress_contact_from_event
                    await suppress_contact_from_event(session, contact.email, "unsubscribe")

                await session.commit()

            except json.JSONDecodeError:
                # If JSON parsing fails, use default classification
                reply.classification = "OTHER"
                reply.confidence = 0.5
                await session.commit()

    except Exception as e:
        print(f"Error classifying reply with AI: {e}")
        # Set default classification on error
        reply.classification = "OTHER"
        reply.confidence = 0.5
        await session.commit()

async def list_messages(
    session: AsyncSession,
    contact_id: Optional[str] = None,
    status: Optional[InboxStatus] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[InboxMessage]:
    """List inbox messages with optional filters.
    
    Args:
        session: Database session
        contact_id: Optional contact ID filter
        status: Optional status filter
        limit: Maximum results
        offset: Offset for pagination
        
    Returns:
        List of inbox messages
    """
    query = select(InboxMessage).options(
        selectinload(InboxMessage.thread),
    )

    if contact_id:
        query = query.where(InboxMessage.contact_id == contact_id)
    if status:
        query = query.where(InboxMessage.status == status)

    query = query.order_by(InboxMessage.date.desc()).limit(limit).offset(offset)

    result = await session.execute(query)
    return list(result.scalars().all())


async def get_message(
    session: AsyncSession,
    message_id: str,
) -> Optional[InboxMessage]:
    """Get a specific inbox message.
    
    Args:
        session: Database session
        message_id: Message ID
        
    Returns:
        Inbox message or None
    """
    result = await session.execute(
        select(InboxMessage).where(InboxMessage.id == message_id)
    )
    return result.scalar_one_or_none()


async def update_message_status(
    session: AsyncSession,
    message_id: str,
    status: InboxStatus,
) -> Optional[InboxMessage]:
    """Update inbox message status.
    
    Args:
        session: Database session
        message_id: Message ID
        status: New status
        
    Returns:
        Updated inbox message or None
    """
    result = await session.execute(
        select(InboxMessage).where(InboxMessage.id == message_id)
    )
    message = result.scalar_one_or_none()
    
    if message:
        message.status = status
        await session.commit()
    return message


async def delete_message(
    session: AsyncSession,
    message_id: str,
) -> Optional[InboxMessage]:
    """Delete an inbox message.
    
    Args:
        session: Database session
        message_id: Message ID
        
    Returns:
        Deleted inbox message or None
    """
    result = await session.execute(
        select(InboxMessage).where(InboxMessage.id == message_id)
    )
    message = result.scalar_one_or_none()
    
    if message:
        await session.delete(message)
        await session.commit()
    return message


async def generate_draft_response_if_needed(
    session: AsyncSession,
    reply_id: str,
) -> None:
    """Generate a draft response if the reply requires one.

    Args:
        session: Database session
        reply_id: Reply ID to generate response for
    """
    # Get the reply
    result = await session.execute(
        select(Reply).where(Reply.id == reply_id)
    )
    reply = result.scalar_one_or_none()

    if not reply or reply.handled:
        return

    # Only generate drafts for replies that need responses
    requires_response = reply.classification in ["INTERESTED", "QUESTION"]
    if not requires_response:
        # Mark as handled if no response needed
        reply.handled = True
        await session.commit()
        return

    # Get the contact for context
    result = await session.execute(
        select(Contact).where(Contact.id == reply.contact_id)
    )
    contact = result.scalar_one_or_none()

    if not contact:
        return

    # Get the original message if available
    original_message = None
    if reply.message_id:
        from app.models.message import Message
        result = await session.execute(
            select(Message).where(Message.id == reply.message_id)
        )
        original_message = result.scalar_one_or_none()

    # Prepare context for AI draft generation
    context = {
        "reply_text": reply.body_text,
        "subject": reply.subject,
        "contact_name": f"{contact.first_name} {contact.last_name}".strip(),
        "contact_email": contact.email,
        "contact_company": contact.company or "",
        "contact_lifecycle_stage": contact.lifecycle_stage,
        "original_subject": original_message.subject if original_message else "",
        "classification": reply.classification,
    }

    try:
        # Create an agent run for draft generation
        from uuid import uuid4
        run_id = str(uuid4())

        # Define the system prompt for draft generation
        system_prompt = """You are an email response assistant. Your task is to generate professional, concise draft responses to email replies.

Follow these guidelines:
1. Be professional and polite
2. Keep responses concise and to the point
3. Address the sender by name
4. Reference their original message where appropriate
5. Provide helpful information or ask clarifying questions
6. Sign off appropriately

For interested contacts, thank them for their interest and offer next steps.
For questions, provide a clear answer or indicate you'll get back to them with more information.

Respond with JSON in this format:
{
  "draft_response": "The full email draft text",
  "subject": "Suggested subject line for the response"
}"""

        # Run the agent to generate the draft
        user_message = f"Generate a draft response to this email:\n\nSubject: {context['subject']}\nFrom: {context['contact_name']} <{context['contact_email']}>\n\n{context['reply_text']}\n\nClassification: {context['classification']}"

        # Use the worker model for draft generation
        result = await run_agent(
            session,
            run_id=run_id,
            kind="inbox",
            system_prompt=system_prompt,
            user_message=user_message,
            model=settings.WORKER_MODEL,
        )

        # Parse the AI response
        if result and "content" in result:
            try:
                draft_data = json.loads(result["content"])

                # Update the reply with draft response
                reply.draft_response = draft_data.get("draft_response", "")
                reply.subject = draft_data.get("subject", f"Re: {reply.subject}")

                # Create an approval for the draft response
                from uuid import uuid4 as uuid_gen
                approval = Approval(
                    id=uuid_gen(),
                    subject_type=ApprovalSubject.REPLY_DRAFT,
                    subject_id=str(reply.id),
                    status=ApprovalStatus.PENDING,
                    summary=f"Draft response to {contact.email} about {reply.subject}",
                )
                session.add(approval)

                # Mark as handled (awaiting approval)
                reply.handled = True

                await session.commit()

            except json.JSONDecodeError:
                print(f"Error parsing draft response JSON: {result['content']}")

    except Exception as e:
        print(f"Error generating draft response: {e}")
