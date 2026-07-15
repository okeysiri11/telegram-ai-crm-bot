"""auto_client_requests contact fields

Revision ID: f9q789012345
Revises: f9p678901234
Create Date: 2026-07-15 10:30:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f9q789012345"
down_revision: Union[str, None] = "f9p678901234"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "auto_client_requests_v1",
        sa.Column("client_phone", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "auto_client_requests_v1",
        sa.Column("source_link", sa.String(length=64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("auto_client_requests_v1", "source_link")
    op.drop_column("auto_client_requests_v1", "client_phone")
