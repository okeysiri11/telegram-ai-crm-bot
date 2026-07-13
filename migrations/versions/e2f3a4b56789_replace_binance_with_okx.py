"""replace_binance_with_okx

Revision ID: e2f3a4b56789
Revises: d1e2f3a45678
Create Date: 2026-07-13 18:45:00.000000

"""
from __future__ import annotations

import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e2f3a4b56789"
down_revision: Union[str, None] = "d1e2f3a45678"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NEW_SOURCES: tuple[tuple[str, str, str, str | None, int], ...] = (
    ("OKX", "EXCHANGE", "OKX Spot (reference)", "https://www.okx.com", 15),
    ("NBU", "BANK", "NBU Official Rates (reference)", "https://bank.gov.ua", 50),
    ("PRIVATBANK", "BANK", "PrivatBank (reference)", "https://api.privatbank.ua", 55),
    ("MONOBANK", "BANK", "Monobank (reference)", "https://api.monobank.ua", 56),
    ("UKRSIBBANK", "REFERENCE", "Ukrsibbank (reference)", None, 60),
    ("MTB_BANK", "REFERENCE", "MTB Bank (reference)", None, 61),
    ("OSCHADBANK", "REFERENCE", "Oschadbank (reference)", None, 62),
    ("TRADINGVIEW", "REFERENCE", "TradingView Intelligence (reference)", None, 70),
)


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE market_v1_sources SET is_active = false WHERE source_code = 'BINANCE'"
        )
    )
    conn = op.get_bind()
    for source_code, source_type, name, base_url, priority in NEW_SOURCES:
        exists = conn.execute(
            sa.text("SELECT 1 FROM market_v1_sources WHERE source_code = :code"),
            {"code": source_code},
        ).first()
        if exists:
            continue
        conn.execute(
            sa.text(
                """
                INSERT INTO market_v1_sources
                (id, source_code, source_type, name, base_url, priority, is_active, failure_count, created_at, updated_at)
                VALUES (:id, :source_code, :source_type, :name, :base_url, :priority, true, 0, NOW(), NOW())
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "source_code": source_code,
                "source_type": source_type,
                "name": name,
                "base_url": base_url,
                "priority": priority,
            },
        )


def downgrade() -> None:
    op.execute(
        sa.text(
            "DELETE FROM market_v1_sources WHERE source_code IN "
            "('OKX','NBU','PRIVATBANK','MONOBANK','UKRSIBBANK','MTB_BANK','OSCHADBANK','TRADINGVIEW')"
        )
    )
    op.execute(
        sa.text(
            "UPDATE market_v1_sources SET is_active = true WHERE source_code = 'BINANCE'"
        )
    )
