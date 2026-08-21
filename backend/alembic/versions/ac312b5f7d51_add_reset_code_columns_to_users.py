"""add reset_code columns to users

Revision ID: ac312b5f7d51
Revises:
Create Date: 2026-08-07 09:58:54.914731

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ac312b5f7d51"
down_revision: Union[str, Sequence[str], None] = "9b49ed7d95ab"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("users", sa.Column("reset_code", sa.String(), nullable=True))
    op.add_column("users", sa.Column("reset_code_expires_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "reset_code_expires_at")
    op.drop_column("users", "reset_code")
