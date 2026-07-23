"""Signal generation and portfolio simulation."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.crypto_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.crypto_enterprise.shared.store import CryptoEnterpriseStore, crypto_enterprise_store

SIGNAL_SIDES = ["long", "short", "flat"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class SignalGeneration:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store

    def _require_strategy(self, strategy_id: str) -> None:
        if self.store.se_strategies.get(strategy_id) is None:
            raise NotFoundError("strategy", strategy_id)

    def entry(
        self,
        *,
        strategy_id: str,
        symbol: str,
        side: str,
        price: float,
        confidence: float = 0.7,
    ) -> dict[str, Any]:
        self._require_strategy(strategy_id)
        if side not in SIGNAL_SIDES:
            raise ValidationError("side must be long|short|flat")
        confidence = float(confidence)
        if confidence < 0 or confidence > 1:
            raise ValidationError("confidence must be 0..1")
        sid = _id("se_entry")
        return self.store.se_entries.save(
            sid,
            {
                "signal_id": sid,
                "kind": "entry",
                "strategy_id": strategy_id,
                "symbol": symbol.upper(),
                "side": side,
                "price": float(price),
                "confidence": confidence,
                "quality": "high" if confidence >= 0.75 else "medium" if confidence >= 0.5 else "low",
                "at": _now(),
            },
        )

    def exit(self, *, strategy_id: str, symbol: str, price: float, reason: str = "target") -> dict[str, Any]:
        self._require_strategy(strategy_id)
        xid = _id("se_exit")
        return self.store.se_exits.save(
            xid,
            {
                "signal_id": xid,
                "kind": "exit",
                "strategy_id": strategy_id,
                "symbol": symbol.upper(),
                "price": float(price),
                "reason": reason,
                "at": _now(),
            },
        )

    def take_profit(self, *, strategy_id: str, symbol: str, targets: list[float]) -> dict[str, Any]:
        if not targets:
            raise ValidationError("targets required")
        tid = _id("se_tp")
        return self.store.se_take_profits.save(
            tid,
            {
                "tp_id": tid,
                "strategy_id": strategy_id,
                "symbol": symbol.upper(),
                "targets": [float(t) for t in targets],
                "at": _now(),
            },
        )

    def stop_loss(self, *, strategy_id: str, symbol: str, stop: float) -> dict[str, Any]:
        sid = _id("se_sl")
        return self.store.se_stop_losses.save(
            sid,
            {
                "sl_id": sid,
                "strategy_id": strategy_id,
                "symbol": symbol.upper(),
                "stop": float(stop),
                "at": _now(),
            },
        )

    def trailing_stop(self, *, strategy_id: str, symbol: str, trail_pct: float) -> dict[str, Any]:
        if trail_pct <= 0:
            raise ValidationError("trail_pct must be > 0")
        tid = _id("se_trail")
        return self.store.se_trailing.save(
            tid,
            {
                "trail_id": tid,
                "strategy_id": strategy_id,
                "symbol": symbol.upper(),
                "trail_pct": float(trail_pct),
                "at": _now(),
            },
        )

    def scale_position(self, *, strategy_id: str, symbol: str, sizes: list[float]) -> dict[str, Any]:
        if not sizes:
            raise ValidationError("sizes required")
        sid = _id("se_scale")
        return self.store.se_scaling.save(
            sid,
            {
                "scale_id": sid,
                "strategy_id": strategy_id,
                "symbol": symbol.upper(),
                "sizes": [float(s) for s in sizes],
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "entries": self.store.se_entries.count(),
            "exits": self.store.se_exits.count(),
            "take_profits": self.store.se_take_profits.count(),
            "stop_losses": self.store.se_stop_losses.count(),
        }


class PortfolioSimulation:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store

    def allocate(self, *, name: str, allocations: dict[str, float]) -> dict[str, Any]:
        if not name or not allocations:
            raise ValidationError("name and allocations required")
        total = sum(allocations.values())
        if abs(total - 100) > 0.5 and abs(total - 1.0) > 0.01:
            raise ValidationError("allocations should sum to 100 or 1.0")
        aid = _id("se_alloc")
        return self.store.se_allocations.save(
            aid,
            {
                "allocation_id": aid,
                "name": name,
                "allocations": allocations,
                "at": _now(),
            },
        )

    def multi_asset(self, *, assets: list[str], capital: float) -> dict[str, Any]:
        if not assets:
            raise ValidationError("assets required")
        mid = _id("se_masset")
        return self.store.se_multi_asset.save(
            mid,
            {
                "sim_id": mid,
                "assets": [a.upper() for a in assets],
                "capital": float(capital),
                "at": _now(),
            },
        )

    def exposure(self, *, long_pct: float, short_pct: float, cash_pct: float) -> dict[str, Any]:
        eid = _id("se_exp")
        return self.store.se_exposure.save(
            eid,
            {
                "exposure_id": eid,
                "long_pct": float(long_pct),
                "short_pct": float(short_pct),
                "cash_pct": float(cash_pct),
                "at": _now(),
            },
        )

    def correlation(self, *, assets: list[str], matrix: list[list[float]] | None = None) -> dict[str, Any]:
        if len(assets) < 2:
            raise ValidationError("at least two assets required")
        cid = _id("se_pcorr")
        return self.store.se_port_corr.save(
            cid,
            {
                "correlation_id": cid,
                "assets": [a.upper() for a in assets],
                "matrix": matrix or [[1.0, 0.4], [0.4, 1.0]],
                "at": _now(),
            },
        )

    def diversification(self, *, score: float, holdings: int) -> dict[str, Any]:
        score = float(score)
        if score < 0 or score > 1:
            raise ValidationError("score must be 0..1")
        did = _id("se_div")
        return self.store.se_diversification.save(
            did,
            {
                "diversification_id": did,
                "score": score,
                "holdings": int(holdings),
                "label": "high" if score >= 0.7 else "moderate" if score >= 0.4 else "low",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "allocations": self.store.se_allocations.count(),
            "multi_asset": self.store.se_multi_asset.count(),
            "diversification": self.store.se_diversification.count(),
        }
