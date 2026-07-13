"""dealer_onboarding_v1

Revision ID: a8b9c0d12345
Revises: f7e8f9012345
Create Date: 2026-07-13 17:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "a8b9c0d12345"
down_revision: Union[str, None] = "f7e8f9012345"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "onboarding_sessions",
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("current_step", sa.String(length=64), nullable=False),
        sa.Column("plan_code", sa.String(length=64), nullable=True),
        sa.Column("pricing_model", sa.String(length=64), nullable=True),
        sa.Column("payment_method", sa.String(length=64), nullable=True),
        sa.Column("payment_id", sa.UUID(), nullable=True),
        sa.Column("tenant_id", sa.UUID(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["payment_id"],
            ["commercial_billing_engine_v1_payments.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_onboarding_sessions_user", "onboarding_sessions", ["telegram_user_id"], unique=False)
    op.create_index("ix_onboarding_sessions_status", "onboarding_sessions", ["status"], unique=False)
    op.create_index("ix_onboarding_sessions_current_step", "onboarding_sessions", ["current_step"], unique=False)
    op.create_index("ix_onboarding_sessions_expires_at", "onboarding_sessions", ["expires_at"], unique=False)

    op.create_table(
        "onboarding_steps",
        sa.Column("session_id", sa.UUID(), nullable=False),
        sa.Column("step_name", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["onboarding_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_onboarding_steps_session", "onboarding_steps", ["session_id"], unique=False)
    op.create_index("ix_onboarding_steps_name", "onboarding_steps", ["step_name"], unique=False)
    op.create_index(
        "ix_onboarding_steps_session_name",
        "onboarding_steps",
        ["session_id", "step_name"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_onboarding_steps_session_name", table_name="onboarding_steps")
    op.drop_index("ix_onboarding_steps_name", table_name="onboarding_steps")
    op.drop_index("ix_onboarding_steps_session", table_name="onboarding_steps")
    op.drop_table("onboarding_steps")
    op.drop_index("ix_onboarding_sessions_expires_at", table_name="onboarding_sessions")
    op.drop_index("ix_onboarding_sessions_current_step", table_name="onboarding_sessions")
    op.drop_index("ix_onboarding_sessions_status", table_name="onboarding_sessions")
    op.drop_index("ix_onboarding_sessions_user", table_name="onboarding_sessions")
    op.drop_table("onboarding_sessions")
