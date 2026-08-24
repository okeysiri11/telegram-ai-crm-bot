# Crypto/OTC incoming transaction registry repository — Sprint 48.0.
#
# The only idempotency-relevant method here is `create()`, which relies on
# CryptoIncomingTransaction's DB-level UniqueConstraint to fail atomically
# under a concurrent duplicate insert (see database/models/crypto_tx_registry.py
# for why this is the correct mechanism vs. an application-level lock). This
# repository does not catch the resulting IntegrityError — that decision
# belongs to the service layer (services/pg_crypto_tx_antifraud_engine.py),
# which needs the transaction to still be open to look up the pre-existing
# duplicate row inside the same request.

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.crypto_tx_registry import (
    TERMINAL_CRYPTO_TX_STATUSES,
    CryptoIncomingTransaction,
    CryptoTxOverrideLink,
)


class CryptoTxRegistryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, **fields) -> CryptoIncomingTransaction:
        row = CryptoIncomingTransaction(**fields)
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_by_id(self, tx_id: uuid.UUID) -> CryptoIncomingTransaction | None:
        result = await self._session.execute(
            select(CryptoIncomingTransaction).where(CryptoIncomingTransaction.id == tx_id)
        )
        return result.scalar_one_or_none()

    async def get_by_identity(
        self, *, network: str, tx_hash: str, token: str, log_index: str = "0"
    ) -> CryptoIncomingTransaction | None:
        result = await self._session.execute(
            select(CryptoIncomingTransaction).where(
                CryptoIncomingTransaction.network == network,
                CryptoIncomingTransaction.tx_hash == tx_hash,
                CryptoIncomingTransaction.token == token,
                CryptoIncomingTransaction.log_index == log_index,
            )
        )
        return result.scalar_one_or_none()

    async def update(self, tx_id: uuid.UUID, **fields) -> CryptoIncomingTransaction | None:
        row = await self.get_by_id(tx_id)
        if row is None:
            return None
        for key, value in fields.items():
            setattr(row, key, value)
        await self._session.flush()
        return row

    async def create_override_link(self, **fields) -> CryptoTxOverrideLink:
        row = CryptoTxOverrideLink(**fields)
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_override_links(self, tx_id: uuid.UUID) -> list[CryptoTxOverrideLink]:
        result = await self._session.execute(
            select(CryptoTxOverrideLink)
            .where(CryptoTxOverrideLink.transaction_id == tx_id)
            .order_by(CryptoTxOverrideLink.created_at.asc())
        )
        return list(result.scalars().all())

    # --- Anomaly detection queries (Sprint 48.0 requirement 9) ---
    # "Same transfer linked to multiple customers" needs the customer_id on
    # each override's linked deal/payment, which lives in different tables
    # (DealEngineV1Deal.client_id / PaymentEngineV1Payment.client_id) — that
    # cross-entity lookup is done in services/pg_crypto_tx_antifraud_engine.py
    # using list_override_links() below plus the deal/payment repositories it
    # already depends on, rather than reaching across tables from here.

    async def recent_by_wallet_and_amount(
        self,
        *,
        wallet_address: str,
        amount,
        window: timedelta,
        exclude_id: uuid.UUID | None = None,
    ) -> list[CryptoIncomingTransaction]:
        """Same wallet + amount registered again within a short window —
        possible duplicate submission with slightly different tx metadata,
        or a replay attempt."""
        cutoff = datetime.now(timezone.utc) - window
        conditions = [
            CryptoIncomingTransaction.wallet_address == wallet_address,
            CryptoIncomingTransaction.amount == amount,
            CryptoIncomingTransaction.first_seen_at >= cutoff,
        ]
        if exclude_id is not None:
            conditions.append(CryptoIncomingTransaction.id != exclude_id)
        result = await self._session.execute(
            select(CryptoIncomingTransaction).where(and_(*conditions))
        )
        return list(result.scalars().all())

    async def count_payout_attempts_by_operator(
        self, *, created_by: int, window: timedelta
    ) -> int:
        """Repeated payout-registration attempts by the same operator/session
        in a short window — potential automation abuse or a stuck retry loop."""
        cutoff = datetime.now(timezone.utc) - window
        result = await self._session.execute(
            select(func.count())
            .select_from(CryptoIncomingTransaction)
            .where(
                CryptoIncomingTransaction.registered_by == created_by,
                CryptoIncomingTransaction.created_at >= cutoff,
            )
        )
        return int(result.scalar_one())

    async def list_terminal_conflicts(
        self, *, network: str, tx_hash: str, token: str
    ) -> list[CryptoIncomingTransaction]:
        """Any row for this tx_hash (any log_index) already in a terminal
        state — used to detect "same tx_hash submitted after prior
        cancellation/closure"."""
        result = await self._session.execute(
            select(CryptoIncomingTransaction).where(
                CryptoIncomingTransaction.network == network,
                CryptoIncomingTransaction.tx_hash == tx_hash,
                CryptoIncomingTransaction.token == token,
                CryptoIncomingTransaction.status.in_(tuple(TERMINAL_CRYPTO_TX_STATUSES)),
            )
        )
        return list(result.scalars().all())
