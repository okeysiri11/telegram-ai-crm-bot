"""FX OHLC quality scoring. Never upgrades quote-only bars to HEALTHY."""

from __future__ import annotations

import time
from typing import Any

from services.fx_market_intel.bars import bar_unix


def _px(bar: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        raw = bar.get(key)
        if raw is None:
            continue
        try:
            n = float(raw)
        except (TypeError, ValueError):
            continue
        return n
    return None


def score_ohlc(bars: list[dict[str, Any]], *, last_n: int = 120, now: float | None = None) -> dict[str, Any]:
    sample = bars[-last_n:] if last_n > 0 else list(bars)
    valid = 0
    zero_range = 0
    non_zero = 0
    duplicate_times = 0
    invalid_ohlc = 0
    timestamp_errors = 0
    real_wick = 0
    real_body = 0
    seen: set[int] = set()
    last_ts = 0
    last_bar_ts = 0
    for b in sample:
        unix = bar_unix(b) or 0
        o = _px(b, "o", "open")
        h = _px(b, "h", "high")
        l = _px(b, "l", "low")
        c = _px(b, "c", "close")
        if unix <= 0:
            timestamp_errors += 1
            invalid_ohlc += 1
            continue
        if unix in seen:
            duplicate_times += 1
        seen.add(unix)
        if last_ts and unix < last_ts:
            timestamp_errors += 1
        last_ts = unix
        last_bar_ts = unix
        if o is None or h is None or l is None or c is None:
            invalid_ohlc += 1
            continue
        if h < l or h < max(o, c) or l > min(o, c):
            invalid_ohlc += 1
            continue
        valid += 1
        if h - l <= 0:
            zero_range += 1
        else:
            non_zero += 1
        if abs(c - o) > 1e-12:
            real_body += 1
        if h > max(o, c) + 1e-12 or l < min(o, c) - 1e-12:
            real_wick += 1
    n = len(sample)
    valid_ratio = (valid / n) if n else 0.0
    zero_ratio = (zero_range / valid) if valid else 1.0
    freshness = None
    if last_bar_ts:
        freshness = max(0.0, (now if now is not None else time.time()) - last_bar_ts)
    if n == 0 or valid == 0:
        grade = "FAILED"
    elif timestamp_errors > 0 and timestamp_errors >= max(1, n // 10):
        grade = "FAILED"
    elif valid_ratio < 0.95:
        grade = "DEGRADED"
    elif zero_ratio >= 0.80:
        grade = "DEGRADED"
    elif n >= 60 and (real_body <= 10 or real_wick <= 5):
        grade = "DEGRADED"
    else:
        grade = "HEALTHY"
    display_mode = "CANDLES" if grade == "HEALTHY" else "DEGRADED_LINE"
    history_kind = "real_ohlc" if grade == "HEALTHY" else "quote_only"
    return {
        "bars": n,
        "valid_bars": valid,
        "zero_range_bars": zero_range,
        "non_zero_range_bars": non_zero,
        "duplicate_times": duplicate_times,
        "invalid_ohlc": invalid_ohlc,
        "timestamp_errors": timestamp_errors,
        "freshness_seconds": freshness,
        "zero_range_ratio": zero_ratio,
        "real_wick_bars": real_wick,
        "real_body_bars": real_body,
        "grade": grade,
        "data_quality": grade,
        "display_mode": display_mode,
        "history_kind": history_kind,
    }
