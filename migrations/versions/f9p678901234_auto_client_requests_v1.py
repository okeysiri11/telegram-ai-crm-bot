"""auto_client_requests_v1

Revision ID: f9p678901234
Revises: f9o567890123
Create Date: 2026-07-14 22:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f9p678901234"
down_revision: Union[str, None] = "f9o567890123"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "auto_client_requests_v1",
        sa.Column("request_number", sa.String(length=32), nullable=False),
        sa.Column("request_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="NEW"),
        sa.Column("client_telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("client_username", sa.String(length=255), nullable=True),
        sa.Column("client_full_name", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("photo_file_id", sa.String(length=255), nullable=True),
        sa.Column("manager_id", sa.UUID(), nullable=True),
        sa.Column("lead_id", sa.UUID(), nullable=True),
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
        sa.ForeignKeyConstraint(["manager_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["lead_id"], ["lead_engine_v1_leads.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_auto_client_requests_v1_number",
        "auto_client_requests_v1",
        ["request_number"],
        unique=True,
    )
    op.create_index(
        "ix_auto_client_requests_v1_client",
        "auto_client_requests_v1",
        ["client_telegram_id"],
    )
    op.create_index(
        "ix_auto_client_requests_v1_manager",
        "auto_client_requests_v1",
        ["manager_id"],
    )
    op.create_index(
        "ix_auto_client_requests_v1_status",
        "auto_client_requests_v1",
        ["status"],
    )
    op.create_index(
        "ix_auto_client_requests_v1_type",
        "auto_client_requests_v1",
        ["request_type"],
    )


def downgrade() -> None:
    op.drop_index("ix_auto_client_requests_v1_type", table_name="auto_client_requests_v1")
    op.drop_index("ix_auto_client_requests_v1_status", table_name="auto_client_requests_v1")
    op.drop_index("ix_auto_client_requests_v1_manager", table_name="auto_client_requests_v1")
    op.drop_index("ix_auto_client_requests_v1_client", table_name="auto_client_requests_v1")
    op.drop_index("ix_auto_client_requests_v1_number", table_name="auto_client_requests_v1")
    op.drop_table("auto_client_requests_v1")
