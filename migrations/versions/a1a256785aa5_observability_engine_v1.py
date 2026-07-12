"""observability_engine_v1

Revision ID: a1a256785aa5
Revises: a36e79485609
Create Date: 2026-07-13 00:02:36.910518

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "a1a256785aa5"
down_revision: Union[str, None] = "a36e79485609"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "observability_engine_v1_business_metrics",
        sa.Column("kpi_name", sa.String(length=128), nullable=False),
        sa.Column("kpi_value", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=False),
        sa.Column("dimensions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_observability_v1_biz_kpi",
        "observability_engine_v1_business_metrics",
        ["kpi_name"],
        unique=False,
    )
    op.create_index(
        "ix_observability_v1_biz_period",
        "observability_engine_v1_business_metrics",
        ["period_start"],
        unique=False,
    )
    op.create_index(
        "ix_observability_v1_biz_recorded",
        "observability_engine_v1_business_metrics",
        ["recorded_at"],
        unique=False,
    )
    op.create_table(
        "observability_engine_v1_error_events",
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("error_type", sa.String(length=128), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("stack_trace", sa.Text(), nullable=True),
        sa.Column("context", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("resolved", sa.Boolean(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_observability_v1_err_recorded",
        "observability_engine_v1_error_events",
        ["recorded_at"],
        unique=False,
    )
    op.create_index(
        "ix_observability_v1_err_resolved",
        "observability_engine_v1_error_events",
        ["resolved"],
        unique=False,
    )
    op.create_index(
        "ix_observability_v1_err_severity",
        "observability_engine_v1_error_events",
        ["severity"],
        unique=False,
    )
    op.create_index(
        "ix_observability_v1_err_source",
        "observability_engine_v1_error_events",
        ["source"],
        unique=False,
    )
    op.create_table(
        "observability_engine_v1_performance_metrics",
        sa.Column("operation_name", sa.String(length=128), nullable=False),
        sa.Column("latency_ms", sa.Numeric(precision=12, scale=3), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_observability_v1_perf_operation",
        "observability_engine_v1_performance_metrics",
        ["operation_name"],
        unique=False,
    )
    op.create_index(
        "ix_observability_v1_perf_recorded",
        "observability_engine_v1_performance_metrics",
        ["recorded_at"],
        unique=False,
    )
    op.create_index(
        "ix_observability_v1_perf_success",
        "observability_engine_v1_performance_metrics",
        ["success"],
        unique=False,
    )
    op.create_table(
        "observability_engine_v1_system_metrics",
        sa.Column("metric_name", sa.String(length=128), nullable=False),
        sa.Column("metric_value", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=False),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_observability_v1_sys_name",
        "observability_engine_v1_system_metrics",
        ["metric_name"],
        unique=False,
    )
    op.create_index(
        "ix_observability_v1_sys_recorded",
        "observability_engine_v1_system_metrics",
        ["recorded_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_observability_v1_sys_recorded",
        table_name="observability_engine_v1_system_metrics",
    )
    op.drop_index(
        "ix_observability_v1_sys_name",
        table_name="observability_engine_v1_system_metrics",
    )
    op.drop_table("observability_engine_v1_system_metrics")
    op.drop_index(
        "ix_observability_v1_perf_success",
        table_name="observability_engine_v1_performance_metrics",
    )
    op.drop_index(
        "ix_observability_v1_perf_recorded",
        table_name="observability_engine_v1_performance_metrics",
    )
    op.drop_index(
        "ix_observability_v1_perf_operation",
        table_name="observability_engine_v1_performance_metrics",
    )
    op.drop_table("observability_engine_v1_performance_metrics")
    op.drop_index(
        "ix_observability_v1_err_source",
        table_name="observability_engine_v1_error_events",
    )
    op.drop_index(
        "ix_observability_v1_err_severity",
        table_name="observability_engine_v1_error_events",
    )
    op.drop_index(
        "ix_observability_v1_err_resolved",
        table_name="observability_engine_v1_error_events",
    )
    op.drop_index(
        "ix_observability_v1_err_recorded",
        table_name="observability_engine_v1_error_events",
    )
    op.drop_table("observability_engine_v1_error_events")
    op.drop_index(
        "ix_observability_v1_biz_recorded",
        table_name="observability_engine_v1_business_metrics",
    )
    op.drop_index(
        "ix_observability_v1_biz_period",
        table_name="observability_engine_v1_business_metrics",
    )
    op.drop_index(
        "ix_observability_v1_biz_kpi",
        table_name="observability_engine_v1_business_metrics",
    )
    op.drop_table("observability_engine_v1_business_metrics")
