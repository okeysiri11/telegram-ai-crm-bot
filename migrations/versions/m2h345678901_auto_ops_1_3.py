"""AUTO 1.3 CRM / sales / receipts tables (additive to AUTO 1.2).

Revision ID: m2h345678901
Revises: l1g234567890
Create Date: 2026-08-18 17:55:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "m2h345678901"
down_revision: Union[str, None] = "l1g234567890"
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

    def _add_col(table: str, column: sa.Column) -> None:
        if not _exists(table):
            return
        exists = conn.exec_driver_sql(
            "SELECT 1 FROM information_schema.columns "
            f"WHERE table_schema = 'public' AND table_name = '{table}' AND column_name = '{column.name}'"
        ).scalar()
        if not exists:
            op.add_column(table, column)

    for col in (
        sa.Column("passport_ref", sa.String(128), nullable=True),
        sa.Column("tax_id", sa.String(64), nullable=True),
        sa.Column("address", sa.String(512), nullable=True),
        sa.Column("id_number", sa.String(64), nullable=True),
        sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    ):
        _add_col("auto_ops_clients", col)
    _add_col("auto_ops_tasks", sa.Column("deal_id", sa.String(64), nullable=True))
    _add_col("auto_ops_documents", sa.Column("deal_id", sa.String(64), nullable=True))

    if not _exists("auto_ops_deals"):
        op.create_table(
            "auto_ops_deals",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("client_id", sa.String(64), nullable=False),
            sa.Column("vehicle_id", sa.String(64), nullable=True),
            sa.Column("stage", sa.String(32), nullable=False, server_default="LEAD"),
            sa.Column("assigned_manager_id", sa.String(128), nullable=True),
            sa.Column("sale_price", sa.Numeric(14, 2), nullable=True),
            sa.Column("currency", sa.String(8), nullable=True),
            sa.Column("source", sa.String(128), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("payload", JSONB(), nullable=True),
            *_ts_cols(),
        )
        op.create_index("ix_auto_ops_deals_org", "auto_ops_deals", ["organization_id"])
        op.create_index("ix_auto_ops_deals_client", "auto_ops_deals", ["client_id"])
        op.create_index("ix_auto_ops_deals_vehicle", "auto_ops_deals", ["vehicle_id"])

    if not _exists("auto_ops_reservations"):
        op.create_table(
            "auto_ops_reservations",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("vehicle_id", sa.String(64), nullable=False),
            sa.Column("client_id", sa.String(64), nullable=False),
            sa.Column("deal_id", sa.String(64), nullable=True),
            sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"),
            sa.Column("expires_at", sa.String(32), nullable=True),
            sa.Column("override_reason", sa.String(512), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("payload", JSONB(), nullable=True),
            *_ts_cols(),
        )
        op.create_index("ix_auto_ops_reservations_org", "auto_ops_reservations", ["organization_id"])

    if not _exists("auto_ops_sales"):
        op.create_table(
            "auto_ops_sales",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("vehicle_id", sa.String(64), nullable=False),
            sa.Column("client_id", sa.String(64), nullable=False),
            sa.Column("deal_id", sa.String(64), nullable=True),
            sa.Column("price", sa.Numeric(14, 2), nullable=False),
            sa.Column("currency", sa.String(8), nullable=False, server_default="USD"),
            sa.Column("status", sa.String(32), nullable=False, server_default="OPEN"),
            sa.Column("completed_at", sa.String(64), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("payload", JSONB(), nullable=True),
            *_ts_cols(),
        )
        op.create_index("ix_auto_ops_sales_org", "auto_ops_sales", ["organization_id"])

    if not _exists("auto_ops_receipts"):
        op.create_table(
            "auto_ops_receipts",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("deal_id", sa.String(64), nullable=True),
            sa.Column("sale_id", sa.String(64), nullable=True),
            sa.Column("vehicle_id", sa.String(64), nullable=True),
            sa.Column("client_id", sa.String(64), nullable=True),
            sa.Column("kind", sa.String(32), nullable=False, server_default="PARTIAL"),
            sa.Column("amount", sa.Numeric(14, 2), nullable=False),
            sa.Column("currency", sa.String(8), nullable=False, server_default="USD"),
            sa.Column("exchange_rate", sa.Numeric(14, 6), nullable=True),
            sa.Column("amount_base_currency", sa.Numeric(14, 2), nullable=True),
            sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
            sa.Column("reference", sa.String(128), nullable=True),
            sa.Column("confirmed_at", sa.String(64), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("payload", JSONB(), nullable=True),
            *_ts_cols(),
        )
        op.create_index("ix_auto_ops_receipts_org", "auto_ops_receipts", ["organization_id"])


def downgrade() -> None:
    op.drop_table("auto_ops_receipts")
    op.drop_table("auto_ops_sales")
    op.drop_table("auto_ops_reservations")
    op.drop_table("auto_ops_deals")
