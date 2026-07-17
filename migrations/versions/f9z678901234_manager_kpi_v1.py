"""Platform KPI tables revision.

Revision ID: f9z678901234
Revises: f9y567890123
Create Date: 2026-07-17 15:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "f9z678901234"
down_revision: Union[str, None] = "f9y567890123"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_KPI_COUNTERS = (
    sa.Column("requests_assigned", sa.Integer(), server_default="0", nullable=False),
    sa.Column("requests_first_response", sa.Integer(), server_default="0", nullable=False),
    sa.Column("requests_completed", sa.Integer(), server_default="0", nullable=False),
    sa.Column("requests_converted", sa.Integer(), server_default="0", nullable=False),
    sa.Column("requests_overdue", sa.Integer(), server_default="0", nullable=False),
    sa.Column("sla_compliant_count", sa.Integer(), server_default="0", nullable=False),
    sa.Column("sla_total_count", sa.Integer(), server_default="0", nullable=False),
    sa.Column("total_first_response_seconds", sa.BigInteger(), server_default="0", nullable=False),
    sa.Column("total_response_seconds", sa.BigInteger(), server_default="0", nullable=False),
    sa.Column("total_resolution_seconds", sa.BigInteger(), server_default="0", nullable=False),
)


def upgrade() -> None:
    op.create_table(
        "manager_daily_kpi",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("manager_id", UUID(as_uuid=True), nullable=False),
        sa.Column("metric_date", sa.Date(), nullable=False),
        sa.Column("vertical", sa.String(length=32), server_default="all", nullable=False),
        *_KPI_COUNTERS,
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("manager_id", "metric_date", "vertical", name="uq_manager_daily_kpi_manager_date_vertical"),
    )
    op.create_index("ix_manager_daily_kpi_manager_id", "manager_daily_kpi", ["manager_id"])
    op.create_index("ix_manager_daily_kpi_metric_date", "manager_daily_kpi", ["metric_date"])
    op.create_index("ix_manager_daily_kpi_vertical", "manager_daily_kpi", ["vertical"])

    op.create_table(
        "manager_monthly_kpi",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("manager_id", UUID(as_uuid=True), nullable=False),
        sa.Column("metric_month", sa.Date(), nullable=False),
        sa.Column("vertical", sa.String(length=32), server_default="all", nullable=False),
        *_KPI_COUNTERS,
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint(
            "manager_id",
            "metric_month",
            "vertical",
            name="uq_manager_monthly_kpi_manager_month_vertical",
        ),
    )
    op.create_index("ix_manager_monthly_kpi_manager_id", "manager_monthly_kpi", ["manager_id"])
    op.create_index("ix_manager_monthly_kpi_metric_month", "manager_monthly_kpi", ["metric_month"])
    op.create_index("ix_manager_monthly_kpi_vertical", "manager_monthly_kpi", ["vertical"])

    op.create_table(
        "vertical_kpi",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("vertical", sa.String(length=32), nullable=False),
        sa.Column("metric_date", sa.Date(), nullable=False),
        sa.Column("requests_created", sa.Integer(), server_default="0", nullable=False),
        sa.Column("requests_assigned", sa.Integer(), server_default="0", nullable=False),
        sa.Column("requests_completed", sa.Integer(), server_default="0", nullable=False),
        sa.Column("requests_converted", sa.Integer(), server_default="0", nullable=False),
        sa.Column("requests_overdue", sa.Integer(), server_default="0", nullable=False),
        sa.Column("sla_compliant_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("sla_total_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_first_response_seconds", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("response_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_resolution_seconds", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("vertical", "metric_date", name="uq_vertical_kpi_vertical_date"),
    )
    op.create_index("ix_vertical_kpi_vertical", "vertical_kpi", ["vertical"])
    op.create_index("ix_vertical_kpi_metric_date", "vertical_kpi", ["metric_date"])


def downgrade() -> None:
    op.drop_index("ix_vertical_kpi_metric_date", table_name="vertical_kpi")
    op.drop_index("ix_vertical_kpi_vertical", table_name="vertical_kpi")
    op.drop_table("vertical_kpi")

    op.drop_index("ix_manager_monthly_kpi_vertical", table_name="manager_monthly_kpi")
    op.drop_index("ix_manager_monthly_kpi_metric_month", table_name="manager_monthly_kpi")
    op.drop_index("ix_manager_monthly_kpi_manager_id", table_name="manager_monthly_kpi")
    op.drop_table("manager_monthly_kpi")

    op.drop_index("ix_manager_daily_kpi_vertical", table_name="manager_daily_kpi")
    op.drop_index("ix_manager_daily_kpi_metric_date", table_name="manager_daily_kpi")
    op.drop_index("ix_manager_daily_kpi_manager_id", table_name="manager_daily_kpi")
    op.drop_table("manager_daily_kpi")
