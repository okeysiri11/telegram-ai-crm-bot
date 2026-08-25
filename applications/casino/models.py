"""Casino domain dataclasses — play-money only."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CasinoVenue:
    venue_id: str
    slug: str
    name: str
    city_building_id: str
    city_route: str
    game: str = "roulette"
    status: str = "open"
    play_money_only: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "venue_id": self.venue_id,
            "slug": self.slug,
            "name": self.name,
            "city_building_id": self.city_building_id,
            "city_route": self.city_route,
            "game": self.game,
            "status": self.status,
            "play_money_only": True,
            "real_money": False,
        }


@dataclass
class PlayWallet:
    wallet_id: str
    tenant_id: str
    player_id: str
    balance_chips: int
    currency_code: str = "CHIPS"

    def to_dict(self) -> dict[str, Any]:
        from applications.casino.config import DEFAULT_CONFIG

        return {
            "wallet_id": self.wallet_id,
            "tenant_id": self.tenant_id,
            "player_id": self.player_id,
            "balance_chips": self.balance_chips,
            "currency_code": self.currency_code,
            "currency_label": DEFAULT_CONFIG.currency_label,
            "display_currency": DEFAULT_CONFIG.display_currency,
            "play_money_only": True,
            "real_money": False,
        }


@dataclass
class LedgerEntry:
    entry_id: str
    tenant_id: str
    player_id: str
    wallet_id: str
    amount_chips: int
    balance_after: int
    entry_type: str
    reference_type: str = ""
    reference_id: str = ""
    idempotency_key: str = ""
    created_ts: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        from applications.casino.config import DEFAULT_CONFIG

        amount = int(self.amount_chips)
        if self.entry_type == "wager":
            operation = "Wager"
            wager = abs(amount)
            win_loss = "loss" if amount < 0 else None
        elif self.entry_type == "payout":
            operation = "Win"
            wager = None
            win_loss = "win"
        elif self.entry_type == "demo_grant":
            operation = "Demo grant"
            wager = None
            win_loss = None
        elif self.entry_type == "opening_grant":
            operation = "Opening grant"
            wager = None
            win_loss = None
        else:
            operation = self.entry_type
            wager = abs(amount) if amount < 0 else None
            win_loss = "win" if amount > 0 else ("loss" if amount < 0 else None)
        return {
            "entry_id": self.entry_id,
            "tenant_id": self.tenant_id,
            "wallet_id": self.wallet_id,
            "amount_chips": amount,
            "balance_after": self.balance_after,
            "entry_type": self.entry_type,
            "reference_type": self.reference_type,
            "reference_id": self.reference_id,
            "idempotency_key": self.idempotency_key,
            "created_ts": self.created_ts,
            "operation": operation,
            "wager": wager,
            "win_loss": win_loss,
            "balance_delta": amount,
            "resulting_balance": self.balance_after,
            "currency_label": DEFAULT_CONFIG.currency_label,
            "display_currency": DEFAULT_CONFIG.display_currency,
            "play_money_only": True,
        }


@dataclass
class RouletteBet:
    bet_id: str
    tenant_id: str
    player_id: str
    round_id: str
    bet_type: str
    numbers: list[int] = field(default_factory=list)
    amount_chips: int = 0
    idempotency_key: str = ""
    status: str = "accepted"
    payout_chips: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "bet_id": self.bet_id,
            "round_id": self.round_id,
            "bet_type": self.bet_type,
            "numbers": list(self.numbers),
            "amount_chips": self.amount_chips,
            "status": self.status,
            "payout_chips": self.payout_chips,
            "idempotency_key": self.idempotency_key,
        }


@dataclass
class RouletteRound:
    round_id: str
    tenant_id: str
    venue_id: str
    status: str = "open"
    result_number: int | None = None
    result_color: str | None = None
    entropy_hex: str = ""
    settled: bool = False
    opened_ts: float = 0.0

    def phase(self) -> str:
        from applications.casino.config import DEFAULT_CONFIG

        if self.settled:
            return "SETTLED"
        if self.result_number is not None:
            return "RESULT"
        import time

        elapsed = max(0.0, time.time() - (self.opened_ts or 0.0))
        open_s = DEFAULT_CONFIG.betting_open_seconds
        close_s = DEFAULT_CONFIG.betting_closing_seconds
        if elapsed < open_s:
            return "BETTING_OPEN"
        if elapsed < open_s + close_s:
            return "BETTING_CLOSING"
        return "NO_MORE_BETS"

    def to_dict(self) -> dict[str, Any]:
        from applications.casino.config import DEFAULT_CONFIG

        return {
            "round_id": self.round_id,
            "tenant_id": self.tenant_id,
            "venue_id": self.venue_id,
            "status": self.status,
            "result_number": self.result_number,
            "result_color": self.result_color,
            "settled": self.settled,
            "server_authoritative": True,
            "opened_ts": self.opened_ts,
            "betting_open_seconds": DEFAULT_CONFIG.betting_open_seconds,
            "betting_closing_seconds": DEFAULT_CONFIG.betting_closing_seconds,
            "phase": self.phase(),
        }
