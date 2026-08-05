"""Workflow Runtime tables — Sprint 36.2.

Revision ID: k4e567890123
Revises: j3d456789012
Create Date: 2026-08-03 15:20:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "k4e567890123"
down_revision: Union[str, None] = "j3d456789012"
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
        "workflow_registry",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("workflow_key", sa.String(128), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("semver", sa.String(64), nullable=False, server_default="1.0.0"),
        sa.Column("owner", sa.String(128), nullable=False, server_default="platform"),
        sa.Column("start_step", sa.String(128), nullable=True),
        sa.Column("definition_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("tags_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        *_ts_cols(),
        sa.UniqueConstraint("workflow_key", name="uq_workflow_registry_workflow_key"),
    )
    op.create_index("ix_workflow_registry_status", "workflow_registry", ["status"])

    op.create_table(
        "workflow_versions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("workflow_key", sa.String(128), nullable=False),
        sa.Column("semver", sa.String(64), nullable=False),
        sa.Column("changelog", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("snapshot_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts_cols(),
        sa.UniqueConstraint("workflow_key", "semver", name="uq_workflow_versions_key_semver"),
    )
    op.create_index("ix_workflow_versions_workflow_key", "workflow_versions", ["workflow_key"])

    op.create_table(
        "workflow_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("run_key", sa.String(64), nullable=False),
        sa.Column("workflow_key", sa.String(128), nullable=False),
        sa.Column("semver", sa.String(64), nullable=False, server_default="1.0.0"),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("mode", sa.String(32), nullable=False, server_default="sync"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("context_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("timeout_sec", sa.Float(), nullable=False, server_default="120"),
        sa.Column("rollback_of", sa.String(64), nullable=True),
        *_ts_cols(),
        sa.UniqueConstraint("run_key", name="uq_workflow_runs_run_key"),
    )
    op.create_index("ix_workflow_runs_workflow_key", "workflow_runs", ["workflow_key"])
    op.create_index("ix_workflow_runs_status", "workflow_runs", ["status"])

    op.create_table(
        "workflow_steps",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("run_key", sa.String(64), nullable=False),
        sa.Column("step_key", sa.String(128), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("kind", sa.String(64), nullable=False, server_default="task"),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Float(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        *_ts_cols(),
    )
    op.create_index("ix_workflow_steps_run_key", "workflow_steps", ["run_key"])

    op.create_table(
        "workflow_variables",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("run_key", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("value_json", JSONB(), nullable=True),
        *_ts_cols(),
        sa.UniqueConstraint("run_key", "name", name="uq_workflow_variables_run_name"),
    )
    op.create_index("ix_workflow_variables_run_key", "workflow_variables", ["run_key"])

    op.create_table(
        "workflow_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("run_key", sa.String(64), nullable=False),
        sa.Column("event", sa.String(64), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("logged_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        *_ts_cols(),
    )
    op.create_index("ix_workflow_logs_run_key", "workflow_logs", ["run_key"])

    op.create_table(
        "workflow_checkpoints",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("run_key", sa.String(64), nullable=False),
        sa.Column("checkpoint_key", sa.String(64), nullable=False),
        sa.Column("label", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("vars_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        *_ts_cols(),
    )
    op.create_index("ix_workflow_checkpoints_run_key", "workflow_checkpoints", ["run_key"])


def downgrade() -> None:
    op.drop_table("workflow_checkpoints")
    op.drop_table("workflow_logs")
    op.drop_table("workflow_variables")
    op.drop_table("workflow_steps")
    op.drop_table("workflow_runs")
    op.drop_table("workflow_versions")
    op.drop_table("workflow_registry")
