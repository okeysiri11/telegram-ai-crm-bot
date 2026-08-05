"""Multi-Agent Runtime tables — Sprint 36.7.

Revision ID: q0k123456789
Revises: p9j012345678
Create Date: 2026-08-03 21:10:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "q0k123456789"
down_revision: Union[str, None] = "p9j012345678"
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
        "agent_registry",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_key", sa.String(64), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("capabilities_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("skills_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("permissions_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("availability", sa.String(32), nullable=False, server_default="available"),
        sa.Column("healthy", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("payload_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts_cols(),
        sa.UniqueConstraint("agent_key", name="uq_agent_registry_agent_key"),
    )
    op.create_index("ix_agent_registry_availability", "agent_registry", ["availability"])

    op.create_table(
        "agent_tasks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("task_key", sa.String(64), nullable=False),
        sa.Column("title", sa.String(512), nullable=False, server_default=""),
        sa.Column("capability", sa.String(128), nullable=False, server_default="work"),
        sa.Column("status", sa.String(32), nullable=False, server_default="queued"),
        sa.Column("agent_key", sa.String(64), nullable=True),
        sa.Column("session_key", sa.String(64), nullable=True),
        sa.Column("plan_key", sa.String(64), nullable=True),
        sa.Column("payload_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("retries", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("timeout_sec", sa.Float(), nullable=False, server_default="30"),
        sa.Column("checkpoint_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("result_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("error", sa.Text(), nullable=True),
        *_ts_cols(),
    )
    op.create_index("ix_agent_tasks_status", "agent_tasks", ["status"])
    op.create_index("ix_agent_tasks_session_key", "agent_tasks", ["session_key"])

    op.create_table(
        "agent_messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("message_key", sa.String(64), nullable=False),
        sa.Column("channel", sa.String(32), nullable=False, server_default="direct"),
        sa.Column("source_agent_key", sa.String(64), nullable=False),
        sa.Column("target_agent_key", sa.String(64), nullable=True),
        sa.Column("topic", sa.String(128), nullable=True),
        sa.Column("payload_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts_cols(),
    )
    op.create_index("ix_agent_messages_channel", "agent_messages", ["channel"])
    op.create_index("ix_agent_messages_topic", "agent_messages", ["topic"])

    op.create_table(
        "agent_sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("session_key", sa.String(64), nullable=False),
        sa.Column("goal", sa.Text(), nullable=False, server_default=""),
        sa.Column("mode", sa.String(32), nullable=False, server_default="sequential"),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("agent_ids_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("shared_context_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("shared_memory_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("payload_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts_cols(),
        sa.UniqueConstraint("session_key", name="uq_agent_sessions_session_key"),
    )
    op.create_index("ix_agent_sessions_status", "agent_sessions", ["status"])

    op.create_table(
        "agent_plans",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("plan_key", sa.String(64), nullable=False),
        sa.Column("session_key", sa.String(64), nullable=True),
        sa.Column("goal", sa.Text(), nullable=False, server_default=""),
        sa.Column("mode", sa.String(32), nullable=False, server_default="sequential"),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("steps_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        *_ts_cols(),
        sa.UniqueConstraint("plan_key", name="uq_agent_plans_plan_key"),
    )
    op.create_index("ix_agent_plans_status", "agent_plans", ["status"])

    op.create_table(
        "agent_execution",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("execution_key", sa.String(64), nullable=False),
        sa.Column("session_key", sa.String(64), nullable=True),
        sa.Column("plan_key", sa.String(64), nullable=True),
        sa.Column("mode", sa.String(32), nullable=False, server_default="sequential"),
        sa.Column("status", sa.String(32), nullable=False, server_default="running"),
        sa.Column("results_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("aggregated_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts_cols(),
    )
    op.create_index("ix_agent_execution_session_key", "agent_execution", ["session_key"])
    op.create_index("ix_agent_execution_status", "agent_execution", ["status"])

    op.create_table(
        "agent_statistics",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("metric_key", sa.String(128), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=False, server_default="0"),
        sa.Column("details_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("note", sa.Text(), nullable=True),
        *_ts_cols(),
    )
    op.create_index("ix_agent_statistics_metric_key", "agent_statistics", ["metric_key"])


def downgrade() -> None:
    for table in (
        "agent_statistics",
        "agent_execution",
        "agent_plans",
        "agent_sessions",
        "agent_messages",
        "agent_tasks",
        "agent_registry",
    ):
        op.drop_table(table)
