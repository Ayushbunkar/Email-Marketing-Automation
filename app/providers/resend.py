"""Resend email provider driver."""

import hashlib
import hmac
import json
from typing import Dict, List, Optional

import httpx

from app.config import settings
from app.providers.base import EmailProvider, SendRequest, SendResult, NormalizedEvent


class ResendProvider(EmailProvider):
    """Resend email provider driver."""

    def __init__(self, api_key: str = None):
        """Initialize the Resend provider."""
        self.api_key = api_key or settings.RESEND_API_KEY
        self.base_url = "https://api.resend.com"
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def send(self, req: SendRequest) -> SendResult:
        """Send an email via Resend API."""
        try:
            response = await self.client.post(
                "/emails",
                json={
                    "from": f"{req.from_name} <{req.from_email}>",
                    "to": [req.to_email],
                    "subject": req.subject,
                    "html": req.html,
                    "text": req.text,
                    "headers": req.headers,
                },
            )
            response.raise_for_status()
            data = response.json()
            return SendResult(
                provider_message_id=data.get("id", ""),
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
        """Verify Resend webhook signature."""
        signature = headers.get("X-Signature", "")
        if not signature:
            return False

        expected_signature = hmac.new(
            key=settings.RESEND_WEBHOOK_SECRET.encode(),
            msg=body,
            digestmod=hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)

    def parse_webhook(self, body: bytes) -> List[NormalizedEvent]:
        """Parse Resend webhook payload."""
        try:
            data = json.loads(body)
            event_type = data.get("type", "")

            # Map Resend event types to our event types
            event_map = {
                "email.delivered": "delivered",
                "email.opened": "open",
                "email.clicked": "click",
                "email.bounced": "bounce_hard",
                "email.complained": "complaint",
                "email.unsubscribed": "unsubscribe",
            }

            return [
                NormalizedEvent(
                    event_type=event_map.get(event_type, event_type),
                    message_id=data.get("id"),
                    contact_id=data.get("to", [None])[0],
                    payload=data,
                )
            ]
        except Exception:
            return []

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()