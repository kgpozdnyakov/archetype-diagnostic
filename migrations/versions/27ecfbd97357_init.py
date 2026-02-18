"""init

Revision ID: 27ecfbd97357
Revises: 
Create Date: 2026-02-17 21:54:16.241584

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "27ecfbd97357"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    test_status = sa.Enum("draft", "published", name="teststatus")
    question_type = sa.Enum("single", "scale", name="questiontype")

    op.create_table(
        "test_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False, unique=True),
        sa.Column("status", test_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "questions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("version_id", sa.Integer(), sa.ForeignKey("test_versions.id"), nullable=False),
        sa.Column("text", sa.String(length=500), nullable=False),
        sa.Column("type", question_type, nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("driver_tag", sa.String(length=100), nullable=True),
        sa.Column("group_name", sa.String(length=120), nullable=True),
    )

    op.create_table(
        "options",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("question_id", sa.Integer(), sa.ForeignKey("questions.id"), nullable=False),
        sa.Column("text", sa.String(length=300), nullable=False),
        sa.Column("value", sa.Integer(), nullable=True),
        sa.Column("weights", sa.JSON(), nullable=False),
    )

    op.create_table(
        "assessments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("version_id", sa.Integer(), sa.ForeignKey("test_versions.id"), nullable=False),
        sa.Column("user_label", sa.String(length=120), nullable=True),
        sa.Column("answers", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("drivers", sa.JSON(), nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("assessments")
    op.drop_table("options")
    op.drop_table("questions")
    op.drop_table("test_versions")

    op.execute("DROP TYPE IF EXISTS questiontype")
    op.execute("DROP TYPE IF EXISTS teststatus")
