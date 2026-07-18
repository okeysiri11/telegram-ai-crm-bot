"""Platform configuration center — versioned settings in PostgreSQL.

Revision ID: f9f234567890
Revises: f9e123456789
Create Date: 2026-07-18 16:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "f9f234567890"
down_revision: Union[str, None] = "f9e123456789"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "platform_config",
        sa.Column("key", sa.String(length=256), primary_key=True),
        sa.Column("section", sa.String(length=64), nullable=False),
        sa.Column("value", JSONB(), nullable=True),
        sa.Column("value_type", sa.String(length=32), server_default="json", nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("updated_by", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_platform_config_section", "platform_config", ["section"])
    op.create_index("ix_platform_config_version", "platform_config", ["version"])

    op.create_table(
        "platform_config_history",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("config_key", sa.String(length=256), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("old_value", JSONB(), nullable=True),
        sa.Column("new_value", JSONB(), nullable=True),
        sa.Column("action", sa.String(length=32), server_default="set", nullable=False),
        sa.Column("changed_by", sa.String(length=128), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("config_key", "version", name="uq_platform_config_history_key_version"),
    )
    op.create_index("ix_platform_config_history_config_key", "platform_config_history", ["config_key"])
    op.create_index("ix_platform_config_history_changed_at", "platform_config_history", ["changed_at"])


def downgrade() -> None:
    op.drop_index("ix_platform_config_history_changed_at", table_name="platform_config_history")
    op.drop_index("ix_platform_config_history_config_key", table_name="platform_config_history")
    op.drop_table("platform_config_history")
    op.drop_index("ix_platform_config_version", table_name="platform_config")
    op.drop_index("ix_platform_config_section", table_name="platform_config")
    op.drop_table("platform_config")
