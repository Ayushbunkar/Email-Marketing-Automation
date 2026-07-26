"""Mock email provider for development and testing."""

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from app.providers.base import EmailProvider, SendRequest, SendResult, NormalizedEvent


class MockProvider(EmailProvider):
    """Mock email provider that writes emails to files instead of sending them."""

    def __init__(self, outbox_path: str = "./outbox"):
        """Initialize the mock provider."""
        self.outbox_path = Path(outbox_path)
        self.outbox_path.mkdir(parents=True, exist_ok=True)

    async def send(self, req: SendRequest) -> SendResult:
        """Write email to .eml file and return fake message ID."""
        message_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        # Create .eml file content
        eml_content = f"""From: {req.from_name} <{req.from_email}>
To: {req.to_name or req.to_email} <{req.to_email}>
Subject: {req.subject}
Date: {timestamp}
Message-ID: <{message_id}@hermes.local>
List-Unsubscribe: <{req.headers.get('List-Unsubscribe', '')}>
List-Unsubscribe-Post: List-Unsubscribe=One-Click

{req.text}
"""

        # Write to file
        filename = self.outbox_path / f"{message_id}.eml"
        with open(filename, "w") as f:
            f.write(eml_content)

        return SendResult(
            provider_message_id=message_id,
            accepted=True,
            error=None,
        )

    def verify_webhook(self, headers: Dict[str, str], body: bytes) -> bool:
        """Mock webhook verification - always returns True."""
        return True

    def parse_webhook(self, body: bytes) -> List[NormalizedEvent]:
        """Parse mock webhook payload."""
        return []

    def get_outbox_path(self) -> Path:
        """Get the outbox directory path."""
        return self.outbox_path