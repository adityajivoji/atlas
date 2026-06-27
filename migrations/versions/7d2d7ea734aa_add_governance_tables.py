"""add governance tables

Revision ID: 7d2d7ea734aa
Revises: ba93ec4dd525
Create Date: 2026-03-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "7d2d7ea734aa"
down_revision: Union[str, Sequence[str], None] = "ba93ec4dd525"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_log",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("actor_user_name", sa.String(), nullable=True),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("resource", sa.String(), nullable=True),
        sa.Column("ip_address", sa.String(), nullable=True),
        sa.Column("user_agent", sa.String(), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_log_action"), "audit_log", ["action"], unique=False)
    op.create_index(op.f("ix_audit_log_actor_user_name"), "audit_log", ["actor_user_name"], unique=False)
    op.create_index(op.f("ix_audit_log_created_at"), "audit_log", ["created_at"], unique=False)
    op.create_index(op.f("ix_audit_log_status"), "audit_log", ["status"], unique=False)

    op.create_table(
        "login_history",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_name", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("failure_reason", sa.String(), nullable=True),
        sa.Column("ip_address", sa.String(), nullable=True),
        sa.Column("user_agent", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_login_history_created_at"), "login_history", ["created_at"], unique=False)
    op.create_index(op.f("ix_login_history_email"), "login_history", ["email"], unique=False)
    op.create_index(op.f("ix_login_history_success"), "login_history", ["success"], unique=False)
    op.create_index(op.f("ix_login_history_user_name"), "login_history", ["user_name"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_login_history_user_name"), table_name="login_history")
    op.drop_index(op.f("ix_login_history_success"), table_name="login_history")
    op.drop_index(op.f("ix_login_history_email"), table_name="login_history")
    op.drop_index(op.f("ix_login_history_created_at"), table_name="login_history")
    op.drop_table("login_history")

    op.drop_index(op.f("ix_audit_log_status"), table_name="audit_log")
    op.drop_index(op.f("ix_audit_log_created_at"), table_name="audit_log")
    op.drop_index(op.f("ix_audit_log_actor_user_name"), table_name="audit_log")
    op.drop_index(op.f("ix_audit_log_action"), table_name="audit_log")
    op.drop_table("audit_log")
