"""automotive_revenue_engine_v1

Revision ID: c6d7e8901234
Revises: b5c6d7e89012
Create Date: 2026-07-13 21:00:00.000000

"""
from __future__ import annotations

import json
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "c6d7e8901234"
down_revision: Union[str, None] = "b5c6d7e89012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NOTARY_PARTNER = (
    "bidex_notary",
    "BidEx Notary",
    "NOTARY",
    None,
    None,
    False,
    "📜",
)


def _ts_cols():
    return [
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    ]


def _insert_notary_partner(conn) -> None:
    code, name, ptype, website, channel, tenant_mode, emoji = NOTARY_PARTNER
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


def upgrade() -> None:
    op.create_table(
        "automotive_revenue_v1_partner_leads",
        sa.Column("tenant_id", sa.UUID(), nullable=True),
        sa.Column("partner_id", sa.UUID(), nullable=False),
        sa.Column("lead_id", sa.UUID(), nullable=False),
        sa.Column("source_id", sa.String(length=128), nullable=True),
        sa.Column("vertical", sa.String(length=32), nullable=False),
        sa.Column("commission_amount", sa.Numeric(precision=20, scale=2), server_default="0", nullable=False),
        sa.Column("commission_status", sa.String(length=32), server_default="PENDING", nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        *_ts_cols(),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["partner_id"], ["automotive_partner_v1_partners.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lead_id"], ["lead_automation_engine_v1_leads.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_automotive_revenue_v1_partner_leads_tenant",
        "automotive_revenue_v1_partner_leads",
        ["tenant_id"],
    )
    op.create_index(
        "ix_automotive_revenue_v1_partner_leads_partner",
        "automotive_revenue_v1_partner_leads",
        ["partner_id"],
    )
    op.create_index(
        "ix_automotive_revenue_v1_partner_leads_lead",
        "automotive_revenue_v1_partner_leads",
        ["lead_id"],
    )
    op.create_index(
        "ix_automotive_revenue_v1_partner_leads_status",
        "automotive_revenue_v1_partner_leads",
        ["commission_status"],
    )
    op.create_index(
        "ix_automotive_revenue_v1_partner_leads_vertical",
        "automotive_revenue_v1_partner_leads",
        ["vertical"],
    )

    op.create_table(
        "automotive_revenue_v1_partner_commissions",
        sa.Column("tenant_id", sa.UUID(), nullable=True),
        sa.Column("partner_id", sa.UUID(), nullable=False),
        sa.Column("partner_lead_id", sa.UUID(), nullable=True),
        sa.Column("lead_id", sa.UUID(), nullable=True),
        sa.Column("source_id", sa.String(length=128), nullable=True),
        sa.Column("service_type", sa.String(length=32), nullable=False),
        sa.Column("commission_amount", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("commission_status", sa.String(length=32), server_default="PENDING", nullable=False),
        sa.Column("rate_pct", sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column("deal_id", sa.UUID(), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        *_ts_cols(),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["partner_id"], ["automotive_partner_v1_partners.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["partner_lead_id"],
            ["automotive_revenue_v1_partner_leads.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["lead_id"], ["lead_automation_engine_v1_leads.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_automotive_revenue_v1_partner_comm_tenant",
        "automotive_revenue_v1_partner_commissions",
        ["tenant_id"],
    )
    op.create_index(
        "ix_automotive_revenue_v1_partner_comm_partner",
        "automotive_revenue_v1_partner_commissions",
        ["partner_id"],
    )
    op.create_index(
        "ix_automotive_revenue_v1_partner_comm_status",
        "automotive_revenue_v1_partner_commissions",
        ["commission_status"],
    )
    op.create_index(
        "ix_automotive_revenue_v1_partner_comm_service",
        "automotive_revenue_v1_partner_commissions",
        ["service_type"],
    )

    op.create_table(
        "automotive_revenue_v1_partner_settlements",
        sa.Column("tenant_id", sa.UUID(), nullable=True),
        sa.Column("partner_id", sa.UUID(), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("total_amount", sa.Numeric(precision=20, scale=2), server_default="0", nullable=False),
        sa.Column("currency", sa.String(length=8), server_default="UAH", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="OPEN", nullable=False),
        sa.Column("settled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        *_ts_cols(),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["partner_id"], ["automotive_partner_v1_partners.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_automotive_revenue_v1_settlements_tenant",
        "automotive_revenue_v1_partner_settlements",
        ["tenant_id"],
    )
    op.create_index(
        "ix_automotive_revenue_v1_settlements_partner",
        "automotive_revenue_v1_partner_settlements",
        ["partner_id"],
    )
    op.create_index(
        "ix_automotive_revenue_v1_settlements_status",
        "automotive_revenue_v1_partner_settlements",
        ["status"],
    )

    op.create_table(
        "automotive_revenue_v1_partner_payouts",
        sa.Column("tenant_id", sa.UUID(), nullable=True),
        sa.Column("partner_id", sa.UUID(), nullable=False),
        sa.Column("settlement_id", sa.UUID(), nullable=True),
        sa.Column("amount", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=8), server_default="UAH", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="PENDING", nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        *_ts_cols(),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["partner_id"], ["automotive_partner_v1_partners.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["settlement_id"],
            ["automotive_revenue_v1_partner_settlements.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_automotive_revenue_v1_payouts_tenant",
        "automotive_revenue_v1_partner_payouts",
        ["tenant_id"],
    )
    op.create_index(
        "ix_automotive_revenue_v1_payouts_partner",
        "automotive_revenue_v1_partner_payouts",
        ["partner_id"],
    )
    op.create_index(
        "ix_automotive_revenue_v1_payouts_status",
        "automotive_revenue_v1_partner_payouts",
        ["status"],
    )
    op.create_index(
        "ix_automotive_revenue_v1_payouts_settlement",
        "automotive_revenue_v1_partner_payouts",
        ["settlement_id"],
    )

    op.create_table(
        "automotive_revenue_v1_deal_commissions",
        sa.Column("tenant_id", sa.UUID(), nullable=True),
        sa.Column("deal_id", sa.UUID(), nullable=True),
        sa.Column("partner_id", sa.UUID(), nullable=True),
        sa.Column("lead_id", sa.UUID(), nullable=True),
        sa.Column("source_id", sa.String(length=128), nullable=True),
        sa.Column("service_type", sa.String(length=32), nullable=False),
        sa.Column("commission_amount", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("commission_status", sa.String(length=32), server_default="PENDING", nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        *_ts_cols(),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["partner_id"], ["automotive_partner_v1_partners.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["lead_id"], ["lead_automation_engine_v1_leads.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_automotive_revenue_v1_deal_comm_tenant",
        "automotive_revenue_v1_deal_commissions",
        ["tenant_id"],
    )
    op.create_index(
        "ix_automotive_revenue_v1_deal_comm_deal",
        "automotive_revenue_v1_deal_commissions",
        ["deal_id"],
    )
    op.create_index(
        "ix_automotive_revenue_v1_deal_comm_partner",
        "automotive_revenue_v1_deal_commissions",
        ["partner_id"],
    )
    op.create_index(
        "ix_automotive_revenue_v1_deal_comm_status",
        "automotive_revenue_v1_deal_commissions",
        ["commission_status"],
    )

    op.create_table(
        "automotive_revenue_v1_deal_profit",
        sa.Column("tenant_id", sa.UUID(), nullable=True),
        sa.Column("deal_id", sa.UUID(), nullable=True),
        sa.Column("lead_id", sa.UUID(), nullable=True),
        sa.Column("revenue", sa.Numeric(precision=20, scale=2), server_default="0", nullable=False),
        sa.Column("cost", sa.Numeric(precision=20, scale=2), server_default="0", nullable=False),
        sa.Column("profit", sa.Numeric(precision=20, scale=2), server_default="0", nullable=False),
        sa.Column("margin_pct", sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column("period_month", sa.String(length=7), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        *_ts_cols(),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lead_id"], ["lead_automation_engine_v1_leads.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_automotive_revenue_v1_deal_profit_tenant",
        "automotive_revenue_v1_deal_profit",
        ["tenant_id"],
    )
    op.create_index(
        "ix_automotive_revenue_v1_deal_profit_deal",
        "automotive_revenue_v1_deal_profit",
        ["deal_id"],
    )
    op.create_index(
        "ix_automotive_revenue_v1_deal_profit_period",
        "automotive_revenue_v1_deal_profit",
        ["period_month"],
    )

    op.create_table(
        "automotive_revenue_v1_dealer_referrals",
        sa.Column("tenant_id", sa.UUID(), nullable=True),
        sa.Column("partner_id", sa.UUID(), nullable=False),
        sa.Column("lead_id", sa.UUID(), nullable=False),
        sa.Column("source_id", sa.String(length=128), nullable=True),
        sa.Column("referrer_user_id", sa.BigInteger(), nullable=True),
        sa.Column("customer_name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="NEW", nullable=False),
        sa.Column("commission_amount", sa.Numeric(precision=20, scale=2), server_default="0", nullable=False),
        sa.Column("commission_status", sa.String(length=32), server_default="PENDING", nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        *_ts_cols(),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["partner_id"], ["automotive_partner_v1_partners.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lead_id"], ["lead_automation_engine_v1_leads.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_automotive_revenue_v1_referrals_tenant",
        "automotive_revenue_v1_dealer_referrals",
        ["tenant_id"],
    )
    op.create_index(
        "ix_automotive_revenue_v1_referrals_partner",
        "automotive_revenue_v1_dealer_referrals",
        ["partner_id"],
    )
    op.create_index(
        "ix_automotive_revenue_v1_referrals_lead",
        "automotive_revenue_v1_dealer_referrals",
        ["lead_id"],
    )
    op.create_index(
        "ix_automotive_revenue_v1_referrals_status",
        "automotive_revenue_v1_dealer_referrals",
        ["commission_status"],
    )

    conn = op.get_bind()
    _insert_notary_partner(conn)


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("DELETE FROM automotive_partner_v1_partners WHERE code = 'bidex_notary'")
    )

    op.drop_index(
        "ix_automotive_revenue_v1_referrals_status",
        table_name="automotive_revenue_v1_dealer_referrals",
    )
    op.drop_index(
        "ix_automotive_revenue_v1_referrals_lead",
        table_name="automotive_revenue_v1_dealer_referrals",
    )
    op.drop_index(
        "ix_automotive_revenue_v1_referrals_partner",
        table_name="automotive_revenue_v1_dealer_referrals",
    )
    op.drop_index(
        "ix_automotive_revenue_v1_referrals_tenant",
        table_name="automotive_revenue_v1_dealer_referrals",
    )
    op.drop_table("automotive_revenue_v1_dealer_referrals")

    op.drop_index(
        "ix_automotive_revenue_v1_deal_profit_period",
        table_name="automotive_revenue_v1_deal_profit",
    )
    op.drop_index(
        "ix_automotive_revenue_v1_deal_profit_deal",
        table_name="automotive_revenue_v1_deal_profit",
    )
    op.drop_index(
        "ix_automotive_revenue_v1_deal_profit_tenant",
        table_name="automotive_revenue_v1_deal_profit",
    )
    op.drop_table("automotive_revenue_v1_deal_profit")

    op.drop_index(
        "ix_automotive_revenue_v1_deal_comm_status",
        table_name="automotive_revenue_v1_deal_commissions",
    )
    op.drop_index(
        "ix_automotive_revenue_v1_deal_comm_partner",
        table_name="automotive_revenue_v1_deal_commissions",
    )
    op.drop_index(
        "ix_automotive_revenue_v1_deal_comm_deal",
        table_name="automotive_revenue_v1_deal_commissions",
    )
    op.drop_index(
        "ix_automotive_revenue_v1_deal_comm_tenant",
        table_name="automotive_revenue_v1_deal_commissions",
    )
    op.drop_table("automotive_revenue_v1_deal_commissions")

    op.drop_index(
        "ix_automotive_revenue_v1_payouts_settlement",
        table_name="automotive_revenue_v1_partner_payouts",
    )
    op.drop_index(
        "ix_automotive_revenue_v1_payouts_status",
        table_name="automotive_revenue_v1_partner_payouts",
    )
    op.drop_index(
        "ix_automotive_revenue_v1_payouts_partner",
        table_name="automotive_revenue_v1_partner_payouts",
    )
    op.drop_index(
        "ix_automotive_revenue_v1_payouts_tenant",
        table_name="automotive_revenue_v1_partner_payouts",
    )
    op.drop_table("automotive_revenue_v1_partner_payouts")

    op.drop_index(
        "ix_automotive_revenue_v1_settlements_status",
        table_name="automotive_revenue_v1_partner_settlements",
    )
    op.drop_index(
        "ix_automotive_revenue_v1_settlements_partner",
        table_name="automotive_revenue_v1_partner_settlements",
    )
    op.drop_index(
        "ix_automotive_revenue_v1_settlements_tenant",
        table_name="automotive_revenue_v1_partner_settlements",
    )
    op.drop_table("automotive_revenue_v1_partner_settlements")

    op.drop_index(
        "ix_automotive_revenue_v1_partner_comm_service",
        table_name="automotive_revenue_v1_partner_commissions",
    )
    op.drop_index(
        "ix_automotive_revenue_v1_partner_comm_status",
        table_name="automotive_revenue_v1_partner_commissions",
    )
    op.drop_index(
        "ix_automotive_revenue_v1_partner_comm_partner",
        table_name="automotive_revenue_v1_partner_commissions",
    )
    op.drop_index(
        "ix_automotive_revenue_v1_partner_comm_tenant",
        table_name="automotive_revenue_v1_partner_commissions",
    )
    op.drop_table("automotive_revenue_v1_partner_commissions")

    op.drop_index(
        "ix_automotive_revenue_v1_partner_leads_vertical",
        table_name="automotive_revenue_v1_partner_leads",
    )
    op.drop_index(
        "ix_automotive_revenue_v1_partner_leads_status",
        table_name="automotive_revenue_v1_partner_leads",
    )
    op.drop_index(
        "ix_automotive_revenue_v1_partner_leads_lead",
        table_name="automotive_revenue_v1_partner_leads",
    )
    op.drop_index(
        "ix_automotive_revenue_v1_partner_leads_partner",
        table_name="automotive_revenue_v1_partner_leads",
    )
    op.drop_index(
        "ix_automotive_revenue_v1_partner_leads_tenant",
        table_name="automotive_revenue_v1_partner_leads",
    )
    op.drop_table("automotive_revenue_v1_partner_leads")
