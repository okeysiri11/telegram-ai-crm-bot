"""Casino play-money foundation (Sprint 15).

Revision ID: t9p012345678
Revises: s8n901234567
Create Date: 2026-08-25 14:10:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "t9p012345678"
down_revision: Union[str, None] = "s8n901234567"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ts_cols():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    ]


def upgrade() -> None:
    conn = op.get_bind()

    def _exists(name: str) -> bool:
        return conn.exec_driver_sql(f"SELECT to_regclass('public.{name}')").scalar() is not None

    if not _exists("casino_venues"):
        op.create_table(
            "casino_venues",
            sa.Column("venue_id", sa.String(64), primary_key=True),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("slug", sa.String(64), nullable=False),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("city_building_id", sa.String(64), nullable=False, server_default="casino"),
            sa.Column("city_route", sa.String(255), nullable=False),
            sa.Column("game", sa.String(64), nullable=False, server_default="roulette"),
            sa.Column("status", sa.String(32), nullable=False, server_default="open"),
            sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            *_ts_cols(),
        )
        op.create_index("ix_casino_venues_tenant", "casino_venues", ["tenant_id"])
        op.create_index("uq_casino_venues_tenant_slug", "casino_venues", ["tenant_id", "slug"], unique=True)

    if not _exists("casino_wallets"):
        op.create_table(
            "casino_wallets",
            sa.Column("wallet_id", sa.String(64), primary_key=True),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("player_id", sa.String(64), nullable=False),
            sa.Column("balance_chips", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("currency_code", sa.String(16), nullable=False, server_default="CHIPS"),
            *_ts_cols(),
        )
        op.create_index("ix_casino_wallets_tenant", "casino_wallets", ["tenant_id"])
        op.create_index("uq_casino_wallets_tenant_player", "casino_wallets", ["tenant_id", "player_id"], unique=True)

    if not _exists("casino_ledger"):
        op.create_table(
            "casino_ledger",
            sa.Column("entry_id", sa.String(64), primary_key=True),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("player_id", sa.String(64), nullable=False),
            sa.Column("wallet_id", sa.String(64), nullable=False),
            sa.Column("amount_chips", sa.Integer(), nullable=False),
            sa.Column("balance_after", sa.Integer(), nullable=False),
            sa.Column("entry_type", sa.String(64), nullable=False),
            sa.Column("reference_type", sa.String(64), nullable=False, server_default=""),
            sa.Column("reference_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("idempotency_key", sa.String(128), nullable=False),
            sa.Column("created_ts", sa.Float(), nullable=False, server_default="0"),
            sa.Column("note", sa.Text(), nullable=False, server_default=""),
            *_ts_cols(),
        )
        op.create_index("ix_casino_ledger_tenant_player", "casino_ledger", ["tenant_id", "player_id"])
        op.create_index(
            "ix_casino_ledger_reference",
            "casino_ledger",
            ["tenant_id", "reference_type", "reference_id"],
        )
        op.create_index(
            "uq_casino_ledger_tenant_idempotency",
            "casino_ledger",
            ["tenant_id", "idempotency_key"],
            unique=True,
        )

    if not _exists("casino_roulette_rounds"):
        op.create_table(
            "casino_roulette_rounds",
            sa.Column("round_id", sa.String(64), primary_key=True),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("venue_id", sa.String(64), nullable=False),
            sa.Column("status", sa.String(32), nullable=False, server_default="open"),
            sa.Column("result_number", sa.Integer(), nullable=True),
            sa.Column("result_color", sa.String(16), nullable=True),
            sa.Column("entropy_hex", sa.String(64), nullable=False, server_default=""),
            sa.Column("settled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            *_ts_cols(),
        )
        op.create_index("ix_casino_rounds_tenant_venue", "casino_roulette_rounds", ["tenant_id", "venue_id"])

    if not _exists("casino_roulette_bets"):
        op.create_table(
            "casino_roulette_bets",
            sa.Column("bet_id", sa.String(64), primary_key=True),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("player_id", sa.String(64), nullable=False),
            sa.Column("round_id", sa.String(64), nullable=False),
            sa.Column("bet_type", sa.String(32), nullable=False),
            sa.Column("numbers", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
            sa.Column("amount_chips", sa.Integer(), nullable=False),
            sa.Column("idempotency_key", sa.String(128), nullable=False),
            sa.Column("status", sa.String(32), nullable=False, server_default="accepted"),
            sa.Column("payout_chips", sa.Integer(), nullable=False, server_default="0"),
            *_ts_cols(),
        )
        op.create_index("ix_casino_bets_round", "casino_roulette_bets", ["tenant_id", "round_id"])
        op.create_index(
            "uq_casino_bets_tenant_idempotency",
            "casino_roulette_bets",
            ["tenant_id", "idempotency_key"],
            unique=True,
        )


def downgrade() -> None:
    for name in (
        "casino_roulette_bets",
        "casino_roulette_rounds",
        "casino_ledger",
        "casino_wallets",
        "casino_venues",
    ):
        op.drop_table(name)
