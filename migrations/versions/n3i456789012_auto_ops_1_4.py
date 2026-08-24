"""AUTO 1.4 Telegram members / outbox (additive to AUTO 1.3).

Revision ID: n3i456789012
Revises: m2h345678901
Create Date: 2026-08-19 08:50:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "n3i456789012"
down_revision: Union[str, None] = "m2h345678901"
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
    conn = op.get_bind()

    def _exists(name: str) -> bool:
        return conn.exec_driver_sql(f"SELECT to_regclass('public.{name}')").scalar() is not None

    if not _exists("auto_ops_telegram_members"):
        op.create_table(
            "auto_ops_telegram_members",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("telegram_id", sa.BigInteger(), nullable=False),
            sa.Column("role", sa.String(32), nullable=False, server_default="auto_manager"),
            sa.Column("username", sa.String(128), nullable=True),
            sa.Column("label", sa.String(256), nullable=True),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("payload", JSONB(), nullable=True),
            *_ts_cols(),
        )
        op.create_index("ix_auto_ops_tg_members_org", "auto_ops_telegram_members", ["organization_id"])
        op.create_index("ix_auto_ops_tg_members_tid", "auto_ops_telegram_members", ["telegram_id"])

    if not _exists("auto_ops_telegram_outbox"):
        op.create_table(
            "auto_ops_telegram_outbox",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("telegram_id", sa.BigInteger(), nullable=False),
            sa.Column("kind", sa.String(32), nullable=False, server_default="event"),
            sa.Column("text", sa.Text(), nullable=True),
            sa.Column("dedupe_key", sa.String(256), nullable=True),
            sa.Column("payload", JSONB(), nullable=True),
            *_ts_cols(),
        )
        op.create_index("ix_auto_ops_tg_outbox_org", "auto_ops_telegram_outbox", ["organization_id"])


def downgrade() -> None:
    pass
