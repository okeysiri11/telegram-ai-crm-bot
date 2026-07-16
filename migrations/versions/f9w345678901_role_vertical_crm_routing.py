"""Role-based vertical CRM routing foundation

Revision ID: f9w345678901
Revises: f9v234567890
Create Date: 2026-07-16 16:30:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "f9w345678901"
down_revision: Union[str, None] = "f9v234567890"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("role", sa.String(length=64), nullable=True))
    op.add_column("users", sa.Column("verticals", JSONB(), nullable=True))
    op.create_index("ix_users_role", "users", ["role"])

    op.create_table(
        "manager_vertical_subscriptions_v1",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("vertical", sa.String(length=32), nullable=False),
        sa.Column("role_code", sa.String(length=64), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint(
            "user_id",
            "vertical",
            name="uq_manager_vertical_subscriptions_v1_user_vertical",
        ),
    )
    op.create_index(
        "ix_manager_vertical_subscriptions_v1_vertical",
        "manager_vertical_subscriptions_v1",
        ["vertical"],
    )
    op.create_index(
        "ix_manager_vertical_subscriptions_v1_telegram",
        "manager_vertical_subscriptions_v1",
        ["telegram_user_id"],
    )
    op.create_index(
        "ix_manager_vertical_subscriptions_v1_active",
        "manager_vertical_subscriptions_v1",
        ["is_active"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_manager_vertical_subscriptions_v1_active",
        table_name="manager_vertical_subscriptions_v1",
    )
    op.drop_index(
        "ix_manager_vertical_subscriptions_v1_telegram",
        table_name="manager_vertical_subscriptions_v1",
    )
    op.drop_index(
        "ix_manager_vertical_subscriptions_v1_vertical",
        table_name="manager_vertical_subscriptions_v1",
    )
    op.drop_table("manager_vertical_subscriptions_v1")
    op.drop_index("ix_users_role", table_name="users")
    op.drop_column("users", "verticals")
    op.drop_column("users", "role")
