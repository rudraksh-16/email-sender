"""add smtp max_per_day

Revision ID: b3c9f1a2d4e8
Revises: eea0cb900193
Create Date: 2026-05-20 16:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b3c9f1a2d4e8"
down_revision: Union[str, None] = "eea0cb900193"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("smtp_accounts", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("max_per_day", sa.Integer(), nullable=False, server_default="2000")
        )


def downgrade() -> None:
    with op.batch_alter_table("smtp_accounts", schema=None) as batch_op:
        batch_op.drop_column("max_per_day")
