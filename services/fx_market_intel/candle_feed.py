"""FX candle + quote reliability: TTL cache, single-flight, last-good, 429 backoff.

React charts never talk to Yahoo. All callers go through get_candles / cached quotes.
No fabricated OHLC. Empty/error responses never overwrite last-good cache.
"""

from __future__ import annotations

import asyncio
import math
import os
import time
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, TypeVar

from services.fx_market_intel.symbols import normalize_symbol
from services.fx_market_intel import yahoo_feed as yahoo_feed
from services.fx_market_intel.yahoo_feed import (
    DXY_SUPPORTED_TIMEFRAMES,
    SUPPORTED_TIMEFRAMES,
    YAHOO_SYMBOLS,
    YahooHttpError,
    normalize_timeframe,
    yahoo_interval_range,
)

T = TypeVar("T")

QUOTE_TTL_SEC = 4.0
CANDLE_TTL_SEC = {
    "1m": 30.0,
    "5m": 60.0,
    "15m": 120.0,
    "1H": 300.0,
    "4H": 600.0,
    "1D": 1800.0,
    "1W": 3600.0,
}
BACKOFF_SEC = (30.0, 60.0, 120.0, 300.0)
MAX_BACKOFF_SEC = 300.0

_candle_ttl: dict[str, dict[str, Any]] = {}
_candle_last_good: dict[str, dict[str, Any]] = {}
_quote_ttl: dict[str, dict[str, Any]] = {}
_quote_last_good: dict[str, dict[str, Any]] = {}
_cooldown_until: dict[str, float] = {}
_backoff_step: dict[str, int] = {}
_inflight: dict[str, asyncio.Task[Any]] = {}


def reset_fx_market_cache() -> None:
    _candle_ttl.clear()
    _candle_last_good.clear()
    _quote_ttl.clear()
    _quote_last_good.clear()
    _cooldown_until.clear()
    _backoff_step.clear()
    _inflight.clear()


def _key(symbol: str, timeframe: str | None = None) -> str:
    sym = normalize_symbol(symbol)
    if timeframe is None:
        return f"quote:{sym}"
    return f"candle:{sym}:{normalize_timeframe(timeframe, instrument=sym)}"


def _ttl_for(timeframe: str) -> float:
    return CANDLE_TTL_SEC.get(timeframe, 300.0)


def alternative_provider_name() -> str | None:
    name = (os.environ.get("FX_CANDLE_PROVIDER") or "").strip()
    if name and name.lower() not in {"yahoo", "yahoo_finance", ""}:
        return name
    if (os.environ.get("FINNHUB_API_KEY") or "").strip():
        return "finnhub"
    if (os.environ.get("TWELVEDATA_API_KEY") or os.environ.get("TWELVE_DATA_API_KEY") or "").strip():
        return "twelvedata"
    if (os.environ.get("POLYGON_API_KEY") or "").strip():
        return "polygon"
    return None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _bar_unix(bar: dict[str, Any]) -> int | None:
    raw = bar.get("time")
    if raw is None:
        raw = bar.get("t")
    if isinstance(raw, (int, float)) and math.isfinite(float(raw)) and float(raw) > 0:
        n = float(raw)
        return int(n / 1000) if n > 1e12 else int(n)
    if isinstance(raw, str) and raw:
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
        return int(dt.timestamp())
    return None


def detect_source_resolution(bars: list[dict[str, Any]]) -> str:
    times: list[int] = []
    for b in bars:
        u = _bar_unix(b)
        if u:
            times.append(u)
    times = sorted(set(times))
    if len(times) < 2:
        return "unknown"
    deltas = sorted(times[i] - times[i - 1] for i in range(1, len(times)) if times[i] > times[i - 1])
    if not deltas:
        return "unknown"
    mid = deltas[len(deltas) // 2]
    if mid <= 90:
        return "1m"
    if mid <= 240:
        return "2m"
    if mid <= 450:
        return "5m"
    if mid <= 1200:
        return "15m"
    if mid <= 8000:
        return "60m"
    if mid <= 20000:
        return "4h"
    if mid <= 200000:
        return "1d"
    return "1w"


def _with_meta(payload: dict[str, Any], **extra: Any) -> dict[str, Any]:
    out = {**payload, **extra}
    bars = list(out.get("bars") or [])
    out["bar_count"] = len(bars)
    out["chart_ready"] = len(bars) > 0
    if bars:
        last = bars[-1]
        out.setdefault("last_close", last.get("c"))
        out.setdefault("last_bar_at", last.get("t") or last.get("time"))
        out["source_resolution"] = extra.get("source_resolution") or detect_source_resolution(bars)
    return out


def _stale_from_last_good(key: str, *, source_status: str, message: str) -> dict[str, Any] | None:
    good = _candle_last_good.get(key)
    if not good:
        return None
    return _with_meta(
        dict(good["payload"]),
        stale=True,
        source_status=source_status,
        status="delayed",
        message=message,
        fetched_at=good["payload"].get("fetched_at") or _now_iso(),
        cache="last_good",
    )


async def _coalesce(key: str, factory: Callable[[], Awaitable[T]]) -> T:
    existing = _inflight.get(key)
    if existing and not existing.done():
        return await asyncio.shield(existing)
    task = asyncio.create_task(factory())
    _inflight[key] = task
    try:
        return await task
    finally:
        if _inflight.get(key) is task:
            _inflight.pop(key, None)


def _parse_retry_after(value: str | None, fallback: float) -> float:
    if not value:
        return fallback
    try:
        return min(MAX_BACKOFF_SEC, max(1.0, float(value)))
    except (TypeError, ValueError):
        return fallback


def _set_cooldown(key: str, retry_after: str | None) -> float:
    step = _backoff_step.get(key, 0)
    wait = _parse_retry_after(retry_after, BACKOFF_SEC[min(step, len(BACKOFF_SEC) - 1)])
    _backoff_step[key] = min(step + 1, len(BACKOFF_SEC) - 1)
    until = time.monotonic() + wait
    _cooldown_until[key] = until
    return wait


def _clear_cooldown(key: str) -> None:
    _cooldown_until.pop(key, None)
    _backoff_step.pop(key, None)


async def fetch_alternative_candles(symbol: str, timeframe: str) -> dict[str, Any] | None:
    """Optional second candle provider. Returns None unless FX_CANDLE_PROVIDER is wired.

    Do not invent API keys. Plug in later with one env variable.
    """
    name = alternative_provider_name()
    if not name:
        return None
    return None


async def _fetch_yahoo_candles(symbol: str, timeframe: str) -> dict[str, Any]:
    sym = normalize_symbol(symbol)
    tf = normalize_timeframe(timeframe, instrument=sym)
    yahoo = YAHOO_SYMBOLS.get(sym)
    supported = list(DXY_SUPPORTED_TIMEFRAMES if sym == "DXY" else SUPPORTED_TIMEFRAMES)
    interval, range_ = yahoo_interval_range(sym, tf)
    base = {
        "symbol": sym,
        "timeframe": tf,
        "requested_timeframe": tf,
        "supported_timeframes": supported,
        "provider": "yahoo",
        "provider_symbol": yahoo,
        "chart_engine": "lightweight_charts",
        "yahoo_interval": interval,
        "alternative_provider": alternative_provider_name(),
    }
    if not yahoo:
        return _with_meta(
            {
                **base,
                "status": "needs_config",
                "message": f"Нет источника баров для {sym}",
                "bars": [],
                "source_status": "needs_config",
                "stale": False,
            }
        )
    result = await yahoo_feed.fetch_yahoo_chart(yahoo, interval=interval, range_=range_)
    bars = yahoo_feed.normalize_yahoo_bars(result, timeframe=tf, instrument=sym)
    if not bars:
        return _with_meta(
            {
                **base,
                "status": "insufficient_data",
                "message": "Yahoo вернул пустые бары",
                "bars": [],
                "source": f"Yahoo Finance ({yahoo})",
                "source_status": "insufficient_data",
                "stale": False,
            }
        )
    last = bars[-1]
    resolution = detect_source_resolution(bars)
    return _with_meta(
        {
            **base,
            "status": "connected",
            "message": "OK",
            "bars": bars,
            "last_close": last.get("c"),
            "last_bar_at": last.get("t"),
            "source": f"Yahoo Finance ({yahoo})",
            "fetched_at": _now_iso(),
            "source_status": "live",
            "stale": False,
            "source_resolution": resolution,
            "cache": "miss",
        }
    )


async def get_candles(symbol: str, timeframe: str = "1H") -> dict[str, Any]:
    """Canonical candle fetch: cache → single-flight Yahoo → last-good on 429/error."""
    sym = normalize_symbol(symbol)
    tf = normalize_timeframe(timeframe, instrument=sym)
    key = _key(sym, tf)
    now = time.monotonic()

    cool = _cooldown_until.get(key)
    if cool and now < cool:
        cached = _stale_from_last_good(
            key,
            source_status="rate_limited",
            message="RATE LIMITED — showing last received data",
        )
        if cached:
            return cached
        return _with_meta(
            {
                "symbol": sym,
                "timeframe": tf,
                "requested_timeframe": tf,
                "provider": "yahoo",
                "provider_symbol": YAHOO_SYMBOLS.get(sym),
                "chart_engine": "lightweight_charts",
                "status": "rate_limited",
                "source_status": "rate_limited",
                "stale": True,
                "bars": [],
                "message": "Источник временно ограничил запросы",
            }
        )

    hit = _candle_ttl.get(key)
    if hit and now < float(hit["expires_at"]):
        payload = dict(hit["payload"])
        payload["cache"] = "ttl"
        payload["stale"] = False
        payload.setdefault("source_status", "live")
        return payload

    async def _run() -> dict[str, Any]:
        try:
            alt = await fetch_alternative_candles(sym, tf)
            pack = alt if alt and alt.get("bars") else await _fetch_yahoo_candles(sym, tf)
        except YahooHttpError as exc:
            wait = _set_cooldown(key, exc.retry_after)
            cached = _stale_from_last_good(
                key,
                source_status="rate_limited",
                message="RATE LIMITED — showing last received data",
            )
            if cached:
                cached["retry_after_sec"] = wait
                return cached
            return _with_meta(
                {
                    "symbol": sym,
                    "timeframe": tf,
                    "requested_timeframe": tf,
                    "provider": "yahoo",
                    "provider_symbol": YAHOO_SYMBOLS.get(sym),
                    "chart_engine": "lightweight_charts",
                    "status": "rate_limited",
                    "source_status": "rate_limited",
                    "stale": True,
                    "bars": [],
                    "retry_after_sec": wait,
                    "message": f"Источник временно ограничил запросы (Yahoo HTTP {exc.status})",
                }
            )
        except Exception as exc:
            cached = _stale_from_last_good(
                key,
                source_status="error",
                message="Обновление источника…",
            )
            if cached:
                return cached
            return _with_meta(
                {
                    "symbol": sym,
                    "timeframe": tf,
                    "requested_timeframe": tf,
                    "provider": "yahoo",
                    "provider_symbol": YAHOO_SYMBOLS.get(sym),
                    "chart_engine": "lightweight_charts",
                    "status": "error",
                    "source_status": "error",
                    "stale": False,
                    "bars": [],
                    "message": f"Бары недоступны: {exc}",
                }
            )
        if pack.get("bars"):
            _clear_cooldown(key)
            stored = dict(pack)
            _candle_last_good[key] = {"payload": stored, "stored_at": time.monotonic()}
            _candle_ttl[key] = {"payload": stored, "expires_at": time.monotonic() + _ttl_for(tf)}
            return stored
        cached = _stale_from_last_good(key, source_status="insufficient_data", message="Обновление источника…")
        if cached:
            return cached
        return pack

    return await _coalesce(key, _run)


async def cached_quote(symbol: str, factory: Callable[[], Awaitable[dict[str, Any]]]) -> dict[str, Any]:
    key = _key(symbol)
    now = time.monotonic()
    hit = _quote_ttl.get(key)
    if hit and now < float(hit["expires_at"]):
        q = dict(hit["payload"])
        q["cache"] = "ttl"
        return q

    async def _run() -> dict[str, Any]:
        try:
            q = await factory()
        except Exception:
            good = _quote_last_good.get(key)
            if good:
                out = dict(good["payload"])
                out["stale"] = True
                out["source_status"] = "error"
                out["status"] = "delayed"
                return out
            raise
        mid = q.get("mid")
        try:
            mid_f = float(mid) if mid is not None else None
        except (TypeError, ValueError):
            mid_f = None
        if mid_f is not None and not yahoo_feed.price_in_instrument_band(normalize_symbol(symbol), mid_f):
            q = {**q, "mid": None, "status": "error", "message": f"rejected corrupt quote {mid}"}
            mid = None
        status = str(q.get("status") or "")
        if mid is not None and status in {"connected", "live", "delayed"}:
            _quote_last_good[key] = {"payload": dict(q), "stored_at": time.monotonic()}
            _quote_ttl[key] = {"payload": dict(q), "expires_at": time.monotonic() + QUOTE_TTL_SEC}
            return q
        good = _quote_last_good.get(key)
        if good and mid is None:
            out = dict(good["payload"])
            out["stale"] = True
            out["source_status"] = "rate_limited" if "429" in str(q.get("message") or "") else "error"
            out["status"] = "delayed"
            out["message"] = q.get("message") or out.get("message")
            return out
        return q

    return await _coalesce(key, _run)
