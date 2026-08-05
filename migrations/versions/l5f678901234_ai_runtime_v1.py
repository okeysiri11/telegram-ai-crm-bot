"""AI Runtime tables — Sprint 36.3.

Revision ID: l5f678901234
Revises: k4e567890123
Create Date: 2026-08-03 16:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "l5f678901234"
down_revision: Union[str, None] = "k4e567890123"
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
        "ai_providers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("provider_key", sa.String(64), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("status", sa.String(32), nullable=False, server_default="available"),
        sa.Column("latency_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column("config_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("models_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        *_ts_cols(),
        sa.UniqueConstraint("provider_key", name="uq_ai_providers_provider_key"),
    )
    op.create_index("ix_ai_providers_status", "ai_providers", ["status"])

    op.create_table(
        "ai_models",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("provider_key", sa.String(64), nullable=False),
        sa.Column("model_key", sa.String(128), nullable=False),
        sa.Column("display_name", sa.String(256), nullable=False),
        sa.Column("context_window", sa.Integer(), nullable=False, server_default="8192"),
        sa.Column("status", sa.String(32), nullable=False, server_default="available"),
        sa.Column("capabilities_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("pricing_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("task_types_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        *_ts_cols(),
        sa.UniqueConstraint("provider_key", "model_key", name="uq_ai_models_provider_model"),
    )
    op.create_index("ix_ai_models_provider_key", "ai_models", ["provider_key"])

    op.create_table(
        "ai_runtime_sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("session_key", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("provider_key", sa.String(64), nullable=True),
        sa.Column("model_key", sa.String(128), nullable=True),
        sa.Column("user_id", sa.String(128), nullable=True),
        sa.Column("tenant_id", sa.String(128), nullable=True),
        sa.Column("request_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("context_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        *_ts_cols(),
        sa.UniqueConstraint("session_key", name="uq_ai_runtime_sessions_session_key"),
    )
    op.create_index("ix_ai_runtime_sessions_status", "ai_runtime_sessions", ["status"])

    op.create_table(
        "prompt_templates",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("template_key", sa.String(128), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("body", sa.Text(), nullable=False, server_default=""),
        sa.Column("system_prompt", sa.Text(), nullable=False, server_default=""),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("parent_key", sa.String(128), nullable=True),
        sa.Column("active_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("variables_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        *_ts_cols(),
        sa.UniqueConstraint("template_key", name="uq_prompt_templates_template_key"),
    )

    op.create_table(
        "prompt_versions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("template_key", sa.String(128), nullable=False),
        sa.Column("semver", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("body", sa.Text(), nullable=False, server_default=""),
        sa.Column("system_prompt", sa.Text(), nullable=False, server_default=""),
        sa.Column("changelog", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("variables_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        *_ts_cols(),
        sa.UniqueConstraint("template_key", "semver", name="uq_prompt_versions_template_semver"),
    )
    op.create_index("ix_prompt_versions_template_key", "prompt_versions", ["template_key"])

    op.create_table(
        "tool_registry",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tool_key", sa.String(128), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("parameters_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("permission", sa.String(32), nullable=False, server_default="allow"),
        sa.Column("mcp_compatible", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("timeout_sec", sa.Float(), nullable=False, server_default="30"),
        sa.Column("sandbox", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        *_ts_cols(),
        sa.UniqueConstraint("tool_key", name="uq_tool_registry_tool_key"),
    )
    op.create_index("ix_tool_registry_enabled", "tool_registry", ["enabled"])

    op.create_table(
        "tool_executions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("execution_key", sa.String(64), nullable=False),
        sa.Column("tool_key", sa.String(128), nullable=False),
        sa.Column("session_key", sa.String(64), nullable=True),
        sa.Column("arguments_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("result_json", JSONB(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Float(), nullable=False, server_default="0"),
        *_ts_cols(),
    )
    op.create_index("ix_tool_executions_tool_key", "tool_executions", ["tool_key"])
    op.create_index("ix_tool_executions_session_key", "tool_executions", ["session_key"])

    op.create_table(
        "ai_runtime_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("log_key", sa.String(64), nullable=False),
        sa.Column("level", sa.String(16), nullable=False, server_default="info"),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("session_key", sa.String(64), nullable=True),
        sa.Column("provider_key", sa.String(64), nullable=True),
        sa.Column("model_key", sa.String(128), nullable=True),
        sa.Column("details_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts_cols(),
    )
    op.create_index("ix_ai_runtime_logs_session_key", "ai_runtime_logs", ["session_key"])
    op.create_index("ix_ai_runtime_logs_level", "ai_runtime_logs", ["level"])


def downgrade() -> None:
    for table in (
        "ai_runtime_logs",
        "tool_executions",
        "tool_registry",
        "prompt_versions",
        "prompt_templates",
        "ai_runtime_sessions",
        "ai_models",
        "ai_providers",
    ):
        op.drop_table(table)
