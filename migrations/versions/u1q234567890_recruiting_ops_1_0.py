"""Recruiting Ops durable registry — Sprint Recruiting 1.0 (additive).

Revision ID: u1q234567890
Revises: t9p012345678
Create Date: 2026-08-27 09:40:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "u1q234567890"
down_revision: Union[str, None] = "t9p012345678"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.exec_driver_sql("SELECT to_regclass('public.recruiting_ops_records')").scalar():
        return
    op.create_table(
        "recruiting_ops_records",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
        sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("status", sa.String(64), nullable=False, server_default="active"),
        sa.Column("payload", JSONB(), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_by", sa.String(128), nullable=True),
        sa.Column("archive_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
    )
    op.create_index("ix_recruiting_ops_records_org_kind", "recruiting_ops_records", ["organization_id", "kind"])
    op.create_index("ix_recruiting_ops_records_tenant", "recruiting_ops_records", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_recruiting_ops_records_tenant", table_name="recruiting_ops_records")
    op.drop_index("ix_recruiting_ops_records_org_kind", table_name="recruiting_ops_records")
    op.drop_table("recruiting_ops_records")
