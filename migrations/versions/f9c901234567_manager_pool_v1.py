"""Platform manager_pool table.

Revision ID: f9c901234567
Revises: f9b890123456
Create Date: 2026-07-18 12:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "f9c901234567"
down_revision: Union[str, None] = "f9b890123456"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "manager_pool",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("vertical", sa.String(length=32), nullable=False),
        sa.Column("priority", sa.Integer(), server_default="100", nullable=False),
        sa.Column("weight", sa.Integer(), server_default="100", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("current_load", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("telegram_id", "vertical", name="uq_manager_pool_telegram_vertical"),
    )
    op.create_index("ix_manager_pool_vertical", "manager_pool", ["vertical"])
    op.create_index("ix_manager_pool_is_active", "manager_pool", ["is_active"])
    op.create_index("ix_manager_pool_priority", "manager_pool", ["priority"])
    op.create_index("ix_manager_pool_current_load", "manager_pool", ["current_load"])
    op.create_index("ix_manager_pool_last_assigned_at", "manager_pool", ["last_assigned_at"])


def downgrade() -> None:
    op.drop_index("ix_manager_pool_last_assigned_at", table_name="manager_pool")
    op.drop_index("ix_manager_pool_current_load", table_name="manager_pool")
    op.drop_index("ix_manager_pool_priority", table_name="manager_pool")
    op.drop_index("ix_manager_pool_is_active", table_name="manager_pool")
    op.drop_index("ix_manager_pool_vertical", table_name="manager_pool")
    op.drop_table("manager_pool")
