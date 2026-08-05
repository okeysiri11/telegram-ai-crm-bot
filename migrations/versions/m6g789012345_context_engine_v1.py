"""Context Engine tables — Sprint 36.4.

Revision ID: m6g789012345
Revises: l5f678901234
Create Date: 2026-08-03 17:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "m6g789012345"
down_revision: Union[str, None] = "l5f678901234"
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
        "context_sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("session_key", sa.String(64), nullable=False),
        sa.Column("user_id", sa.String(128), nullable=True),
        sa.Column("tenant_id", sa.String(128), nullable=True),
        sa.Column("principal", sa.String(128), nullable=False, server_default="system"),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("fragment_ids_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payload_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts_cols(),
        sa.UniqueConstraint("session_key", name="uq_context_sessions_session_key"),
    )
    op.create_index("ix_context_sessions_status", "context_sessions", ["status"])

    op.create_table(
        "context_sources",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("source_key", sa.String(64), nullable=False),
        sa.Column("display_name", sa.String(256), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("rank", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("config_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts_cols(),
        sa.UniqueConstraint("source_key", name="uq_context_sources_source_key"),
    )
    op.create_index("ix_context_sources_enabled", "context_sources", ["enabled"])

    op.create_table(
        "context_cache",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("cache_key", sa.String(128), nullable=False),
        sa.Column("bundle_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("hits", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        *_ts_cols(),
        sa.UniqueConstraint("cache_key", name="uq_context_cache_cache_key"),
    )
    op.create_index("ix_context_cache_expires_at", "context_cache", ["expires_at"])

    op.create_table(
        "context_history",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("history_key", sa.String(64), nullable=False),
        sa.Column("session_key", sa.String(64), nullable=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("details_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts_cols(),
    )
    op.create_index("ix_context_history_session_key", "context_history", ["session_key"])

    op.create_table(
        "context_permissions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("permission_key", sa.String(64), nullable=False),
        sa.Column("principal", sa.String(128), nullable=False),
        sa.Column("source_key", sa.String(64), nullable=False, server_default="*"),
        sa.Column("action", sa.String(32), nullable=False, server_default="read"),
        sa.Column("max_sensitivity", sa.String(32), nullable=False, server_default="internal"),
        sa.Column("isolation_key", sa.String(128), nullable=True),
        sa.Column("policy_version", sa.Integer(), nullable=False, server_default="1"),
        *_ts_cols(),
    )
    op.create_index("ix_context_permissions_principal", "context_permissions", ["principal"])
    op.create_index("ix_context_permissions_source", "context_permissions", ["source_key"])

    op.create_table(
        "context_embeddings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("embedding_key", sa.String(64), nullable=False),
        sa.Column("fragment_key", sa.String(64), nullable=False),
        sa.Column("dims", sa.Integer(), nullable=False, server_default="8"),
        sa.Column("vector_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("model", sa.String(128), nullable=False, server_default="dummy"),
        *_ts_cols(),
    )
    op.create_index("ix_context_embeddings_fragment_key", "context_embeddings", ["fragment_key"])

    op.create_table(
        "context_statistics",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("metric_key", sa.String(128), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=False, server_default="0"),
        sa.Column("details_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("note", sa.Text(), nullable=True),
        *_ts_cols(),
    )
    op.create_index("ix_context_statistics_metric_key", "context_statistics", ["metric_key"])


def downgrade() -> None:
    for table in (
        "context_statistics",
        "context_embeddings",
        "context_permissions",
        "context_history",
        "context_cache",
        "context_sources",
        "context_sessions",
    ):
        op.drop_table(table)
