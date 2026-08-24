"""Auto Marketplace Web CRM durable tables (additive).

Revision ID: q6l789012345
Revises: p5k678901234
Create Date: 2026-08-24 09:10:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "q6l789012345"
down_revision: Union[str, None] = "p5k678901234"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ts_cols():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    ]


def upgrade() -> None:
    conn = op.get_bind()

    def _exists(name: str) -> bool:
        return conn.exec_driver_sql(f"SELECT to_regclass('public.{name}')").scalar() is not None

    if not _exists("auto_marketplace_crm_customers"):
        op.create_table(
            "auto_marketplace_crm_customers",
            sa.Column("customer_id", sa.String(64), primary_key=True),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("first_name", sa.String(255), nullable=False, server_default=""),
            sa.Column("last_name", sa.String(255), nullable=False, server_default=""),
            sa.Column("email", sa.String(255), nullable=False, server_default=""),
            sa.Column("phone", sa.String(64), nullable=False, server_default=""),
            sa.Column("segment", sa.String(64), nullable=False, server_default="standard"),
            sa.Column("intent_score", sa.Float(), nullable=False, server_default="0"),
            sa.Column("lifetime_value", sa.Float(), nullable=False, server_default="0"),
            sa.Column("owner_agent_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("created_ts", sa.Float(), nullable=False, server_default="0"),
            sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            *_ts_cols(),
        )
        op.create_index("ix_am_crm_customers_tenant", "auto_marketplace_crm_customers", ["tenant_id"])
        op.create_index(
            "ix_am_crm_customers_tenant_email",
            "auto_marketplace_crm_customers",
            ["tenant_id", "email"],
        )
        op.create_index(
            "ix_am_crm_customers_tenant_segment",
            "auto_marketplace_crm_customers",
            ["tenant_id", "segment"],
        )

    if not _exists("auto_marketplace_crm_leads"):
        op.create_table(
            "auto_marketplace_crm_leads",
            sa.Column("lead_id", sa.String(64), primary_key=True),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("customer_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("vehicle_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("dealer_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("source", sa.String(64), nullable=False, server_default="web"),
            sa.Column("status", sa.String(64), nullable=False, server_default="new"),
            sa.Column("score", sa.Float(), nullable=False, server_default="0"),
            sa.Column("assigned_agent_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("notes", sa.Text(), nullable=False, server_default=""),
            sa.Column("created_ts", sa.Float(), nullable=False, server_default="0"),
            sa.Column("qualified_at", sa.Float(), nullable=True),
            sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            *_ts_cols(),
        )
        op.create_index("ix_am_crm_leads_tenant", "auto_marketplace_crm_leads", ["tenant_id"])
        op.create_index(
            "ix_am_crm_leads_tenant_dealer",
            "auto_marketplace_crm_leads",
            ["tenant_id", "dealer_id"],
        )
        op.create_index(
            "ix_am_crm_leads_tenant_status",
            "auto_marketplace_crm_leads",
            ["tenant_id", "status"],
        )
        op.create_index(
            "ix_am_crm_leads_tenant_customer",
            "auto_marketplace_crm_leads",
            ["tenant_id", "customer_id"],
        )

    if not _exists("auto_marketplace_crm_deals"):
        op.create_table(
            "auto_marketplace_crm_deals",
            sa.Column("deal_id", sa.String(64), primary_key=True),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("opportunity_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("customer_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("dealer_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("vehicle_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("stage", sa.String(64), nullable=False, server_default="prospect"),
            sa.Column("amount", sa.Float(), nullable=False, server_default="0"),
            sa.Column("probability", sa.Float(), nullable=False, server_default="0.1"),
            sa.Column("win", sa.Boolean(), nullable=True),
            sa.Column("owner_agent_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("created_ts", sa.Float(), nullable=False, server_default="0"),
            sa.Column("closed_at", sa.Float(), nullable=True),
            sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            *_ts_cols(),
        )
        op.create_index("ix_am_crm_deals_tenant", "auto_marketplace_crm_deals", ["tenant_id"])
        op.create_index(
            "ix_am_crm_deals_tenant_dealer",
            "auto_marketplace_crm_deals",
            ["tenant_id", "dealer_id"],
        )
        op.create_index(
            "ix_am_crm_deals_tenant_stage",
            "auto_marketplace_crm_deals",
            ["tenant_id", "stage"],
        )
        op.create_index(
            "ix_am_crm_deals_tenant_customer",
            "auto_marketplace_crm_deals",
            ["tenant_id", "customer_id"],
        )


def downgrade() -> None:
    conn = op.get_bind()

    def _exists(name: str) -> bool:
        return conn.exec_driver_sql(f"SELECT to_regclass('public.{name}')").scalar() is not None

    for table in (
        "auto_marketplace_crm_deals",
        "auto_marketplace_crm_leads",
        "auto_marketplace_crm_customers",
    ):
        if _exists(table):
            op.drop_table(table)
