"""marketing_analytics_v1

Revision ID: f7h890123456
Revises: f6g789012345
Create Date: 2026-07-14 14:00:00.000000

"""
from __future__ import annotations

import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f7h890123456"
down_revision: Union[str, None] = "f6g789012345"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SOURCE_COSTS = [
    ("facebook", "Facebook", 12.00),
    ("instagram", "Instagram", 10.00),
    ("tiktok", "TikTok", 8.00),
    ("telegram", "Telegram", 3.00),
    ("google", "Google", 15.00),
    ("referral", "Referral", 5.00),
    ("boroda_cars", "Boroda Cars", 2.00),
    ("other", "Other", 6.00),
]


def upgrade() -> None:
    op.create_table(
        "marketing_analytics_v1_source_costs",
        sa.Column("source_key", sa.String(length=50), nullable=False),
        sa.Column("display_name", sa.String(length=80), nullable=False),
        sa.Column("cost_per_lead", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_key", name="uq_marketing_analytics_v1_source_key"),
    )
    op.create_index(
        "ix_marketing_analytics_v1_costs_key",
        "marketing_analytics_v1_source_costs",
        ["source_key"],
    )

    costs_table = sa.table(
        "marketing_analytics_v1_source_costs",
        sa.column("id", sa.UUID()),
        sa.column("source_key", sa.String()),
        sa.column("display_name", sa.String()),
        sa.column("cost_per_lead", sa.Numeric(18, 2)),
        sa.column("currency", sa.String()),
    )
    op.bulk_insert(
        costs_table,
        [
            {
                "id": uuid.uuid4(),
                "source_key": key,
                "display_name": name,
                "cost_per_lead": cost,
                "currency": "USD",
            }
            for key, name, cost in SOURCE_COSTS
        ],
    )

    op.add_column(
        "lead_engine_v1_leads",
        sa.Column("referrer", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "lead_engine_v1_leads",
        sa.Column("marketing_source", sa.String(length=50), nullable=True),
    )
    op.create_index(
        "ix_lead_engine_v1_utm_campaign",
        "lead_engine_v1_leads",
        ["utm_campaign"],
    )
    op.create_index(
        "ix_lead_engine_v1_marketing_source",
        "lead_engine_v1_leads",
        ["marketing_source"],
    )
    op.create_index(
        "ix_lead_engine_v1_referrer",
        "lead_engine_v1_leads",
        ["referrer"],
    )

    op.execute(
        sa.text(
            "UPDATE lead_engine_v1_leads SET referrer = referral_code "
            "WHERE referral_code IS NOT NULL AND referral_code != ''"
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE lead_engine_v1_leads SET marketing_source = CASE
                WHEN LOWER(COALESCE(utm_source, '')) IN ('facebook', 'fb') THEN 'facebook'
                WHEN LOWER(COALESCE(utm_source, '')) IN ('instagram', 'ig') THEN 'instagram'
                WHEN LOWER(COALESCE(utm_source, '')) IN ('tiktok', 'tt') THEN 'tiktok'
                WHEN LOWER(COALESCE(utm_source, '')) IN ('telegram', 'tg') THEN 'telegram'
                WHEN LOWER(COALESCE(utm_source, '')) IN ('google', 'gclid') THEN 'google'
                WHEN LOWER(COALESCE(utm_source, '')) IN ('referral', 'ref') THEN 'referral'
                WHEN LOWER(COALESCE(utm_source, '')) LIKE '%boroda%' THEN 'boroda_cars'
                WHEN LOWER(COALESCE(source_link, '')) LIKE '%boroda%' THEN 'boroda_cars'
                WHEN referral_code IS NOT NULL AND referral_code != '' THEN 'referral'
                WHEN utm_source IS NOT NULL AND utm_source != '' THEN 'other'
                ELSE 'telegram'
            END
            WHERE marketing_source IS NULL
            """
        )
    )


def downgrade() -> None:
    op.drop_index("ix_lead_engine_v1_referrer", table_name="lead_engine_v1_leads")
    op.drop_index("ix_lead_engine_v1_marketing_source", table_name="lead_engine_v1_leads")
    op.drop_index("ix_lead_engine_v1_utm_campaign", table_name="lead_engine_v1_leads")
    op.drop_column("lead_engine_v1_leads", "marketing_source")
    op.drop_column("lead_engine_v1_leads", "referrer")

    op.drop_index(
        "ix_marketing_analytics_v1_costs_key",
        table_name="marketing_analytics_v1_source_costs",
    )
    op.drop_table("marketing_analytics_v1_source_costs")
