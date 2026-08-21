"""add recaps table and participants_list_of_recaps column

Revision ID: 32a77d0481b9
Revises: b92f95f2759e
Create Date: 2026-08-21 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "32a77d0481b9"
down_revision: Union[str, Sequence[str], None] = "b92f95f2759e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "recaps",
        sa.Column("recap_id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.Column("transcription", sa.String(), nullable=False),
        sa.Column("reporting", postgresql.JSONB(), nullable=False),
        sa.Column("emails", sa.String(), nullable=False),
    )
    op.add_column("users", sa.Column("participants_list_of_recaps", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "participants_list_of_recaps")
    op.drop_table("recaps")
