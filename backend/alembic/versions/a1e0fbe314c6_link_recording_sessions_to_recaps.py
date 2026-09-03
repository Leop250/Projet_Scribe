"""link recording_sessions to recaps

Revision ID: a1e0fbe314c6
Revises: 32a77d0481b9
Create Date: 2026-08-21 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "a1e0fbe314c6"
down_revision: Union[str, Sequence[str], None] = "32a77d0481b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "recording_sessions",
        sa.Column("recap_id", sa.Integer(), sa.ForeignKey("recaps.recap_id"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("recording_sessions", "recap_id")
