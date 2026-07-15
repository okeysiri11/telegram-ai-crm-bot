"""Production hardening — audit_log, inventory, SLA, platform roles

Revision ID: f9t012345678
Revises: f9s901234567
Create Date: 2026-07-15 17:40:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "f9t012345678"
down_revision: Union[str, None] = "f9s901234567"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_log",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=128), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("payload", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_audit_log_event_type", "audit_log", ["event_type"])
    op.create_index("ix_audit_log_entity", "audit_log", ["entity_type", "entity_id"])
    op.create_index("ix_audit_log_user_id", "audit_log", ["user_id"])
    op.create_index("ix_audit_log_created_at", "audit_log", ["created_at"])

    op.create_table(
        "inventory",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("brand", sa.String(length=128), nullable=True),
        sa.Column("model", sa.String(length=128), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("price", sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column("currency", sa.String(length=8), nullable=True),
        sa.Column("photos", JSONB, nullable=True),
        sa.Column("vin", sa.String(length=17), nullable=True),
        sa.Column("seller_id", sa.BigInteger(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="DRAFT"),
        sa.Column("fuel", sa.String(length=64), nullable=True),
        sa.Column("transmission", sa.String(length=64), nullable=True),
        sa.Column("mileage", sa.Integer(), nullable=True),
        sa.Column("city", sa.String(length=128), nullable=True),
        sa.Column("engine", sa.String(length=64), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "marketplace_listing_id",
            UUID(as_uuid=True),
            sa.ForeignKey("marketplace_listings.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_inventory_status", "inventory", ["status"])
    op.create_index("ix_inventory_seller", "inventory", ["seller_id"])
    op.create_index("ix_inventory_brand_model", "inventory", ["brand", "model"])
    op.create_index("ix_inventory_year", "inventory", ["year"])
    op.create_index("ix_inventory_price", "inventory", ["price"])
    op.create_index("ix_inventory_city", "inventory", ["city"])
    op.create_index("ix_inventory_fuel", "inventory", ["fuel"])

    op.create_table(
        "lead_sla_records",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "client_request_id",
            UUID(as_uuid=True),
            sa.ForeignKey("client_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("request_number", sa.String(length=32), nullable=False),
        sa.Column("created_at_lead", sa.DateTime(timezone=True), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("first_response_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("time_to_assignment_sec", sa.Integer(), nullable=True),
        sa.Column("time_to_first_response_sec", sa.Integer(), nullable=True),
        sa.Column("time_to_close_sec", sa.Integer(), nullable=True),
        sa.Column("priority", sa.String(length=16), nullable=False, server_default="MEDIUM"),
        sa.Column("sla_breached", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("escalation_level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("manager_telegram_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_lead_sla_request", "lead_sla_records", ["client_request_id"], unique=True)
    op.create_index("ix_lead_sla_priority", "lead_sla_records", ["priority"])
    op.create_index("ix_lead_sla_breached", "lead_sla_records", ["sla_breached"])


def downgrade() -> None:
    op.drop_index("ix_lead_sla_breached", table_name="lead_sla_records")
    op.drop_index("ix_lead_sla_priority", table_name="lead_sla_records")
    op.drop_index("ix_lead_sla_request", table_name="lead_sla_records")
    op.drop_table("lead_sla_records")
    op.drop_index("ix_inventory_fuel", table_name="inventory")
    op.drop_index("ix_inventory_city", table_name="inventory")
    op.drop_index("ix_inventory_price", table_name="inventory")
    op.drop_index("ix_inventory_year", table_name="inventory")
    op.drop_index("ix_inventory_brand_model", table_name="inventory")
    op.drop_index("ix_inventory_seller", table_name="inventory")
    op.drop_index("ix_inventory_status", table_name="inventory")
    op.drop_table("inventory")
    op.drop_index("ix_audit_log_created_at", table_name="audit_log")
    op.drop_index("ix_audit_log_user_id", table_name="audit_log")
    op.drop_index("ix_audit_log_entity", table_name="audit_log")
    op.drop_index("ix_audit_log_event_type", table_name="audit_log")
    op.drop_table("audit_log")
