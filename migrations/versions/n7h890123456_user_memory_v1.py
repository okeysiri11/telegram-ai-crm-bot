"""User memory table — PostgreSQL replacement for SQLite user_memory.

Revision ID: n7h890123456
Revises: m6g789012345
Create Date: 2026-08-03 17:40:00.000000

Sprint 37.1: fully idempotent (table/index may already exist).
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "n7h890123456"
down_revision: Union[str, None] = "m6g789012345"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    existing = set(inspect(bind).get_table_names())
    if "user_memory" not in existing:
        op.create_table(
            "user_memory",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("telegram_id", sa.BigInteger(), nullable=False),
            sa.Column("memory_key", sa.String(64), nullable=False),
            sa.Column("memory_value", sa.Text(), nullable=False, server_default=""),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("version", sa.Integer(), server_default="1", nullable=False),
            sa.Column("change_id", sa.String(length=64), nullable=True),
            sa.Column("source_client", sa.String(length=32), nullable=True),
            sa.Column("workspace_id", sa.String(length=128), nullable=True),
            sa.Column("created_by", sa.String(length=128), nullable=True),
            sa.Column("updated_by", sa.String(length=128), nullable=True),
            sa.Column("metadata_json", JSONB(), nullable=True),
            sa.UniqueConstraint("telegram_id", "memory_key", name="uq_user_memory_telegram_key"),
        )
    # IF NOT EXISTS avoids aborting the migration transaction on legacy DBs.
    bind.execute(text("CREATE INDEX IF NOT EXISTS ix_user_memory_telegram_id ON user_memory (telegram_id)"))


def downgrade() -> None:
    bind = op.get_bind()
    existing = set(inspect(bind).get_table_names())
    if "user_memory" not in existing:
        return
    bind.execute(text("DROP INDEX IF EXISTS ix_user_memory_telegram_id"))
    op.drop_table("user_memory")
