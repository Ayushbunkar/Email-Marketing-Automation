"""change is_dynamic column type from JSON to Boolean

Revision ID: c392d2221cee
Revises: 001_initial_migration
Create Date: 2026-07-26 16:13:14.930063

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c392d2221cee"
down_revision: Union[str, None] = "001_initial_migration"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("segments", "is_dynamic", type_=sa.Boolean, server_default="true")


def downgrade() -> None:
    op.alter_column("segments", "is_dynamic", type_=sa.JSON, server_default="{}")
