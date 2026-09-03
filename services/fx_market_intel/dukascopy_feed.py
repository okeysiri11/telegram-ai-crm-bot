"""Dukascopy public tick datafeed → canonical EURUSD 1m OHLC.

This is a documented HTTP historical datafeed (not HTML scraping, not TradingView).
No API key. Ticks are aggregated with true OHLC: open=first, high=max, low=min, close=last.
"""

from __future__ import annotations

import asyncio
import logging
import lzma
import struct
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable

import aiohttp

from services.fx_market_intel.bars import canonical_bar, normalize_canonical_bars

logger = logging.getLogger(__name__)

DUKASCOPY_BASE = "https://datafeed.dukascopy.com/datafeed"
EURUSD_INSTRUMENT = "EURUSD"
PRICE_SCALE = 100_000.0
HEADERS = {"User-Agent": "ADOS-FX-Intel/50.16"}
HOUR_TIMEOUT_SEC = 12.0
OVERALL_TIMEOUT_SEC = 16.0

_FetchHour = Callable[[datetime], Awaitable[bytes | None]]


def dukascopy_hour_url(instrument: str, hour: datetime) -> str:
    h = hour.astimezone(timezone.utc)
    return f"{DUKASCOPY_BASE}/{instrument}/{h.year}/{h.month - 1:02d}/{h.day:02d}/{h.hour:02d}h_ticks.bi5"


def decode_bi5_ticks(raw: bytes, hour_start: datetime) -> list[tuple[float, float, float]]:
    if not raw:
        return []
    try:
        data = lzma.decompress(raw)
    except lzma.LZMAError:
        data = lzma.decompress(raw, format=lzma.FORMAT_ALONE)
    start = hour_start.astimezone(timezone.utc).timestamp()
    ticks: list[tuple[float, float, float]] = []
    for i in range(0, len(data) - 19, 20):
        tms, ask_i, bid_i, _ask_v, _bid_v = struct.unpack(">IIIff", data[i : i + 20])
        bid = bid_i / PRICE_SCALE
        ask = ask_i / PRICE_SCALE
        if bid <= 0 or ask <= 0:
            continue
        ticks.append((start + tms / 1000.0, bid, ask))
    return ticks


def ticks_to_1m_bars(ticks: list[tuple[float, float, float]], *, source: str) -> list[dict[str, Any]]:
    buckets: dict[int, dict[str, float]] = {}
    order: list[int] = []
    for ts, bid, ask in ticks:
        mid = (bid + ask) / 2.0
        key = int(ts) // 60 * 60
        cur = buckets.get(key)
        if cur is None:
            buckets[key] = {"o": mid, "h": mid, "l": mid, "c": mid}
            order.append(key)
        else:
            cur["h"] = max(cur["h"], mid)
            cur["l"] = min(cur["l"], mid)
            cur["c"] = mid
    bars: list[dict[str, Any]] = []
    for key in order:
        cur = buckets[key]
        bar = canonical_bar(
            time=key,
            open_=cur["o"],
            high=cur["h"],
            low=cur["l"],
            close=cur["c"],
            source=source,
            source_resolution="1m",
            instrument="EUR/USD",
        )
        if bar:
            bars.append(bar)
    return normalize_canonical_bars(bars, instrument="EUR/USD", source=source, source_resolution="1m")


async def fetch_hour_bytes(hour: datetime, *, session: aiohttp.ClientSession, instrument: str = EURUSD_INSTRUMENT) -> bytes | None:
    url = dukascopy_hour_url(instrument, hour)
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=HOUR_TIMEOUT_SEC)) as resp:
            if resp.status == 404:
                return None
            if resp.status >= 400:
                logger.warning("dukascopy HTTP %s for %s", resp.status, url)
                return None
            return await resp.read()
    except Exception:
        logger.warning("dukascopy hour fetch failed %s", url, exc_info=True)
        return None


def recent_hours(count: int, *, now: datetime | None = None) -> list[datetime]:
    current = (now or datetime.now(timezone.utc)).replace(minute=0, second=0, microsecond=0)
    # Current hour file is often unpublished or hangs; use completed hours only.
    last_complete = current - timedelta(hours=1)
    return [last_complete - timedelta(hours=i) for i in range(count - 1, -1, -1)]


async def fetch_eurusd_1m(
    *,
    hours: int = 3,
    now: datetime | None = None,
    fetch_hour: _FetchHour | None = None,
) -> list[dict[str, Any]]:
    source = "Dukascopy (EURUSD ticks)"
    hours_list = recent_hours(max(1, hours), now=now)

    async def _collect(fetch: _FetchHour) -> list[bytes | None]:
        tasks = [asyncio.create_task(fetch(h)) for h in hours_list]
        done, pending = await asyncio.wait(tasks, timeout=OVERALL_TIMEOUT_SEC)
        for task in pending:
            task.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)
        blobs: list[bytes | None] = [None] * len(hours_list)
        for i, task in enumerate(tasks):
            if task in done and not task.cancelled() and task.exception() is None:
                blobs[i] = task.result()
        return blobs

    if fetch_hour is None:
        async with aiohttp.ClientSession(headers=HEADERS) as session:

            async def _default(hour: datetime) -> bytes | None:
                return await fetch_hour_bytes(hour, session=session)

            blobs = await _collect(_default)
    else:
        blobs = await _collect(fetch_hour)
    ticks: list[tuple[float, float, float]] = []
    for hour, blob in zip(hours_list, blobs):
        if not blob:
            continue
        ticks.extend(decode_bi5_ticks(blob, hour))
    ticks.sort(key=lambda t: t[0])
    return ticks_to_1m_bars(ticks, source=source)
