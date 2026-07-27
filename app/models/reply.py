"""Reply model and related types."""

from enum import Enum

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import CITEXT, ENUM, UUID
from sqlalchemy.sql import func

from app.db import Base


class ReplyClass(str, Enum):
    """Reply classification."""

    INTERESTED = "interested"
    QUESTION = "question"
    NOT_INTERESTED = "not_interested"
    UNSUBSCRIBE_REQUEST = "unsubscribe_request"
    OUT_OF_OFFICE = "out_of_office"
    AUTO_REPLY = "auto_reply"
    OTHER = "other"


class Reply(Base):
    """Reply model for inbound email replies."""

    __tablename__ = "replies"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id"))
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"))
    from_email = Column(CITEXT, nullable=False)
    subject = Column(Text)
    body_text = Column(Text, nullable=False)
    classification = Column(ENUM(ReplyClass))
    confidence = Column(JSON)
    draft_response = Column(Text)
    handled = Column(JSON, nullable=False, server_default="false")
    received_at = Column(DateTime(timezone=True), nullable=False)
    imap_uid = Column(String(255), unique=True)

    def __repr__(self) -> str:
        return f"<Reply(id={self.id}, from_email={self.from_email})>"
