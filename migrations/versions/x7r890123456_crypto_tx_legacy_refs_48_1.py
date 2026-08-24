"""Crypto/OTC typed legacy deal/payment references — Sprint 48.1.

Sprint 48.0's crypto_incoming_transactions.deal_id/payout_id are UUID FKs
into deal_engine_v1_deals/payment_engine_v1_payments — but real crypto/OTC
deals live in the legacy SQLite crypto_deals/crypto_payments tables
(integer IDs), which DealEngineV1 does not support as a vertical
(DEAL_ENGINE_V1_SUPPORTED_VERTICALS = {"auto", "agro"} only; confirmed by
reading database/models/deal_engine_v1.py during Sprint 48.1's audit). The
two ID spaces are incompatible — a legacy integer ID cannot be stored in a
UUID column, and must not be smuggled in as a string.

This migration adds explicit, separate, nullable integer columns
(legacy_deal_id, legacy_payment_id) so services/crypto_payout_orchestrator.py
can preserve the real deal/payment reference without overloading the UUID
columns, which stay reserved for a future real DealEngineV1 migration
(tracked separately — see docs/SPRINT_48_1_RESULT.md's "Remaining technical
debt"; NOT performed in this migration). No FK constraint is added for the
legacy columns — they reference a different (SQLite) database, so a
Postgres FK is not representable; referential integrity for these is the
orchestrator's responsibility (it always resolves the legacy row before
writing the reference).

Purely additive: nullable columns, no backfill, no data loss, no changes to
Sprint 48.0's existing columns.

Idempotent by column existence, not just table existence: downgrade() below
is a deliberate no-op (same non-destructive precedent as u4o567890123/
v5p678901234), which means a downgrade does NOT drop these columns — so a
downgrade-then-upgrade cycle must not crash on a duplicate ADD COLUMN.
Verified during Sprint 48.1 by actually running `alembic downgrade -1` then
`alembic upgrade head` against a real database, not just inspecting the
source (the first version of this migration did crash exactly this way;
this version fixes it).

Revision ID: x7r890123456
Revises: w6q789012345
Create Date: 2026-08-09 12:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "x7r890123456"
down_revision: Union[str, None] = "w6q789012345"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_NEW_COLUMNS = ("legacy_deal_id", "legacy_payment_id")


def _existing_columns(bind, table: str) -> set[str]:
    rows = bind.execute(
        sa.text("SELECT column_name FROM information_schema.columns WHERE table_name = :t"),
        {"t": table},
    ).fetchall()
    return {r[0] for r in rows}


def upgrade() -> None:
    bind = op.get_bind()

    if bind.execute(sa.text("SELECT to_regclass('crypto_incoming_transactions') IS NOT NULL")).scalar():
        present = _existing_columns(bind, "crypto_incoming_transactions")
        missing = [c for c in _NEW_COLUMNS if c not in present]
        if missing:
            with op.batch_alter_table("crypto_incoming_transactions") as batch:
                for col in missing:
                    batch.add_column(sa.Column(col, sa.Integer(), nullable=True))
        existing_indexes = {
            r[0]
            for r in bind.execute(
                sa.text("SELECT indexname FROM pg_indexes WHERE tablename = 'crypto_incoming_transactions'")
            ).fetchall()
        }
        if "ix_crypto_incoming_tx_legacy_deal" not in existing_indexes:
            op.create_index(
                "ix_crypto_incoming_tx_legacy_deal",
                "crypto_incoming_transactions",
                ["legacy_deal_id"],
            )
        if "ix_crypto_incoming_tx_legacy_payment" not in existing_indexes:
            op.create_index(
                "ix_crypto_incoming_tx_legacy_payment",
                "crypto_incoming_transactions",
                ["legacy_payment_id"],
            )

    if bind.execute(sa.text("SELECT to_regclass('crypto_tx_override_links') IS NOT NULL")).scalar():
        present = _existing_columns(bind, "crypto_tx_override_links")
        missing = [c for c in _NEW_COLUMNS if c not in present]
        if missing:
            with op.batch_alter_table("crypto_tx_override_links") as batch:
                for col in missing:
                    batch.add_column(sa.Column(col, sa.Integer(), nullable=True))


def downgrade() -> None:
    # Non-destructive-migration precedent (see u4o567890123, v5p678901234):
    # deliberate no-op. Dropping columns that may already hold real
    # audit-relevant references is a separate, explicit decision, not an
    # automatic consequence of a downgrade. upgrade() above is written to
    # tolerate this (idempotent by column existence) precisely because this
    # no-op means the columns survive a downgrade.
    pass
