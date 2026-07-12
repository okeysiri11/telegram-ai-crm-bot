"""market_data_uah_pairs

Revision ID: 9658b0f2b04c
Revises: a4074b1534de
Create Date: 2026-07-12 18:23:00.000000

"""
from __future__ import annotations

import json
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "9658b0f2b04c"
down_revision: Union[str, None] = "a4074b1534de"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UAH_RATE = {
    "bid": "0.024",
    "ask": "0.0242",
    "last": "0.0241",
    "volume_24h": "0",
}


def upgrade() -> None:
    bind = op.get_bind()
    row = bind.execute(
        sa.text("SELECT config FROM market_v1_sources WHERE source_code = 'FX'")
    ).first()
    if not row:
        return
    config = dict(row[0] or {})
    rates = dict(config.get("rates") or {})
    rates["UAH"] = UAH_RATE
    bind.execute(
        sa.text(
            "UPDATE market_v1_sources SET config = CAST(:config AS jsonb) "
            "WHERE source_code = 'FX'"
        ),
        {"config": json.dumps({**config, "rates": rates})},
    )


def downgrade() -> None:
    bind = op.get_bind()
    row = bind.execute(
        sa.text("SELECT config FROM market_v1_sources WHERE source_code = 'FX'")
    ).first()
    if not row or not row[0]:
        return
    config = dict(row[0])
    rates = dict(config.get("rates") or {})
    rates.pop("UAH", None)
    bind.execute(
        sa.text(
            "UPDATE market_v1_sources SET config = CAST(:config AS jsonb) "
            "WHERE source_code = 'FX'"
        ),
        {"config": json.dumps({**config, "rates": rates})},
    )
