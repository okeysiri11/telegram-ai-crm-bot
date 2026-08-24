"""AUTO 1.5 status history / finance accounts (additive to AUTO 1.4).

Revision ID: o4j567890123
Revises: n3i456789012
Create Date: 2026-08-19 09:50:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "o4j567890123"
down_revision: Union[str, None] = "n3i456789012"
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

    def _has_col(table: str, col: str) -> bool:
        return (
            conn.exec_driver_sql(
                "SELECT 1 FROM information_schema.columns "
                f"WHERE table_schema = 'public' AND table_name = '{table}' AND column_name = '{col}'"
            ).scalar()
            is not None
        )

    if _exists("auto_ops_vehicles"):
        if not _has_col("auto_ops_vehicles", "is_demo"):
            op.add_column("auto_ops_vehicles", sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.text("false")))
        if not _has_col("auto_ops_vehicles", "workspace_id"):
            op.add_column("auto_ops_vehicles", sa.Column("workspace_id", sa.String(128), nullable=True))

    if _exists("auto_ops_expenses") and not _has_col("auto_ops_expenses", "due_at"):
        op.add_column("auto_ops_expenses", sa.Column("due_at", sa.String(32), nullable=True))

    if _exists("auto_ops_deals"):
        if not _has_col("auto_ops_deals", "due_at"):
            op.add_column("auto_ops_deals", sa.Column("due_at", sa.String(32), nullable=True))
        if not _has_col("auto_ops_deals", "payment_due"):
            op.add_column("auto_ops_deals", sa.Column("payment_due", sa.String(32), nullable=True))

    if _exists("auto_ops_receipts") and not _has_col("auto_ops_receipts", "due_at"):
        op.add_column("auto_ops_receipts", sa.Column("due_at", sa.String(32), nullable=True))

    if not _exists("auto_ops_status_history"):
        op.create_table(
            "auto_ops_status_history",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("workspace_id", sa.String(128), nullable=True),
            sa.Column("vehicle_id", sa.String(64), nullable=False),
            sa.Column("status", sa.String(32), nullable=False),
            sa.Column("entered_at", sa.String(64), nullable=True),
            sa.Column("left_at", sa.String(64), nullable=True),
            sa.Column("source", sa.String(16), nullable=True),
            sa.Column("payload", JSONB(), nullable=True),
            *_ts_cols(),
        )
        op.create_index("ix_auto_ops_status_hist_org", "auto_ops_status_history", ["organization_id"])
        op.create_index("ix_auto_ops_status_hist_vehicle", "auto_ops_status_history", ["organization_id", "vehicle_id"])
        op.create_index("ix_auto_ops_status_hist_status", "auto_ops_status_history", ["organization_id", "status"])
        op.create_index("ix_auto_ops_status_hist_entered", "auto_ops_status_history", ["organization_id", "entered_at"])

    if not _exists("auto_ops_finance_accounts"):
        op.create_table(
            "auto_ops_finance_accounts",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("workspace_id", sa.String(128), nullable=True),
            sa.Column("account_type", sa.String(32), nullable=False, server_default="OTHER"),
            sa.Column("label", sa.String(256), nullable=True),
            sa.Column("currency", sa.String(8), nullable=False, server_default="USD"),
            sa.Column("balance", sa.Numeric(14, 2), nullable=True),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("payload", JSONB(), nullable=True),
            *_ts_cols(),
        )
        op.create_index("ix_auto_ops_fin_acct_org", "auto_ops_finance_accounts", ["organization_id"])
        op.create_index("ix_auto_ops_fin_acct_type", "auto_ops_finance_accounts", ["organization_id", "account_type"])


def downgrade() -> None:
    pass
