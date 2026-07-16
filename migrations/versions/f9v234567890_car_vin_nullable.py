"""Allow nullable VIN on car_engine_v1_cars

Revision ID: f9v234567890
Revises: f9u123456789
Create Date: 2026-07-16 13:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f9v234567890"
down_revision: Union[str, None] = "f9u123456789"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "car_engine_v1_cars",
        "vin",
        existing_type=sa.String(length=50),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "car_engine_v1_cars",
        "vin",
        existing_type=sa.String(length=50),
        nullable=False,
    )
