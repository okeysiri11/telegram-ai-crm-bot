"""Order book intelligence and trade flow analysis."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.crypto_enterprise.shared.exceptions import ValidationError
from applications.crypto_enterprise.shared.store import CryptoEnterpriseStore, crypto_enterprise_store

TRADE_SIDES = ["buy", "sell"]
TRADE_CLASSES = ["aggressive", "passive", "large", "retail"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class OrderBookIntelligence:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store

    def snapshot(self, *, symbol: str, bids: list[list[float]] | None = None, asks: list[list[float]] | None = None) -> dict[str, Any]:
        if not symbol:
            raise ValidationError("symbol required")
        bids = bids or [[68000.0, 12.5], [67990.0, 8.2], [67980.0, 15.0]]
        asks = asks or [[68010.0, 10.1], [68020.0, 7.4], [68030.0, 11.8]]
        oid = _id("mm_ob")
        return self.store.mm_order_books.save(
            oid,
            {
                "book_id": oid,
                "symbol": symbol.upper(),
                "bids": bids,
                "asks": asks,
                "best_bid": bids[0][0],
                "best_ask": asks[0][0],
                "spread": round(asks[0][0] - bids[0][0], 4),
                "at": _now(),
            },
        )

    def depth(self, *, symbol: str, levels: int = 10) -> dict[str, Any]:
        if levels < 1:
            raise ValidationError("levels must be >= 1")
        did = _id("mm_depth")
        return self.store.mm_depth.save(
            did,
            {
                "depth_id": did,
                "symbol": symbol.upper(),
                "levels": int(levels),
                "bid_liquidity": round(120.5 * levels / 10, 2),
                "ask_liquidity": round(118.2 * levels / 10, 2),
                "at": _now(),
            },
        )

    def bid_ask(self, *, symbol: str, bid: float, ask: float) -> dict[str, Any]:
        if bid <= 0 or ask <= 0 or ask < bid:
            raise ValidationError("valid bid/ask required")
        aid = _id("mm_ba")
        return self.store.mm_bid_ask.save(
            aid,
            {
                "analysis_id": aid,
                "symbol": symbol.upper(),
                "bid": float(bid),
                "ask": float(ask),
                "mid": round((bid + ask) / 2, 4),
                "spread_bps": round((ask - bid) / ((bid + ask) / 2) * 10000, 2),
                "at": _now(),
            },
        )

    def heatmap(self, *, symbol: str, buckets: int = 20) -> dict[str, Any]:
        hid = _id("mm_heat")
        return self.store.mm_heatmaps.save(
            hid,
            {
                "heatmap_id": hid,
                "symbol": symbol.upper(),
                "buckets": int(buckets),
                "intensity": 0.74,
                "at": _now(),
            },
        )

    def imbalance(self, *, symbol: str, bid_volume: float, ask_volume: float) -> dict[str, Any]:
        total = bid_volume + ask_volume
        if total <= 0:
            raise ValidationError("volumes required")
        ratio = (bid_volume - ask_volume) / total
        iid = _id("mm_imb")
        return self.store.mm_imbalance.save(
            iid,
            {
                "imbalance_id": iid,
                "symbol": symbol.upper(),
                "bid_volume": float(bid_volume),
                "ask_volume": float(ask_volume),
                "ratio": round(ratio, 4),
                "bias": "bid" if ratio > 0.1 else "ask" if ratio < -0.1 else "neutral",
                "at": _now(),
            },
        )

    def large_order(self, *, symbol: str, side: str, size: float, price: float) -> dict[str, Any]:
        if side not in TRADE_SIDES:
            raise ValidationError("side must be buy|sell")
        lid = _id("mm_large")
        return self.store.mm_large_orders.save(
            lid,
            {
                "order_id": lid,
                "symbol": symbol.upper(),
                "side": side,
                "size": float(size),
                "price": float(price),
                "flag": "large",
                "at": _now(),
            },
        )

    def iceberg(self, *, symbol: str, side: str, visible: float, estimated_total: float) -> dict[str, Any]:
        iid = _id("mm_ice")
        return self.store.mm_icebergs.save(
            iid,
            {
                "detection_id": iid,
                "symbol": symbol.upper(),
                "side": side,
                "visible": float(visible),
                "estimated_total": float(estimated_total),
                "confidence": 0.78,
                "at": _now(),
            },
        )

    def spoofing(self, *, symbol: str, side: str, size: float, cancelled_pct: float) -> dict[str, Any]:
        sid = _id("mm_spoof")
        return self.store.mm_spoofing.save(
            sid,
            {
                "detection_id": sid,
                "symbol": symbol.upper(),
                "side": side,
                "size": float(size),
                "cancelled_pct": float(cancelled_pct),
                "flagged": cancelled_pct >= 0.8,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "order_books": self.store.mm_order_books.count(),
            "depth": self.store.mm_depth.count(),
            "imbalance": self.store.mm_imbalance.count(),
            "large_orders": self.store.mm_large_orders.count(),
            "icebergs": self.store.mm_icebergs.count(),
            "spoofing": self.store.mm_spoofing.count(),
        }


class TradeFlowAnalysis:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store

    def time_and_sales(self, *, symbol: str, price: float, size: float, side: str) -> dict[str, Any]:
        if side not in TRADE_SIDES:
            raise ValidationError("side must be buy|sell")
        tid = _id("mm_ts")
        return self.store.mm_time_sales.save(
            tid,
            {
                "trade_id": tid,
                "symbol": symbol.upper(),
                "price": float(price),
                "size": float(size),
                "side": side,
                "at": _now(),
            },
        )

    def classify(self, *, symbol: str, trade_class: str, size: float) -> dict[str, Any]:
        if trade_class not in TRADE_CLASSES:
            raise ValidationError(f"trade_class must be one of {TRADE_CLASSES}")
        cid = _id("mm_tcl")
        return self.store.mm_trade_class.save(
            cid,
            {
                "classification_id": cid,
                "symbol": symbol.upper(),
                "trade_class": trade_class,
                "size": float(size),
                "at": _now(),
            },
        )

    def pressure(self, *, symbol: str, buy_volume: float, sell_volume: float) -> dict[str, Any]:
        total = buy_volume + sell_volume
        if total <= 0:
            raise ValidationError("volumes required")
        pid = _id("mm_press")
        return self.store.mm_pressure.save(
            pid,
            {
                "pressure_id": pid,
                "symbol": symbol.upper(),
                "buy_volume": float(buy_volume),
                "sell_volume": float(sell_volume),
                "buy_pct": round(buy_volume / total * 100, 2),
                "bias": "buy" if buy_volume > sell_volume else "sell",
                "at": _now(),
            },
        )

    def volume_delta(self, *, symbol: str, delta: float) -> dict[str, Any]:
        vid = _id("mm_vd")
        return self.store.mm_volume_delta.save(
            vid,
            {
                "delta_id": vid,
                "symbol": symbol.upper(),
                "delta": float(delta),
                "at": _now(),
            },
        )

    def cvd(self, *, symbol: str, cumulative: float) -> dict[str, Any]:
        cid = _id("mm_cvd")
        return self.store.mm_cvd.save(
            cid,
            {
                "cvd_id": cid,
                "symbol": symbol.upper(),
                "cumulative": float(cumulative),
                "trend": "rising" if cumulative > 0 else "falling",
                "at": _now(),
            },
        )

    def aggressive(self, *, symbol: str, side: str, size: float) -> dict[str, Any]:
        aid = _id("mm_agg")
        return self.store.mm_aggressive.save(
            aid,
            {
                "detection_id": aid,
                "symbol": symbol.upper(),
                "side": side,
                "size": float(size),
                "at": _now(),
            },
        )

    def large_trade(self, *, symbol: str, side: str, size: float, price: float) -> dict[str, Any]:
        lid = _id("mm_lt")
        return self.store.mm_large_trades.save(
            lid,
            {
                "trade_id": lid,
                "symbol": symbol.upper(),
                "side": side,
                "size": float(size),
                "price": float(price),
                "at": _now(),
            },
        )

    def analytics(self, *, symbol: str) -> dict[str, Any]:
        aid = _id("mm_tfa")
        return self.store.mm_flow_analytics.save(
            aid,
            {
                "analytics_id": aid,
                "symbol": symbol.upper(),
                "trades": self.store.mm_time_sales.count(),
                "cvd_points": self.store.mm_cvd.count(),
                "large_trades": self.store.mm_large_trades.count(),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "time_sales": self.store.mm_time_sales.count(),
            "pressure": self.store.mm_pressure.count(),
            "cvd": self.store.mm_cvd.count(),
            "large_trades": self.store.mm_large_trades.count(),
        }
