"""automotive_partner_branding_v1

Revision ID: b5c6d7e89012
Revises: a4b5c6d78901
Create Date: 2026-07-13 20:00:00.000000

"""
from __future__ import annotations

import json
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "b5c6d7e89012"
down_revision: Union[str, None] = "a4b5c6d78901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_PARTNERS = (
    ("credit_agricole", "Credit Agricole", "CREDIT", "https://credit-agricole.ua", None, False, "🏦"),
    ("privatbank", "PrivatBank", "CREDIT", "https://privatbank.ua", None, False, "💳"),
    ("eco_leasing", "Eco Leasing", "LEASING", "https://ecoleasing.ua", None, False, "♻️"),
    ("smart_auto_cargo", "Smart Auto Cargo", "LOGISTICS", "https://smartautocargo.ua", None, False, "🚚"),
    ("bidex_legal", "BidEx Legal", "LEGAL", None, None, False, "⚖️"),
)

DEFAULT_CTAS = (
    ("website", "🌐 Visit website", "url", None, 10),
    ("callback", "📞 Request callback", "lead", None, 20),
)

SGTAS_EXTRA_CTAS = (
    ("products", "📋 View products", "products", None, 5),
)


def _insert_partner(conn, code, name, ptype, website, channel, tenant_mode, emoji):
    partner_id = str(uuid.uuid4())
    conn.execute(
        sa.text(
            """
            INSERT INTO automotive_partner_v1_partners
            (id, code, name, partner_type, website, telegram_channel, tenant_mode_enabled, is_active, metadata, created_at, updated_at)
            VALUES (:id, :code, :name, :ptype, :website, :channel, :tenant_mode, true, :metadata, NOW(), NOW())
            ON CONFLICT (code) DO NOTHING
            """
        ),
        {
            "id": partner_id,
            "code": code,
            "name": name,
            "ptype": ptype,
            "website": website,
            "channel": channel,
            "tenant_mode": tenant_mode,
            "metadata": json.dumps({"logo_emoji": emoji}),
        },
    )
    row = conn.execute(
        sa.text("SELECT id FROM automotive_partner_v1_partners WHERE code = :code"),
        {"code": code},
    ).first()
    return str(row[0]) if row else partner_id


def _insert_branding(conn, partner_id, title, description, logo_url, emoji, sort_order, logo_enabled=True):
    conn.execute(
        sa.text(
            """
            INSERT INTO automotive_partner_v1_branding
            (id, partner_id, card_title, short_description, logo_url, logo_emoji, logo_enabled, sort_order, is_active, created_at, updated_at)
            VALUES (:id, :partner_id, :title, :description, :logo_url, :emoji, :logo_enabled, :sort_order, true, NOW(), NOW())
            ON CONFLICT (partner_id) DO NOTHING
            """
        ),
        {
            "id": str(uuid.uuid4()),
            "partner_id": partner_id,
            "title": title,
            "description": description,
            "logo_url": logo_url,
            "emoji": emoji,
            "logo_enabled": logo_enabled,
            "sort_order": sort_order,
        },
    )


def _insert_ctas(conn, partner_id, ctas, website):
    for cta_code, label, action_type, action_value, sort_order in ctas:
        value = action_value or (website if action_type == "url" else None)
        conn.execute(
            sa.text(
                """
                INSERT INTO automotive_partner_v1_cta_buttons
                (id, partner_id, cta_code, label, action_type, action_value, sort_order, is_active, created_at, updated_at)
                VALUES (:id, :partner_id, :cta_code, :label, :action_type, :action_value, :sort_order, true, NOW(), NOW())
                ON CONFLICT (partner_id, cta_code) DO NOTHING
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "partner_id": partner_id,
                "cta_code": cta_code,
                "label": label,
                "action_type": action_type,
                "action_value": value,
                "sort_order": sort_order,
            },
        )


def upgrade() -> None:
    op.create_table(
        "automotive_partner_v1_branding",
        sa.Column("partner_id", sa.UUID(), nullable=False),
        sa.Column("card_title", sa.String(length=255), nullable=True),
        sa.Column("short_description", sa.Text(), nullable=True),
        sa.Column("logo_url", sa.String(length=1024), nullable=True),
        sa.Column("logo_file_id", sa.String(length=512), nullable=True),
        sa.Column("logo_emoji", sa.String(length=16), nullable=True),
        sa.Column("logo_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["partner_id"], ["automotive_partner_v1_partners.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("partner_id", name="uq_automotive_partner_v1_branding_partner"),
    )
    op.create_index("ix_automotive_partner_v1_branding_active", "automotive_partner_v1_branding", ["is_active"])

    op.create_table(
        "automotive_partner_v1_cta_buttons",
        sa.Column("partner_id", sa.UUID(), nullable=False),
        sa.Column("cta_code", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=128), nullable=False),
        sa.Column("action_type", sa.String(length=32), nullable=False),
        sa.Column("action_value", sa.String(length=512), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["partner_id"], ["automotive_partner_v1_partners.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("partner_id", "cta_code", name="uq_automotive_partner_v1_cta_code"),
    )
    op.create_index("ix_automotive_partner_v1_cta_partner", "automotive_partner_v1_cta_buttons", ["partner_id"])
    op.create_index("ix_automotive_partner_v1_cta_active", "automotive_partner_v1_cta_buttons", ["is_active"])

    conn = op.get_bind()

    sgtas_row = conn.execute(
        sa.text("SELECT id, website FROM automotive_partner_v1_partners WHERE code = 'sgtas'")
    ).first()
    if sgtas_row:
        sgtas_id = str(sgtas_row[0])
        sgtas_site = sgtas_row[1]
        _insert_branding(
            conn,
            sgtas_id,
            "SG TAS",
            "Ukrainian insurance leader — OSAGO, CASCO, Green Card, travel and property coverage.",
            "https://sgtas.ua/local/templates/main/images/logo.svg",
            "🛡",
            10,
            True,
        )
        _insert_ctas(conn, sgtas_id, SGTAS_EXTRA_CTAS + DEFAULT_CTAS, sgtas_site)

    descriptions = {
        "credit_agricole": "Auto loans and credit programs for vehicle purchases.",
        "privatbank": "PrivatBank auto credit and installment plans for dealers and buyers.",
        "eco_leasing": "Eco-friendly vehicle leasing for businesses and private clients.",
        "smart_auto_cargo": "Vehicle logistics, delivery, and cross-border auto transport.",
        "bidex_legal": "Legal support for automotive deals, contracts, and compliance.",
    }
    websites = {
        "credit_agricole": "https://credit-agricole.ua",
        "privatbank": "https://privatbank.ua",
        "eco_leasing": "https://ecoleasing.ua",
        "smart_auto_cargo": "https://smartautocargo.ua",
        "bidex_legal": "https://bidex.ua",
    }

    for idx, (code, name, ptype, website, channel, tenant_mode, emoji) in enumerate(NEW_PARTNERS):
        partner_id = _insert_partner(conn, code, name, ptype, website, channel, tenant_mode, emoji)
        _insert_branding(
            conn,
            partner_id,
            name,
            descriptions.get(code, f"{name} automotive partner."),
            None,
            emoji,
            (idx + 1) * 10,
            True,
        )
        _insert_ctas(conn, partner_id, DEFAULT_CTAS, websites.get(code, website))


def downgrade() -> None:
    op.drop_index("ix_automotive_partner_v1_cta_active", table_name="automotive_partner_v1_cta_buttons")
    op.drop_index("ix_automotive_partner_v1_cta_partner", table_name="automotive_partner_v1_cta_buttons")
    op.drop_table("automotive_partner_v1_cta_buttons")
    op.drop_index("ix_automotive_partner_v1_branding_active", table_name="automotive_partner_v1_branding")
    op.drop_table("automotive_partner_v1_branding")
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "DELETE FROM automotive_partner_v1_partners WHERE code IN "
            "('credit_agricole','privatbank','eco_leasing','smart_auto_cargo','bidex_legal')"
        )
    )
