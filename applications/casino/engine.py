"""Casino engine — play-money lobby, wallet, ledger, roulette, rooms."""

from __future__ import annotations

import time
import uuid
from typing import Any

from applications.casino.config import DEFAULT_CONFIG, CasinoConfig
from applications.casino.exceptions import NotFoundError, RateLimitError, ValidationError
from applications.casino.models import RouletteBet
from applications.casino.persistence import (
    PostgresCasinoStore,
    casino_persistence_mode,
    memory_store,
    reset_casino_store,
)
from applications.casino.roulette import resolve_bet_numbers, settle_bet, spin_european
from applications.casino import multiplayer
from applications.casino.tables import FLOOR_AREAS, get_table, live_room_id
from applications.casino.tenant import current_casino_tenant


class CasinoEngine:
    def __init__(self, *, config: CasinoConfig | None = None) -> None:
        self.config = config or DEFAULT_CONFIG
        self._pg = PostgresCasinoStore()

    def reset(self) -> None:
        reset_casino_store()
        multiplayer.reset_rooms()

    def _memory(self):
        return memory_store()

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "application": self.config.application_name,
            "application_version": self.config.application_version,
            "api_prefix": self.config.api_prefix,
            "play_money_only": True,
            "real_money_implemented": False,
            "payment_processing_implemented": False,
            "currency_label": self.config.currency_label,
            "display_currency": self.config.display_currency,
            "persistence": casino_persistence_mode(),
            "default_venue_id": self.config.default_venue_id,
            "city_building_id": self.config.city_building_id,
        }

    async def list_venues(self):
        if casino_persistence_mode() == "memory":
            return [v.to_dict() for v in self._memory().venues()]
        return [v.to_dict() for v in await self._pg.venues()]

    async def get_venue(self, venue_id: str):
        if casino_persistence_mode() == "memory":
            return self._memory().get_venue(venue_id).to_dict()
        return (await self._pg.get_venue(venue_id)).to_dict()

    async def search_venues(self, query: str) -> list[dict[str, Any]]:
        q = (query or "").strip().lower()
        items = await self.list_venues()
        if not q:
            return items
        return [
            v
            for v in items
            if q in v["name"].lower()
            or q in v["slug"].lower()
            or q in v["city_building_id"].lower()
            or q in "casino roulette odessa venue казино рулетка одесса демо фишки"
        ]

    async def lobby(self) -> dict[str, Any]:
        venues = await self.list_venues()
        return {
            "title": "Play-money casino lobby",
            "play_money_only": True,
            "real_money_implemented": False,
            "currency_label": self.config.currency_label,
            "display_currency": self.config.display_currency,
            "chip_denoms": list(self.config.chip_denoms),
            "venues": venues,
            "games": [{"id": "roulette", "name": "European Roulette", "demo": True}],
            "floor": list(FLOOR_AREAS),
            "city_entry": {
                "building_id": self.config.city_building_id,
                "route": "/casino",
                "venue_route": f"/casino/venues/{self.config.default_venue_id}",
                "enter_label": "Войти в казино",
            },
        }

    async def games(self) -> dict[str, Any]:
        return {
            "items": list(FLOOR_AREAS),
            "play_money_only": True,
            "real_money_implemented": False,
        }

    def _grant_meta(self, *, last_ts: float | None, balance: int) -> dict[str, Any]:
        now = time.time()
        cooldown = self.config.demo_grant_cooldown_seconds
        retry = 0
        if last_ts:
            elapsed = now - last_ts
            if elapsed < cooldown:
                retry = int(cooldown - elapsed)
        capped = balance >= self.config.demo_grant_balance_cap
        return {
            "demo_grant_chips": self.config.demo_grant_chips,
            "demo_grant_available": retry == 0 and not capped,
            "demo_grant_retry_after_seconds": retry,
            "demo_grant_capped": capped,
        }

    async def _last_demo_grant_ts(self, player_id: str) -> float | None:
        if casino_persistence_mode() == "memory":
            return self._memory().last_entry_ts(player_id, "demo_grant")
        return await self._pg.last_entry_ts(player_id, "demo_grant")

    async def wallet(self, player_id: str):
        if casino_persistence_mode() == "memory":
            payload = self._memory().get_or_create_wallet(player_id).to_dict()
        else:
            payload = (await self._pg.get_or_create_wallet(player_id)).to_dict()
        last_ts = await self._last_demo_grant_ts(player_id)
        payload.update(self._grant_meta(last_ts=last_ts, balance=int(payload["balance_chips"])))
        return payload

    async def ledger(self, player_id: str, *, limit: int = 50):
        if casino_persistence_mode() == "memory":
            rows = self._memory().list_ledger(player_id, limit=limit)
        else:
            rows = await self._pg.list_ledger(player_id, limit=limit)
        return {"items": [r.to_dict() for r in rows], "play_money_only": True}

    async def demo_grant(self, player_id: str, *, client_payload: dict[str, Any] | None = None) -> dict[str, Any]:
        forbidden = {"amount", "amount_chips", "balance", "balance_chips", "chips"}
        if client_payload:
            for key in forbidden:
                if key in client_payload and client_payload[key] is not None:
                    raise ValidationError("client cannot set demo grant amount")
        wallet = await self.wallet(player_id)
        balance = int(wallet["balance_chips"])
        if balance >= self.config.demo_grant_balance_cap:
            raise ValidationError("demo chip balance is already at the play-money cap")
        last_ts = await self._last_demo_grant_ts(player_id)
        now = time.time()
        cooldown = self.config.demo_grant_cooldown_seconds
        if last_ts and (now - last_ts) < cooldown:
            retry = int(cooldown - (now - last_ts))
            raise RateLimitError("demo grant cooldown", retry_after=max(retry, 1))
        amount = self.config.demo_grant_chips
        window = int(now // cooldown)
        key = f"demo_grant:{current_casino_tenant()}:{player_id}:{window}"
        if casino_persistence_mode() == "memory":
            self._memory().credit(
                player_id,
                amount,
                entry_type="demo_grant",
                reference_id="demo-grant",
                idempotency_key=key,
                reference_type="wallet",
            )
        else:
            await self._pg.apply_delta(
                player_id,
                amount,
                entry_type="demo_grant",
                reference_id="demo-grant",
                idempotency_key=key,
                reference_type="wallet",
            )
        return await self.wallet(player_id)

    async def open_round(self, venue_id: str):
        if casino_persistence_mode() == "memory":
            return self._memory().open_round(venue_id).to_dict()
        return (await self._pg.open_round(venue_id)).to_dict()

    async def get_round(self, round_id: str):
        if casino_persistence_mode() == "memory":
            rnd = self._memory().get_round(round_id)
            bets = self._memory().bets_for_round(round_id)
        else:
            rnd = await self._pg.get_round(round_id)
            bets = await self._pg.bets_for_round(round_id)
        payload = rnd.to_dict()
        payload["bets"] = [b.to_dict() for b in bets]
        return payload

    async def place_bet(
        self,
        *,
        player_id: str,
        round_id: str,
        bet_type: str,
        amount_chips: int,
        numbers: list[int] | None,
        idempotency_key: str,
    ) -> dict[str, Any]:
        if amount_chips < self.config.min_wager or amount_chips > self.config.max_wager:
            raise ValidationError(
                f"wager must be between {self.config.min_wager} and {self.config.max_wager} chips"
            )
        covered = resolve_bet_numbers(bet_type, numbers)
        if casino_persistence_mode() == "memory":
            rnd = self._memory().get_round(round_id)
        else:
            rnd = await self._pg.get_round(round_id)
        if rnd.status != "open" or rnd.settled:
            raise ValidationError("round is not open")
        bet_id = f"bet_{uuid.uuid4().hex[:16]}"
        key = idempotency_key.strip() or f"bet:{round_id}:{player_id}:{bet_id}"
        debit_key = f"wager:{key}"
        if casino_persistence_mode() == "memory":
            existing = None
            for b in self._memory().bets_for_round(round_id):
                if b.idempotency_key == key:
                    existing = b
                    break
            if existing:
                return existing.to_dict()
            self._memory().debit(
                player_id,
                amount_chips,
                entry_type="wager",
                reference_id=round_id,
                idempotency_key=debit_key,
            )
            bet = RouletteBet(
                bet_id=bet_id,
                tenant_id=current_casino_tenant(),
                player_id=player_id,
                round_id=round_id,
                bet_type=bet_type,
                numbers=covered,
                amount_chips=amount_chips,
                idempotency_key=key,
            )
            return self._memory().place_bet(bet).to_dict()

        await self._pg.apply_delta(
            player_id,
            -amount_chips,
            entry_type="wager",
            reference_id=round_id,
            idempotency_key=debit_key,
        )
        bet = RouletteBet(
            bet_id=bet_id,
            tenant_id=current_casino_tenant(),
            player_id=player_id,
            round_id=round_id,
            bet_type=bet_type,
            numbers=covered,
            amount_chips=amount_chips,
            idempotency_key=key,
        )
        stored = await self._pg.place_bet(bet)
        return stored.to_dict()

    async def spin(self, round_id: str) -> dict[str, Any]:
        if casino_persistence_mode() == "memory":
            rnd = self._memory().get_round(round_id)
            if rnd.settled:
                payload = rnd.to_dict()
                payload["bets"] = [b.to_dict() for b in self._memory().bets_for_round(round_id)]
                payload["duplicate_settlement_guard"] = True
                return payload
            spin = spin_european()
            rnd.result_number = int(spin["number"])
            rnd.result_color = str(spin["color"])
            rnd.entropy_hex = str(spin["entropy_hex"])
            bets = self._memory().bets_for_round(round_id)
            for bet in bets:
                payout = settle_bet(
                    bet_type=bet.bet_type,
                    numbers=bet.numbers,
                    amount_chips=bet.amount_chips,
                    result_number=rnd.result_number,
                )
                bet.payout_chips = payout
                bet.status = "won" if payout else "lost"
                if payout:
                    self._memory().credit(
                        bet.player_id,
                        payout,
                        entry_type="payout",
                        reference_id=bet.bet_id,
                        idempotency_key=f"payout:{bet.bet_id}",
                    )
            self._memory().mark_settled(rnd)
            payload = rnd.to_dict()
            payload["bets"] = [b.to_dict() for b in bets]
            payload["duplicate_settlement_guard"] = True
            return payload

        rnd = await self._pg.get_round(round_id)
        if rnd.settled:
            payload = rnd.to_dict()
            payload["bets"] = [b.to_dict() for b in await self._pg.bets_for_round(round_id)]
            payload["duplicate_settlement_guard"] = True
            return payload
        spin = spin_european()
        rnd.result_number = int(spin["number"])
        rnd.result_color = str(spin["color"])
        rnd.entropy_hex = str(spin["entropy_hex"])
        rnd.settled = True
        rnd.status = "settled"
        await self._pg.save_round(rnd)
        bets = await self._pg.bets_for_round(round_id)
        for bet in bets:
            payout = settle_bet(
                bet_type=bet.bet_type,
                numbers=bet.numbers,
                amount_chips=bet.amount_chips,
                result_number=rnd.result_number,
            )
            bet.payout_chips = payout
            bet.status = "won" if payout else "lost"
            await self._pg.save_bet(bet)
            if payout:
                await self._pg.apply_delta(
                    bet.player_id,
                    payout,
                    entry_type="payout",
                    reference_id=bet.bet_id,
                    idempotency_key=f"payout:{bet.bet_id}",
                )
        payload = rnd.to_dict()
        payload["bets"] = [b.to_dict() for b in bets]
        payload["duplicate_settlement_guard"] = True
        return payload

    async def join_room(self, venue_id: str, player_id: str, room_id: str | None = None):
        await self.get_venue(venue_id)
        return await multiplayer.join_room(venue_id, player_id, room_id)

    async def leave_room(self, venue_id: str, player_id: str, room_id: str | None = None):
        await self.get_venue(venue_id)
        return await multiplayer.leave_room(venue_id, player_id, room_id)

    async def room(self, venue_id: str, room_id: str | None = None):
        await self.get_venue(venue_id)
        if room_id:
            table = get_table(live_room_id(room_id))
            if table is None:
                raise NotFoundError(f"room not found: {room_id}")
            return await multiplayer.room_presence(venue_id, room_id)
        return await multiplayer.rooms_for_venue(venue_id)


casino_engine = CasinoEngine()
