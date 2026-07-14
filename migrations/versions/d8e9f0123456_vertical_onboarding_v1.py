"""vertical_onboarding_v1

Revision ID: d8e9f0123456
Revises: d7e8f9012345
Create Date: 2026-07-14 10:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d8e9f0123456"
down_revision: Union[str, None] = "d7e8f9012345"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_vertical_preferences_v1",
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("vertical", sa.String(length=32), nullable=True),
        sa.Column("language", sa.String(length=8), nullable=False, server_default="ru"),
        sa.Column("role", sa.String(length=64), nullable=True),
        sa.Column("onboarding_step", sa.String(length=32), nullable=True),
        sa.Column(
            "onboarding_completed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_user_id"),
    )
    op.create_index(
        "ix_user_vertical_prefs_telegram",
        "user_vertical_preferences_v1",
        ["telegram_user_id"],
        unique=True,
    )
    op.create_index(
        "ix_user_vertical_prefs_vertical",
        "user_vertical_preferences_v1",
        ["vertical"],
    )
    op.create_index(
        "ix_user_vertical_prefs_language",
        "user_vertical_preferences_v1",
        ["language"],
    )


def downgrade() -> None:
    op.drop_index("ix_user_vertical_prefs_language", table_name="user_vertical_preferences_v1")
    op.drop_index("ix_user_vertical_prefs_vertical", table_name="user_vertical_preferences_v1")
    op.drop_index("ix_user_vertical_prefs_telegram", table_name="user_vertical_preferences_v1")
    op.drop_table("user_vertical_preferences_v1")
