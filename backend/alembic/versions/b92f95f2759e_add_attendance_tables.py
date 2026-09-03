"""add attendance tables

Revision ID: b92f95f2759e
Revises: ac312b5f7d51
Create Date: 2026-08-21 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "b92f95f2759e"
down_revision: Union[str, Sequence[str], None] = "ac312b5f7d51"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "recording_sessions",
        sa.Column("session_id", sa.Integer(), primary_key=True, index=True),
        sa.Column("token", sa.String(), nullable=False, unique=True, index=True),
        sa.Column("organizer_id", sa.Integer(), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("headcount", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "attendance_signatures",
        sa.Column("signature_id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "session_id",
            sa.Integer(),
            sa.ForeignKey("recording_sessions.session_id"),
            nullable=False,
            index=True,
        ),
        sa.Column("nom", sa.String(), nullable=False),
        sa.Column("image_data", sa.String(), nullable=False),
        sa.Column("signed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("attendance_signatures")
    op.drop_table("recording_sessions")
