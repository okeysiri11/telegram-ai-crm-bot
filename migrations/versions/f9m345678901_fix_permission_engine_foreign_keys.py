"""fix permission engine foreign keys

Revision ID: f9m345678901
Revises: f9l234567890
Create Date: 2026-07-14 18:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "f9m345678901"
down_revision: Union[str, None] = "f9l234567890"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            DELETE FROM permission_engine_user_roles pur
            WHERE NOT EXISTS (
                SELECT 1 FROM users u WHERE u.telegram_id = pur.user_id
            )
            """
        )
    )
    op.add_column(
        "permission_engine_user_roles",
        sa.Column("user_uuid", sa.UUID(), nullable=True),
    )
    op.execute(
        sa.text(
            """
            UPDATE permission_engine_user_roles pur
            SET user_uuid = u.id
            FROM users u
            WHERE u.telegram_id = pur.user_id
            """
        )
    )
    op.drop_constraint(
        "permission_engine_user_roles_pkey",
        "permission_engine_user_roles",
        type_="primary",
    )
    op.drop_column("permission_engine_user_roles", "user_id")
    op.alter_column(
        "permission_engine_user_roles",
        "user_uuid",
        new_column_name="user_id",
        nullable=False,
    )
    op.create_primary_key(
        "permission_engine_user_roles_pkey",
        "permission_engine_user_roles",
        ["user_id", "role_id"],
    )
    op.create_foreign_key(
        "fk_permission_engine_user_roles_user_id",
        "permission_engine_user_roles",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_permission_engine_user_roles_user_id",
        "permission_engine_user_roles",
        type_="foreignkey",
    )
    op.drop_constraint(
        "permission_engine_user_roles_pkey",
        "permission_engine_user_roles",
        type_="primary",
    )
    op.add_column(
        "permission_engine_user_roles",
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=True),
    )
    op.execute(
        sa.text(
            """
            UPDATE permission_engine_user_roles pur
            SET telegram_user_id = u.telegram_id
            FROM users u
            WHERE u.id = pur.user_id
            """
        )
    )
    op.drop_column("permission_engine_user_roles", "user_id")
    op.alter_column(
        "permission_engine_user_roles",
        "telegram_user_id",
        new_column_name="user_id",
        nullable=False,
    )
    op.create_primary_key(
        "permission_engine_user_roles_pkey",
        "permission_engine_user_roles",
        ["user_id", "role_id"],
    )
