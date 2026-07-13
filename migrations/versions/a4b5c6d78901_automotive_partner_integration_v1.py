"""automotive_partner_integration_v1

Revision ID: a4b5c6d78901
Revises: f3a4b5c67890
Create Date: 2026-07-13 19:30:00.000000

"""
from __future__ import annotations

import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "a4b5c6d78901"
down_revision: Union[str, None] = "f3a4b5c67890"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SGTAS_ID = str(uuid.uuid4())
BORODA_ID = str(uuid.uuid4())

SGTAS_PRODUCTS = (
    ("OSAGO", "OSAGO", "Mandatory auto liability insurance (Автоцивілка)", 10),
    ("CASCO", "CASCO", "Comprehensive vehicle insurance (КАСКО)", 20),
    ("GREEN_CARD", "Green Card", "International motor insurance (Зелена картка)", 30),
    ("TRAVEL", "Travel Insurance", "Travel insurance for drivers and passengers", 40),
    ("PROPERTY", "Property Insurance", "Property and home insurance", 50),
)


def upgrade() -> None:
    op.create_table(
        "automotive_partner_v1_partners",
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("partner_type", sa.String(length=32), nullable=False),
        sa.Column("website", sa.String(length=512), nullable=True),
        sa.Column("telegram_channel", sa.String(length=128), nullable=True),
        sa.Column("tenant_mode_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_automotive_partner_v1_partners_code"),
    )
    op.create_index("ix_automotive_partner_v1_partners_type", "automotive_partner_v1_partners", ["partner_type"])
    op.create_index("ix_automotive_partner_v1_partners_active", "automotive_partner_v1_partners", ["is_active"])

    op.create_table(
        "automotive_partner_v1_partner_products",
        sa.Column("partner_id", sa.UUID(), nullable=False),
        sa.Column("product_code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("external_url", sa.String(length=512), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["partner_id"], ["automotive_partner_v1_partners.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("partner_id", "product_code", name="uq_automotive_partner_v1_products_code"),
    )
    op.create_index("ix_automotive_partner_v1_products_partner", "automotive_partner_v1_partner_products", ["partner_id"])
    op.create_index("ix_automotive_partner_v1_products_active", "automotive_partner_v1_partner_products", ["is_active"])

    op.create_table(
        "automotive_partner_v1_dealer_sources",
        sa.Column("partner_id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=True),
        sa.Column("source_code", sa.String(length=64), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("channel_username", sa.String(length=128), nullable=True),
        sa.Column("channel_id", sa.String(length=64), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["partner_id"], ["automotive_partner_v1_partners.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["partner_tenant_engine_v1_tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("partner_id", "source_code", name="uq_automotive_partner_v1_dealer_sources_code"),
    )
    op.create_index("ix_automotive_partner_v1_dealer_sources_tenant", "automotive_partner_v1_dealer_sources", ["tenant_id"])
    op.create_index("ix_automotive_partner_v1_dealer_sources_partner", "automotive_partner_v1_dealer_sources", ["partner_id"])
    op.create_index("ix_automotive_partner_v1_dealer_sources_active", "automotive_partner_v1_dealer_sources", ["is_active"])

    op.create_table(
        "automotive_partner_v1_insurance_offers",
        sa.Column("partner_id", sa.UUID(), nullable=False),
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("external_url", sa.String(length=512), nullable=True),
        sa.Column("premium_from", sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default=sa.text("'UAH'")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["partner_id"], ["automotive_partner_v1_partners.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["automotive_partner_v1_partner_products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["partner_tenant_engine_v1_tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_automotive_partner_v1_insurance_offers_partner", "automotive_partner_v1_insurance_offers", ["partner_id"])
    op.create_index("ix_automotive_partner_v1_insurance_offers_product", "automotive_partner_v1_insurance_offers", ["product_id"])
    op.create_index("ix_automotive_partner_v1_insurance_offers_tenant", "automotive_partner_v1_insurance_offers", ["tenant_id"])
    op.create_index("ix_automotive_partner_v1_insurance_offers_active", "automotive_partner_v1_insurance_offers", ["is_active"])

    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            INSERT INTO automotive_partner_v1_partners
            (id, code, name, partner_type, website, telegram_channel, tenant_mode_enabled, is_active, metadata, created_at, updated_at)
            VALUES
            (:sgtas_id, 'sgtas', 'SG TAS', 'INSURANCE', 'https://sgtas.ua', NULL, false, true, '{"brand":"SG TAS"}'::jsonb, NOW(), NOW()),
            (:boroda_id, 'boroda_cars', 'Boroda Cars', 'DEALER', NULL, '@boroda_cars', true, true, '{"display_name":"Boroda Cars"}'::jsonb, NOW(), NOW())
            """
        ),
        {"sgtas_id": SGTAS_ID, "boroda_id": BORODA_ID},
    )

    for product_code, name, description, sort_order in SGTAS_PRODUCTS:
        product_id = str(uuid.uuid4())
        conn.execute(
            sa.text(
                """
                INSERT INTO automotive_partner_v1_partner_products
                (id, partner_id, product_code, name, description, external_url, sort_order, is_active, created_at, updated_at)
                VALUES (:id, :partner_id, :product_code, :name, :description, :external_url, :sort_order, true, NOW(), NOW())
                """
            ),
            {
                "id": product_id,
                "partner_id": SGTAS_ID,
                "product_code": product_code,
                "name": name,
                "description": description,
                "external_url": "https://sgtas.ua",
                "sort_order": sort_order,
            },
        )
        conn.execute(
            sa.text(
                """
                INSERT INTO automotive_partner_v1_insurance_offers
                (id, partner_id, product_id, tenant_id, title, summary, external_url, currency, is_active, created_at, updated_at)
                VALUES (:id, :partner_id, :product_id, NULL, :title, :summary, :external_url, 'UAH', true, NOW(), NOW())
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "partner_id": SGTAS_ID,
                "product_id": product_id,
                "title": f"SG TAS — {name}",
                "summary": description,
                "external_url": "https://sgtas.ua",
            },
        )

    conn.execute(
        sa.text(
            """
            INSERT INTO automotive_partner_v1_dealer_sources
            (id, partner_id, tenant_id, source_code, source_type, channel_username, channel_id, is_active, metadata, created_at, updated_at)
            VALUES (:id, :partner_id, NULL, 'boroda_cars_telegram', 'telegram_channel', 'boroda_cars', NULL, true, '{"multi_dealer_ready": true}'::jsonb, NOW(), NOW())
            """
        ),
        {"id": str(uuid.uuid4()), "partner_id": BORODA_ID},
    )


def downgrade() -> None:
    op.drop_index("ix_automotive_partner_v1_insurance_offers_active", table_name="automotive_partner_v1_insurance_offers")
    op.drop_index("ix_automotive_partner_v1_insurance_offers_tenant", table_name="automotive_partner_v1_insurance_offers")
    op.drop_index("ix_automotive_partner_v1_insurance_offers_product", table_name="automotive_partner_v1_insurance_offers")
    op.drop_index("ix_automotive_partner_v1_insurance_offers_partner", table_name="automotive_partner_v1_insurance_offers")
    op.drop_table("automotive_partner_v1_insurance_offers")
    op.drop_index("ix_automotive_partner_v1_dealer_sources_active", table_name="automotive_partner_v1_dealer_sources")
    op.drop_index("ix_automotive_partner_v1_dealer_sources_partner", table_name="automotive_partner_v1_dealer_sources")
    op.drop_index("ix_automotive_partner_v1_dealer_sources_tenant", table_name="automotive_partner_v1_dealer_sources")
    op.drop_table("automotive_partner_v1_dealer_sources")
    op.drop_index("ix_automotive_partner_v1_products_active", table_name="automotive_partner_v1_partner_products")
    op.drop_index("ix_automotive_partner_v1_products_partner", table_name="automotive_partner_v1_partner_products")
    op.drop_table("automotive_partner_v1_partner_products")
    op.drop_index("ix_automotive_partner_v1_partners_active", table_name="automotive_partner_v1_partners")
    op.drop_index("ix_automotive_partner_v1_partners_type", table_name="automotive_partner_v1_partners")
    op.drop_table("automotive_partner_v1_partners")
