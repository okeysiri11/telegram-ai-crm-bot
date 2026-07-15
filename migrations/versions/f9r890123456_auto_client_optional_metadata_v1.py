"""auto_client_requests optional metadata fields

Revision ID: f9r890123456
Revises: f9q789012345
Create Date: 2026-07-15 14:30:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "f9r890123456"
down_revision: Union[str, None] = "f9q789012345"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "auto_client_requests_v1",
        sa.Column("vin", sa.String(length=17), nullable=True),
    )
    op.add_column(
        "auto_client_requests_v1",
        sa.Column("brand", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "auto_client_requests_v1",
        sa.Column("model", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "auto_client_requests_v1",
        sa.Column("year", sa.Integer(), nullable=True),
    )
    op.add_column(
        "auto_client_requests_v1",
        sa.Column("mileage", sa.Integer(), nullable=True),
    )
    op.add_column(
        "auto_client_requests_v1",
        sa.Column("budget", sa.Numeric(precision=14, scale=2), nullable=True),
    )
    op.add_column(
        "auto_client_requests_v1",
        sa.Column("price", sa.Numeric(precision=14, scale=2), nullable=True),
    )
    op.add_column(
        "auto_client_requests_v1",
        sa.Column("service_type", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "auto_client_requests_v1",
        sa.Column("photo_file_ids", JSONB, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("auto_client_requests_v1", "photo_file_ids")
    op.drop_column("auto_client_requests_v1", "service_type")
    op.drop_column("auto_client_requests_v1", "price")
    op.drop_column("auto_client_requests_v1", "budget")
    op.drop_column("auto_client_requests_v1", "mileage")
    op.drop_column("auto_client_requests_v1", "year")
    op.drop_column("auto_client_requests_v1", "model")
    op.drop_column("auto_client_requests_v1", "brand")
    op.drop_column("auto_client_requests_v1", "vin")
