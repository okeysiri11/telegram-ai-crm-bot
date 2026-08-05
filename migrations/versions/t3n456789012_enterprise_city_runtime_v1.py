"""Enterprise City Runtime tables — Sprint 37.0.

Revision ID: t3n456789012
Revises: s2m345678901
Create Date: 2026-08-04 11:45:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "t3n456789012"
down_revision: Union[str, None] = "s2m345678901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ts_cols():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("change_id", sa.String(length=64), nullable=True),
        sa.Column("source_client", sa.String(length=32), nullable=True),
        sa.Column("workspace_id", sa.String(length=128), nullable=True),
        sa.Column("created_by", sa.String(length=128), nullable=True),
        sa.Column("updated_by", sa.String(length=128), nullable=True),
        sa.Column("metadata_json", JSONB(), nullable=True),
    ]


def upgrade() -> None:
    op.create_table(
        "platform_registry",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("service_key", sa.String(128), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("display_name", sa.String(256), nullable=False),
        sa.Column("route", sa.String(256), nullable=False, server_default="/platform"),
        sa.Column("category", sa.String(64), nullable=False, server_default="platform"),
        sa.Column("status", sa.String(32), nullable=False, server_default="healthy"),
        sa.Column("sprint", sa.String(32), nullable=False, server_default=""),
        sa.Column("api_prefixes_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("dependencies_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("payload_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts_cols(),
        sa.UniqueConstraint("service_key", name="uq_platform_registry_service_key"),
    )
    op.create_index("ix_platform_registry_category", "platform_registry", ["category"])

    op.create_table(
        "platform_sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("session_key", sa.String(128), nullable=False),
        sa.Column("user_id", sa.String(128), nullable=False),
        sa.Column("roles_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("permissions_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("shared_context_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("shared_memory_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("active_module", sa.String(128), nullable=True),
        sa.Column("payload_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts_cols(),
        sa.UniqueConstraint("session_key", name="uq_platform_sessions_session_key"),
    )
    op.create_index("ix_platform_sessions_user_id", "platform_sessions", ["user_id"])

    op.create_table(
        "platform_metrics",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("metric_key", sa.String(128), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("value", sa.Float(), nullable=False, server_default="0"),
        sa.Column("unit", sa.String(32), nullable=False, server_default=""),
        sa.Column("category", sa.String(64), nullable=False, server_default="kpi"),
        sa.Column("labels_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts_cols(),
        sa.UniqueConstraint("metric_key", name="uq_platform_metrics_metric_key"),
    )
    op.create_index("ix_platform_metrics_name", "platform_metrics", ["name"])
    op.create_index("ix_platform_metrics_category", "platform_metrics", ["category"])

    op.create_table(
        "platform_health",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("component_key", sa.String(128), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("level", sa.String(32), nullable=False, server_default="healthy"),
        sa.Column("message", sa.Text(), nullable=False, server_default=""),
        sa.Column("latency_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts_cols(),
        sa.UniqueConstraint("component_key", name="uq_platform_health_component_key"),
    )
    op.create_index("ix_platform_health_level", "platform_health", ["level"])

    op.create_table(
        "platform_usage",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("usage_key", sa.String(128), nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("module", sa.String(128), nullable=False),
        sa.Column("user_id", sa.String(128), nullable=False, server_default="system"),
        sa.Column("details_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts_cols(),
    )
    op.create_index("ix_platform_usage_module", "platform_usage", ["module"])
    op.create_index("ix_platform_usage_action", "platform_usage", ["action"])

    op.create_table(
        "platform_configuration",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("config_key", sa.String(256), nullable=False),
        sa.Column("value_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("category", sa.String(64), nullable=False, server_default="general"),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        *_ts_cols(),
        sa.UniqueConstraint("config_key", name="uq_platform_configuration_config_key"),
    )
    op.create_index("ix_platform_configuration_category", "platform_configuration", ["category"])


def downgrade() -> None:
    op.drop_table("platform_configuration")
    op.drop_table("platform_usage")
    op.drop_table("platform_health")
    op.drop_table("platform_metrics")
    op.drop_table("platform_sessions")
    op.drop_table("platform_registry")
