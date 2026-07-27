"""Inbox pipeline for processing inbound emails."""

import re
from datetime import datetime
from email import message_from_bytes
from email.header import decode_header, make_header
from email.utils import parseaddr
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.contact import Contact, ContactStatus
from app.models.event import Event, EventType
from app.models.inbox import InboxMessage, InboxStatus, InboxThread
from app.providers.inbound_imap import InboundIMAPProvider


class HTMLTextExtractor(HTMLParser):
    """Simple HTML to text converter."""

    def __init__(self):
        super().__init__()
        self.text = []
        self.current_text = []

    def handle_data(self, data):
        self.current_text.append(data)

    def handle_endtag(self, tag):
        if tag in ["p", "br", "div", "li"]:
            if self.current_text:
                self.text.append("".join(self.current_text).strip())
                self.current_text = []
            self.text.append("\n")
        elif tag == "li":
            self.text.append("\n")

    def get_text(self):
        return "".join(self.text).strip()


def extract_text_from_html(html: str) -> str:
    """Extract plain text from HTML."""
    parser = HTMLTextExtractor()
    parser.feed(html)
    return parser.get_text()


def extract_email_address(text: str) -> Optional[str]:
    """Extract email address from text."""
    # Simple email regex
    pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    match = re.search(pattern, text)
    if match:
        return match.group(0)
    return None


def parse_inbound_email(raw_email: bytes) -> Dict[str, Any]:
    """Parse raw email bytes into structured data.

    Args:
        raw_email: Raw email bytes

    Returns:
        Dictionary with email data
    """
    msg = message_from_bytes(raw_email)

    # Extract headers
    headers = {}
    for key, value in msg.items():
        headers[key] = str(make_header(decode_header(value)))

    # Extract sender
    from_addr = headers.get("From", "")
    from_name, from_email = parseaddr(from_addr)

    # Extract recipients
    to_addrs = headers.get("To", "")
    to_list = [parseaddr(addr)[1] for addr in to_addrs.split(",") if addr.strip()]

    # Extract subject
    subject = headers.get("Subject", "")

    # Extract body
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                try:
                    body = part.get_payload(decode=True).decode("utf-8")
                except Exception:
                    body = part.get_payload(decode=True).decode("latin-1")
                break
            elif content_type == "text/html":
                try:
                    html = part.get_payload(decode=True).decode("utf-8")
                    body = extract_text_from_html(html)
                except Exception:
                    pass
    else:
        try:
            body = msg.get_payload(decode=True).decode("utf-8")
        except Exception:
            body = msg.get_payload(decode=True).decode("latin-1")

    # Extract attachments
    attachments = []
    if msg.is_multipart():
        for part in msg.walk():
            content_disposition = part.get_content_disposition()
            if content_disposition == "attachment":
                attachments.append(
                    {
                        "filename": part.get_filename(),
                        "content_type": part.get_content_type(),
                        "size": len(part.get_payload(decode=True)),
                    }
                )

    return {
        "message_id": headers.get("Message-ID", ""),
        "from_email": from_email,
        "from_name": from_name,
        "to_emails": to_list,
        "subject": subject,
        "body": body,
        "html": msg.get_payload(decode=True).decode("utf-8")
        if msg.is_multipart()
        else "",
        "date": headers.get("Date", ""),
        "headers": headers,
        "attachments": attachments,
    }


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


async def find_or_create_thread(
    session: AsyncSession,
    contact: Contact,
    subject: str,
) -> InboxThread:
    """Find or create an inbox thread.

    Args:
        session: Database session
        contact: Contact
        subject: Email subject

    Returns:
        InboxThread object
    """
    result = await session.execute(
        select(InboxThread)
        .where(InboxThread.contact_id == contact.id)
        .where(InboxThread.subject == subject)
        .order_by(InboxThread.created_at.desc())
    )
    thread = result.scalar_one_or_none()

    if not thread:
        thread = InboxThread(
            contact_id=contact.id,
            subject=subject,
            status=InboxStatus.UNREAD,
        )
        session.add(thread)
        await session.commit()

    return thread


async def process_inbound_email(
    session: AsyncSession,
    raw_email: bytes,
) -> InboxMessage:
    """Process an inbound email.

    Args:
        session: Database session
        raw_email: Raw email bytes

    Returns:
        InboxMessage object
    """
    # Parse email
    email_data = parse_inbound_email(raw_email)

    # Find or create contact
    contact = await find_or_create_contact(
        session,
        email_data["from_email"],
        email_data["from_name"],
    )

    # Find or create thread
    thread = await find_or_create_thread(
        session,
        contact,
        email_data["subject"],
    )

    # Check for duplicates
    if email_data["message_id"]:
        result = await session.execute(
            select(InboxMessage).where(
                InboxMessage.message_id == email_data["message_id"]
            )
        )
        if result.scalar_one_or_none():
            return None  # Duplicate

    # Create inbox message
    message = InboxMessage(
        thread_id=thread.id,
        contact_id=contact.id,
        message_id=email_data["message_id"],
        subject=email_data["subject"],
        body=email_data["body"],
        html=email_data.get("html", ""),
        from_email=email_data["from_email"],
        from_name=email_data["from_name"],
        to_emails=email_data["to_emails"],
        date=email_data["date"],
        headers=email_data["headers"],
        attachments=email_data.get("attachments", []),
        status=InboxStatus.UNREAD,
    )
    session.add(message)
    await session.commit()

    # Update thread
    thread.last_message_at = datetime.utcnow()
    thread.status = InboxStatus.UNREAD
    await session.commit()

    # Record event
    event = Event(
        contact_id=contact.id,
        type=EventType.INBOUND_EMAIL,
        payload={
            "message_id": message.id,
            "subject": email_data["subject"],
        },
        occurred_at=datetime.utcnow(),
    )
    session.add(event)
    await session.commit()

    return message


async def poll_inbox(
    session: AsyncSession,
    provider: InboundIMAPProvider,
) -> List[InboxMessage]:
    """Poll inbox for new emails.

    Args:
        session: Database session
        provider: IMAP provider

    Returns:
        List of new messages
    """
    raw_emails = await provider.poll()

    messages = []
    for raw_email in raw_emails:
        message = await process_inbound_email(session, raw_email)
        if message:
            messages.append(message)

    return messages


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
