"""automotive_treasury_v1

Revision ID: c0d1e2f34567
Revises: b9c0d1e23456
Create Date: 2026-07-13 18:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "c0d1e2f34567"
down_revision: Union[str, None] = "b9c0d1e23456"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "automotive_treasury_v1_rate_sheets",
        sa.Column("tenant_id", sa.UUID(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("usd_buy", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("usd_sell", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("eur_buy", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("eur_sell", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("usdt_buy", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("usdt_sell", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("usd_white_premium", sa.Numeric(precision=20, scale=6), nullable=True),
        sa.Column("usd_blue_premium", sa.Numeric(precision=20, scale=6), nullable=True),
        sa.Column("source_channel_id", sa.String(length=64), nullable=True),
        sa.Column("source_message_id", sa.BigInteger(), nullable=True),
        sa.Column("source_text", sa.Text(), nullable=True),
        sa.Column("source_updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by_user_id", sa.BigInteger(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", name="uq_automotive_treasury_v1_rate_sheets_tenant"),
    )
    op.create_index(
        "ix_automotive_treasury_v1_rate_sheets_tenant",
        "automotive_treasury_v1_rate_sheets",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        "ix_automotive_treasury_v1_rate_sheets_active",
        "automotive_treasury_v1_rate_sheets",
        ["is_active"],
        unique=False,
    )
    op.create_index(
        "ix_automotive_treasury_v1_rate_sheets_updated",
        "automotive_treasury_v1_rate_sheets",
        ["source_updated_at"],
        unique=False,
    )

    op.create_table(
        "automotive_treasury_v1_rate_history",
        sa.Column("tenant_id", sa.UUID(), nullable=True),
        sa.Column("rates", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("source_channel_id", sa.String(length=64), nullable=True),
        sa.Column("source_message_id", sa.BigInteger(), nullable=True),
        sa.Column("source_text", sa.Text(), nullable=True),
        sa.Column("source_updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by_user_id", sa.BigInteger(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_automotive_treasury_v1_history_tenant",
        "automotive_treasury_v1_rate_history",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        "ix_automotive_treasury_v1_history_updated",
        "automotive_treasury_v1_rate_history",
        ["source_updated_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_automotive_treasury_v1_history_updated", table_name="automotive_treasury_v1_rate_history")
    op.drop_index("ix_automotive_treasury_v1_history_tenant", table_name="automotive_treasury_v1_rate_history")
    op.drop_table("automotive_treasury_v1_rate_history")
    op.drop_index("ix_automotive_treasury_v1_rate_sheets_updated", table_name="automotive_treasury_v1_rate_sheets")
    op.drop_index("ix_automotive_treasury_v1_rate_sheets_active", table_name="automotive_treasury_v1_rate_sheets")
    op.drop_index("ix_automotive_treasury_v1_rate_sheets_tenant", table_name="automotive_treasury_v1_rate_sheets")
    op.drop_table("automotive_treasury_v1_rate_sheets")
