"""Initial migration with all models and extensions.

Revision ID: 001_initial_migration
Revises: 
Create Date: 2026-07-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial_migration"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgvector")

    # Create lifecycle_stage enum
    op.execute("CREATE TYPE lifecycle_stage AS ENUM ('lead','subscriber','engaged','customer','churned')")

    # Create contact_status enum
    op.execute("CREATE TYPE contact_status AS ENUM ('active','unsubscribed','bounced','complained','suppressed')")

    # Create campaign_status enum
    op.execute("CREATE TYPE campaign_status AS ENUM ('draft','pending_approval','approved','scheduled','running','paused','completed','archived')")

    # Create campaign_type enum
    op.execute("CREATE TYPE campaign_type AS ENUM ('one_shot','sequence','trigger')")

    # Create message_status enum
    op.execute("CREATE TYPE message_status AS ENUM ('queued','pending_approval','approved','sending','sent','delivered','bounced','failed','suppressed','canceled')")

    # Create event_type enum
    op.execute("CREATE TYPE event_type AS ENUM ('delivered','open','click','bounce_hard','bounce_soft','complaint','unsubscribe','reply')")

    # Create suppression_reason enum
    op.execute("CREATE TYPE suppression_reason AS ENUM ('unsubscribe','hard_bounce','complaint','manual','legal_request')")

    # Create reply_class enum
    op.execute("CREATE TYPE reply_class AS ENUM ('interested','question','not_interested','unsubscribe_request','out_of_office','auto_reply','other')")

    # Create agent_run_kind enum
    op.execute("CREATE TYPE agent_run_kind AS ENUM ('campaign_planner','copywriter','inbox','optimizer','adhoc_chat')")

    # Create approval_status enum
    op.execute("CREATE TYPE approval_status AS ENUM ('pending','approved','rejected')")

    # Create approval_subject enum
    op.execute("CREATE TYPE approval_subject AS ENUM ('campaign','reply_draft','proposal')")

    # Create contacts table
    op.create_table(
        "contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("first_name", sa.Text(), nullable=True),
        sa.Column("last_name", sa.Text(), nullable=True),
        sa.Column("company", sa.Text(), nullable=True),
        sa.Column("attributes", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("lifecycle_stage", sa.Enum("lead", "subscriber", "engaged", "customer", "churned", name="lifecycle_stage"), server_default="lead", nullable=False),
        sa.Column("status", sa.Enum("active", "unsubscribed", "bounced", "complained", "suppressed", name="contact_status"), server_default="active", nullable=False),
        sa.Column("consent_source", sa.Text(), nullable=True),
        sa.Column("consent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("timezone", sa.Text(), server_default="Asia/Kolkata", nullable=False),
        sa.Column("last_emailed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("embedding", postgresql.vector.Vector(768), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_contacts_status", "contacts", ["status"], unique=False)
    op.create_index("ix_contacts_lifecycle_stage", "contacts", ["lifecycle_stage"], unique=False)

    # Create segments table
    op.create_table(
        "segments",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("definition", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("is_dynamic", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_by", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create campaigns table
    op.create_table(
        "campaigns",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column("type", sa.Enum("one_shot", "sequence", "trigger", name="campaign_type"), nullable=False),
        sa.Column("status", sa.Enum("draft", "pending_approval", "approved", "scheduled", "running", "paused", "completed", "archived", name="campaign_status"), server_default="draft", nullable=False),
        sa.Column("segment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("settings", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(length=50), nullable=False),
        sa.Column("approved_by", sa.String(length=50), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create campaign_steps table
    op.create_table(
        "campaign_steps",
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("step_index", sa.Integer(), nullable=False),
        sa.Column("delay_hours", sa.Integer(), server_default="0", nullable=False),
        sa.Column("send_condition", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("campaign_id", "step_index"),
        sa.UniqueConstraint("campaign_id", "step_index"),
    )

    # Create templates table
    op.create_table(
        "templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("step_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("subject", sa.Text(), nullable=False),
        sa.Column("preheader", sa.Text(), nullable=True),
        sa.Column("body_markdown", sa.Text(), nullable=False),
        sa.Column("variant_label", sa.String(length=10), server_default="A", nullable=False),
        sa.Column("variables", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["step_id"], ["campaign_steps.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create messages table
    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("step_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.Enum("queued", "pending_approval", "approved", "sending", "sent", "delivered", "bounced", "failed", "suppressed", "canceled", name="message_status"), server_default="queued", nullable=False),
        sa.Column("provider_message_id", sa.String(length=255), nullable=True),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("provider_event_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("campaign_id", "step_id", "contact_id"),
        sa.UniqueConstraint("provider_message_id"),
    )
    op.create_index("ix_messages_status_scheduled_for", "messages", ["status", "scheduled_for"], unique=False)

    # Create events table
    op.create_table(
        "events",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("type", sa.Enum("delivered", "open", "click", "bounce_hard", "bounce_soft", "complaint", "unsubscribe", "reply", name="event_type"), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("provider_event_id", sa.String(length=255), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"]),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_events_contact_type_occurred", "events", ["contact_id", "type", "occurred_at"], unique=False)

    # Create suppressions table
    op.create_table(
        "suppressions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("reason", sa.Enum("unsubscribe", "hard_bounce", "complaint", "manual", "legal_request", name="suppression_reason"), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    # Create replies table
    op.create_table(
        "replies",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("from_email", sa.Text(), nullable=False),
        sa.Column("subject", sa.Text(), nullable=True),
        sa.Column("body_text", sa.Text(), nullable=False),
        sa.Column("classification", sa.Enum("interested", "question", "not_interested", "unsubscribe_request", "out_of_office", "auto_reply", "other", name="reply_class"), nullable=True),
        sa.Column("confidence", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("draft_response", sa.Text(), nullable=True),
        sa.Column("handled", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("imap_uid", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"]),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("imap_uid"),
    )

    # Create agent_runs table
    op.create_table(
        "agent_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("kind", sa.Enum("campaign_planner", "copywriter", "inbox", "optimizer", "adhoc_chat", name="agent_run_kind"), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("model", sa.String(length=255), nullable=False),
        sa.Column("input", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("output", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("transcript", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("tokens_in", postgresql.JSONB(astext_type=sa.Text()), server_default="0", nullable=False),
        sa.Column("tokens_out", postgresql.JSONB(astext_type=sa.Text()), server_default="0", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create approvals table
    op.create_table(
        "approvals",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("subject_type", sa.Enum("campaign", "reply_draft", "proposal", name="approval_subject"), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.Enum("pending", "approved", "rejected", name="approval_status"), server_default="pending", nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("decided_by", sa.String(length=50), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_approvals_pending ON approvals (subject_type, subject_id) WHERE status = 'pending'")

    # Create proposals table
    op.create_table(
        "proposals",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("changes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.Enum("pending", "approved", "rejected", name="approval_status"), server_default="pending", nullable=False),
        sa.Column("source_run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["source_run_id"], ["agent_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table("proposals")
    op.drop_table("approvals")
    op.drop_table("agent_runs")
    op.drop_table("replies")
    op.drop_table("suppressions")
    op.drop_table("events")
    op.drop_table("messages")
    op.drop_table("templates")
    op.drop_table("campaign_steps")
    op.drop_table("campaigns")
    op.drop_table("segments")
    op.drop_table("contacts")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS lifecycle_stage")
    op.execute("DROP TYPE IF EXISTS contact_status")
    op.execute("DROP TYPE IF EXISTS campaign_status")
    op.execute("DROP TYPE IF EXISTS campaign_type")
    op.execute("DROP TYPE IF EXISTS message_status")
    op.execute("DROP TYPE IF EXISTS event_type")
    op.execute("DROP TYPE IF EXISTS suppression_reason")
    op.execute("DROP TYPE IF EXISTS reply_class")
    op.execute("DROP TYPE IF EXISTS agent_run_kind")
    op.execute("DROP TYPE IF EXISTS approval_status")
    op.execute("DROP TYPE IF EXISTS approval_subject")