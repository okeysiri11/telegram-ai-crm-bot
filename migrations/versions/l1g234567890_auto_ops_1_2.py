"""AUTO 1.2 customs / broker / VAT tables (additive to AUTO 1.1).

Revision ID: l1g234567890
Revises: k0f123456789
Create Date: 2026-08-18 17:10:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "l1g234567890"
down_revision: Union[str, None] = "k0f123456789"
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
            "SELECT 1 FROM information_schema.columns WHERE table_name=%s AND column_name=%s",
            (table, column.name),
        ).scalar()
        if not exists:
            op.add_column(table, column)

    _add_col("auto_ops_expenses", sa.Column("customs_id", sa.String(64), nullable=True))
    _add_col("auto_ops_tasks", sa.Column("customs_id", sa.String(64), nullable=True))
    _add_col("auto_ops_documents", sa.Column("broker_id", sa.String(64), nullable=True))

    if not _exists("auto_ops_customs_cases"):
        op.create_table(
            "auto_ops_customs_cases",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("vehicle_id", sa.String(64), nullable=False),
            sa.Column("status", sa.String(32), nullable=False, server_default="DOCUMENTS_PREP"),
            sa.Column("broker_id", sa.String(64), nullable=True),
            sa.Column("customs_office", sa.String(256), nullable=True),
            sa.Column("declaration_number", sa.String(128), nullable=True),
            sa.Column("customs_value", sa.Numeric(14, 2), nullable=True),
            sa.Column("currency", sa.String(8), nullable=True),
            sa.Column("fx_rate_to_uah", sa.Numeric(14, 6), nullable=True),
            sa.Column("engine_cc", sa.Numeric(14, 2), nullable=True),
            sa.Column("fuel_type", sa.String(64), nullable=True),
            sa.Column("year", sa.Integer(), nullable=True),
            sa.Column("broker_fee_uah", sa.Numeric(14, 2), nullable=True),
            sa.Column("duty_uah", sa.Numeric(14, 2), nullable=True),
            sa.Column("excise_uah", sa.Numeric(14, 2), nullable=True),
            sa.Column("import_vat_uah", sa.Numeric(14, 2), nullable=True),
            sa.Column("state_total_uah", sa.Numeric(14, 2), nullable=True),
            sa.Column("grand_total_uah", sa.Numeric(14, 2), nullable=True),
            sa.Column("location_current", sa.String(256), nullable=True),
            sa.Column("responsible_manager_id", sa.String(128), nullable=True),
            sa.Column("cert_status", sa.String(32), nullable=True),
            sa.Column("cert_body", sa.String(256), nullable=True),
            sa.Column("cert_number", sa.String(128), nullable=True),
            sa.Column("cert_date", sa.String(32), nullable=True),
            sa.Column("reg_status", sa.String(32), nullable=True),
            sa.Column("plate_expected", sa.String(32), nullable=True),
            sa.Column("mreo_office", sa.String(256), nullable=True),
            sa.Column("mreo_date", sa.String(32), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("payload", JSONB(), nullable=True),
            *_ts_cols(),
        )
        op.create_index("ix_auto_ops_customs_cases_org", "auto_ops_customs_cases", ["organization_id"])
        op.create_index("ix_auto_ops_customs_cases_vehicle", "auto_ops_customs_cases", ["vehicle_id"])
        op.create_index("ix_auto_ops_customs_cases_status", "auto_ops_customs_cases", ["organization_id", "status"])

    if not _exists("auto_ops_brokers"):
        op.create_table(
            "auto_ops_brokers",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("company_name", sa.String(256), nullable=False),
            sa.Column("type", sa.String(32), nullable=False, server_default="customs_broker"),
            sa.Column("country", sa.String(64), nullable=True),
            sa.Column("contact_person", sa.String(256), nullable=True),
            sa.Column("phone", sa.String(64), nullable=True),
            sa.Column("email", sa.String(256), nullable=True),
            sa.Column("telegram", sa.String(128), nullable=True),
            sa.Column("tax_id", sa.String(64), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("rating", sa.String(16), nullable=True),
            sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("payload", JSONB(), nullable=True),
            *_ts_cols(),
        )
        op.create_index("ix_auto_ops_brokers_org", "auto_ops_brokers", ["organization_id"])

    if not _exists("auto_ops_customs_settings"):
        op.create_table(
            "auto_ops_customs_settings",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("duty_rate", sa.Numeric(8, 4), nullable=True),
            sa.Column("vat_rate", sa.Numeric(8, 4), nullable=True),
            sa.Column("payload", JSONB(), nullable=True),
            *_ts_cols(),
        )
        op.create_index("ix_auto_ops_customs_settings_org", "auto_ops_customs_settings", ["organization_id"])


def downgrade() -> None:
    op.drop_table("auto_ops_customs_settings")
    op.drop_table("auto_ops_brokers")
    op.drop_table("auto_ops_customs_cases")
