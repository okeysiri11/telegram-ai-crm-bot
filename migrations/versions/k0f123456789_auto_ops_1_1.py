"""AUTO 1.1 logistics tables (additive to AUTO 1.0).

Revision ID: k0f123456789
Revises: j9e012345678
Create Date: 2026-08-18 16:20:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "k0f123456789"
down_revision: Union[str, None] = "j9e012345678"
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

    _add_col("auto_ops_expenses", sa.Column("shipment_id", sa.String(64), nullable=True))
    _add_col("auto_ops_tasks", sa.Column("shipment_id", sa.String(64), nullable=True))
    _add_col("auto_ops_tasks", sa.Column("priority", sa.String(32), nullable=True))
    for col in (
        sa.Column("container_id", sa.String(64), nullable=True),
        sa.Column("carrier_id", sa.String(64), nullable=True),
        sa.Column("driver_id", sa.String(64), nullable=True),
        sa.Column("truck_id", sa.String(64), nullable=True),
        sa.Column("vessel_id", sa.String(64), nullable=True),
        sa.Column("archived_at", sa.String(64), nullable=True),
        sa.Column("previous_file_id", sa.String(64), nullable=True),
    ):
        _add_col("auto_ops_documents", col)
    _add_col("auto_ops_photos", sa.Column("shipment_id", sa.String(64), nullable=True))
    _add_col("auto_ops_photos", sa.Column("location", sa.String(256), nullable=True))
    _add_col("auto_ops_photos", sa.Column("captured_at", sa.String(64), nullable=True))

    if not _exists("auto_ops_shipments"):
        op.create_table(
            "auto_ops_shipments",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("vehicle_id", sa.String(64), nullable=False),
            sa.Column("shipment_type", sa.String(32), nullable=False, server_default="CONTAINER"),
            sa.Column("status", sa.String(32), nullable=False, server_default="PLANNED"),
            sa.Column("origin_country", sa.String(64), nullable=True),
            sa.Column("origin_location", sa.String(256), nullable=True),
            sa.Column("destination_country", sa.String(64), nullable=True),
            sa.Column("destination_location", sa.String(256), nullable=True),
            sa.Column("pickup_address", sa.String(512), nullable=True),
            sa.Column("pickup_date_planned", sa.String(32), nullable=True),
            sa.Column("pickup_date_actual", sa.String(32), nullable=True),
            sa.Column("carrier_id", sa.String(64), nullable=True),
            sa.Column("driver_id", sa.String(64), nullable=True),
            sa.Column("truck_id", sa.String(64), nullable=True),
            sa.Column("container_id", sa.String(64), nullable=True),
            sa.Column("vessel_id", sa.String(64), nullable=True),
            sa.Column("booking_number", sa.String(128), nullable=True),
            sa.Column("bill_of_lading_number", sa.String(128), nullable=True),
            sa.Column("tracking_reference", sa.String(128), nullable=True),
            sa.Column("origin_port_id", sa.String(64), nullable=True),
            sa.Column("destination_port_id", sa.String(64), nullable=True),
            sa.Column("etd", sa.String(32), nullable=True),
            sa.Column("atd", sa.String(32), nullable=True),
            sa.Column("eta", sa.String(32), nullable=True),
            sa.Column("ata", sa.String(32), nullable=True),
            sa.Column("planned_eta", sa.String(32), nullable=True),
            sa.Column("current_eta", sa.String(32), nullable=True),
            sa.Column("eta_source", sa.String(32), nullable=True),
            sa.Column("customs_handoff_date", sa.String(32), nullable=True),
            sa.Column("delivery_date_planned", sa.String(32), nullable=True),
            sa.Column("delivery_date_actual", sa.String(32), nullable=True),
            sa.Column("responsible_manager_id", sa.String(128), nullable=True),
            sa.Column("origin_lat", sa.String(32), nullable=True),
            sa.Column("origin_lng", sa.String(32), nullable=True),
            sa.Column("destination_lat", sa.String(32), nullable=True),
            sa.Column("destination_lng", sa.String(32), nullable=True),
            sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("payload", JSONB(), nullable=True),
            *_ts_cols(),
        )
        op.create_index("ix_auto_ops_shipments_org", "auto_ops_shipments", ["organization_id"])
        op.create_index("ix_auto_ops_shipments_vehicle", "auto_ops_shipments", ["vehicle_id"])
        op.create_index("ix_auto_ops_shipments_status", "auto_ops_shipments", ["organization_id", "status"])

    if not _exists("auto_ops_carriers"):
        op.create_table(
            "auto_ops_carriers",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("company_name", sa.String(256), nullable=False),
            sa.Column("type", sa.String(32), nullable=False, server_default="other"),
            sa.Column("country", sa.String(64), nullable=True),
            sa.Column("contact_person", sa.String(256), nullable=True),
            sa.Column("phone", sa.String(64), nullable=True),
            sa.Column("email", sa.String(256), nullable=True),
            sa.Column("telegram", sa.String(128), nullable=True),
            sa.Column("whatsapp", sa.String(64), nullable=True),
            sa.Column("website", sa.String(512), nullable=True),
            sa.Column("address", sa.String(512), nullable=True),
            sa.Column("tax_id", sa.String(64), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("rating", sa.String(16), nullable=True),
            sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("payload", JSONB(), nullable=True),
            *_ts_cols(),
        )
        op.create_index("ix_auto_ops_carriers_org", "auto_ops_carriers", ["organization_id"])

    if not _exists("auto_ops_drivers"):
        op.create_table(
            "auto_ops_drivers",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("full_name", sa.String(256), nullable=False),
            sa.Column("phone", sa.String(64), nullable=True),
            sa.Column("telegram", sa.String(128), nullable=True),
            sa.Column("whatsapp", sa.String(64), nullable=True),
            sa.Column("passport_ref", sa.String(128), nullable=True),
            sa.Column("driver_license", sa.String(128), nullable=True),
            sa.Column("carrier_id", sa.String(64), nullable=True),
            sa.Column("truck_id", sa.String(64), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("payload", JSONB(), nullable=True),
            *_ts_cols(),
        )
        op.create_index("ix_auto_ops_drivers_org", "auto_ops_drivers", ["organization_id"])

    if not _exists("auto_ops_trucks"):
        op.create_table(
            "auto_ops_trucks",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("type", sa.String(32), nullable=False, server_default="truck"),
            sa.Column("plate_number", sa.String(64), nullable=False),
            sa.Column("country", sa.String(64), nullable=True),
            sa.Column("brand", sa.String(128), nullable=True),
            sa.Column("model", sa.String(128), nullable=True),
            sa.Column("vin", sa.String(32), nullable=True),
            sa.Column("carrier_id", sa.String(64), nullable=True),
            sa.Column("driver_id", sa.String(64), nullable=True),
            sa.Column("capacity", sa.String(64), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("payload", JSONB(), nullable=True),
            *_ts_cols(),
        )
        op.create_index("ix_auto_ops_trucks_org", "auto_ops_trucks", ["organization_id"])

    if not _exists("auto_ops_containers"):
        op.create_table(
            "auto_ops_containers",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("container_number", sa.String(32), nullable=False),
            sa.Column("container_type", sa.String(16), nullable=False, server_default="40HC"),
            sa.Column("shipping_line", sa.String(128), nullable=True),
            sa.Column("booking_number", sa.String(128), nullable=True),
            sa.Column("seal_number", sa.String(64), nullable=True),
            sa.Column("origin_port", sa.String(64), nullable=True),
            sa.Column("destination_port", sa.String(64), nullable=True),
            sa.Column("etd", sa.String(32), nullable=True),
            sa.Column("eta", sa.String(32), nullable=True),
            sa.Column("status", sa.String(32), nullable=False, server_default="PLANNED"),
            sa.Column("current_location", sa.String(256), nullable=True),
            sa.Column("tracking_url", sa.String(1024), nullable=True),
            sa.Column("tracking_mode", sa.String(32), nullable=True),
            sa.Column("responsible_manager_id", sa.String(128), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("payload", JSONB(), nullable=True),
            *_ts_cols(),
            sa.UniqueConstraint("organization_id", "container_number", name="uq_auto_ops_containers_org_number"),
        )
        op.create_index("ix_auto_ops_containers_org", "auto_ops_containers", ["organization_id"])

    if not _exists("auto_ops_container_vehicles"):
        op.create_table(
            "auto_ops_container_vehicles",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("container_id", sa.String(64), nullable=False),
            sa.Column("vehicle_id", sa.String(64), nullable=False),
            sa.Column("released_at", sa.String(64), nullable=True),
            sa.Column("payload", JSONB(), nullable=True),
            *_ts_cols(),
        )
        op.create_index("ix_auto_ops_container_vehicles_org", "auto_ops_container_vehicles", ["organization_id"])

    if not _exists("auto_ops_vessels"):
        op.create_table(
            "auto_ops_vessels",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("name", sa.String(256), nullable=False),
            sa.Column("imo", sa.String(32), nullable=True),
            sa.Column("mmsi", sa.String(32), nullable=True),
            sa.Column("shipping_line", sa.String(128), nullable=True),
            sa.Column("voyage_number", sa.String(64), nullable=True),
            sa.Column("origin_port", sa.String(64), nullable=True),
            sa.Column("destination_port", sa.String(64), nullable=True),
            sa.Column("etd", sa.String(32), nullable=True),
            sa.Column("eta", sa.String(32), nullable=True),
            sa.Column("status", sa.String(32), nullable=False, server_default="PLANNED"),
            sa.Column("tracking_url", sa.String(1024), nullable=True),
            sa.Column("position_source", sa.String(32), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("payload", JSONB(), nullable=True),
            *_ts_cols(),
        )
        op.create_index("ix_auto_ops_vessels_org", "auto_ops_vessels", ["organization_id"])

    if not _exists("auto_ops_ports"):
        op.create_table(
            "auto_ops_ports",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("name", sa.String(256), nullable=False),
            sa.Column("unlocode", sa.String(8), nullable=True),
            sa.Column("country", sa.String(64), nullable=True),
            sa.Column("city", sa.String(128), nullable=True),
            sa.Column("address", sa.String(512), nullable=True),
            sa.Column("timezone", sa.String(64), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("payload", JSONB(), nullable=True),
            *_ts_cols(),
        )
        op.create_index("ix_auto_ops_ports_org", "auto_ops_ports", ["organization_id"])

    if not _exists("auto_ops_logistics_events"):
        op.create_table(
            "auto_ops_logistics_events",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("shipment_id", sa.String(64), nullable=False),
            sa.Column("event_type", sa.String(64), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("actor_id", sa.String(128), nullable=True),
            sa.Column("actor_role", sa.String(64), nullable=True),
            sa.Column("source", sa.String(32), nullable=True),
            sa.Column("location", sa.String(256), nullable=True),
            sa.Column("document_id", sa.String(64), nullable=True),
            sa.Column("photo_id", sa.String(64), nullable=True),
            sa.Column("immutable", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("payload", JSONB(), nullable=True),
            *_ts_cols(),
        )
        op.create_index("ix_auto_ops_logistics_events_ship", "auto_ops_logistics_events", ["shipment_id"])

    if not _exists("auto_ops_notifications"):
        op.create_table(
            "auto_ops_notifications",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("notification_type", sa.String(64), nullable=False),
            sa.Column("title", sa.String(512), nullable=False),
            sa.Column("entity_type", sa.String(64), nullable=True),
            sa.Column("entity_id", sa.String(64), nullable=True),
            sa.Column("shipment_id", sa.String(64), nullable=True),
            sa.Column("vehicle_id", sa.String(64), nullable=True),
            sa.Column("dedupe_key", sa.String(256), nullable=True),
            sa.Column("channel", sa.String(32), nullable=True),
            sa.Column("payload", JSONB(), nullable=True),
            *_ts_cols(),
        )
        op.create_index("ix_auto_ops_notifications_org", "auto_ops_notifications", ["organization_id"])

    if not _exists("auto_ops_logistics_settings"):
        op.create_table(
            "auto_ops_logistics_settings",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("yellow_days", sa.Integer(), nullable=True),
            sa.Column("orange_days", sa.Integer(), nullable=True),
            sa.Column("default_origin_country", sa.String(64), nullable=True),
            sa.Column("default_destination_country", sa.String(64), nullable=True),
            sa.Column("default_origin_port", sa.String(64), nullable=True),
            sa.Column("default_destination_port", sa.String(64), nullable=True),
            sa.Column("payload", JSONB(), nullable=True),
            *_ts_cols(),
        )
        op.create_index("ix_auto_ops_logistics_settings_org", "auto_ops_logistics_settings", ["organization_id"])


def downgrade() -> None:
    for name in (
        "auto_ops_logistics_settings",
        "auto_ops_notifications",
        "auto_ops_logistics_events",
        "auto_ops_ports",
        "auto_ops_vessels",
        "auto_ops_container_vehicles",
        "auto_ops_containers",
        "auto_ops_trucks",
        "auto_ops_drivers",
        "auto_ops_carriers",
        "auto_ops_shipments",
    ):
        op.drop_table(name)
