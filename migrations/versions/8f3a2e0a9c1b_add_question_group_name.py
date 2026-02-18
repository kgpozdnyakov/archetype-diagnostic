"""add question group name

Revision ID: 8f3a2e0a9c1b
Revises: 27ecfbd97357
Create Date: 2026-02-18 11:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8f3a2e0a9c1b"
down_revision: str | Sequence[str] | None = "27ecfbd97357"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("questions", sa.Column("group_name", sa.String(length=120), nullable=True))


def downgrade() -> None:
    op.drop_column("questions", "group_name")
