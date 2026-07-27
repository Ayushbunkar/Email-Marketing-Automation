"""IMAP provider for inbound email polling."""

import asyncio
from typing import Dict, List, Optional

from imap_tools import A, MailBox

from app.providers.base import EmailProvider, NormalizedEvent, SendRequest, SendResult


class InboundIMAPProvider:
    """IMAP provider for polling inbound emails."""

    def __init__(
        self,
        host: str,
        port: int = 993,
        username: str = "",
        password: str = "",
        folder: str = "INBOX",
    ):
        """Initialize the IMAP provider."""
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.folder = folder

    async def poll(self) -> List[dict]:
        """Poll IMAP for new emails."""
        messages = []
        try:
            async with asyncio.to_thread(
                MailBox(self.host, self.port).login,
                self.username,
                self.password,
            ) as mailbox:
                mailbox.folder.set(self.folder)
                for msg in mailbox.fetch(A(unseen=True)):
                    messages.append(
                        {
                            "from": msg.from_values,
                            "to": msg.to,
                            "subject": msg.subject,
                            "text": msg.text,
                            "html": msg.html,
                            "uid": msg.uid,
                            "date": msg.date,
                            "headers": dict(msg.headers),
                        }
                    )
        except Exception as e:
            print(f"IMAP poll error: {e}")
        return messages

    async def mark_seen(self, uid: str) -> None:
        """Mark a message as seen."""
        try:
            async with asyncio.to_thread(
                MailBox(self.host, self.port).login,
                self.username,
                self.password,
            ) as mailbox:
                mailbox.folder.set(self.folder)
                mailbox.seen(uid)
        except Exception as e:
            print(f"Error marking message as seen: {e}")

    async def fetch_message(self, uid: str) -> Optional[dict]:
        """Fetch a specific message by UID."""
        try:
            async with asyncio.to_thread(
                MailBox(self.host, self.port).login,
                self.username,
                self.password,
            ) as mailbox:
                mailbox.folder.set(self.folder)
                for msg in mailbox.fetch(uids=uid):
                    return {
                        "from": msg.from_values,
                        "to": msg.to,
                        "subject": msg.subject,
                        "text": msg.text,
                        "html": msg.html,
                        "uid": msg.uid,
                        "date": msg.date,
                        "headers": dict(msg.headers),
                    }
        except Exception as e:
            print(f"Error fetching message: {e}")
        return None


class InboundProvider(EmailProvider):
    """Email provider for inbound email handling."""

    def __init__(
        self,
        host: str,
        port: int = 993,
        username: str = "",
        password: str = "",
        folder: str = "INBOX",
    ):
        """Initialize the inbound provider."""
        self.imap = InboundIMAPProvider(host, port, username, password, folder)

    async def send(self, req: SendRequest) -> SendResult:
        """Send is not supported for inbound provider."""
        return SendResult(
            provider_message_id="",
            accepted=False,
            error="Inbound provider does not support sending",
        )

    def verify_webhook(self, headers: Dict[str, str], body: bytes) -> bool:
        """Verify webhook signature - always returns True for IMAP (no webhook support)."""
        return True

    def parse_webhook(self, body: bytes) -> List[NormalizedEvent]:
        """Parse webhook payload - returns empty list for IMAP (no webhook support)."""
        return []
