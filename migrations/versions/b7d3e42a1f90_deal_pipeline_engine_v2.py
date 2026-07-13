"""deal_pipeline_engine_v2

Revision ID: b7d3e42a1f90
Revises: a8f2e91b4c03
Create Date: 2026-07-13 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "b7d3e42a1f90"
down_revision: Union[str, None] = "a8f2e91b4c03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "deal_pipeline_engine_v2_deals",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("sales_lead_id", sa.UUID(), nullable=True),
        sa.Column("car_id", sa.UUID(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("current_stage", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("assigned_manager_id", sa.BigInteger(), nullable=True),
        sa.Column("deal_value", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("sla_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("customer_name", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
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
            ["car_id"],
            ["car_engine_v1_cars.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["multi_company_v1_companies.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["sales_lead_id"],
            ["ai_sales_agent_v1_sales_leads.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["partner_tenant_engine_v1_tenants.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_deal_pipeline_engine_v2_deals_manager",
        "deal_pipeline_engine_v2_deals",
        ["assigned_manager_id"],
        unique=False,
    )
    op.create_index(
        "ix_deal_pipeline_engine_v2_deals_sales_lead",
        "deal_pipeline_engine_v2_deals",
        ["sales_lead_id"],
        unique=False,
    )
    op.create_index(
        "ix_deal_pipeline_engine_v2_deals_sla",
        "deal_pipeline_engine_v2_deals",
        ["sla_due_at"],
        unique=False,
    )
    op.create_index(
        "ix_deal_pipeline_engine_v2_deals_stage",
        "deal_pipeline_engine_v2_deals",
        ["current_stage"],
        unique=False,
    )
    op.create_index(
        "ix_deal_pipeline_engine_v2_deals_status",
        "deal_pipeline_engine_v2_deals",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_deal_pipeline_engine_v2_deals_tenant",
        "deal_pipeline_engine_v2_deals",
        ["tenant_id"],
        unique=False,
    )

    op.create_table(
        "deal_pipeline_engine_v2_deal_stages",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("stage_code", sa.String(length=40), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("sla_hours", sa.Integer(), nullable=False),
        sa.Column("is_terminal", sa.Boolean(), nullable=False),
        sa.Column("allowed_next_stages", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
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
        sa.CheckConstraint("sla_hours >= 0", name="ck_deal_pipeline_engine_v2_stages_sla"),
        sa.CheckConstraint("sort_order >= 0", name="ck_deal_pipeline_engine_v2_stages_order"),
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
            "stage_code",
            name="uq_deal_pipeline_engine_v2_stages_tenant_code",
        ),
    )
    op.create_index(
        "ix_deal_pipeline_engine_v2_stages_code",
        "deal_pipeline_engine_v2_deal_stages",
        ["stage_code"],
        unique=False,
    )
    op.create_index(
        "ix_deal_pipeline_engine_v2_stages_tenant",
        "deal_pipeline_engine_v2_deal_stages",
        ["tenant_id"],
        unique=False,
    )

    op.create_table(
        "deal_pipeline_engine_v2_deal_stage_history",
        sa.Column("deal_id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("from_stage", sa.String(length=40), nullable=True),
        sa.Column("to_stage", sa.String(length=40), nullable=False),
        sa.Column("changed_by", sa.BigInteger(), nullable=True),
        sa.Column("validation_passed", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
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
            ["deal_id"],
            ["deal_pipeline_engine_v2_deals.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["partner_tenant_engine_v1_tenants.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_deal_pipeline_engine_v2_history_deal",
        "deal_pipeline_engine_v2_deal_stage_history",
        ["deal_id"],
        unique=False,
    )
    op.create_index(
        "ix_deal_pipeline_engine_v2_history_tenant",
        "deal_pipeline_engine_v2_deal_stage_history",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        "ix_deal_pipeline_engine_v2_history_to",
        "deal_pipeline_engine_v2_deal_stage_history",
        ["to_stage"],
        unique=False,
    )

    op.create_table(
        "deal_pipeline_engine_v2_deal_tasks",
        sa.Column("deal_id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("task_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("assigned_to", sa.BigInteger(), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("auto_created", sa.Boolean(), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
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
            ["deal_id"],
            ["deal_pipeline_engine_v2_deals.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["partner_tenant_engine_v1_tenants.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_deal_pipeline_engine_v2_tasks_assignee",
        "deal_pipeline_engine_v2_deal_tasks",
        ["assigned_to"],
        unique=False,
    )
    op.create_index(
        "ix_deal_pipeline_engine_v2_tasks_deal",
        "deal_pipeline_engine_v2_deal_tasks",
        ["deal_id"],
        unique=False,
    )
    op.create_index(
        "ix_deal_pipeline_engine_v2_tasks_due",
        "deal_pipeline_engine_v2_deal_tasks",
        ["due_at"],
        unique=False,
    )
    op.create_index(
        "ix_deal_pipeline_engine_v2_tasks_status",
        "deal_pipeline_engine_v2_deal_tasks",
        ["status"],
        unique=False,
    )

    op.create_table(
        "deal_pipeline_engine_v2_deal_comments",
        sa.Column("deal_id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("author_id", sa.BigInteger(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_internal", sa.Boolean(), nullable=False),
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
            ["deal_id"],
            ["deal_pipeline_engine_v2_deals.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["partner_tenant_engine_v1_tenants.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_deal_pipeline_engine_v2_comments_deal",
        "deal_pipeline_engine_v2_deal_comments",
        ["deal_id"],
        unique=False,
    )
    op.create_index(
        "ix_deal_pipeline_engine_v2_comments_tenant",
        "deal_pipeline_engine_v2_deal_comments",
        ["tenant_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_deal_pipeline_engine_v2_comments_tenant",
        table_name="deal_pipeline_engine_v2_deal_comments",
    )
    op.drop_index(
        "ix_deal_pipeline_engine_v2_comments_deal",
        table_name="deal_pipeline_engine_v2_deal_comments",
    )
    op.drop_table("deal_pipeline_engine_v2_deal_comments")

    op.drop_index(
        "ix_deal_pipeline_engine_v2_tasks_status",
        table_name="deal_pipeline_engine_v2_deal_tasks",
    )
    op.drop_index(
        "ix_deal_pipeline_engine_v2_tasks_due",
        table_name="deal_pipeline_engine_v2_deal_tasks",
    )
    op.drop_index(
        "ix_deal_pipeline_engine_v2_tasks_deal",
        table_name="deal_pipeline_engine_v2_deal_tasks",
    )
    op.drop_index(
        "ix_deal_pipeline_engine_v2_tasks_assignee",
        table_name="deal_pipeline_engine_v2_deal_tasks",
    )
    op.drop_table("deal_pipeline_engine_v2_deal_tasks")

    op.drop_index(
        "ix_deal_pipeline_engine_v2_history_to",
        table_name="deal_pipeline_engine_v2_deal_stage_history",
    )
    op.drop_index(
        "ix_deal_pipeline_engine_v2_history_tenant",
        table_name="deal_pipeline_engine_v2_deal_stage_history",
    )
    op.drop_index(
        "ix_deal_pipeline_engine_v2_history_deal",
        table_name="deal_pipeline_engine_v2_deal_stage_history",
    )
    op.drop_table("deal_pipeline_engine_v2_deal_stage_history")

    op.drop_index(
        "ix_deal_pipeline_engine_v2_stages_tenant",
        table_name="deal_pipeline_engine_v2_deal_stages",
    )
    op.drop_index(
        "ix_deal_pipeline_engine_v2_stages_code",
        table_name="deal_pipeline_engine_v2_deal_stages",
    )
    op.drop_table("deal_pipeline_engine_v2_deal_stages")

    op.drop_index(
        "ix_deal_pipeline_engine_v2_deals_tenant",
        table_name="deal_pipeline_engine_v2_deals",
    )
    op.drop_index(
        "ix_deal_pipeline_engine_v2_deals_status",
        table_name="deal_pipeline_engine_v2_deals",
    )
    op.drop_index(
        "ix_deal_pipeline_engine_v2_deals_stage",
        table_name="deal_pipeline_engine_v2_deals",
    )
    op.drop_index(
        "ix_deal_pipeline_engine_v2_deals_sla",
        table_name="deal_pipeline_engine_v2_deals",
    )
    op.drop_index(
        "ix_deal_pipeline_engine_v2_deals_sales_lead",
        table_name="deal_pipeline_engine_v2_deals",
    )
    op.drop_index(
        "ix_deal_pipeline_engine_v2_deals_manager",
        table_name="deal_pipeline_engine_v2_deals",
    )
    op.drop_table("deal_pipeline_engine_v2_deals")
