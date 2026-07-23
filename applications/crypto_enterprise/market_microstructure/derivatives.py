"""Derivatives, liquidation, and liquidity intelligence."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.crypto_enterprise.shared.exceptions import ValidationError
from applications.crypto_enterprise.shared.store import CryptoEnterpriseStore, crypto_enterprise_store

LIQ_SIDES = ["long", "short"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class DerivativesIntelligence:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store

    def open_interest(self, *, symbol: str, oi: float, change_pct: float = 0.0) -> dict[str, Any]:
        if oi < 0:
            raise ValidationError("oi must be >= 0")
        oid = _id("mm_oi")
        return self.store.mm_open_interest.save(
            oid,
            {
                "oi_id": oid,
                "symbol": symbol.upper(),
                "open_interest": float(oi),
                "change_pct": float(change_pct),
                "at": _now(),
            },
        )

    def funding_rate(self, *, symbol: str, rate: float) -> dict[str, Any]:
        fid = _id("mm_fund")
        return self.store.mm_funding.save(
            fid,
            {
                "funding_id": fid,
                "symbol": symbol.upper(),
                "rate": float(rate),
                "bias": "longs_pay" if rate > 0 else "shorts_pay" if rate < 0 else "flat",
                "at": _now(),
            },
        )

    def long_short_ratio(self, *, symbol: str, long_pct: float, short_pct: float) -> dict[str, Any]:
        if abs(long_pct + short_pct - 100) > 0.5:
            raise ValidationError("long_pct + short_pct should equal 100")
        rid = _id("mm_lsr")
        return self.store.mm_long_short.save(
            rid,
            {
                "ratio_id": rid,
                "symbol": symbol.upper(),
                "long_pct": float(long_pct),
                "short_pct": float(short_pct),
                "ratio": round(long_pct / max(short_pct, 0.01), 4),
                "at": _now(),
            },
        )

    def basis(self, *, symbol: str, spot: float, futures: float) -> dict[str, Any]:
        bid = _id("mm_basis")
        return self.store.mm_basis.save(
            bid,
            {
                "basis_id": bid,
                "symbol": symbol.upper(),
                "spot": float(spot),
                "futures": float(futures),
                "basis": round(futures - spot, 4),
                "basis_pct": round((futures - spot) / max(spot, 1e-9) * 100, 4),
                "at": _now(),
            },
        )

    def futures_premium(self, *, symbol: str, premium_pct: float) -> dict[str, Any]:
        pid = _id("mm_prem")
        return self.store.mm_premium.save(
            pid,
            {
                "premium_id": pid,
                "symbol": symbol.upper(),
                "premium_pct": float(premium_pct),
                "at": _now(),
            },
        )

    def options_overview(self, *, symbol: str, put_call_ratio: float, iv: float) -> dict[str, Any]:
        oid = _id("mm_opt")
        return self.store.mm_options.save(
            oid,
            {
                "overview_id": oid,
                "symbol": symbol.upper(),
                "put_call_ratio": float(put_call_ratio),
                "iv": float(iv),
                "at": _now(),
            },
        )

    def expiration_calendar(self, *, symbol: str, expiries: list[str]) -> dict[str, Any]:
        if not expiries:
            raise ValidationError("expiries required")
        eid = _id("mm_exp")
        return self.store.mm_expirations.save(
            eid,
            {
                "calendar_id": eid,
                "symbol": symbol.upper(),
                "expiries": expiries,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "open_interest": self.store.mm_open_interest.count(),
            "funding": self.store.mm_funding.count(),
            "long_short": self.store.mm_long_short.count(),
            "options": self.store.mm_options.count(),
        }


class LiquidationIntelligence:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store

    def liquidation(self, *, symbol: str, side: str, size: float, price: float) -> dict[str, Any]:
        if side not in LIQ_SIDES:
            raise ValidationError("side must be long|short")
        lid = _id("mm_liq")
        store = self.store.mm_long_liqs if side == "long" else self.store.mm_short_liqs
        return store.save(
            lid,
            {
                "liquidation_id": lid,
                "symbol": symbol.upper(),
                "side": side,
                "size": float(size),
                "price": float(price),
                "at": _now(),
            },
        )

    def heatmap(self, *, symbol: str, clusters: int = 8) -> dict[str, Any]:
        hid = _id("mm_lheath")
        return self.store.mm_liq_heatmaps.save(
            hid,
            {
                "heatmap_id": hid,
                "symbol": symbol.upper(),
                "clusters": int(clusters),
                "intensity": 0.68,
                "at": _now(),
            },
        )

    def cluster(self, *, symbol: str, price: float, size: float, side: str) -> dict[str, Any]:
        cid = _id("mm_lclust")
        return self.store.mm_liq_clusters.save(
            cid,
            {
                "cluster_id": cid,
                "symbol": symbol.upper(),
                "price": float(price),
                "size": float(size),
                "side": side,
                "at": _now(),
            },
        )

    def cascade(self, *, symbol: str, levels: int, total_size: float) -> dict[str, Any]:
        cid = _id("mm_casc")
        return self.store.mm_cascades.save(
            cid,
            {
                "cascade_id": cid,
                "symbol": symbol.upper(),
                "levels": int(levels),
                "total_size": float(total_size),
                "detected": levels >= 3,
                "at": _now(),
            },
        )

    def alert(self, *, symbol: str, side: str, size: float, price: float) -> dict[str, Any]:
        aid = _id("mm_lalert")
        return self.store.mm_liq_alerts.save(
            aid,
            {
                "alert_id": aid,
                "symbol": symbol.upper(),
                "side": side,
                "size": float(size),
                "price": float(price),
                "forced": True,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "long_liqs": self.store.mm_long_liqs.count(),
            "short_liqs": self.store.mm_short_liqs.count(),
            "cascades": self.store.mm_cascades.count(),
            "alerts": self.store.mm_liq_alerts.count(),
        }


class LiquidityIntelligence:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store

    def zone(self, *, symbol: str, price_low: float, price_high: float, strength: float) -> dict[str, Any]:
        zid = _id("mm_zone")
        return self.store.mm_liq_zones.save(
            zid,
            {
                "zone_id": zid,
                "symbol": symbol.upper(),
                "price_low": float(price_low),
                "price_high": float(price_high),
                "strength": float(strength),
                "at": _now(),
            },
        )

    def support_liquidity(self, *, symbol: str, price: float, size: float) -> dict[str, Any]:
        sid = _id("mm_supliq")
        return self.store.mm_support_liq.save(
            sid,
            {
                "level_id": sid,
                "symbol": symbol.upper(),
                "price": float(price),
                "size": float(size),
                "kind": "support",
                "at": _now(),
            },
        )

    def resistance_liquidity(self, *, symbol: str, price: float, size: float) -> dict[str, Any]:
        rid = _id("mm_resliq")
        return self.store.mm_resistance_liq.save(
            rid,
            {
                "level_id": rid,
                "symbol": symbol.upper(),
                "price": float(price),
                "size": float(size),
                "kind": "resistance",
                "at": _now(),
            },
        )

    def stop_hunt(self, *, symbol: str, direction: str, swept_price: float) -> dict[str, Any]:
        if direction not in ("above", "below"):
            raise ValidationError("direction must be above|below")
        hid = _id("mm_hunt")
        return self.store.mm_stop_hunts.save(
            hid,
            {
                "hunt_id": hid,
                "symbol": symbol.upper(),
                "direction": direction,
                "swept_price": float(swept_price),
                "at": _now(),
            },
        )

    def market_maker(self, *, symbol: str, activity_score: float) -> dict[str, Any]:
        mid = _id("mm_mm")
        return self.store.mm_market_makers.save(
            mid,
            {
                "activity_id": mid,
                "symbol": symbol.upper(),
                "activity_score": float(activity_score),
                "label": "active" if activity_score >= 0.6 else "quiet",
                "at": _now(),
            },
        )

    def absorption(self, *, symbol: str, side: str, size: float) -> dict[str, Any]:
        aid = _id("mm_abs")
        return self.store.mm_absorption.save(
            aid,
            {
                "absorption_id": aid,
                "symbol": symbol.upper(),
                "side": side,
                "size": float(size),
                "detected": True,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "zones": self.store.mm_liq_zones.count(),
            "stop_hunts": self.store.mm_stop_hunts.count(),
            "absorption": self.store.mm_absorption.count(),
        }
