"""Agent model and related types."""

from enum import Enum

from sqlalchemy import Column, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.sql import func

from app.db import Base


class AgentRunKind(str, Enum):
    """Agent run kind."""

    CAMPAIGN_PLANNER = "campaign_planner"
    COPYWRITER = "copywriter"
    INBOX = "inbox"
    OPTIMIZER = "optimizer"
    ADHOC_CHAT = "adhoc_chat"


class AgentRun(Base):
    """Agent run model for tracking LLM agent executions."""

    __tablename__ = "agent_runs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    kind = Column(
        ENUM(AgentRunKind),
        nullable=False,
    )
    status = Column(String(50), nullable=False)
    model = Column(String(255), nullable=False)
    input = Column(JSON, nullable=False)
    output = Column(JSON)
    transcript = Column(JSON, nullable=False, server_default="[]")
    tokens_in = Column(JSON, nullable=False, server_default="0")
    tokens_out = Column(JSON, nullable=False, server_default="0")
    started_at = Column(DateTime(timezone=True), nullable=False)
    finished_at = Column(DateTime(timezone=True))
    error = Column(Text)

    def __repr__(self) -> str:
        return f"<AgentRun(id={self.id}, kind={self.kind}, status={self.status})>"


class ApprovalStatus(str, Enum):
    """Approval status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ApprovalSubject(str, Enum):
    """Approval subject type."""

    CAMPAIGN = "campaign"
    REPLY_DRAFT = "reply_draft"
    PROPOSAL = "proposal"


class Approval(Base):
    """Approval model for human approval workflow."""

    __tablename__ = "approvals"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    subject_type = Column(
        ENUM(ApprovalSubject),
        nullable=False,
    )
    subject_id = Column(UUID(as_uuid=True), nullable=False)
    status = Column(
        ENUM(ApprovalStatus),
        nullable=False,
        server_default="pending",
    )
    summary = Column(Text, nullable=False)
    decided_by = Column(String(50))
    decided_at = Column(DateTime(timezone=True))
    notes = Column(Text)

    __table_args__ = (
        func.unique(
            subject_type,
            subject_id,
        ).where(status == "pending"),
    )

    def __repr__(self) -> str:
        return f"<Approval(id={self.id}, status={self.status})>"


class Proposal(Base):
    """Proposal model for optimizer recommendations."""

    __tablename__ = "proposals"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    title = Column(String(255), nullable=False)
    rationale = Column(Text, nullable=False)
    changes = Column(JSON, nullable=False)
    status = Column(
        ENUM(ApprovalStatus),
        nullable=False,
        server_default="pending",
    )
    source_run_id = Column(UUID(as_uuid=True), ForeignKey("agent_runs.id"))

    def __repr__(self) -> str:
        return f"<Proposal(id={self.id}, title={self.title})>"