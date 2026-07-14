"""auto_client_request_fields_v1

Revision ID: f9o567890123
Revises: f9n456789012
Create Date: 2026-07-14 21:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f9o567890123"
down_revision: Union[str, None] = "f9n456789012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "lead_engine_v1_leads",
        sa.Column("client_request_type", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "lead_engine_v1_leads",
        sa.Column("client_description", sa.Text(), nullable=True),
    )
    op.add_column(
        "lead_engine_v1_leads",
        sa.Column("client_photo_file_id", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("lead_engine_v1_leads", "client_photo_file_id")
    op.drop_column("lead_engine_v1_leads", "client_description")
    op.drop_column("lead_engine_v1_leads", "client_request_type")
