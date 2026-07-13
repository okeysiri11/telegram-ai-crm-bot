"""analytics_engine_v1

Revision ID: a2b3c4d5e6f7
Revises: 51167f09661c
Create Date: 2026-07-13 14:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "a2b3c4d5e6f7"
down_revision: Union[str, None] = "51167f09661c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "analytics_engine_v1_lead_statistics",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("metric_date", sa.Date(), nullable=False),
        sa.Column("total_leads", sa.Integer(), nullable=False),
        sa.Column("qualified_leads", sa.Integer(), nullable=False),
        sa.Column("leads_by_source", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("cpl", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("conversion_rate", sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column("lead_source_roi", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["multi_company_v1_companies.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["partner_tenant_engine_v1_tenants.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "metric_date",
            name="uq_analytics_engine_v1_lead_stats_tenant_date",
        ),
    )
    op.create_index(
        "ix_analytics_engine_v1_lead_stats_date",
        "analytics_engine_v1_lead_statistics",
        ["metric_date"],
        unique=False,
    )
    op.create_index(
        "ix_analytics_engine_v1_lead_stats_tenant",
        "analytics_engine_v1_lead_statistics",
        ["tenant_id"],
        unique=False,
    )

    op.create_table(
        "analytics_engine_v1_sales_statistics",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("metric_date", sa.Date(), nullable=False),
        sa.Column("deals_won", sa.Integer(), nullable=False),
        sa.Column("deals_lost", sa.Integer(), nullable=False),
        sa.Column("total_revenue", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("average_deal_size", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("conversion_rate", sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column("vehicle_turnover", sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["multi_company_v1_companies.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["partner_tenant_engine_v1_tenants.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "metric_date",
            name="uq_analytics_engine_v1_sales_stats_tenant_date",
        ),
    )
    op.create_index(
        "ix_analytics_engine_v1_sales_stats_date",
        "analytics_engine_v1_sales_statistics",
        ["metric_date"],
        unique=False,
    )
    op.create_index(
        "ix_analytics_engine_v1_sales_stats_tenant",
        "analytics_engine_v1_sales_statistics",
        ["tenant_id"],
        unique=False,
    )

    op.create_table(
        "analytics_engine_v1_advertising_statistics",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("metric_date", sa.Date(), nullable=False),
        sa.Column("total_spend", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("total_impressions", sa.Integer(), nullable=False),
        sa.Column("total_clicks", sa.Integer(), nullable=False),
        sa.Column("leads_from_ads", sa.Integer(), nullable=False),
        sa.Column("cac", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("cpl", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("campaign_metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["multi_company_v1_companies.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["partner_tenant_engine_v1_tenants.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "metric_date",
            name="uq_analytics_engine_v1_ad_stats_tenant_date",
        ),
    )
    op.create_index(
        "ix_analytics_engine_v1_ad_stats_date",
        "analytics_engine_v1_advertising_statistics",
        ["metric_date"],
        unique=False,
    )
    op.create_index(
        "ix_analytics_engine_v1_ad_stats_tenant",
        "analytics_engine_v1_advertising_statistics",
        ["tenant_id"],
        unique=False,
    )

    op.create_table(
        "analytics_engine_v1_manager_statistics",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("manager_id", sa.BigInteger(), nullable=False),
        sa.Column("metric_date", sa.Date(), nullable=False),
        sa.Column("leads_assigned", sa.Integer(), nullable=False),
        sa.Column("deals_closed", sa.Integer(), nullable=False),
        sa.Column("revenue", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("conversion_rate", sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column("performance_score", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["multi_company_v1_companies.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["partner_tenant_engine_v1_tenants.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "manager_id",
            "metric_date",
            name="uq_analytics_engine_v1_mgr_stats_tenant_mgr_date",
        ),
    )
    op.create_index(
        "ix_analytics_engine_v1_mgr_stats_date",
        "analytics_engine_v1_manager_statistics",
        ["metric_date"],
        unique=False,
    )
    op.create_index(
        "ix_analytics_engine_v1_mgr_stats_manager",
        "analytics_engine_v1_manager_statistics",
        ["manager_id"],
        unique=False,
    )
    op.create_index(
        "ix_analytics_engine_v1_mgr_stats_tenant",
        "analytics_engine_v1_manager_statistics",
        ["tenant_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_analytics_engine_v1_mgr_stats_tenant",
        table_name="analytics_engine_v1_manager_statistics",
    )
    op.drop_index(
        "ix_analytics_engine_v1_mgr_stats_manager",
        table_name="analytics_engine_v1_manager_statistics",
    )
    op.drop_index(
        "ix_analytics_engine_v1_mgr_stats_date",
        table_name="analytics_engine_v1_manager_statistics",
    )
    op.drop_table("analytics_engine_v1_manager_statistics")

    op.drop_index(
        "ix_analytics_engine_v1_ad_stats_tenant",
        table_name="analytics_engine_v1_advertising_statistics",
    )
    op.drop_index(
        "ix_analytics_engine_v1_ad_stats_date",
        table_name="analytics_engine_v1_advertising_statistics",
    )
    op.drop_table("analytics_engine_v1_advertising_statistics")

    op.drop_index(
        "ix_analytics_engine_v1_sales_stats_tenant",
        table_name="analytics_engine_v1_sales_statistics",
    )
    op.drop_index(
        "ix_analytics_engine_v1_sales_stats_date",
        table_name="analytics_engine_v1_sales_statistics",
    )
    op.drop_table("analytics_engine_v1_sales_statistics")

    op.drop_index(
        "ix_analytics_engine_v1_lead_stats_tenant",
        table_name="analytics_engine_v1_lead_statistics",
    )
    op.drop_index(
        "ix_analytics_engine_v1_lead_stats_date",
        table_name="analytics_engine_v1_lead_statistics",
    )
    op.drop_table("analytics_engine_v1_lead_statistics")
