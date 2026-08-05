"""Unified identity foundation — Sprint 34.2A.

Revision ID: g0a123456789
Revises: f9f234567890
Create Date: 2026-08-02 17:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "g0a123456789"
down_revision: Union[str, None] = "f9f234567890"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("phone", sa.String(length=32), nullable=True))
    op.add_column("users", sa.Column("display_name", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("avatar_url", sa.String(length=1024), nullable=True))
    op.add_column(
        "users",
        sa.Column("status", sa.String(length=32), server_default="active", nullable=False),
    )
    op.add_column("users", sa.Column("preferences", JSONB(), nullable=True))
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "users",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email) WHERE email IS NOT NULL"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_phone ON users (phone) WHERE phone IS NOT NULL"
    )

    op.execute(
        "UPDATE users SET display_name = full_name "
        "WHERE display_name IS NULL AND full_name IS NOT NULL"
    )

    op.create_table(
        "user_identity_links",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("external_id", sa.String(length=512), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("provider", "external_id", name="uq_user_identity_links_provider_external"),
    )
    op.create_index("ix_user_identity_links_user_id", "user_identity_links", ["user_id"])

    op.execute(
        """
        INSERT INTO user_identity_links (id, user_id, provider, external_id, verified_at, created_at)
        SELECT gen_random_uuid(), u.id, 'telegram', u.telegram_id::text, now(), now()
        FROM users u
        WHERE u.telegram_id IS NOT NULL
          AND NOT EXISTS (
            SELECT 1 FROM user_identity_links l
            WHERE l.provider = 'telegram' AND l.external_id = u.telegram_id::text
          )
        """
    )


def downgrade() -> None:
    op.drop_index("ix_user_identity_links_user_id", table_name="user_identity_links")
    op.drop_table("user_identity_links")
    op.execute("DROP INDEX IF EXISTS ix_users_phone")
    op.execute("DROP INDEX IF EXISTS ix_users_email")
    op.drop_column("users", "updated_at")
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "preferences")
    op.drop_column("users", "status")
    op.drop_column("users", "avatar_url")
    op.drop_column("users", "display_name")
    op.drop_column("users", "phone")
    op.drop_column("users", "email")
