"""AUTO 1.0 private import/dealership ops tables (additive).

Revision ID: j9e012345678
Revises: i8d901234567
Create Date: 2026-08-18 15:30:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "j9e012345678"
down_revision: Union[str, None] = "i8d901234567"
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

    if not _exists("auto_ops_vehicles"):
        op.create_table(
            "auto_ops_vehicles",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("vin", sa.String(32), nullable=False),
            sa.Column("vin_nonstandard", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("internal_number", sa.String(64), nullable=True),
            sa.Column("status", sa.String(32), nullable=False, server_default="INTEREST"),
            sa.Column("manufacturer", sa.String(128), nullable=True),
            sa.Column("model", sa.String(128), nullable=True),
            sa.Column("year", sa.Integer(), nullable=True),
            sa.Column("trim", sa.String(128), nullable=True),
            sa.Column("body_type", sa.String(64), nullable=True),
            sa.Column("fuel_type", sa.String(64), nullable=True),
            sa.Column("engine", sa.String(128), nullable=True),
            sa.Column("transmission", sa.String(64), nullable=True),
            sa.Column("drive_type", sa.String(64), nullable=True),
            sa.Column("exterior_color", sa.String(64), nullable=True),
            sa.Column("interior_color", sa.String(64), nullable=True),
            sa.Column("mileage", sa.Numeric(14, 2), nullable=True),
            sa.Column("mileage_unit", sa.String(16), nullable=True),
            sa.Column("country_of_origin", sa.String(64), nullable=True),
            sa.Column("purchase_country", sa.String(64), nullable=True),
            sa.Column("auction_name", sa.String(128), nullable=True),
            sa.Column("auction_lot", sa.String(64), nullable=True),
            sa.Column("auction_url", sa.String(1024), nullable=True),
            sa.Column("purchase_date", sa.String(32), nullable=True),
            sa.Column("purchase_price", sa.Numeric(14, 2), nullable=True),
            sa.Column("purchase_currency", sa.String(8), nullable=True),
            sa.Column("buyer_fee", sa.Numeric(14, 2), nullable=True),
            sa.Column("estimated_market_value", sa.Numeric(14, 2), nullable=True),
            sa.Column("location_current", sa.String(256), nullable=True),
            sa.Column("origin_port", sa.String(128), nullable=True),
            sa.Column("destination_port", sa.String(128), nullable=True),
            sa.Column("assigned_manager_id", sa.String(128), nullable=True),
            sa.Column("client_id", sa.String(64), nullable=True),
            sa.Column("cover_photo_id", sa.String(64), nullable=True),
            sa.Column("sale_price_expected", sa.Numeric(14, 2), nullable=True),
            sa.Column("sale_price_actual", sa.Numeric(14, 2), nullable=True),
            sa.Column("sale_date", sa.String(32), nullable=True),
            sa.Column("sale_currency", sa.String(8), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("payload", JSONB(), nullable=True),
            *_ts_cols(),
            sa.UniqueConstraint("organization_id", "vin", name="uq_auto_ops_vehicles_org_vin"),
        )
        op.create_index("ix_auto_ops_vehicles_org", "auto_ops_vehicles", ["organization_id"])
        op.create_index("ix_auto_ops_vehicles_status", "auto_ops_vehicles", ["organization_id", "status"])
        op.create_index("ix_auto_ops_vehicles_vin", "auto_ops_vehicles", ["vin"])

    if not _exists("auto_ops_expenses"):
        op.create_table(
            "auto_ops_expenses",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("vehicle_id", sa.String(64), nullable=False),
            sa.Column("category", sa.String(32), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("amount", sa.Numeric(14, 2), nullable=False),
            sa.Column("currency", sa.String(8), nullable=False, server_default="USD"),
            sa.Column("exchange_rate", sa.Numeric(14, 6), nullable=True),
            sa.Column("amount_base_currency", sa.Numeric(14, 2), nullable=True),
            sa.Column("payment_date", sa.String(32), nullable=True),
            sa.Column("counterparty", sa.String(256), nullable=True),
            sa.Column("payment_method", sa.String(64), nullable=True),
            sa.Column("payment_status", sa.String(32), nullable=False, server_default="paid"),
            sa.Column("document_id", sa.String(64), nullable=True),
            sa.Column("payload", JSONB(), nullable=True),
            *_ts_cols(),
        )
        op.create_index("ix_auto_ops_expenses_org", "auto_ops_expenses", ["organization_id"])
        op.create_index("ix_auto_ops_expenses_vehicle", "auto_ops_expenses", ["vehicle_id"])

    if not _exists("auto_ops_documents"):
        op.create_table(
            "auto_ops_documents",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("document_type", sa.String(64), nullable=False, server_default="other"),
            sa.Column("title", sa.String(512), nullable=True),
            sa.Column("file_name", sa.String(512), nullable=False),
            sa.Column("file_id", sa.String(64), nullable=True),
            sa.Column("owner_type", sa.String(32), nullable=False, server_default="vehicle"),
            sa.Column("vehicle_id", sa.String(64), nullable=True),
            sa.Column("client_id", sa.String(64), nullable=True),
            sa.Column("shipment_id", sa.String(64), nullable=True),
            sa.Column("customs_id", sa.String(64), nullable=True),
            sa.Column("sale_id", sa.String(64), nullable=True),
            sa.Column("payment_id", sa.String(64), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("uploaded_by", sa.String(128), nullable=True),
            sa.Column("payload", JSONB(), nullable=True),
            *_ts_cols(),
        )
        op.create_index("ix_auto_ops_documents_org", "auto_ops_documents", ["organization_id"])

    if not _exists("auto_ops_photos"):
        op.create_table(
            "auto_ops_photos",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("vehicle_id", sa.String(64), nullable=False),
            sa.Column("category", sa.String(32), nullable=False, server_default="OTHER"),
            sa.Column("file_id", sa.String(64), nullable=False),
            sa.Column("file_name", sa.String(512), nullable=True),
            sa.Column("is_cover", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("uploaded_by", sa.String(128), nullable=True),
            sa.Column("payload", JSONB(), nullable=True),
            *_ts_cols(),
        )
        op.create_index("ix_auto_ops_photos_vehicle", "auto_ops_photos", ["vehicle_id"])

    if not _exists("auto_ops_clients"):
        op.create_table(
            "auto_ops_clients",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("name", sa.String(256), nullable=False),
            sa.Column("phone", sa.String(64), nullable=True),
            sa.Column("telegram", sa.String(128), nullable=True),
            sa.Column("email", sa.String(256), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("assigned_manager_id", sa.String(128), nullable=True),
            sa.Column("source", sa.String(128), nullable=True),
            sa.Column("status", sa.String(32), nullable=False, server_default="lead"),
            sa.Column("payload", JSONB(), nullable=True),
            *_ts_cols(),
        )
        op.create_index("ix_auto_ops_clients_org", "auto_ops_clients", ["organization_id"])

    if not _exists("auto_ops_tasks"):
        op.create_table(
            "auto_ops_tasks",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("title", sa.String(512), nullable=False),
            sa.Column("status", sa.String(32), nullable=False, server_default="open"),
            sa.Column("vehicle_id", sa.String(64), nullable=True),
            sa.Column("client_id", sa.String(64), nullable=True),
            sa.Column("assigned_manager_id", sa.String(128), nullable=True),
            sa.Column("due_at", sa.String(64), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("payload", JSONB(), nullable=True),
            *_ts_cols(),
        )
        op.create_index("ix_auto_ops_tasks_org", "auto_ops_tasks", ["organization_id"])

    if not _exists("auto_ops_audit"):
        op.create_table(
            "auto_ops_audit",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("actor_id", sa.String(128), nullable=True),
            sa.Column("actor_role", sa.String(64), nullable=True),
            sa.Column("action", sa.String(64), nullable=False),
            sa.Column("entity_type", sa.String(64), nullable=False),
            sa.Column("entity_id", sa.String(64), nullable=False),
            sa.Column("old_value", JSONB(), nullable=True),
            sa.Column("new_value", JSONB(), nullable=True),
            sa.Column("summary", sa.Text(), nullable=True),
            *_ts_cols(),
        )
        op.create_index("ix_auto_ops_audit_org", "auto_ops_audit", ["organization_id"])
        op.create_index("ix_auto_ops_audit_entity", "auto_ops_audit", ["entity_type", "entity_id"])

    if not _exists("auto_ops_files"):
        op.create_table(
            "auto_ops_files",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("file_name", sa.String(512), nullable=False),
            sa.Column("mime_type", sa.String(128), nullable=True),
            sa.Column("storage_path", sa.String(1024), nullable=False),
            sa.Column("size_bytes", sa.Integer(), nullable=True),
            sa.Column("uploaded_by", sa.String(128), nullable=True),
            sa.Column("entity_type", sa.String(64), nullable=True),
            sa.Column("entity_id", sa.String(64), nullable=True),
            sa.Column("payload", JSONB(), nullable=True),
            *_ts_cols(),
        )
        op.create_index("ix_auto_ops_files_org", "auto_ops_files", ["organization_id"])


def downgrade() -> None:
    for name in (
        "auto_ops_files",
        "auto_ops_audit",
        "auto_ops_tasks",
        "auto_ops_clients",
        "auto_ops_photos",
        "auto_ops_documents",
        "auto_ops_expenses",
        "auto_ops_vehicles",
    ):
        op.drop_table(name)
