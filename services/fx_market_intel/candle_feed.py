"""FX candles: canonical bases, local aggregation, Yahoo circuit breaker, last-good.

React never talks to Yahoo. Higher timeframes are derived from 1m/1h bases.
Empty/error never overwrite last-good. Persistent last-good survives Render restart.
"""

from __future__ import annotations

import asyncio
import os
import time
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, TypeVar

from services.fx_market_intel import yahoo_feed as yahoo_feed
from services.fx_market_intel.bars import (
    aggregate_bars,
    bar_unix,
    normalize_canonical_bars,
    ohlc_range_stats,
)
from services.fx_market_intel.last_good_store import (
    load_last_good,
    memory_get,
    persistent_backend_name,
    reset_last_good_store,
    save_last_good,
)
from services.fx_market_intel.provider_router import (
    provider_health_snapshot,
    reset_provider_health,
    resolve_eurusd_1m,
)
from services.fx_market_intel.quality import score_ohlc
from services.fx_market_intel.symbols import normalize_symbol
from services.fx_market_intel.yahoo_feed import (
    DXY_SUPPORTED_TIMEFRAMES,
    SUPPORTED_TIMEFRAMES,
    YAHOO_SYMBOLS,
    YahooHttpError,
    normalize_timeframe,
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
YAHOO_BREAKER_STEPS = (60.0, 120.0, 300.0, 600.0)
MAX_BACKOFF_SEC = 600.0

_candle_ttl: dict[str, dict[str, Any]] = {}
_candle_last_good: dict[str, dict[str, Any]] = {}
_quote_ttl: dict[str, dict[str, Any]] = {}
_quote_last_good: dict[str, dict[str, Any]] = {}
_inflight: dict[str, asyncio.Task[Any]] = {}
_yahoo_state = "CLOSED"
_yahoo_open_until = 0.0
_yahoo_failures = 0
_yahoo_upstream_calls = 0
_hydrated = False
_yahoo_lock: asyncio.Lock | None = None


def reset_fx_market_cache() -> None:
    global _yahoo_state, _yahoo_open_until, _yahoo_failures, _yahoo_upstream_calls, _hydrated, _yahoo_lock
    _candle_ttl.clear()
    _candle_last_good.clear()
    _quote_ttl.clear()
    _quote_last_good.clear()
    _inflight.clear()
    _yahoo_state = "CLOSED"
    _yahoo_open_until = 0.0
    _yahoo_failures = 0
    _yahoo_upstream_calls = 0
    _hydrated = False
    _yahoo_lock = None
    reset_last_good_store()
    reset_provider_health()


def yahoo_provider_state() -> str:
    return _yahoo_state


def yahoo_upstream_calls() -> int:
    return _yahoo_upstream_calls


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


def detect_source_resolution(bars: list[dict[str, Any]]) -> str:
    times: list[int] = []
    for b in bars:
        u = bar_unix(b)
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
    out["provider_state"] = _yahoo_state
    out["persistent_backend"] = persistent_backend_name()
    out["provider_health"] = provider_health_snapshot()
    if bars:
        last = bars[-1]
        out.setdefault("last_close", last.get("c") if last.get("c") is not None else last.get("close"))
        out.setdefault("last_bar_at", last.get("t") or last.get("time"))
        out.setdefault("source_resolution", extra.get("source_resolution") or detect_source_resolution(bars))
    return out


def _remember(key: str, pack: dict[str, Any], tf: str) -> dict[str, Any]:
    stored = dict(pack)
    _candle_last_good[key] = {"payload": stored, "stored_at": time.monotonic()}
    _candle_ttl[key] = {"payload": stored, "expires_at": time.monotonic() + _ttl_for(tf)}
    return stored


def _from_last_good(key: str, *, source_status: str, message: str) -> dict[str, Any] | None:
    good = _candle_last_good.get(key)
    if not good:
        return None
    return _with_meta(
        dict(good["payload"]),
        stale=True,
        source_status=source_status,
        status="delayed",
        message=message,
        cache="last_good",
        provider_state=_yahoo_state,
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


def _open_breaker(retry_after: str | None) -> float:
    global _yahoo_state, _yahoo_open_until, _yahoo_failures
    _yahoo_failures += 1
    idx = min(_yahoo_failures - 1, len(YAHOO_BREAKER_STEPS) - 1)
    wait = YAHOO_BREAKER_STEPS[idx]
    if retry_after:
        try:
            wait = min(MAX_BACKOFF_SEC, max(wait, float(retry_after)))
        except (TypeError, ValueError):
            pass
    _yahoo_state = "OPEN"
    _yahoo_open_until = time.monotonic() + wait
    return wait


def _close_breaker() -> None:
    global _yahoo_state, _yahoo_failures, _yahoo_open_until
    _yahoo_state = "CLOSED"
    _yahoo_failures = 0
    _yahoo_open_until = 0.0


def _breaker_allows_yahoo() -> bool:
    global _yahoo_state
    if _yahoo_state == "CLOSED":
        return True
    if time.monotonic() >= _yahoo_open_until:
        _yahoo_state = "HALF_OPEN"
        return True
    return False


async def fetch_alternative_candles(symbol: str, timeframe: str) -> dict[str, Any] | None:
    name = alternative_provider_name()
    if not name:
        return None
    return None


async def _hydrate_persistent() -> None:
    global _hydrated
    if _hydrated:
        return
    _hydrated = True
    for sym, res, tier in (
        ("EUR/USD", "1m", "real"),
        ("EUR/USD", "1m", "degraded"),
        ("EUR/USD", "1H", "real"),
        ("EUR/USD", "1D", "real"),
        ("DXY", "1H", "real"),
        ("DXY", "15m", "real"),
    ):
        payload = await load_last_good(sym, res, tier)
        if payload and payload.get("bars"):
            key = _key(sym, res)
            if tier == "degraded" and _candle_last_good.get(key):
                continue
            warmed = {
                **payload,
                "cache": "persistent",
                "source_status": "cached",
                "stale": True,
                "status": "delayed",
                "message": "CACHED",
            }
            _candle_last_good[key] = {"payload": warmed, "stored_at": time.monotonic()}
            _candle_ttl[key] = {"payload": warmed, "expires_at": time.monotonic() + _ttl_for(res)}


def _display_pack(
    *,
    symbol: str,
    tf: str,
    bars: list[dict[str, Any]],
    base_resolution: str,
    aggregated: bool,
    source: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    last = bars[-1] if bars else {}
    quality = ohlc_range_stats(bars, 120 if tf == "1m" else 200) if bars else None
    aggregation = f"{base_resolution} -> aggregated {tf}" if aggregated else None
    pack = _with_meta(
        {
            "symbol": symbol,
            "timeframe": tf,
            "requested_timeframe": tf,
            "displayed_timeframe": tf,
            "base_resolution": base_resolution,
            "source_resolution": base_resolution,
            "aggregated": aggregated,
            "aggregation": aggregation,
            "supported_timeframes": list(DXY_SUPPORTED_TIMEFRAMES if symbol == "DXY" else SUPPORTED_TIMEFRAMES),
            "provider": "yahoo",
            "provider_symbol": YAHOO_SYMBOLS.get(symbol),
            "chart_engine": "lightweight_charts",
            "status": "connected" if bars else "insufficient_data",
            "source_status": "live",
            "stale": False,
            "cache": "miss",
            "message": "OK" if bars else "Нет баров",
            "bars": bars,
            "source": source,
            "fetched_at": _now_iso(),
            "last_close": last.get("c"),
            "last_bar_at": last.get("t") or last.get("time"),
            "quality": quality,
            "data_quality": (quality or {}).get("data_quality"),
            **(extra or {}),
        }
    )
    if quality:
        pack["zero_range_bars"] = quality["zero_range_bars"]
        pack["near_zero_range_bars"] = quality["near_zero_range_bars"]
        pack["unique_close_values"] = quality["unique_close_values"]
        pack["min_range"] = quality["min_range"]
        pack["median_range"] = quality["median_range"]
        pack["max_range"] = quality["max_range"]
        pack["visible_non_zero_range_bars"] = quality["visible_non_zero_range_bars"]
    return pack


async def _fetch_yahoo_raw(symbol: str, interval: str, range_: str, tf: str) -> dict[str, Any]:
    global _yahoo_upstream_calls, _yahoo_lock
    yahoo = YAHOO_SYMBOLS.get(symbol)
    if not yahoo:
        raise RuntimeError(f"no yahoo symbol for {symbol}")
    if _yahoo_lock is None:
        _yahoo_lock = asyncio.Lock()
    async with _yahoo_lock:
        if not _breaker_allows_yahoo():
            raise YahooHttpError(429, str(max(1, int(_yahoo_open_until - time.monotonic()))))
        _yahoo_upstream_calls += 1
        result = await yahoo_feed.fetch_yahoo_chart(yahoo, interval=interval, range_=range_)
        _close_breaker()
    bars = yahoo_feed.normalize_yahoo_bars(result, timeframe=tf, instrument=symbol)
    canon = normalize_canonical_bars(
        bars,
        instrument=symbol,
        source=f"Yahoo Finance ({yahoo})",
        source_resolution=detect_source_resolution(bars) if bars else interval,
    )
    if not canon:
        raise RuntimeError("Yahoo empty bars")
    resolution = detect_source_resolution(canon)
    for b in canon:
        b["source_resolution"] = resolution
        b["source"] = f"Yahoo Finance ({yahoo})"
    return _display_pack(
        symbol=symbol,
        tf=tf,
        bars=canon,
        base_resolution=resolution,
        aggregated=False,
        source=f"Yahoo Finance ({yahoo})",
        extra={"yahoo_interval": interval, "yahoo_range": range_},
    )


async def _yahoo_or_last_good(symbol: str, tf: str, interval: str, range_: str) -> dict[str, Any]:
    key = _key(symbol, tf)

    async def _run() -> dict[str, Any]:
        try:
            alt = await fetch_alternative_candles(symbol, tf)
            pack = alt if alt and alt.get("bars") else await _fetch_yahoo_raw(symbol, interval, range_, tf)
        except YahooHttpError as exc:
            if _yahoo_state == "OPEN" and time.monotonic() < _yahoo_open_until:
                wait = max(1.0, _yahoo_open_until - time.monotonic())
            else:
                wait = _open_breaker(exc.retry_after)
            cached = _from_last_good(key, source_status="rate_limited", message="RATE LIMITED — showing last received data")
            if cached:
                cached["retry_after_sec"] = wait
                return cached
            persisted = (
                memory_get(symbol, tf, "real")
                or memory_get(symbol, tf, "degraded")
                or await load_last_good(symbol, tf, "real")
                or await load_last_good(symbol, tf, "degraded")
            )
            if persisted and persisted.get("bars"):
                return _with_meta(
                    persisted,
                    stale=True,
                    cache="persistent",
                    source_status="rate_limited",
                    status="delayed",
                    message="RATE LIMITED — showing last received data",
                    retry_after_sec=wait,
                )
            return _with_meta(
                {
                    "symbol": symbol,
                    "timeframe": tf,
                    "requested_timeframe": tf,
                    "provider": "yahoo",
                    "status": "rate_limited",
                    "source_status": "rate_limited",
                    "stale": True,
                    "bars": [],
                    "retry_after_sec": wait,
                    "message": f"Источник временно ограничил запросы (Yahoo HTTP {exc.status})",
                }
            )
        except Exception as exc:
            cached = _from_last_good(key, source_status="error", message="Обновление источника…")
            if cached:
                return cached
            return _with_meta(
                {
                    "symbol": symbol,
                    "timeframe": tf,
                    "requested_timeframe": tf,
                    "provider": "yahoo",
                    "status": "error",
                    "source_status": "error",
                    "bars": [],
                    "message": f"Бары недоступны: {exc}",
                }
            )
        if pack.get("bars"):
            score = score_ohlc(list(pack["bars"]), last_n=120 if tf == "1m" else 200)
            pack["data_quality"] = score["grade"]
            pack["display_mode"] = "CANDLES" if score["grade"] == "HEALTHY" else ("DEGRADED_LINE" if tf == "1m" else "CANDLES")
            pack["history_kind"] = score["history_kind"]
            pack["real_wick_bars"] = score["real_wick_bars"]
            pack["real_body_bars"] = score["real_body_bars"]
            pack["zero_range_ratio"] = score["zero_range_ratio"]
            _remember(key, pack, tf)
            tier = "real" if score["grade"] == "HEALTHY" else "degraded"
            asyncio.create_task(save_last_good(symbol, tf, pack, tier=tier))
            return pack
        cached = _from_last_good(key, source_status="insufficient_data", message="Обновление источника…")
        return cached or pack

    return await _coalesce(key, _run)


def _ttl_hit(key: str) -> dict[str, Any] | None:
    hit = _candle_ttl.get(key)
    if hit and time.monotonic() < float(hit["expires_at"]):
        payload = dict(hit["payload"])
        cached = str(payload.get("cache") or "")
        cache = cached if cached in {"persistent", "last_good"} else "ttl"
        return _with_meta(
            payload,
            cache=cache,
            stale=bool(payload.get("stale")) or cache in {"persistent", "last_good"},
            source_status=payload.get("source_status") or ("cached" if cache != "ttl" else "live"),
            provider_state=_yahoo_state,
        )
    return None


async def _base_eurusd_1m() -> dict[str, Any]:
    key = _key("EUR/USD", "1m")
    hit = _ttl_hit(key)
    if hit:
        return hit

    async def yahoo_factory() -> dict[str, Any]:
        try:
            return await _fetch_yahoo_raw("EUR/USD", "1m", "1d", "1m")
        except YahooHttpError as exc:
            if _yahoo_state == "OPEN" and time.monotonic() < _yahoo_open_until:
                wait = max(1.0, _yahoo_open_until - time.monotonic())
            else:
                wait = _open_breaker(exc.retry_after)
            return _with_meta(
                {
                    "symbol": "EUR/USD",
                    "timeframe": "1m",
                    "requested_timeframe": "1m",
                    "provider": "yahoo",
                    "status": "rate_limited",
                    "source_status": "rate_limited",
                    "stale": True,
                    "bars": [],
                    "retry_after_sec": wait,
                    "message": f"Источник временно ограничил запросы (Yahoo HTTP {exc.status})",
                }
            )
        except Exception as exc:
            return _with_meta(
                {
                    "symbol": "EUR/USD",
                    "timeframe": "1m",
                    "provider": "yahoo",
                    "status": "error",
                    "source_status": "error",
                    "bars": [],
                    "message": str(exc),
                }
            )

    pack = await resolve_eurusd_1m(pack_factory=_display_pack, yahoo_factory=yahoo_factory)
    pack["live_quote_provider"] = pack.get("live_quote_provider") or "yahoo"
    pack["provider_health"] = provider_health_snapshot()
    if pack.get("bars"):
        _remember(key, pack, "1m")
        tier = "real" if pack.get("display_mode") == "CANDLES" and pack.get("data_quality") == "HEALTHY" else "degraded"
        asyncio.create_task(save_last_good("EUR/USD", "1m", pack, tier=tier))
    return pack


async def _base_eurusd_1h() -> dict[str, Any]:
    key = _key("EUR/USD", "1H")
    hit = _ttl_hit(key)
    if hit:
        return hit
    return await _yahoo_or_last_good("EUR/USD", "1H", "60m", "30d")


async def _base_eurusd_1d() -> dict[str, Any]:
    key = _key("EUR/USD", "1D")
    hit = _ttl_hit(key)
    if hit:
        return hit
    return await _yahoo_or_last_good("EUR/USD", "1D", "1d", "2y")


async def _base_dxy_1h() -> dict[str, Any]:
    key = _key("DXY", "1H")
    hit = _ttl_hit(key)
    if hit:
        return hit
    return await _yahoo_or_last_good("DXY", "1H", "60m", "30d")


async def _base_dxy_15m() -> dict[str, Any]:
    key = _key("DXY", "15m")
    hit = _ttl_hit(key)
    if hit:
        return hit
    return await _yahoo_or_last_good("DXY", "15m", "15m", "5d")


def _derived_from(
    base: dict[str, Any],
    *,
    symbol: str,
    tf: str,
    base_resolution: str,
) -> dict[str, Any]:
    bars = aggregate_bars(
        list(base.get("bars") or []),
        tf,
        instrument=symbol,
        source=str(base.get("source") or "yahoo"),
        source_resolution=base_resolution,
    )
    pack = _display_pack(
        symbol=symbol,
        tf=tf,
        bars=bars,
        base_resolution=base_resolution,
        aggregated=True,
        source=str(base.get("source") or "yahoo"),
        extra={
            "cache": base.get("cache") or "derived",
            "stale": bool(base.get("stale")),
            "source_status": base.get("source_status") or "live",
            "status": "connected" if bars else base.get("status") or "insufficient_data",
            "message": "OK" if bars else str(base.get("message") or "Нет баров для агрегации"),
        },
    )
    if bars:
        score = score_ohlc(bars, last_n=120 if tf == "1m" else 200)
        pack["data_quality"] = score["grade"]
        pack["display_mode"] = "CANDLES" if score["grade"] == "HEALTHY" else ("DEGRADED_LINE" if tf == "1m" else "CANDLES")
        pack["history_kind"] = "real_ohlc" if score["grade"] == "HEALTHY" else score["history_kind"]
        pack["real_wick_bars"] = score["real_wick_bars"]
        pack["real_body_bars"] = score["real_body_bars"]
        pack["zero_range_ratio"] = score["zero_range_ratio"]
        if score["grade"] == "HEALTHY":
            pack["message"] = "OK" if bars else pack.get("message")
        _remember(_key(symbol, tf), pack, tf)
    elif base.get("status") in {"rate_limited", "delayed"}:
        pack["status"] = "rate_limited"
        pack["source_status"] = "rate_limited"
        pack["stale"] = True
    return pack


def _unavailable_dxy_intraday(tf: str) -> dict[str, Any]:
    return _with_meta(
        {
            "symbol": "DXY",
            "timeframe": tf,
            "requested_timeframe": tf,
            "displayed_timeframe": tf,
            "base_resolution": "60m",
            "source_resolution": "60m",
            "aggregated": False,
            "status": "unavailable",
            "source_status": "UNAVAILABLE_AT_SOURCE_RESOLUTION",
            "chart_ready": False,
            "bars": [],
            "provider": "yahoo",
            "provider_symbol": YAHOO_SYMBOLS.get("DXY"),
            "message": "UNAVAILABLE_AT_SOURCE_RESOLUTION: Yahoo DX-Y.NYB has no true 1m/5m",
            "DXY_SOURCE_UNAVAILABLE": "yes",
            "supported_timeframes": list(DXY_SUPPORTED_TIMEFRAMES),
        }
    )


async def get_candles(symbol: str, timeframe: str = "1H") -> dict[str, Any]:
    await _hydrate_persistent()
    sym = normalize_symbol(symbol)
    tf = normalize_timeframe(timeframe, instrument=sym)

    if sym == "DXY" and tf in {"1m", "5m"}:
        return _unavailable_dxy_intraday(tf)

    key = _key(sym, tf)
    hit = _ttl_hit(key)
    if hit and tf not in {"5m", "15m", "4H", "1W"}:
        return hit

    if sym == "EUR/USD":
        if tf == "1m":
            return await _base_eurusd_1m()
        if tf == "5m":
            one = await _base_eurusd_1m()
            if one.get("bars"):
                return _derived_from(one, symbol=sym, tf="5m", base_resolution=str(one.get("source_resolution") or "1m"))
            return await _yahoo_or_last_good(sym, "5m", "5m", "5d")
        if tf == "15m":
            one = await _base_eurusd_1m()
            if one.get("bars"):
                return _derived_from(one, symbol=sym, tf="15m", base_resolution=str(one.get("source_resolution") or "1m"))
            five = await _yahoo_or_last_good(sym, "5m", "5m", "5d")
            return _derived_from(five, symbol=sym, tf="15m", base_resolution="5m")
        if tf == "1H":
            return await _base_eurusd_1h()
        if tf == "4H":
            hourly = await _base_eurusd_1h()
            return _derived_from(hourly, symbol=sym, tf="4H", base_resolution=str(hourly.get("source_resolution") or "60m"))
        if tf == "1D":
            hourly = await _base_eurusd_1h()
            daily = _derived_from(hourly, symbol=sym, tf="1D", base_resolution=str(hourly.get("source_resolution") or "60m"))
            if (daily.get("bar_count") or 0) >= 20:
                return daily
            return await _base_eurusd_1d()
        if tf == "1W":
            daily = await get_candles(sym, "1D")
            return _derived_from(daily, symbol=sym, tf="1W", base_resolution=str(daily.get("base_resolution") or daily.get("source_resolution") or "1d"))

    if sym == "DXY":
        if tf == "15m":
            return await _base_dxy_15m()
        if tf == "1H":
            return await _base_dxy_1h()
        if tf == "4H":
            hourly = await _base_dxy_1h()
            return _derived_from(hourly, symbol=sym, tf="4H", base_resolution=str(hourly.get("source_resolution") or "60m"))
        if tf == "1D":
            hourly = await _base_dxy_1h()
            return _derived_from(hourly, symbol=sym, tf="1D", base_resolution=str(hourly.get("source_resolution") or "60m"))
        if tf == "1W":
            daily = await get_candles(sym, "1D")
            return _derived_from(daily, symbol=sym, tf="1W", base_resolution=str(daily.get("source_resolution") or "1d"))

    return await _yahoo_or_last_good(sym, tf, "60m", "10d")


async def cached_quote(symbol: str, factory: Callable[[], Awaitable[dict[str, Any]]]) -> dict[str, Any]:
    key = _key(symbol)
    now = time.monotonic()
    hit = _quote_ttl.get(key)
    if hit and now < float(hit["expires_at"]):
        q = dict(hit["payload"])
        q["cache"] = "ttl"
        q["provider_state"] = _yahoo_state
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
            q["provider_state"] = _yahoo_state
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
