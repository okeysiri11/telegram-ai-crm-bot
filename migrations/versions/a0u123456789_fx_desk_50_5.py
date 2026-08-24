"""FX desk hardening — Sprint 50.5 configs + paper idempotency.

Revision ID: a0u123456789
Revises: z9t012345678
Create Date: 2026-08-12 08:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "a0u123456789"
down_revision: Union[str, None] = "z9t012345678"
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

    if not _exists("fx_mi_desk_configs"):
        op.create_table(
            "fx_mi_desk_configs",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("config_key", sa.String(64), nullable=False),
            sa.Column("payload", JSONB(), nullable=False),
            *_ts_cols(),
            sa.UniqueConstraint("tenant_id", "config_key", name="uq_fx_mi_desk_configs_tenant_key"),
        )
        op.create_index("ix_fx_mi_desk_configs_tenant", "fx_mi_desk_configs", ["tenant_id"])

    if not _exists("fx_mi_paper_accounts"):
        op.create_table(
            "fx_mi_paper_accounts",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("currency", sa.String(8), nullable=False, server_default="USD"),
            sa.Column("balance", sa.Float(), nullable=False),
            sa.Column("realized_pnl", sa.Float(), nullable=False, server_default="0"),
            sa.Column("payload", JSONB(), nullable=True),
            *_ts_cols(),
            sa.UniqueConstraint("tenant_id", name="uq_fx_mi_paper_accounts_tenant"),
        )

    # idempotency column on paper orders if table exists
    if _exists("fx_mi_paper_orders"):
        cols = {r[1] for r in conn.exec_driver_sql("SELECT * FROM information_schema.columns WHERE table_name='fx_mi_paper_orders'").fetchall()} if False else set()
        # safer: try add column
        try:
            op.add_column("fx_mi_paper_orders", sa.Column("idempotency_key", sa.String(128), nullable=True))
            op.create_index("ix_fx_mi_paper_orders_idem", "fx_mi_paper_orders", ["tenant_id", "idempotency_key"], unique=False)
        except Exception:
            pass


def downgrade() -> None:
    op.drop_table("fx_mi_paper_accounts")
    op.drop_table("fx_mi_desk_configs")
