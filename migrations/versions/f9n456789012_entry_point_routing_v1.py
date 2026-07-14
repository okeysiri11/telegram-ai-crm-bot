"""entry_point_routing_v1

Revision ID: f9n456789012
Revises: f9m345678901
Create Date: 2026-07-14 20:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f9n456789012"
down_revision: Union[str, None] = "f9m345678901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_vertical_preferences_v1",
        sa.Column("entry_point", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "user_vertical_preferences_v1",
        sa.Column("current_flow", sa.String(length=32), nullable=True),
    )
    op.create_index(
        "ix_user_vertical_prefs_entry_point",
        "user_vertical_preferences_v1",
        ["entry_point"],
    )
    op.create_index(
        "ix_user_vertical_prefs_current_flow",
        "user_vertical_preferences_v1",
        ["current_flow"],
    )


def downgrade() -> None:
    op.drop_index("ix_user_vertical_prefs_current_flow", table_name="user_vertical_preferences_v1")
    op.drop_index("ix_user_vertical_prefs_entry_point", table_name="user_vertical_preferences_v1")
    op.drop_column("user_vertical_preferences_v1", "current_flow")
    op.drop_column("user_vertical_preferences_v1", "entry_point")
