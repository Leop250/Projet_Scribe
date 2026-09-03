"""add calendar bot tables

Revision ID: 98fa956a4bb4
Revises: d0396f189673
Create Date: 2026-08-31 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "98fa956a4bb4"
down_revision: Union[str, Sequence[str], None] = "d0396f189673"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "calendar_connections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.user_id"),
            nullable=False,
            unique=True,
            index=True,
        ),
        sa.Column("meetingbaas_calendar_uuid", sa.String(), nullable=False),
        sa.Column("google_calendar_id", sa.String(), nullable=False, server_default="primary"),
        sa.Column("google_email", sa.String(), nullable=True),
        sa.Column("connected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "calendar_events",
        sa.Column("event_id", sa.String(), primary_key=True),
        sa.Column("emails", postgresql.JSONB(), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "calendar_bots_state",
        sa.Column("bot_id", sa.String(), primary_key=True),
        sa.Column("state", sa.String(), nullable=True),
        sa.Column(
            "recording_delay_started",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )


def downgrade() -> None:
    op.drop_table("calendar_bots_state")
    op.drop_table("calendar_events")
    op.drop_table("calendar_connections")
