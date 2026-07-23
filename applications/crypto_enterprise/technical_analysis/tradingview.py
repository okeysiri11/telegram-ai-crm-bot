"""TradingView integration and market charts."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.crypto_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.crypto_enterprise.shared.store import CryptoEnterpriseStore, crypto_enterprise_store

TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d", "1w"]
CHART_TYPES = ["candlestick", "heikin_ashi", "line", "area", "volume"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class TradingViewIntegration:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store

    def connect_api(self, *, account: str, api_ref: str = "") -> dict[str, Any]:
        if not account:
            raise ValidationError("TradingView account required")
        cid = _id("ta_tv")
        return self.store.ta_tv_connections.save(
            cid,
            {
                "connection_id": cid,
                "account": account,
                "api_ref": api_ref or f"vault://tradingview/{account}",
                "status": "connected",
                "at": _now(),
            },
        )

    def sync_watchlist(self, *, name: str, symbols: list[str]) -> dict[str, Any]:
        if not name:
            raise ValidationError("watchlist name required")
        if not symbols:
            raise ValidationError("symbols required")
        wid = _id("ta_wl")
        return self.store.ta_watchlists.save(
            wid,
            {
                "watchlist_id": wid,
                "name": name,
                "symbols": [s.upper() for s in symbols],
                "synced": True,
                "at": _now(),
            },
        )

    def sync_chart(self, *, symbol: str, timeframe: str = "1h") -> dict[str, Any]:
        if not symbol:
            raise ValidationError("symbol required")
        if timeframe not in TIMEFRAMES:
            raise ValidationError(f"timeframe must be one of {TIMEFRAMES}")
        cid = _id("ta_csync")
        return self.store.ta_chart_sync.save(
            cid,
            {
                "sync_id": cid,
                "symbol": symbol.upper(),
                "timeframe": timeframe,
                "synced": True,
                "at": _now(),
            },
        )

    def set_timeframe(self, *, chart_id: str, timeframe: str) -> dict[str, Any]:
        if timeframe not in TIMEFRAMES:
            raise ValidationError(f"timeframe must be one of {TIMEFRAMES}")
        tid = _id("ta_tf")
        return self.store.ta_timeframes.save(
            tid,
            {
                "timeframe_id": tid,
                "chart_id": chart_id,
                "timeframe": timeframe,
                "at": _now(),
            },
        )

    def sync_drawing(self, *, chart_id: str, drawing_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if not chart_id:
            raise ValidationError("chart_id required")
        did = _id("ta_draw")
        return self.store.ta_drawings.save(
            did,
            {
                "drawing_id": did,
                "chart_id": chart_id,
                "drawing_type": drawing_type,
                "payload": payload or {},
                "synced": True,
                "at": _now(),
            },
        )

    def create_alert(self, *, symbol: str, condition: str, price: float) -> dict[str, Any]:
        if not symbol or not condition:
            raise ValidationError("symbol and condition required")
        aid = _id("ta_alrt")
        return self.store.ta_alerts.save(
            aid,
            {
                "alert_id": aid,
                "symbol": symbol.upper(),
                "condition": condition,
                "price": float(price),
                "active": True,
                "at": _now(),
            },
        )

    def multi_chart(self, *, layout: str, symbols: list[str]) -> dict[str, Any]:
        if not symbols:
            raise ValidationError("symbols required")
        mid = _id("ta_mchart")
        return self.store.ta_multi_charts.save(
            mid,
            {
                "layout_id": mid,
                "layout": layout or "2x2",
                "symbols": [s.upper() for s in symbols],
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "connections": self.store.ta_tv_connections.count(),
            "watchlists": self.store.ta_watchlists.count(),
            "alerts": self.store.ta_alerts.count(),
            "multi_charts": self.store.ta_multi_charts.count(),
        }


class MarketCharts:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store
        self.chart_types = list(CHART_TYPES)

    def create(
        self,
        *,
        symbol: str,
        chart_type: str = "candlestick",
        timeframe: str = "1h",
    ) -> dict[str, Any]:
        if not symbol:
            raise ValidationError("symbol required")
        if chart_type not in CHART_TYPES:
            raise ValidationError(f"chart_type must be one of {CHART_TYPES}")
        if timeframe not in TIMEFRAMES:
            raise ValidationError(f"timeframe must be one of {TIMEFRAMES}")
        cid = _id("ta_chart")
        return self.store.ta_charts.save(
            cid,
            {
                "chart_id": cid,
                "symbol": symbol.upper(),
                "chart_type": chart_type,
                "timeframe": timeframe,
                "created_at": _now(),
            },
        )

    def multi_timeframe(self, *, symbol: str, timeframes: list[str] | None = None) -> dict[str, Any]:
        tfs = timeframes or ["15m", "1h", "4h", "1d"]
        for tf in tfs:
            if tf not in TIMEFRAMES:
                raise ValidationError(f"timeframe must be one of {TIMEFRAMES}")
        mid = _id("ta_mtf")
        return self.store.ta_mtf.save(
            mid,
            {
                "analysis_id": mid,
                "symbol": symbol.upper(),
                "timeframes": tfs,
                "at": _now(),
            },
        )

    def playback(self, *, chart_id: str, from_ts: str, to_ts: str) -> dict[str, Any]:
        if self.store.ta_charts.get(chart_id) is None:
            raise NotFoundError("chart", chart_id)
        pid = _id("ta_play")
        return self.store.ta_playback.save(
            pid,
            {
                "playback_id": pid,
                "chart_id": chart_id,
                "from_ts": from_ts,
                "to_ts": to_ts,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "charts": self.store.ta_charts.count(),
            "mtf": self.store.ta_mtf.count(),
            "playback": self.store.ta_playback.count(),
            "types": self.chart_types,
        }
