"""add refresh session table

Revision ID: f0f1a2b3c4d5
Revises: 7d2d7ea734aa
Create Date: 2026-03-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f0f1a2b3c4d5"
down_revision: Union[str, Sequence[str], None] = "7d2d7ea734aa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "refresh_session",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("user_name", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_reason", sa.String(), nullable=True),
        sa.Column("replaced_by_session_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_refresh_session_created_at"), "refresh_session", ["created_at"], unique=False)
    op.create_index(op.f("ix_refresh_session_expires_at"), "refresh_session", ["expires_at"], unique=False)
    op.create_index(op.f("ix_refresh_session_revoked"), "refresh_session", ["revoked"], unique=False)
    op.create_index(op.f("ix_refresh_session_user_id"), "refresh_session", ["user_id"], unique=False)
    op.create_index(op.f("ix_refresh_session_user_name"), "refresh_session", ["user_name"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_refresh_session_user_name"), table_name="refresh_session")
    op.drop_index(op.f("ix_refresh_session_user_id"), table_name="refresh_session")
    op.drop_index(op.f("ix_refresh_session_revoked"), table_name="refresh_session")
    op.drop_index(op.f("ix_refresh_session_expires_at"), table_name="refresh_session")
    op.drop_index(op.f("ix_refresh_session_created_at"), table_name="refresh_session")
    op.drop_table("refresh_session")
