"""bidex_telegram_quote_parser_v1

Revision ID: f3a4b5c67890
Revises: e2f3a4b56789
Create Date: 2026-07-13 19:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f3a4b5c67890"
down_revision: Union[str, None] = "e2f3a4b56789"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "automotive_treasury_v1_rate_sheets",
        sa.Column("eurusd_buy", sa.Numeric(precision=20, scale=6), nullable=True),
    )
    op.add_column(
        "automotive_treasury_v1_rate_sheets",
        sa.Column("eurusd_sell", sa.Numeric(precision=20, scale=6), nullable=True),
    )
    op.add_column(
        "automotive_treasury_v1_rate_sheets",
        sa.Column("usdt_buy_markup_percent", sa.Numeric(precision=12, scale=6), nullable=True),
    )
    op.add_column(
        "automotive_treasury_v1_rate_sheets",
        sa.Column("usdt_sell_markup_percent", sa.Numeric(precision=12, scale=6), nullable=True),
    )
    op.add_column(
        "automotive_treasury_v1_rate_sheets",
        sa.Column("source_authority", sa.String(length=64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("automotive_treasury_v1_rate_sheets", "source_authority")
    op.drop_column("automotive_treasury_v1_rate_sheets", "usdt_sell_markup_percent")
    op.drop_column("automotive_treasury_v1_rate_sheets", "usdt_buy_markup_percent")
    op.drop_column("automotive_treasury_v1_rate_sheets", "eurusd_sell")
    op.drop_column("automotive_treasury_v1_rate_sheets", "eurusd_buy")
