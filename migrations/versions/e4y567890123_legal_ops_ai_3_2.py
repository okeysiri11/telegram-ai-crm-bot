"""Lawyer 3.2 — AI analyses persistence (additive).

Revision ID: e4y567890123
Revises: d3x456789012
Create Date: 2026-08-12 17:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "e4y567890123"
down_revision: Union[str, None] = "d3x456789012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _exists(conn, name: str) -> bool:
    return conn.exec_driver_sql(f"SELECT to_regclass('public.{name}')").scalar() is not None


def upgrade() -> None:
    conn = op.get_bind()
    if not _exists(conn, "legal_ops_ai_analyses"):
        op.create_table(
            "legal_ops_ai_analyses",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("workspace_kind", sa.String(32), nullable=False, server_default="analysis"),
            sa.Column("action", sa.String(64), nullable=True),
            sa.Column("mode", sa.String(64), nullable=True),
            sa.Column("target_type", sa.String(64), nullable=True),
            sa.Column("target_id", sa.String(64), nullable=True),
            sa.Column("client_id", sa.String(64), nullable=True),
            sa.Column("case_id", sa.String(64), nullable=True),
            sa.Column("question", sa.Text(), nullable=True),
            sa.Column("result", JSONB(), nullable=True),
            sa.Column("sources", JSONB(), nullable=True),
            sa.Column("context_snapshot", JSONB(), nullable=True),
            sa.Column("provider_meta", JSONB(), nullable=True),
            sa.Column("created_tasks", JSONB(), nullable=True),
            sa.Column("created_events", JSONB(), nullable=True),
            sa.Column("created_documents", JSONB(), nullable=True),
            sa.Column("actor_role", sa.String(64), nullable=True),
            sa.Column("actor_id", sa.String(128), nullable=True),
            sa.Column("status", sa.String(32), nullable=False, server_default="active"),
            sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("archived_by", sa.String(128), nullable=True),
            sa.Column("archive_reason", sa.Text(), nullable=True),
            sa.Column("payload", JSONB(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("version", sa.Integer(), server_default="1", nullable=False),
            sa.Column("change_id", sa.String(length=64), nullable=True),
            sa.Column("source_client", sa.String(length=32), nullable=True),
            sa.Column("workspace_id", sa.String(length=128), nullable=True),
            sa.Column("created_by", sa.String(length=128), nullable=True),
            sa.Column("updated_by", sa.String(length=128), nullable=True),
            sa.Column("metadata_json", JSONB(), nullable=True),
        )
        op.create_index("ix_legal_ops_ai_analyses_org", "legal_ops_ai_analyses", ["organization_id"])
        op.create_index("ix_legal_ops_ai_analyses_case", "legal_ops_ai_analyses", ["case_id"])
        op.create_index("ix_legal_ops_ai_analyses_target", "legal_ops_ai_analyses", ["target_type", "target_id"])


def downgrade() -> None:
    pass
