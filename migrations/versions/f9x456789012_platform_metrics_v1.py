"""Platform metrics tables — request lifecycle, manager rollups, daily aggregates.

Revision ID: f9x456789012
Revises: f9w345678901
Create Date: 2026-07-17 12:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "f9x456789012"
down_revision: Union[str, None] = "f9w345678901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "request_metrics",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("request_number", sa.String(length=32), nullable=False),
        sa.Column("request_id", UUID(as_uuid=True), nullable=True),
        sa.Column("vertical", sa.String(length=32), nullable=False),
        sa.Column("request_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="NEW"),
        sa.Column("manager_id", UUID(as_uuid=True), nullable=True),
        sa.Column("client_telegram_id", sa.BigInteger(), nullable=True),
        sa.Column("request_created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("first_response_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("time_to_assign_seconds", sa.Integer(), nullable=True),
        sa.Column("time_to_first_response_seconds", sa.Integer(), nullable=True),
        sa.Column("time_to_close_seconds", sa.Integer(), nullable=True),
        sa.Column("converted_to_deal", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("request_number", name="uq_request_metrics_number"),
    )
    op.create_index("ix_request_metrics_request_created_at", "request_metrics", ["request_created_at"])
    op.create_index("ix_request_metrics_vertical", "request_metrics", ["vertical"])
    op.create_index("ix_request_metrics_manager_id", "request_metrics", ["manager_id"])
    op.create_index("ix_request_metrics_status", "request_metrics", ["status"])
    op.create_index(
        "ix_request_metrics_vertical_created",
        "request_metrics",
        ["vertical", "request_created_at"],
    )

    op.create_table(
        "manager_metrics",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("manager_id", UUID(as_uuid=True), nullable=False),
        sa.Column("metric_date", sa.Date(), nullable=False),
        sa.Column("vertical", sa.String(length=32), nullable=False),
        sa.Column("requests_assigned", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("requests_with_response", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("requests_closed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deals_won", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_response_time_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint(
            "manager_id",
            "metric_date",
            "vertical",
            name="uq_manager_metrics_manager_date_vertical",
        ),
    )
    op.create_index("ix_manager_metrics_manager_id", "manager_metrics", ["manager_id"])
    op.create_index("ix_manager_metrics_metric_date", "manager_metrics", ["metric_date"])
    op.create_index("ix_manager_metrics_vertical", "manager_metrics", ["vertical"])

    op.create_table(
        "platform_metrics_daily",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("metric_date", sa.Date(), nullable=False),
        sa.Column("vertical", sa.String(length=32), nullable=False),
        sa.Column("requests_created", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("requests_assigned", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("requests_closed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("requests_deal", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_response_time_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("response_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("requests_by_type", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint(
            "metric_date",
            "vertical",
            name="uq_platform_metrics_daily_date_vertical",
        ),
    )
    op.create_index("ix_platform_metrics_daily_metric_date", "platform_metrics_daily", ["metric_date"])
    op.create_index("ix_platform_metrics_daily_vertical", "platform_metrics_daily", ["vertical"])
    op.create_index("ix_platform_metrics_daily_created_at", "platform_metrics_daily", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_platform_metrics_daily_created_at", table_name="platform_metrics_daily")
    op.drop_index("ix_platform_metrics_daily_vertical", table_name="platform_metrics_daily")
    op.drop_index("ix_platform_metrics_daily_metric_date", table_name="platform_metrics_daily")
    op.drop_table("platform_metrics_daily")

    op.drop_index("ix_manager_metrics_vertical", table_name="manager_metrics")
    op.drop_index("ix_manager_metrics_metric_date", table_name="manager_metrics")
    op.drop_index("ix_manager_metrics_manager_id", table_name="manager_metrics")
    op.drop_table("manager_metrics")

    op.drop_index("ix_request_metrics_vertical_created", table_name="request_metrics")
    op.drop_index("ix_request_metrics_status", table_name="request_metrics")
    op.drop_index("ix_request_metrics_manager_id", table_name="request_metrics")
    op.drop_index("ix_request_metrics_vertical", table_name="request_metrics")
    op.drop_index("ix_request_metrics_request_created_at", table_name="request_metrics")
    op.drop_table("request_metrics")
