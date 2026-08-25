"""Casino persistence — Postgres is production SoT; memory is test-only."""

from __future__ import annotations

import os
import time
import uuid
from typing import Any

from applications.casino.config import DEFAULT_CONFIG
from applications.casino.exceptions import DuplicateSettlementError, InsufficientChipsError, NotFoundError, ValidationError
from applications.casino.models import CasinoVenue, LedgerEntry, PlayWallet, RouletteBet, RouletteRound
from applications.casino.tenant import current_casino_tenant

_MEMORY_MODES = frozenset({"memory", "mem", "in_memory", "in-memory"})


def casino_persistence_mode() -> str:
    raw = os.environ.get("CASINO_PERSISTENCE", "").strip().lower()
    if raw in _MEMORY_MODES:
        return "memory"
    return "postgres"


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


ODESSA_PRIME = CasinoVenue(
    venue_id=DEFAULT_CONFIG.default_venue_id,
    slug=DEFAULT_CONFIG.default_venue_id,
    name="Odessa Prime Casino",
    city_building_id=DEFAULT_CONFIG.city_building_id,
    city_route=f"/casino/venues/{DEFAULT_CONFIG.default_venue_id}",
    game="roulette",
    status="open",
    play_money_only=True,
)


class MemoryCasinoStore:
    def __init__(self) -> None:
        self.wallets: dict[tuple[str, str], PlayWallet] = {}
        self.ledger: list[LedgerEntry] = []
        self.rounds: dict[str, RouletteRound] = {}
        self.bets: dict[str, RouletteBet] = {}
        self._ledger_keys: set[tuple[str, str]] = set()
        self._bet_keys: set[tuple[str, str]] = set()

    def reset(self) -> None:
        self.__init__()

    def venues(self) -> list[CasinoVenue]:
        return [ODESSA_PRIME]

    def get_venue(self, venue_id: str) -> CasinoVenue:
        if venue_id in {ODESSA_PRIME.venue_id, ODESSA_PRIME.slug}:
            return ODESSA_PRIME
        raise NotFoundError(f"venue not found: {venue_id}")

    def get_or_create_wallet(self, player_id: str) -> PlayWallet:
        tenant = current_casino_tenant()
        key = (tenant, player_id)
        existing = self.wallets.get(key)
        if existing:
            return existing
        wallet = PlayWallet(
            wallet_id=_new_id("wal"),
            tenant_id=tenant,
            player_id=player_id,
            balance_chips=0,
        )
        self.wallets[key] = wallet
        self._append_ledger(
            wallet,
            amount=DEFAULT_CONFIG.opening_chips,
            entry_type="opening_grant",
            reference_type="wallet",
            reference_id=wallet.wallet_id,
            idempotency_key=f"open:{tenant}:{player_id}",
        )
        return wallet

    def _append_ledger(
        self,
        wallet: PlayWallet,
        *,
        amount: int,
        entry_type: str,
        reference_type: str,
        reference_id: str,
        idempotency_key: str,
    ) -> LedgerEntry:
        tenant = wallet.tenant_id
        key = (tenant, idempotency_key)
        if key in self._ledger_keys:
            for row in self.ledger:
                if row.tenant_id == tenant and row.idempotency_key == idempotency_key:
                    return row
        nxt = wallet.balance_chips + amount
        if nxt < 0:
            raise InsufficientChipsError("insufficient play chips")
        wallet.balance_chips = nxt
        entry = LedgerEntry(
            entry_id=_new_id("led"),
            tenant_id=tenant,
            player_id=wallet.player_id,
            wallet_id=wallet.wallet_id,
            amount_chips=amount,
            balance_after=nxt,
            entry_type=entry_type,
            reference_type=reference_type,
            reference_id=reference_id,
            idempotency_key=idempotency_key,
            created_ts=time.time(),
        )
        self._ledger_keys.add(key)
        self.ledger.append(entry)
        return entry

    def list_ledger(self, player_id: str, *, limit: int = 50) -> list[LedgerEntry]:
        tenant = current_casino_tenant()
        rows = [e for e in self.ledger if e.tenant_id == tenant and e.player_id == player_id]
        return list(reversed(rows[-limit:]))

    def debit(self, player_id: str, amount: int, *, entry_type: str, reference_id: str, idempotency_key: str) -> PlayWallet:
        if amount <= 0:
            raise ValidationError("debit amount must be positive")
        wallet = self.get_or_create_wallet(player_id)
        self._append_ledger(
            wallet,
            amount=-amount,
            entry_type=entry_type,
            reference_type="roulette",
            reference_id=reference_id,
            idempotency_key=idempotency_key,
        )
        return wallet

    def credit(self, player_id: str, amount: int, *, entry_type: str, reference_id: str, idempotency_key: str) -> PlayWallet:
        if amount < 0:
            raise ValidationError("credit amount must be non-negative")
        wallet = self.get_or_create_wallet(player_id)
        if amount == 0:
            return wallet
        self._append_ledger(
            wallet,
            amount=amount,
            entry_type=entry_type,
            reference_type="roulette",
            reference_id=reference_id,
            idempotency_key=idempotency_key,
        )
        return wallet

    def open_round(self, venue_id: str) -> RouletteRound:
        self.get_venue(venue_id)
        rnd = RouletteRound(
            round_id=_new_id("rnd"),
            tenant_id=current_casino_tenant(),
            venue_id=venue_id,
            status="open",
        )
        self.rounds[rnd.round_id] = rnd
        return rnd

    def get_round(self, round_id: str) -> RouletteRound:
        rnd = self.rounds.get(round_id)
        if not rnd or rnd.tenant_id != current_casino_tenant():
            raise NotFoundError(f"round not found: {round_id}")
        return rnd

    def place_bet(self, bet: RouletteBet) -> RouletteBet:
        key = (bet.tenant_id, bet.idempotency_key)
        if key in self._bet_keys:
            for existing in self.bets.values():
                if existing.tenant_id == bet.tenant_id and existing.idempotency_key == bet.idempotency_key:
                    return existing
        self._bet_keys.add(key)
        self.bets[bet.bet_id] = bet
        return bet

    def bets_for_round(self, round_id: str) -> list[RouletteBet]:
        tenant = current_casino_tenant()
        return [b for b in self.bets.values() if b.round_id == round_id and b.tenant_id == tenant]

    def mark_settled(self, rnd: RouletteRound) -> bool:
        if rnd.settled:
            return False
        rnd.settled = True
        rnd.status = "settled"
        return True


_MEMORY = MemoryCasinoStore()


def memory_store() -> MemoryCasinoStore:
    return _MEMORY


def reset_casino_store() -> None:
    _MEMORY.reset()


class PostgresCasinoStore:
    """Thin async adapter used by the engine when CASINO_PERSISTENCE=postgres."""

    async def ensure_seed_venue(self) -> None:
        from sqlalchemy import select

        from database.models.casino import CasinoVenueRow
        from database.session import get_session

        tenant = current_casino_tenant()
        async with get_session() as session:
            existing = await session.scalar(
                select(CasinoVenueRow).where(
                    CasinoVenueRow.tenant_id == tenant,
                    CasinoVenueRow.venue_id == ODESSA_PRIME.venue_id,
                )
            )
            if existing:
                return
            session.add(
                CasinoVenueRow(
                    venue_id=ODESSA_PRIME.venue_id,
                    tenant_id=tenant,
                    slug=ODESSA_PRIME.slug,
                    name=ODESSA_PRIME.name,
                    city_building_id=ODESSA_PRIME.city_building_id,
                    city_route=ODESSA_PRIME.city_route,
                    game="roulette",
                    status="open",
                    payload={"play_money_only": True},
                )
            )

    async def venues(self) -> list[CasinoVenue]:
        from sqlalchemy import select

        from database.models.casino import CasinoVenueRow
        from database.session import get_session

        await self.ensure_seed_venue()
        tenant = current_casino_tenant()
        async with get_session() as session:
            rows = list(
                (
                    await session.scalars(select(CasinoVenueRow).where(CasinoVenueRow.tenant_id == tenant))
                ).all()
            )
        if not rows:
            return [ODESSA_PRIME]
        return [
            CasinoVenue(
                venue_id=r.venue_id,
                slug=r.slug,
                name=r.name,
                city_building_id=r.city_building_id,
                city_route=r.city_route,
                game=r.game,
                status=r.status,
            )
            for r in rows
        ]

    async def get_venue(self, venue_id: str) -> CasinoVenue:
        for venue in await self.venues():
            if venue.venue_id == venue_id or venue.slug == venue_id:
                return venue
        raise NotFoundError(f"venue not found: {venue_id}")

    async def get_or_create_wallet(self, player_id: str) -> PlayWallet:
        from sqlalchemy import select

        from database.models.casino import CasinoLedgerRow, CasinoWalletRow
        from database.session import get_session

        tenant = current_casino_tenant()
        async with get_session() as session:
            row = await session.scalar(
                select(CasinoWalletRow).where(
                    CasinoWalletRow.tenant_id == tenant,
                    CasinoWalletRow.player_id == player_id,
                )
            )
            if row:
                return PlayWallet(
                    wallet_id=row.wallet_id,
                    tenant_id=row.tenant_id,
                    player_id=row.player_id,
                    balance_chips=int(row.balance_chips),
                    currency_code=row.currency_code,
                )
            wallet_id = _new_id("wal")
            session.add(
                CasinoWalletRow(
                    wallet_id=wallet_id,
                    tenant_id=tenant,
                    player_id=player_id,
                    balance_chips=DEFAULT_CONFIG.opening_chips,
                    currency_code=DEFAULT_CONFIG.currency_code,
                )
            )
            session.add(
                CasinoLedgerRow(
                    entry_id=_new_id("led"),
                    tenant_id=tenant,
                    player_id=player_id,
                    wallet_id=wallet_id,
                    amount_chips=DEFAULT_CONFIG.opening_chips,
                    balance_after=DEFAULT_CONFIG.opening_chips,
                    entry_type="opening_grant",
                    reference_type="wallet",
                    reference_id=wallet_id,
                    idempotency_key=f"open:{tenant}:{player_id}",
                    created_ts=time.time(),
                )
            )
        return PlayWallet(
            wallet_id=wallet_id,
            tenant_id=tenant,
            player_id=player_id,
            balance_chips=DEFAULT_CONFIG.opening_chips,
        )

    async def list_ledger(self, player_id: str, *, limit: int = 50) -> list[LedgerEntry]:
        from sqlalchemy import select

        from database.models.casino import CasinoLedgerRow
        from database.session import get_session

        tenant = current_casino_tenant()
        async with get_session() as session:
            rows = list(
                (
                    await session.scalars(
                        select(CasinoLedgerRow)
                        .where(
                            CasinoLedgerRow.tenant_id == tenant,
                            CasinoLedgerRow.player_id == player_id,
                        )
                        .order_by(CasinoLedgerRow.created_ts.desc())
                        .limit(limit)
                    )
                ).all()
            )
        return [
            LedgerEntry(
                entry_id=r.entry_id,
                tenant_id=r.tenant_id,
                player_id=r.player_id,
                wallet_id=r.wallet_id,
                amount_chips=int(r.amount_chips),
                balance_after=int(r.balance_after),
                entry_type=r.entry_type,
                reference_type=r.reference_type,
                reference_id=r.reference_id,
                idempotency_key=r.idempotency_key,
                created_ts=float(r.created_ts or 0),
            )
            for r in rows
        ]

    async def apply_delta(
        self,
        player_id: str,
        amount: int,
        *,
        entry_type: str,
        reference_id: str,
        idempotency_key: str,
    ) -> PlayWallet:
        from sqlalchemy import select
        from sqlalchemy.exc import IntegrityError

        from database.models.casino import CasinoLedgerRow, CasinoWalletRow
        from database.session import get_session

        wallet = await self.get_or_create_wallet(player_id)
        tenant = current_casino_tenant()
        try:
            async with get_session() as session:
                row = await session.scalar(
                    select(CasinoWalletRow).where(CasinoWalletRow.wallet_id == wallet.wallet_id)
                )
                if row is None:
                    raise NotFoundError("wallet missing")
                nxt = int(row.balance_chips) + amount
                if nxt < 0:
                    raise InsufficientChipsError("insufficient play chips")
                existing = await session.scalar(
                    select(CasinoLedgerRow).where(
                        CasinoLedgerRow.tenant_id == tenant,
                        CasinoLedgerRow.idempotency_key == idempotency_key,
                    )
                )
                if existing:
                    return PlayWallet(
                        wallet_id=row.wallet_id,
                        tenant_id=row.tenant_id,
                        player_id=row.player_id,
                        balance_chips=int(row.balance_chips),
                        currency_code=row.currency_code,
                    )
                row.balance_chips = nxt
                session.add(
                    CasinoLedgerRow(
                        entry_id=_new_id("led"),
                        tenant_id=tenant,
                        player_id=player_id,
                        wallet_id=row.wallet_id,
                        amount_chips=amount,
                        balance_after=nxt,
                        entry_type=entry_type,
                        reference_type="roulette",
                        reference_id=reference_id,
                        idempotency_key=idempotency_key,
                        created_ts=time.time(),
                    )
                )
                return PlayWallet(
                    wallet_id=row.wallet_id,
                    tenant_id=row.tenant_id,
                    player_id=row.player_id,
                    balance_chips=nxt,
                    currency_code=row.currency_code,
                )
        except IntegrityError as exc:
            raise DuplicateSettlementError("duplicate ledger entry") from exc

    async def open_round(self, venue_id: str) -> RouletteRound:
        from database.models.casino import CasinoRouletteRoundRow
        from database.session import get_session

        await self.get_venue(venue_id)
        rnd = RouletteRound(
            round_id=_new_id("rnd"),
            tenant_id=current_casino_tenant(),
            venue_id=venue_id,
            status="open",
        )
        async with get_session() as session:
            session.add(
                CasinoRouletteRoundRow(
                    round_id=rnd.round_id,
                    tenant_id=rnd.tenant_id,
                    venue_id=rnd.venue_id,
                    status="open",
                    entropy_hex="",
                    settled=False,
                    payload={},
                )
            )
        return rnd

    async def get_round(self, round_id: str) -> RouletteRound:
        from sqlalchemy import select

        from database.models.casino import CasinoRouletteRoundRow
        from database.session import get_session

        tenant = current_casino_tenant()
        async with get_session() as session:
            row = await session.scalar(
                select(CasinoRouletteRoundRow).where(
                    CasinoRouletteRoundRow.round_id == round_id,
                    CasinoRouletteRoundRow.tenant_id == tenant,
                )
            )
        if not row:
            raise NotFoundError(f"round not found: {round_id}")
        return RouletteRound(
            round_id=row.round_id,
            tenant_id=row.tenant_id,
            venue_id=row.venue_id,
            status=row.status,
            result_number=row.result_number,
            result_color=row.result_color,
            entropy_hex=row.entropy_hex,
            settled=bool(row.settled),
        )

    async def save_round(self, rnd: RouletteRound) -> None:
        from sqlalchemy import select

        from database.models.casino import CasinoRouletteRoundRow
        from database.session import get_session

        async with get_session() as session:
            row = await session.scalar(
                select(CasinoRouletteRoundRow).where(CasinoRouletteRoundRow.round_id == rnd.round_id)
            )
            if row is None:
                raise NotFoundError(f"round not found: {rnd.round_id}")
            row.status = rnd.status
            row.result_number = rnd.result_number
            row.result_color = rnd.result_color
            row.entropy_hex = rnd.entropy_hex
            row.settled = rnd.settled

    async def place_bet(self, bet: RouletteBet) -> RouletteBet:
        from sqlalchemy import select
        from sqlalchemy.exc import IntegrityError

        from database.models.casino import CasinoRouletteBetRow
        from database.session import get_session

        try:
            async with get_session() as session:
                existing = await session.scalar(
                    select(CasinoRouletteBetRow).where(
                        CasinoRouletteBetRow.tenant_id == bet.tenant_id,
                        CasinoRouletteBetRow.idempotency_key == bet.idempotency_key,
                    )
                )
                if existing:
                    return RouletteBet(
                        bet_id=existing.bet_id,
                        tenant_id=existing.tenant_id,
                        player_id=existing.player_id,
                        round_id=existing.round_id,
                        bet_type=existing.bet_type,
                        numbers=list(existing.numbers or []),
                        amount_chips=int(existing.amount_chips),
                        idempotency_key=existing.idempotency_key,
                        status=existing.status,
                        payout_chips=int(existing.payout_chips),
                    )
                session.add(
                    CasinoRouletteBetRow(
                        bet_id=bet.bet_id,
                        tenant_id=bet.tenant_id,
                        player_id=bet.player_id,
                        round_id=bet.round_id,
                        bet_type=bet.bet_type,
                        numbers=list(bet.numbers),
                        amount_chips=bet.amount_chips,
                        idempotency_key=bet.idempotency_key,
                        status=bet.status,
                        payout_chips=bet.payout_chips,
                    )
                )
            return bet
        except IntegrityError:
            return await self.place_bet(bet)

    async def bets_for_round(self, round_id: str) -> list[RouletteBet]:
        from sqlalchemy import select

        from database.models.casino import CasinoRouletteBetRow
        from database.session import get_session

        tenant = current_casino_tenant()
        async with get_session() as session:
            rows = list(
                (
                    await session.scalars(
                        select(CasinoRouletteBetRow).where(
                            CasinoRouletteBetRow.tenant_id == tenant,
                            CasinoRouletteBetRow.round_id == round_id,
                        )
                    )
                ).all()
            )
        return [
            RouletteBet(
                bet_id=r.bet_id,
                tenant_id=r.tenant_id,
                player_id=r.player_id,
                round_id=r.round_id,
                bet_type=r.bet_type,
                numbers=list(r.numbers or []),
                amount_chips=int(r.amount_chips),
                idempotency_key=r.idempotency_key,
                status=r.status,
                payout_chips=int(r.payout_chips),
            )
            for r in rows
        ]

    async def save_bet(self, bet: RouletteBet) -> None:
        from sqlalchemy import select

        from database.models.casino import CasinoRouletteBetRow
        from database.session import get_session

        async with get_session() as session:
            row = await session.scalar(
                select(CasinoRouletteBetRow).where(CasinoRouletteBetRow.bet_id == bet.bet_id)
            )
            if row is None:
                return
            row.status = bet.status
            row.payout_chips = bet.payout_chips
