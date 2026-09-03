"""Canonical FX bars and local timeframe aggregation. No synthetic empty buckets."""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Any

from services.fx_market_intel.yahoo_feed import valid_ohlc


def bar_unix(bar: dict[str, Any]) -> int | None:
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


def _px(value: Any) -> float | None:
    try:
        n = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(n):
        return None
    return n


def canonical_bar(
    *,
    time: int,
    open_: float,
    high: float,
    low: float,
    close: float,
    volume: float | None = None,
    source: str = "yahoo",
    source_resolution: str = "1m",
    instrument: str | None = None,
) -> dict[str, Any] | None:
    if not valid_ohlc(open_, high, low, close, instrument):
        return None
    iso = datetime.fromtimestamp(int(time), tz=timezone.utc).isoformat()
    return {
        "time": int(time),
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "t": iso,
        "o": open_,
        "h": high,
        "l": low,
        "c": close,
        "v": volume,
        "source": source,
        "source_resolution": source_resolution,
        "provider": source,
    }


def normalize_canonical_bars(
    bars: list[dict[str, Any]],
    *,
    instrument: str | None = None,
    source: str = "yahoo",
    source_resolution: str = "1m",
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for raw in bars:
        unix = bar_unix(raw)
        if unix is None:
            continue
        o = _px(raw.get("open", raw.get("o")))
        h = _px(raw.get("high", raw.get("h")))
        l = _px(raw.get("low", raw.get("l")))
        c = _px(raw.get("close", raw.get("c")))
        if o is None or h is None or l is None or c is None:
            continue
        bar = canonical_bar(
            time=unix,
            open_=o,
            high=h,
            low=l,
            close=c,
            volume=_px(raw.get("v") or raw.get("volume")),
            source=str(raw.get("source") or source),
            source_resolution=str(raw.get("source_resolution") or source_resolution),
            instrument=instrument,
        )
        if not bar:
            continue
        if out and out[-1]["time"] == bar["time"]:
            out[-1] = bar
            continue
        out.append(bar)
    out.sort(key=lambda b: int(b["time"]))
    deduped: list[dict[str, Any]] = []
    for b in out:
        if deduped and deduped[-1]["time"] == b["time"]:
            deduped[-1] = b
        elif deduped and deduped[-1]["time"] >= b["time"]:
            continue
        else:
            deduped.append(b)
    return deduped


def bucket_start_unix(ts: int, timeframe: str) -> int:
    t = int(ts)
    tf = timeframe.strip()
    if tf in {"5m", "5M"}:
        return (t // 300) * 300
    if tf in {"15m", "15M"}:
        return (t // 900) * 900
    if tf in {"1h", "1H"}:
        return (t // 3600) * 3600
    if tf in {"4h", "4H"}:
        return (t // 14400) * 14400
    if tf in {"1d", "1D"}:
        dt = datetime.fromtimestamp(t, tz=timezone.utc)
        return int(datetime(dt.year, dt.month, dt.day, tzinfo=timezone.utc).timestamp())
    if tf in {"1w", "1W"}:
        dt = datetime.fromtimestamp(t, tz=timezone.utc)
        monday = dt.date() - timedelta(days=dt.weekday())
        return int(datetime(monday.year, monday.month, monday.day, tzinfo=timezone.utc).timestamp())
    return (t // 60) * 60


def aggregate_bars(
    bars: list[dict[str, Any]],
    timeframe: str,
    *,
    instrument: str | None = None,
    source: str = "yahoo",
    source_resolution: str = "1m",
) -> list[dict[str, Any]]:
    """OHLC aggregate: open=first.open, high=max, low=min, close=last.close. Skip empty buckets."""
    ordered = normalize_canonical_bars(bars, instrument=instrument, source=source, source_resolution=source_resolution)
    buckets: dict[int, list[dict[str, Any]]] = {}
    order: list[int] = []
    for b in ordered:
        key = bucket_start_unix(int(b["time"]), timeframe)
        if key not in buckets:
            buckets[key] = []
            order.append(key)
        buckets[key].append(b)
    out: list[dict[str, Any]] = []
    for key in order:
        group = buckets[key]
        if not group:
            continue
        open_ = float(group[0]["open"])
        high = max(float(g["high"]) for g in group)
        low = min(float(g["low"]) for g in group)
        close = float(group[-1]["close"])
        vol_vals = [float(g["v"]) for g in group if g.get("v") is not None]
        bar = canonical_bar(
            time=key,
            open_=open_,
            high=high,
            low=low,
            close=close,
            volume=sum(vol_vals) if vol_vals else None,
            source=source,
            source_resolution=source_resolution,
            instrument=instrument,
        )
        if bar:
            bar["timeframe"] = timeframe if timeframe in {"1m", "5m", "15m"} else timeframe.upper().replace("1H", "1H")
            if timeframe in {"1h", "1H"}:
                bar["timeframe"] = "1H"
            elif timeframe in {"4h", "4H"}:
                bar["timeframe"] = "4H"
            elif timeframe in {"1d", "1D"}:
                bar["timeframe"] = "1D"
            elif timeframe in {"1w", "1W"}:
                bar["timeframe"] = "1W"
            elif timeframe in {"5m", "5M"}:
                bar["timeframe"] = "5m"
            elif timeframe in {"15m", "15M"}:
                bar["timeframe"] = "15m"
            out.append(bar)
    return out


def ohlc_range_stats(bars: list[dict[str, Any]], last_n: int = 200) -> dict[str, Any]:
    sample = bars[-last_n:] if last_n > 0 else bars
    ranges: list[float] = []
    bodies: list[float] = []
    closes: list[float] = []
    for b in sample:
        h = float(b.get("h") if b.get("h") is not None else b.get("high") or 0)
        l = float(b.get("l") if b.get("l") is not None else b.get("low") or 0)
        o = float(b.get("o") if b.get("o") is not None else b.get("open") or 0)
        c = float(b.get("c") if b.get("c") is not None else b.get("close") or 0)
        ranges.append(h - l)
        bodies.append(abs(c - o))
        closes.append(round(c, 5))
    if not ranges:
        return {
            "sample": 0,
            "zero_range_bars": 0,
            "near_zero_range_bars": 0,
            "unique_close_values": 0,
            "min_range": 0.0,
            "median_range": 0.0,
            "max_range": 0.0,
            "visible_non_zero_range_bars": 0,
            "data_quality": "DEGRADED",
        }
    ordered = sorted(ranges)
    mid = ordered[len(ordered) // 2]
    zero = sum(1 for r in ranges if r == 0)
    near = sum(1 for r in ranges if r < 1e-5)
    nonzero = sum(1 for r in ranges if r > 0)
    quality = "HEALTHY" if nonzero > 20 else "DEGRADED"
    return {
        "sample": len(ranges),
        "zero_range_bars": zero,
        "near_zero_range_bars": near,
        "unique_close_values": len(set(closes)),
        "min_range": ordered[0],
        "median_range": mid,
        "max_range": ordered[-1],
        "visible_non_zero_range_bars": nonzero,
        "data_quality": quality,
    }
