"""Optional authenticated FX candle adapters. Never invent API keys."""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Any

import aiohttp

from services.fx_market_intel.bars import canonical_bar, normalize_canonical_bars


def configured_keyed_provider() -> str | None:
    name = (os.environ.get("FX_CANDLE_PROVIDER") or "").strip().lower()
    if name in {"twelvedata", "twelve_data", "twelve"} or (os.environ.get("TWELVEDATA_API_KEY") or os.environ.get("TWELVE_DATA_API_KEY") or "").strip():
        if (os.environ.get("TWELVEDATA_API_KEY") or os.environ.get("TWELVE_DATA_API_KEY") or "").strip():
            return "twelvedata"
    if name in {"finnhub"} or (os.environ.get("FINNHUB_API_KEY") or "").strip():
        if (os.environ.get("FINNHUB_API_KEY") or "").strip():
            return "finnhub"
    if name in {"polygon"} or (os.environ.get("POLYGON_API_KEY") or "").strip():
        if (os.environ.get("POLYGON_API_KEY") or "").strip():
            return "polygon"
    return None


def _key_present(name: str) -> bool:
    if name == "twelvedata":
        return bool((os.environ.get("TWELVEDATA_API_KEY") or os.environ.get("TWELVE_DATA_API_KEY") or "").strip())
    if name == "finnhub":
        return bool((os.environ.get("FINNHUB_API_KEY") or "").strip())
    if name == "polygon":
        return bool((os.environ.get("POLYGON_API_KEY") or "").strip())
    return False


def _twelve_key() -> str:
    return (os.environ.get("TWELVEDATA_API_KEY") or os.environ.get("TWELVE_DATA_API_KEY") or "").strip()


def _to_bars(rows: list[dict[str, Any]], *, source: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for raw in rows:
        unix = raw.get("time")
        if unix is None:
            continue
        bar = canonical_bar(
            time=int(unix),
            open_=float(raw["open"]),
            high=float(raw["high"]),
            low=float(raw["low"]),
            close=float(raw["close"]),
            volume=float(raw["volume"]) if raw.get("volume") is not None else None,
            source=source,
            source_resolution="1m",
            instrument="EUR/USD",
        )
        if bar:
            out.append(bar)
    return normalize_canonical_bars(out, instrument="EUR/USD", source=source, source_resolution="1m")


async def fetch_keyed_eurusd_1m() -> list[dict[str, Any]] | None:
    name = configured_keyed_provider()
    if not name or not _key_present(name):
        return None
    if name == "twelvedata":
        return await _twelvedata_1m()
    if name == "finnhub":
        return await _finnhub_1m()
    if name == "polygon":
        return await _polygon_1m()
    return None


async def _twelvedata_1m() -> list[dict[str, Any]]:
    key = _twelve_key()
    url = "https://api.twelvedata.com/time_series"
    params = {"symbol": "EUR/USD", "interval": "1min", "outputsize": "180", "apikey": key}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=20)) as resp:
            body = await resp.json(content_type=None)
    rows = []
    for item in body.get("values") or []:
        dt = datetime.fromisoformat(str(item.get("datetime")).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        rows.append(
            {
                "time": int(dt.timestamp()),
                "open": item.get("open"),
                "high": item.get("high"),
                "low": item.get("low"),
                "close": item.get("close"),
                "volume": item.get("volume"),
            }
        )
    rows.reverse()
    return _to_bars(rows, source="Twelve Data")


async def _finnhub_1m() -> list[dict[str, Any]]:
    token = (os.environ.get("FINNHUB_API_KEY") or "").strip()
    now = int(time.time())
    url = "https://finnhub.io/api/v1/forex/candle"
    params = {"symbol": "OANDA:EUR_USD", "resolution": "1", "from": now - 4 * 3600, "to": now, "token": token}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=20)) as resp:
            body = await resp.json(content_type=None)
    times = body.get("t") or []
    rows = []
    for i, ts in enumerate(times):
        rows.append(
            {
                "time": int(ts),
                "open": (body.get("o") or [None])[i] if i < len(body.get("o") or []) else None,
                "high": (body.get("h") or [None])[i] if i < len(body.get("h") or []) else None,
                "low": (body.get("l") or [None])[i] if i < len(body.get("l") or []) else None,
                "close": (body.get("c") or [None])[i] if i < len(body.get("c") or []) else None,
                "volume": (body.get("v") or [None])[i] if i < len(body.get("v") or []) else None,
            }
        )
    return _to_bars(rows, source="Finnhub")


async def _polygon_1m() -> list[dict[str, Any]]:
    token = (os.environ.get("POLYGON_API_KEY") or "").strip()
    now = int(time.time() * 1000)
    frm = now - 4 * 3600 * 1000
    url = f"https://api.polygon.io/v2/aggs/ticker/C:EURUSD/range/1/minute/{frm}/{now}"
    params = {"adjusted": "true", "sort": "asc", "limit": 180, "apiKey": token}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=20)) as resp:
            body = await resp.json(content_type=None)
    rows = []
    for item in body.get("results") or []:
        rows.append(
            {
                "time": int(item["t"] / 1000),
                "open": item.get("o"),
                "high": item.get("h"),
                "low": item.get("l"),
                "close": item.get("c"),
                "volume": item.get("v"),
            }
        )
    return _to_bars(rows, source="Polygon")
