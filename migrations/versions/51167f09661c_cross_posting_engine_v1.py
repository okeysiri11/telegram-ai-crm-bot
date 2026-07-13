"""cross_posting_engine_v1

Revision ID: 51167f09661c
Revises: b7d3e42a1f90
Create Date: 2026-07-13 14:15:15.018532

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "51167f09661c"
down_revision: Union[str, None] = "b7d3e42a1f90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cross_posting_engine_v1_posting_templates",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("channel_type", sa.String(length=30), nullable=False),
        sa.Column("body_template", sa.Text(), nullable=False),
        sa.Column("default_variables", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
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
            "code",
            name="uq_cross_posting_engine_v1_templates_tenant_code",
        ),
    )
    op.create_index(
        "ix_cross_posting_engine_v1_templates_channel",
        "cross_posting_engine_v1_posting_templates",
        ["channel_type"],
        unique=False,
    )
    op.create_index(
        "ix_cross_posting_engine_v1_templates_tenant",
        "cross_posting_engine_v1_posting_templates",
        ["tenant_id"],
        unique=False,
    )

    op.create_table(
        "cross_posting_engine_v1_posting_channels",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("channel_integration_id", sa.UUID(), nullable=True),
        sa.Column("channel_type", sa.String(length=30), nullable=False),
        sa.Column("external_id", sa.String(length=120), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
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
            ["channel_integration_id"],
            ["channel_integration_engine_v1_channels.id"],
            ondelete="SET NULL",
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
            "channel_type",
            "external_id",
            name="uq_cross_posting_engine_v1_channels_tenant_type_ext",
        ),
    )
    op.create_index(
        "ix_cross_posting_engine_v1_channels_active",
        "cross_posting_engine_v1_posting_channels",
        ["is_active"],
        unique=False,
    )
    op.create_index(
        "ix_cross_posting_engine_v1_channels_tenant",
        "cross_posting_engine_v1_posting_channels",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        "ix_cross_posting_engine_v1_channels_type",
        "cross_posting_engine_v1_posting_channels",
        ["channel_type"],
        unique=False,
    )

    op.create_table(
        "cross_posting_engine_v1_posting_jobs",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("channel_id", sa.UUID(), nullable=False),
        sa.Column("template_id", sa.UUID(), nullable=True),
        sa.Column("car_id", sa.UUID(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_repost", sa.Boolean(), nullable=False),
        sa.Column("source_job_id", sa.UUID(), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
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
        sa.ForeignKeyConstraint(["car_id"], ["car_engine_v1_cars.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["channel_id"],
            ["cross_posting_engine_v1_posting_channels.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["multi_company_v1_companies.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_job_id"],
            ["cross_posting_engine_v1_posting_jobs.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["template_id"],
            ["cross_posting_engine_v1_posting_templates.id"],
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
        "ix_cross_posting_engine_v1_jobs_channel",
        "cross_posting_engine_v1_posting_jobs",
        ["channel_id"],
        unique=False,
    )
    op.create_index(
        "ix_cross_posting_engine_v1_jobs_hash",
        "cross_posting_engine_v1_posting_jobs",
        ["content_hash"],
        unique=False,
    )
    op.create_index(
        "ix_cross_posting_engine_v1_jobs_scheduled",
        "cross_posting_engine_v1_posting_jobs",
        ["scheduled_at"],
        unique=False,
    )
    op.create_index(
        "ix_cross_posting_engine_v1_jobs_status",
        "cross_posting_engine_v1_posting_jobs",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_cross_posting_engine_v1_jobs_tenant",
        "cross_posting_engine_v1_posting_jobs",
        ["tenant_id"],
        unique=False,
    )

    op.create_table(
        "cross_posting_engine_v1_posting_results",
        sa.Column("job_id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("channel_type", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("external_post_id", sa.String(length=255), nullable=True),
        sa.Column("published_url", sa.String(length=512), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("views", sa.Integer(), nullable=False),
        sa.Column("likes", sa.Integer(), nullable=False),
        sa.Column("shares", sa.Integer(), nullable=False),
        sa.Column("comments", sa.Integer(), nullable=False),
        sa.Column("clicks", sa.Integer(), nullable=False),
        sa.Column("analytics_collected_at", sa.DateTime(timezone=True), nullable=True),
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
            ["job_id"],
            ["cross_posting_engine_v1_posting_jobs.id"],
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
        "ix_cross_posting_engine_v1_results_external",
        "cross_posting_engine_v1_posting_results",
        ["external_post_id"],
        unique=False,
    )
    op.create_index(
        "ix_cross_posting_engine_v1_results_job",
        "cross_posting_engine_v1_posting_results",
        ["job_id"],
        unique=False,
    )
    op.create_index(
        "ix_cross_posting_engine_v1_results_status",
        "cross_posting_engine_v1_posting_results",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_cross_posting_engine_v1_results_tenant",
        "cross_posting_engine_v1_posting_results",
        ["tenant_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_cross_posting_engine_v1_results_tenant",
        table_name="cross_posting_engine_v1_posting_results",
    )
    op.drop_index(
        "ix_cross_posting_engine_v1_results_status",
        table_name="cross_posting_engine_v1_posting_results",
    )
    op.drop_index(
        "ix_cross_posting_engine_v1_results_job",
        table_name="cross_posting_engine_v1_posting_results",
    )
    op.drop_index(
        "ix_cross_posting_engine_v1_results_external",
        table_name="cross_posting_engine_v1_posting_results",
    )
    op.drop_table("cross_posting_engine_v1_posting_results")

    op.drop_index(
        "ix_cross_posting_engine_v1_jobs_tenant",
        table_name="cross_posting_engine_v1_posting_jobs",
    )
    op.drop_index(
        "ix_cross_posting_engine_v1_jobs_status",
        table_name="cross_posting_engine_v1_posting_jobs",
    )
    op.drop_index(
        "ix_cross_posting_engine_v1_jobs_scheduled",
        table_name="cross_posting_engine_v1_posting_jobs",
    )
    op.drop_index(
        "ix_cross_posting_engine_v1_jobs_hash",
        table_name="cross_posting_engine_v1_posting_jobs",
    )
    op.drop_index(
        "ix_cross_posting_engine_v1_jobs_channel",
        table_name="cross_posting_engine_v1_posting_jobs",
    )
    op.drop_table("cross_posting_engine_v1_posting_jobs")

    op.drop_index(
        "ix_cross_posting_engine_v1_channels_type",
        table_name="cross_posting_engine_v1_posting_channels",
    )
    op.drop_index(
        "ix_cross_posting_engine_v1_channels_tenant",
        table_name="cross_posting_engine_v1_posting_channels",
    )
    op.drop_index(
        "ix_cross_posting_engine_v1_channels_active",
        table_name="cross_posting_engine_v1_posting_channels",
    )
    op.drop_table("cross_posting_engine_v1_posting_channels")

    op.drop_index(
        "ix_cross_posting_engine_v1_templates_tenant",
        table_name="cross_posting_engine_v1_posting_templates",
    )
    op.drop_index(
        "ix_cross_posting_engine_v1_templates_channel",
        table_name="cross_posting_engine_v1_posting_templates",
    )
    op.drop_table("cross_posting_engine_v1_posting_templates")
