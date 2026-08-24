"""AGRO Production 1.0 — generic durable ops registry (additive).

Revision ID: i8d901234567
Revises: h7c890123456
Create Date: 2026-08-16 11:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "i8d901234567"
down_revision: Union[str, None] = "h7c890123456"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.exec_driver_sql("SELECT to_regclass('public.agro_ops_records')").scalar():
        return
    op.create_table(
        "agro_ops_records",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
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
    op.create_index("ix_agro_ops_records_org_kind", "agro_ops_records", ["organization_id", "kind"])
    op.create_index("ix_agro_ops_records_tenant", "agro_ops_records", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_agro_ops_records_tenant", table_name="agro_ops_records")
    op.drop_index("ix_agro_ops_records_org_kind", table_name="agro_ops_records")
    op.drop_table("agro_ops_records")
