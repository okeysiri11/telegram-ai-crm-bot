"""Workflow engine persistence — executions and step logs.

Revision ID: f9e123456789
Revises: f9d012345678
Create Date: 2026-07-18 15:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "f9e123456789"
down_revision: Union[str, None] = "f9d012345678"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "workflow_executions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("workflow_id", sa.String(length=64), nullable=False),
        sa.Column("vertical", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="PENDING", nullable=False),
        sa.Column("current_step", sa.String(length=64), nullable=True),
        sa.Column("context_json", JSONB(), server_default="{}", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_workflow_executions_workflow_id", "workflow_executions", ["workflow_id"])
    op.create_index("ix_workflow_executions_vertical", "workflow_executions", ["vertical"])
    op.create_index("ix_workflow_executions_status", "workflow_executions", ["status"])
    op.create_index("ix_workflow_executions_started_at", "workflow_executions", ["started_at"])

    op.create_table(
        "workflow_step_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("execution_id", UUID(as_uuid=True), nullable=False),
        sa.Column("step_id", sa.String(length=64), nullable=False),
        sa.Column("step_type", sa.String(length=32), nullable=False),
        sa.Column("duration_ms", sa.Float(), server_default="0", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="OK", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_workflow_step_logs_execution_id", "workflow_step_logs", ["execution_id"])
    op.create_index("ix_workflow_step_logs_step_id", "workflow_step_logs", ["step_id"])


def downgrade() -> None:
    op.drop_index("ix_workflow_step_logs_step_id", table_name="workflow_step_logs")
    op.drop_index("ix_workflow_step_logs_execution_id", table_name="workflow_step_logs")
    op.drop_table("workflow_step_logs")
    op.drop_index("ix_workflow_executions_started_at", table_name="workflow_executions")
    op.drop_index("ix_workflow_executions_status", table_name="workflow_executions")
    op.drop_index("ix_workflow_executions_vertical", table_name="workflow_executions")
    op.drop_index("ix_workflow_executions_workflow_id", table_name="workflow_executions")
    op.drop_table("workflow_executions")
