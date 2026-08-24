"""FX paper trading + journal — Sprint 50.2.

Revision ID: z9t012345678
Revises: y8s901234567
Create Date: 2026-08-11 12:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "z9t012345678"
down_revision: Union[str, None] = "y8s901234567"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ts_cols():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("change_id", sa.String(length=64), nullable=True),
        sa.Column("source_client", sa.String(length=32), nullable=True),
        sa.Column("workspace_id", sa.String(length=128), nullable=True),
        sa.Column("created_by", sa.String(length=128), nullable=True),
        sa.Column("updated_by", sa.String(length=128), nullable=True),
        sa.Column("metadata_json", JSONB(), nullable=True),
    ]


def upgrade() -> None:
    conn = op.get_bind()

    def _exists(name: str) -> bool:
        return conn.exec_driver_sql(f"SELECT to_regclass('public.{name}')").scalar() is not None

    if _exists("fx_mi_paper_orders"):
        return

    op.create_table(
        "fx_mi_paper_orders",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
        sa.Column("order_key", sa.String(64), nullable=False),
        sa.Column("instrument", sa.String(32), nullable=False),
        sa.Column("side", sa.String(8), nullable=False),
        sa.Column("order_type", sa.String(16), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("limit_price", sa.Float(), nullable=True),
        sa.Column("stop_loss", sa.Float(), nullable=True),
        sa.Column("take_profit", sa.Float(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("fill_price", sa.Float(), nullable=True),
        sa.Column("filled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("signal_id", sa.String(64), nullable=True),
        sa.Column("analysis_run_id", sa.String(64), nullable=True),
        sa.Column("payload", JSONB(), nullable=True),
        *_ts_cols(),
    )
    op.create_index("ix_fx_mi_paper_orders_tenant", "fx_mi_paper_orders", ["tenant_id", "created_at"])

    op.create_table(
        "fx_mi_paper_positions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
        sa.Column("position_key", sa.String(64), nullable=False),
        sa.Column("order_key", sa.String(64), nullable=True),
        sa.Column("instrument", sa.String(32), nullable=False),
        sa.Column("side", sa.String(8), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("entry_price", sa.Float(), nullable=False),
        sa.Column("exit_price", sa.Float(), nullable=True),
        sa.Column("stop_loss", sa.Float(), nullable=True),
        sa.Column("take_profit", sa.Float(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("pnl", sa.Float(), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("signal_id", sa.String(64), nullable=True),
        sa.Column("analysis_run_id", sa.String(64), nullable=True),
        sa.Column("payload", JSONB(), nullable=True),
        *_ts_cols(),
    )
    op.create_index("ix_fx_mi_paper_pos_tenant", "fx_mi_paper_positions", ["tenant_id", "status"])

    op.create_table(
        "fx_mi_journal_entries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
        sa.Column("journal_key", sa.String(64), nullable=False),
        sa.Column("instrument", sa.String(32), nullable=True),
        sa.Column("entry_price", sa.Float(), nullable=True),
        sa.Column("exit_price", sa.Float(), nullable=True),
        sa.Column("pnl", sa.Float(), nullable=True),
        sa.Column("duration_sec", sa.Integer(), nullable=True),
        sa.Column("signal_id", sa.String(64), nullable=True),
        sa.Column("analysis_run_id", sa.String(64), nullable=True),
        sa.Column("payload", JSONB(), nullable=True),
        *_ts_cols(),
    )
    op.create_index("ix_fx_mi_journal_tenant", "fx_mi_journal_entries", ["tenant_id", "created_at"])


def downgrade() -> None:
    pass
