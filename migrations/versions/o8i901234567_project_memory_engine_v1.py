"""Project Memory Engine tables — Sprint 36.5.

Revision ID: o8i901234567
Revises: n7h890123456
Create Date: 2026-08-03 18:50:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "o8i901234567"
down_revision: Union[str, None] = "n7h890123456"
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
        "project_memory",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("memory_key", sa.String(64), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False, server_default="project"),
        sa.Column("layer", sa.String(32), nullable=False, server_default="long_term"),
        sa.Column("title", sa.String(512), nullable=False, server_default=""),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("project_id", sa.String(128), nullable=True),
        sa.Column("agent_id", sa.String(128), nullable=True),
        sa.Column("client_id", sa.String(128), nullable=True),
        sa.Column("workflow_id", sa.String(128), nullable=True),
        sa.Column("document_id", sa.String(128), nullable=True),
        sa.Column("tags_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("importance", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payload_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts_cols(),
        sa.UniqueConstraint("memory_key", name="uq_project_memory_memory_key"),
    )
    op.create_index("ix_project_memory_kind", "project_memory", ["kind"])
    op.create_index("ix_project_memory_layer", "project_memory", ["layer"])
    op.create_index("ix_project_memory_project_id", "project_memory", ["project_id"])

    op.create_table(
        "memory_chunks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("chunk_key", sa.String(64), nullable=False),
        sa.Column("memory_key", sa.String(64), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("text", sa.Text(), nullable=False, server_default=""),
        sa.Column("tokens", sa.Integer(), nullable=False, server_default="0"),
        *_ts_cols(),
    )
    op.create_index("ix_memory_chunks_memory_key", "memory_chunks", ["memory_key"])

    op.create_table(
        "memory_embeddings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("embedding_key", sa.String(64), nullable=False),
        sa.Column("memory_key", sa.String(64), nullable=False),
        sa.Column("chunk_key", sa.String(64), nullable=True),
        sa.Column("dims", sa.Integer(), nullable=False, server_default="8"),
        sa.Column("vector_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("model", sa.String(128), nullable=False, server_default="dummy"),
        *_ts_cols(),
    )
    op.create_index("ix_memory_embeddings_memory_key", "memory_embeddings", ["memory_key"])

    op.create_table(
        "memory_relations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("relation_key", sa.String(64), nullable=False),
        sa.Column("from_key", sa.String(64), nullable=False),
        sa.Column("to_key", sa.String(64), nullable=False),
        sa.Column("relation", sa.String(64), nullable=False, server_default="related"),
        sa.Column("weight", sa.Float(), nullable=False, server_default="1"),
        *_ts_cols(),
    )
    op.create_index("ix_memory_relations_from", "memory_relations", ["from_key"])
    op.create_index("ix_memory_relations_to", "memory_relations", ["to_key"])

    op.create_table(
        "memory_sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("session_key", sa.String(64), nullable=False),
        sa.Column("project_id", sa.String(128), nullable=True),
        sa.Column("agent_id", sa.String(128), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("working_set_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("payload_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts_cols(),
        sa.UniqueConstraint("session_key", name="uq_memory_sessions_session_key"),
    )
    op.create_index("ix_memory_sessions_project_id", "memory_sessions", ["project_id"])

    op.create_table(
        "memory_history",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("history_key", sa.String(64), nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("memory_key", sa.String(64), nullable=True),
        sa.Column("session_key", sa.String(64), nullable=True),
        sa.Column("details_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts_cols(),
    )
    op.create_index("ix_memory_history_memory_key", "memory_history", ["memory_key"])
    op.create_index("ix_memory_history_session_key", "memory_history", ["session_key"])

    op.create_table(
        "memory_feedback",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("feedback_key", sa.String(64), nullable=False),
        sa.Column("memory_key", sa.String(64), nullable=False),
        sa.Column("score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("comment", sa.Text(), nullable=False, server_default=""),
        sa.Column("actor", sa.String(128), nullable=False, server_default="system"),
        *_ts_cols(),
    )
    op.create_index("ix_memory_feedback_memory_key", "memory_feedback", ["memory_key"])


def downgrade() -> None:
    for table in (
        "memory_feedback",
        "memory_history",
        "memory_sessions",
        "memory_relations",
        "memory_embeddings",
        "memory_chunks",
        "project_memory",
    ):
        op.drop_table(table)
