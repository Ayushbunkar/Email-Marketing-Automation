"""Brevo email provider driver."""

import hashlib
import hmac
import json
from typing import Any, Dict, List

import httpx

from app.config import settings
from app.providers.base import EmailProvider, NormalizedEvent, SendRequest, SendResult


class BrevoProvider(EmailProvider):
    """Brevo email provider driver."""

    def __init__(self, api_key: str = None):
        """Initialize the Brevo provider."""
        self.api_key = api_key or settings.BREVO_API_KEY
        self.base_url = "https://api.brevo.com/v3"
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "api-key": self.api_key,
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def send(self, req: SendRequest) -> SendResult:
        """Send an email via Brevo API."""
        try:
            response = await self.client.post(
                "/smtp/email",
                json={
                    "sender": {"name": req.from_name, "email": req.from_email},
                    "to": [{"email": req.to_email, "name": req.to_name or ""}],
                    "subject": req.subject,
                    "htmlContent": req.html,
                    "textContent": req.text,
                    "headers": req.headers,
                    "replyTo": {"email": req.reply_to},
                },
            )
            response.raise_for_status()
            data = response.json()
            return SendResult(
                provider_message_id=data.get("messageId", ""),
                accepted=True,
                error=None,
            )
        except httpx.HTTPStatusError as e:
            return SendResult(
                provider_message_id="",
                accepted=False,
                error=str(e),
            )
        except Exception as e:
            return SendResult(
                provider_message_id="",
                accepted=False,
                error=str(e),
            )

    def verify_webhook(self, headers: Dict[str, str], body: bytes) -> bool:
        """Verify Brevo webhook signature."""
        signature = headers.get("api-key", "")
        if not signature:
            return False

        expected_signature = hmac.new(
            key=settings.BREVO_WEBHOOK_SECRET.encode(),
            msg=body,
            digestmod=hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)

    def parse_webhook(self, body: bytes) -> List[NormalizedEvent]:
        """Parse Brevo webhook payload."""
        try:
            data = json.loads(body)
            event_type = data.get("event", "")

            # Map Brevo event types to our event types
            event_map = {
                "sent": "delivered",
                "delivered": "delivered",
                "open": "open",
                "click": "click",
                "bounce": "bounce_hard",
                "spam": "complaint",
                "unsub": "unsubscribe",
                "blocked": "bounce_hard",
                "invalid_email": "bounce_hard",
            }

            return [
                NormalizedEvent(
                    event_type=event_map.get(event_type, event_type),
                    message_id=data.get("messageId"),
                    contact_id=data.get("email"),
                    payload=data,
                )
            ]
        except Exception:
            return []

    def verify_inbound_webhook(self, headers: Dict[str, str], body: bytes) -> bool:
        """Verify Brevo inbound email webhook signature."""
        signature = headers.get("api-key", "")
        if not signature:
            return False

        expected_signature = hmac.new(
            key=settings.BREVO_INBOUND_WEBHOOK_SECRET.encode(),
            msg=body,
            digestmod=hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)

    def parse_inbound_webhook(self, body: bytes) -> Dict[str, Any]:
        """Parse Brevo inbound email webhook payload."""
        try:
            data = json.loads(body)
            return {
                "from_email": data.get("sender", {}).get("email", ""),
                "from_name": data.get("sender", {}).get("name", ""),
                "to_email": data.get("recipients", [{}])[0].get("email", ""),
                "subject": data.get("subject", ""),
                "text_body": data.get("text", ""),
                "html_body": data.get("html", ""),
                "message_id": data.get("messageId", ""),
                "thread_id": data.get("inReplyTo", ""),
                "references": data.get("references", ""),
                "attachments": data.get("attachments", []),
                "received_at": data.get("date", ""),
                "headers": data.get("headers", {}),
            }
        except Exception:
            return {}

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
