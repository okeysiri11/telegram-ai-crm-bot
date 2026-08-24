# Crypto/OTC Incoming Transaction Registry — Sprint 48.0 (security-critical).
#
# Canonical, DB-enforced idempotency for incoming crypto transfers used to
# justify a payout/deal. The UniqueConstraint on
# (network, tx_hash, token, log_index) IS the atomic reservation mechanism:
# Postgres itself serializes concurrent INSERTs against a unique index, so
# two operators racing to register the same on-chain transfer cannot both
# succeed — the loser gets an IntegrityError, which
# repositories/crypto_tx_registry_repository.py translates into "duplicate
# detected". This is deliberately not an application-level lock (locks can be
# bypassed by a second process/pod; a DB unique constraint cannot).
#
# crypto_tx_override_links is append-only and NEVER referenced for the
# original crypto_incoming_transactions.deal_id/payout_id — those columns are
# set once, on first registration/reservation, and never overwritten. An
# approved duplicate override creates an additional row here instead,
# preserving the original linkage per Sprint 48.0's spec: "Never overwrite
# the original linkage to the first deal."

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, VersionMixin


class CryptoTxStatus(str, enum.Enum):
    PENDING = "PENDING"  # registered, not yet claimed by a deal/payout
    RESERVED = "RESERVED"  # claimed for a specific deal/payout, payout not yet completed
    COMPLETED = "COMPLETED"  # payout completed against this transaction
    CANCELLED = "CANCELLED"  # explicitly cancelled/closed, must not be reused silently


TERMINAL_CRYPTO_TX_STATUSES = frozenset(
    {CryptoTxStatus.COMPLETED.value, CryptoTxStatus.CANCELLED.value}
)


class CryptoIncomingTransaction(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    """One row per unique on-chain incoming transfer. The unique constraint
    below is the idempotency guarantee — do not add a code path that deletes
    and re-inserts a row with the same identity; use status transitions."""

    __tablename__ = "crypto_incoming_transactions"
    __table_args__ = (
        UniqueConstraint(
            "network",
            "tx_hash",
            "token",
            "log_index",
            name="uq_crypto_incoming_tx_identity",
        ),
        Index("ix_crypto_incoming_tx_status", "status"),
        Index("ix_crypto_incoming_tx_wallet", "wallet_address"),
        Index("ix_crypto_incoming_tx_deal", "deal_id"),
        Index("ix_crypto_incoming_tx_payout", "payout_id"),
        Index("ix_crypto_incoming_tx_customer", "customer_id"),
        Index("ix_crypto_incoming_tx_tenant", "tenant_id"),
        Index("ix_crypto_incoming_tx_registered_by", "registered_by"),
        Index(
            "ix_crypto_incoming_tx_wallet_amount_time",
            "wallet_address",
            "amount",
            "first_seen_at",
        ),
        Index("ix_crypto_incoming_tx_legacy_deal", "legacy_deal_id"),
        Index("ix_crypto_incoming_tx_legacy_payment", "legacy_payment_id"),
    )

    # Canonical transaction identity (Sprint 48.0 spec, section "Canonical
    # transaction identity"). log_index defaults to "0" (not NULL) so the
    # unique constraint behaves consistently for chains/transfers where a
    # per-log index isn't meaningful — NULL is not distinct-safe across all
    # Postgres versions/config in a multi-column unique constraint.
    network: Mapped[str] = mapped_column(String(32), nullable=False)
    tx_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    token: Mapped[str] = mapped_column(String(32), nullable=False)
    log_index: Mapped[str] = mapped_column(String(16), nullable=False, default="0")

    wallet_address: Mapped[str] = mapped_column(String(128), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)

    deal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deal_engine_v1_deals.id", ondelete="SET NULL"),
        nullable=True,
    )
    payout_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payment_engine_v1_payments.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Telegram id — matches how customers/operators are identified bot-side
    # and in audit_engine_logs.user_id (BigInteger), not the UUID users.id
    # space used by DealEngineV1Deal.client_id.
    customer_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=CryptoTxStatus.PENDING.value
    )

    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    # Named registered_by (not created_by) to avoid colliding with
    # VersionColumnsMixin's generic, free-text created_by/updated_by
    # tracking columns (str, not the actual telegram-id operator identity
    # this domain needs for RBAC/audit). The service layer's public API
    # still uses "created_by" as the parameter name to match the Sprint
    # 48.0 spec's literal wording.
    registered_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    approved_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # Sprint 47.0 Decision 5 / Sprint 47.1 scope model — additive, optional.
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_tenant_engine_v1_tenants.id", ondelete="SET NULL"),
        nullable=True,
    )
    vertical: Mapped[str] = mapped_column(String(64), nullable=False, default="crypto_otc")

    # Sprint 48.1 — typed reference to the *real* crypto/OTC deal/payment,
    # which lives in legacy SQLite (database_legacy.py's crypto_deals/
    # crypto_payments, integer PKs) — a different ID space than deal_id/
    # payout_id above (UUID FKs into DealEngineV1/PaymentEngineV1, which do
    # not support the "crypto" vertical today; DEAL_ENGINE_V1_SUPPORTED_
    # VERTICALS = {"auto", "agro"} only — confirmed by reading
    # database/models/deal_engine_v1.py). Never overloaded into deal_id/
    # payout_id — see this sprint's migration docstring for why. No FK: the
    # referenced row lives in a different (SQLite) database; the
    # orchestrator (services/crypto_payout_orchestrator.py) is responsible
    # for resolving/validating it before writing the reference here, and
    # for never overwriting it once set (same rule as deal_id/payout_id).
    legacy_deal_id: Mapped[int | None] = mapped_column(nullable=True)
    legacy_payment_id: Mapped[int | None] = mapped_column(nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<CryptoIncomingTransaction id={self.id} network={self.network} "
            f"tx_hash={self.tx_hash[:12]}... status={self.status}>"
        )


class CryptoTxOverrideLink(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    """Append-only. One row per approved duplicate override. Never mutates
    CryptoIncomingTransaction.deal_id/payout_id — this table is the only
    place a second deal/payout gets associated with an already-used
    transaction, and every row here is a permanent, auditable fact."""

    __tablename__ = "crypto_tx_override_links"
    __table_args__ = (
        Index("ix_crypto_tx_override_links_tx", "transaction_id"),
        Index("ix_crypto_tx_override_links_deal", "deal_id"),
        Index("ix_crypto_tx_override_links_approved_by", "approved_by"),
    )

    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("crypto_incoming_transactions.id", ondelete="CASCADE"),
        nullable=False,
    )
    deal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deal_engine_v1_deals.id", ondelete="SET NULL"),
        nullable=True,
    )
    payout_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payment_engine_v1_payments.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Sprint 48.1 — same legacy-reference rationale as CryptoIncomingTransaction
    # above. Overrides are disabled in production this sprint (no real
    # step-up auth — see services/pg_crypto_tx_antifraud_engine.py), but the
    # columns exist so the model is ready the moment override is re-enabled.
    legacy_deal_id: Mapped[int | None] = mapped_column(nullable=True)
    legacy_payment_id: Mapped[int | None] = mapped_column(nullable=True)
    approved_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    def __repr__(self) -> str:
        return f"<CryptoTxOverrideLink id={self.id} transaction_id={self.transaction_id}>"
