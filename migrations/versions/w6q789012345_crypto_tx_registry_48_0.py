"""Crypto/OTC incoming transaction registry — Sprint 48.0 (security-critical).

Creates crypto_incoming_transactions (canonical, idempotent registry of
incoming crypto transfers — see database/models/crypto_tx_registry.py for
the full rationale) and crypto_tx_override_links (append-only override
audit relation). The UniqueConstraint on
(network, tx_hash, token, log_index) is the atomic, DB-enforced idempotency
mechanism required by docs/SPRINT_48_0_RESULT.md.

Revision ID: w6q789012345
Revises: v5p678901234
Create Date: 2026-08-09 00:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "w6q789012345"
down_revision: Union[str, None] = "v5p678901234"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ts_cols():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("change_id", sa.String(length=64), nullable=True),
        sa.Column("source_client", sa.String(length=32), nullable=True),
        sa.Column("workspace_id", sa.String(length=128), nullable=True),
        sa.Column("created_by", sa.String(length=128), nullable=True),
        sa.Column("updated_by", sa.String(length=128), nullable=True),
        sa.Column("metadata_json", JSONB(), nullable=True),
    ]


def upgrade() -> None:
    op.create_table(
        "crypto_incoming_transactions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("network", sa.String(32), nullable=False),
        sa.Column("tx_hash", sa.String(128), nullable=False),
        sa.Column("token", sa.String(32), nullable=False),
        sa.Column("log_index", sa.String(16), nullable=False, server_default="0"),
        sa.Column("wallet_address", sa.String(128), nullable=False),
        sa.Column("amount", sa.Numeric(38, 18), nullable=False),
        sa.Column(
            "deal_id", UUID(as_uuid=True),
            sa.ForeignKey("deal_engine_v1_deals.id", ondelete="SET NULL"), nullable=True,
        ),
        sa.Column(
            "payout_id", UUID(as_uuid=True),
            sa.ForeignKey("payment_engine_v1_payments.id", ondelete="SET NULL"), nullable=True,
        ),
        sa.Column("customer_id", sa.BigInteger(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        # Named registered_by, not created_by — VersionColumnsMixin (via
        # _ts_cols() below) already owns a generic, free-text created_by
        # column; this one is the actual telegram-id operator identity.
        sa.Column("registered_by", sa.BigInteger(), nullable=False),
        sa.Column("approved_by", sa.BigInteger(), nullable=True),
        sa.Column(
            "tenant_id", UUID(as_uuid=True),
            sa.ForeignKey("partner_tenant_engine_v1_tenants.id", ondelete="SET NULL"), nullable=True,
        ),
        sa.Column("vertical", sa.String(64), nullable=False, server_default="crypto_otc"),
        sa.Column("notes", sa.Text(), nullable=True),
        *_ts_cols(),
        sa.UniqueConstraint(
            "network", "tx_hash", "token", "log_index",
            name="uq_crypto_incoming_tx_identity",
        ),
    )
    op.create_index("ix_crypto_incoming_tx_status", "crypto_incoming_transactions", ["status"])
    op.create_index("ix_crypto_incoming_tx_wallet", "crypto_incoming_transactions", ["wallet_address"])
    op.create_index("ix_crypto_incoming_tx_deal", "crypto_incoming_transactions", ["deal_id"])
    op.create_index("ix_crypto_incoming_tx_payout", "crypto_incoming_transactions", ["payout_id"])
    op.create_index("ix_crypto_incoming_tx_customer", "crypto_incoming_transactions", ["customer_id"])
    op.create_index("ix_crypto_incoming_tx_tenant", "crypto_incoming_transactions", ["tenant_id"])
    op.create_index("ix_crypto_incoming_tx_registered_by", "crypto_incoming_transactions", ["registered_by"])
    op.create_index(
        "ix_crypto_incoming_tx_wallet_amount_time",
        "crypto_incoming_transactions",
        ["wallet_address", "amount", "first_seen_at"],
    )

    op.create_table(
        "crypto_tx_override_links",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "transaction_id", UUID(as_uuid=True),
            sa.ForeignKey("crypto_incoming_transactions.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "deal_id", UUID(as_uuid=True),
            sa.ForeignKey("deal_engine_v1_deals.id", ondelete="SET NULL"), nullable=True,
        ),
        sa.Column(
            "payout_id", UUID(as_uuid=True),
            sa.ForeignKey("payment_engine_v1_payments.id", ondelete="SET NULL"), nullable=True,
        ),
        sa.Column("approved_by", sa.BigInteger(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        *_ts_cols(),
    )
    op.create_index("ix_crypto_tx_override_links_tx", "crypto_tx_override_links", ["transaction_id"])
    op.create_index("ix_crypto_tx_override_links_deal", "crypto_tx_override_links", ["deal_id"])
    op.create_index("ix_crypto_tx_override_links_approved_by", "crypto_tx_override_links", ["approved_by"])


def downgrade() -> None:
    # Non-destructive by policy in this repo (see u4o567890123's downgrade) —
    # do not drop a security-critical audit/idempotency table on rollback.
    pass
