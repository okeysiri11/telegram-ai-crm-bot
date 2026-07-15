"""CRM platform — client_requests, marketplace_listings, pipeline fields

Revision ID: f9s901234567
Revises: f9r890123456
Create Date: 2026-07-15 17:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "f9s901234567"
down_revision: Union[str, None] = "f9r890123456"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "marketplace_listings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="ACTIVE"),
        sa.Column("seller_telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("seller_username", sa.String(length=255), nullable=True),
        sa.Column("brand", sa.String(length=128), nullable=True),
        sa.Column("model", sa.String(length=128), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("price", sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column("currency", sa.String(length=8), nullable=True),
        sa.Column("fuel", sa.String(length=64), nullable=True),
        sa.Column("engine", sa.String(length=64), nullable=True),
        sa.Column("transmission", sa.String(length=64), nullable=True),
        sa.Column("city", sa.String(length=128), nullable=True),
        sa.Column("mileage", sa.Integer(), nullable=True),
        sa.Column("vin", sa.String(length=17), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("photo_file_ids", JSONB, nullable=True),
        sa.Column("listing_payload", JSONB, nullable=True),
        sa.Column("client_request_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_marketplace_listings_seller", "marketplace_listings", ["seller_telegram_id"])
    op.create_index("ix_marketplace_listings_status", "marketplace_listings", ["status"])
    op.create_index(
        "ix_marketplace_listings_brand_model",
        "marketplace_listings",
        ["brand", "model"],
    )

    op.create_table(
        "client_requests",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("request_number", sa.String(length=32), nullable=False),
        sa.Column("request_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="NEW"),
        sa.Column("funnel_stage", sa.String(length=32), nullable=False, server_default="NEW_LEAD"),
        sa.Column("client_telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("client_username", sa.String(length=255), nullable=True),
        sa.Column("client_first_name", sa.String(length=255), nullable=True),
        sa.Column("client_last_name", sa.String(length=255), nullable=True),
        sa.Column("client_phone", sa.String(length=255), nullable=True),
        sa.Column("client_language_code", sa.String(length=8), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("vin", sa.String(length=17), nullable=True),
        sa.Column("brand", sa.String(length=128), nullable=True),
        sa.Column("model", sa.String(length=128), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("mileage", sa.Integer(), nullable=True),
        sa.Column("budget", sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column("price", sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column("fuel", sa.String(length=64), nullable=True),
        sa.Column("engine", sa.String(length=64), nullable=True),
        sa.Column("transmission", sa.String(length=64), nullable=True),
        sa.Column("city", sa.String(length=128), nullable=True),
        sa.Column("service_type", sa.String(length=128), nullable=True),
        sa.Column("photo_file_ids", JSONB, nullable=True),
        sa.Column("ai_qualification", JSONB, nullable=True),
        sa.Column("manager_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column(
            "auto_request_id",
            UUID(as_uuid=True),
            sa.ForeignKey("auto_client_requests_v1.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "marketplace_listing_id",
            UUID(as_uuid=True),
            sa.ForeignKey("marketplace_listings.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_client_requests_client", "client_requests", ["client_telegram_id"])
    op.create_index("ix_client_requests_manager", "client_requests", ["manager_id"])
    op.create_index("ix_client_requests_status", "client_requests", ["status"])
    op.create_index("ix_client_requests_funnel", "client_requests", ["funnel_stage"])
    op.create_index("ix_client_requests_type", "client_requests", ["request_type"])
    op.create_index("ix_client_requests_number", "client_requests", ["request_number"], unique=True)

    op.add_column(
        "auto_client_requests_v1",
        sa.Column("funnel_stage", sa.String(length=32), nullable=True, server_default="NEW_LEAD"),
    )
    op.add_column(
        "auto_client_requests_v1",
        sa.Column("fuel", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "auto_client_requests_v1",
        sa.Column("engine", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "auto_client_requests_v1",
        sa.Column("transmission", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "auto_client_requests_v1",
        sa.Column("city", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "auto_client_requests_v1",
        sa.Column("client_request_id", UUID(as_uuid=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("auto_client_requests_v1", "client_request_id")
    op.drop_column("auto_client_requests_v1", "city")
    op.drop_column("auto_client_requests_v1", "transmission")
    op.drop_column("auto_client_requests_v1", "engine")
    op.drop_column("auto_client_requests_v1", "fuel")
    op.drop_column("auto_client_requests_v1", "funnel_stage")
    op.drop_index("ix_client_requests_number", table_name="client_requests")
    op.drop_index("ix_client_requests_type", table_name="client_requests")
    op.drop_index("ix_client_requests_funnel", table_name="client_requests")
    op.drop_index("ix_client_requests_status", table_name="client_requests")
    op.drop_index("ix_client_requests_manager", table_name="client_requests")
    op.drop_index("ix_client_requests_client", table_name="client_requests")
    op.drop_table("client_requests")
    op.drop_index("ix_marketplace_listings_brand_model", table_name="marketplace_listings")
    op.drop_index("ix_marketplace_listings_status", table_name="marketplace_listings")
    op.drop_index("ix_marketplace_listings_seller", table_name="marketplace_listings")
    op.drop_table("marketplace_listings")
