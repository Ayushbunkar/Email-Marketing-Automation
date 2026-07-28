"""Replace imap_uid with brevo_message_id in replies table

Revision ID: 3ad1bbdefd9b
Revises: c392d2221cee
Create Date: 2026-07-28 12:10:37.918959

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '3ad1bbdefd9b'
down_revision: Union[str, None] = 'c392d2221cee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Add brevo_message_id column
    op.add_column('replies', sa.Column('brevo_message_id', sa.String(length=255), nullable=True))

    # Migrate data from imap_uid to brevo_message_id if needed
    op.execute("""
        UPDATE replies
        SET brevo_message_id = imap_uid
        WHERE imap_uid IS NOT NULL
    """)

    # Drop imap_uid column
    op.drop_column('replies', 'imap_uid')

    # Add unique constraint to brevo_message_id
    op.create_unique_constraint('uq_replies_brevo_message_id', 'replies', ['brevo_message_id'])

def downgrade() -> None:
    # Add imap_uid column back
    op.add_column('replies', sa.Column('imap_uid', sa.String(length=255), nullable=True))

    # Migrate data from brevo_message_id to imap_uid
    op.execute("""
        UPDATE replies
        SET imap_uid = brevo_message_id
        WHERE brevo_message_id IS NOT NULL
    """)

    # Drop brevo_message_id column
    op.drop_column('replies', 'brevo_message_id')

    # Add unique constraint to imap_uid
    op.create_unique_constraint('uq_replies_imap_uid', 'replies', ['imap_uid'])