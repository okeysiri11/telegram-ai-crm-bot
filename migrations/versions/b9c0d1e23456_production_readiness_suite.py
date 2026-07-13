"""production_readiness_suite

Revision ID: b9c0d1e23456
Revises: a8b9c0d12345
Create Date: 2026-07-13 17:30:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "b9c0d1e23456"
down_revision: Union[str, None] = "a8b9c0d12345"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "system_health",
        sa.Column("check_name", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("suite_version", sa.String(length=32), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_system_health_check_name", "system_health", ["check_name"], unique=False)
    op.create_index("ix_system_health_status", "system_health", ["status"], unique=False)
    op.create_index("ix_system_health_checked_at", "system_health", ["checked_at"], unique=False)

    op.create_table(
        "system_metrics",
        sa.Column("metric_name", sa.String(length=128), nullable=False),
        sa.Column("metric_value", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=False),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_system_metrics_name", "system_metrics", ["metric_name"], unique=False)
    op.create_index("ix_system_metrics_recorded_at", "system_metrics", ["recorded_at"], unique=False)

    op.create_table(
        "system_alerts",
        sa.Column("alert_type", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("component", sa.String(length=64), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_system_alerts_component", "system_alerts", ["component"], unique=False)
    op.create_index("ix_system_alerts_severity", "system_alerts", ["severity"], unique=False)
    op.create_index("ix_system_alerts_resolved_at", "system_alerts", ["resolved_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_system_alerts_resolved_at", table_name="system_alerts")
    op.drop_index("ix_system_alerts_severity", table_name="system_alerts")
    op.drop_index("ix_system_alerts_component", table_name="system_alerts")
    op.drop_table("system_alerts")
    op.drop_index("ix_system_metrics_recorded_at", table_name="system_metrics")
    op.drop_index("ix_system_metrics_name", table_name="system_metrics")
    op.drop_table("system_metrics")
    op.drop_index("ix_system_health_checked_at", table_name="system_health")
    op.drop_index("ix_system_health_status", table_name="system_health")
    op.drop_index("ix_system_health_check_name", table_name="system_health")
    op.drop_table("system_health")
