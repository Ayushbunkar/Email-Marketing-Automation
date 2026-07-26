"""Email provider base classes and protocols."""

from typing import Protocol, Optional, List, Dict, Any
from pydantic import BaseModel


class SendRequest(BaseModel):
    """Request to send an email."""

    to_email: str
    to_name: Optional[str] = None
    from_email: str
    from_name: str
    reply_to: str
    subject: str
    html: str
    text: str
    headers: Dict[str, str]
    idempotency_key: str


class SendResult(BaseModel):
    """Result of sending an email."""

    provider_message_id: str
    accepted: bool
    error: Optional[str] = None


class NormalizedEvent(BaseModel):
    """Normalized event from provider webhook."""

    event_type: str
    message_id: Optional[str] = None
    contact_id: Optional[str] = None
    payload: Dict[str, Any] = {}


class EmailProvider(Protocol):
    """Protocol for email providers."""

    async def send(self, req: SendRequest) -> SendResult:
        """Send an email."""
        ...

    def verify_webhook(self, headers: Dict[str, str], body: bytes) -> bool:
        """Verify webhook signature."""
        ...

    def parse_webhook(self, body: bytes) -> List[NormalizedEvent]:
        """Parse webhook payload."""
        ...