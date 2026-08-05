"""Service Builder tables — Sprint 36.0.

Revision ID: i2c345678901
Revises: h1b234567890
Create Date: 2026-08-03 13:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "i2c345678901"
down_revision: Union[str, None] = "h1b234567890"
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
        "service_registry",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("service_key", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("display_name", sa.String(length=256), nullable=False),
        sa.Column("semver", sa.String(length=64), nullable=False, server_default="0.1.0"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("owner", sa.String(length=128), nullable=False, server_default="platform"),
        sa.Column("category", sa.String(length=64), nullable=False, server_default="other"),
        sa.Column("state", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("icon", sa.String(length=64), nullable=False, server_default="box"),
        sa.Column("manifest_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("configuration_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("module_path", sa.String(length=512), nullable=True),
        sa.Column("entrypoint", sa.String(length=256), nullable=True),
        sa.Column("sandbox_id", sa.String(length=64), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("restart_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        *_ts_cols(),
        sa.UniqueConstraint("service_key", name="uq_service_registry_service_key"),
    )
    op.create_index("ix_service_registry_state", "service_registry", ["state"])
    op.create_index("ix_service_registry_category", "service_registry", ["category"])
    op.create_index("ix_service_registry_owner", "service_registry", ["owner"])

    op.create_table(
        "service_versions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("service_key", sa.String(length=128), nullable=False),
        sa.Column("semver", sa.String(length=64), nullable=False),
        sa.Column("changelog", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("manifest_snapshot", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts_cols(),
        sa.UniqueConstraint("service_key", "semver", name="uq_service_versions_key_semver"),
    )
    op.create_index("ix_service_versions_service_key", "service_versions", ["service_key"])

    op.create_table(
        "service_dependencies",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("service_key", sa.String(length=128), nullable=False),
        sa.Column("depends_on", sa.String(length=128), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        *_ts_cols(),
        sa.UniqueConstraint("service_key", "depends_on", name="uq_service_dependencies_edge"),
    )
    op.create_index("ix_service_dependencies_service_key", "service_dependencies", ["service_key"])
    op.create_index("ix_service_dependencies_depends_on", "service_dependencies", ["depends_on"])

    op.create_table(
        "service_health",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("service_key", sa.String(length=128), nullable=False),
        sa.Column("healthy", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("response_time_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column("memory_mb", sa.Float(), nullable=False, server_default="0"),
        sa.Column("cpu_pct", sa.Float(), nullable=False, server_default="0"),
        sa.Column("errors", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("restart_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("availability_pct", sa.Float(), nullable=False, server_default="100"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("details_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        *_ts_cols(),
    )
    op.create_index("ix_service_health_service_key", "service_health", ["service_key"])
    op.create_index("ix_service_health_recorded_at", "service_health", ["recorded_at"])

    op.create_table(
        "service_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("service_key", sa.String(length=128), nullable=False),
        sa.Column("level", sa.String(length=16), nullable=False, server_default="info"),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("actor", sa.String(length=128), nullable=False, server_default="system"),
        sa.Column("operation", sa.String(length=64), nullable=True),
        sa.Column("old_state", sa.String(length=32), nullable=True),
        sa.Column("new_state", sa.String(length=32), nullable=True),
        sa.Column("duration_ms", sa.Float(), nullable=True),
        sa.Column("result", sa.String(length=32), nullable=False, server_default="ok"),
        sa.Column("details_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts_cols(),
    )
    op.create_index("ix_service_logs_service_key", "service_logs", ["service_key"])
    op.create_index("ix_service_logs_operation", "service_logs", ["operation"])
    op.create_index("ix_service_logs_created_at", "service_logs", ["created_at"])

    op.create_table(
        "service_permissions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("service_key", sa.String(length=128), nullable=False),
        sa.Column("allowed_apis", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("allowed_events", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("allowed_storage", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("allowed_ai_tools", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("allowed_integrations", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        *_ts_cols(),
        sa.UniqueConstraint("service_key", name="uq_service_permissions_service_key"),
    )
    op.create_index("ix_service_permissions_service_key", "service_permissions", ["service_key"])


def downgrade() -> None:
    op.drop_table("service_permissions")
    op.drop_table("service_logs")
    op.drop_table("service_health")
    op.drop_table("service_dependencies")
    op.drop_table("service_versions")
    op.drop_table("service_registry")
