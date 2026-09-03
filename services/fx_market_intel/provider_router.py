"""FX provider router: real OHLC first, Yahoo quote-only last, never overwrite real last-good."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Callable, Awaitable

from services.fx_market_intel.dukascopy_feed import fetch_eurusd_1m as dukascopy_eurusd_1m
from services.fx_market_intel.keyed_feeds import configured_keyed_provider, fetch_keyed_eurusd_1m
from services.fx_market_intel.last_good_store import load_last_good
from services.fx_market_intel.quality import score_ohlc

_health: dict[str, dict[str, Any]] = {}


def reset_provider_health() -> None:
    _health.clear()


def provider_health_snapshot() -> dict[str, dict[str, Any]]:
    return {k: dict(v) for k, v in _health.items()}


def record_health(name: str, **fields: Any) -> None:
    row = _health.get(name) or {"name": name}
    row.update(fields)
    row["updated_at"] = datetime.now(timezone.utc).isoformat()
    _health[name] = row


def _annotate(pack: dict[str, Any], score: dict[str, Any], *, provider: str, history_source: str) -> dict[str, Any]:
    out = dict(pack)
    out["quality"] = {**(out.get("quality") or {}), **score}
    out["data_quality"] = score["grade"]
    out["display_mode"] = score["display_mode"] if score["grade"] != "HEALTHY" else "CANDLES"
    if score["grade"] == "HEALTHY":
        out["display_mode"] = "CANDLES"
        out["history_kind"] = "real_ohlc"
    else:
        out["display_mode"] = "DEGRADED_LINE" if out.get("timeframe") in {"1m", "1M"} else "CANDLES"
        out["history_kind"] = score["history_kind"]
    out["provider"] = provider
    out["history_provider"] = history_source
    out["zero_range_bars"] = score["zero_range_bars"]
    out["visible_non_zero_range_bars"] = score["non_zero_range_bars"]
    out["real_wick_bars"] = score["real_wick_bars"]
    out["real_body_bars"] = score["real_body_bars"]
    out["zero_range_ratio"] = score["zero_range_ratio"]
    out["provider_health"] = provider_health_snapshot()
    if score["grade"] == "DEGRADED":
        out["degraded_reason"] = "Источник дает только минутные ценовые точки без полного OHLC"
        out["message"] = out.get("degraded_reason")
    return out


async def resolve_eurusd_1m(
    *,
    pack_factory: Callable[..., dict[str, Any]],
    yahoo_factory: Callable[[], Awaitable[dict[str, Any]]],
    dukascopy_factory: Callable[[], Awaitable[list[dict[str, Any]]]] | None = None,
    keyed_factory: Callable[[], Awaitable[list[dict[str, Any]] | None]] | None = None,
) -> dict[str, Any]:
    """PRIMARY keyed → Dukascopy → real last-good → degraded Yahoo line."""
    fetch_duka = dukascopy_factory or dukascopy_eurusd_1m
    fetch_keyed = keyed_factory or fetch_keyed_eurusd_1m

    keyed_name = configured_keyed_provider()
    if keyed_name:
        t0 = time.monotonic()
        try:
            bars = await fetch_keyed()
            latency = int((time.monotonic() - t0) * 1000)
            if bars:
                score = score_ohlc(bars, last_n=120)
                record_health(keyed_name, state="HEALTHY" if score["grade"] == "HEALTHY" else "DEGRADED", quality=score["grade"], latency_ms=latency, last_success=datetime.now(timezone.utc).isoformat())
                if score["grade"] == "HEALTHY":
                    pack = pack_factory(symbol="EUR/USD", tf="1m", bars=bars, base_resolution="1m", aggregated=False, source=keyed_name)
                    return _annotate(pack, score, provider=keyed_name, history_source=keyed_name)
            else:
                record_health(keyed_name, state="FAILED", quality="FAILED", latency_ms=latency, last_failure="empty")
        except Exception as exc:
            record_health(keyed_name, state="FAILED", quality="FAILED", last_failure=str(exc)[:180])

    t0 = time.monotonic()
    try:
        duka_bars = await fetch_duka()
        latency = int((time.monotonic() - t0) * 1000)
        score = score_ohlc(duka_bars, last_n=120)
        record_health(
            "dukascopy",
            state="HEALTHY" if score["grade"] == "HEALTHY" else ("DEGRADED" if duka_bars else "FAILED"),
            quality=score["grade"],
            latency_ms=latency,
            last_success=datetime.now(timezone.utc).isoformat() if duka_bars else None,
            last_failure=None if duka_bars else "empty",
        )
        if score["grade"] == "HEALTHY":
            pack = pack_factory(symbol="EUR/USD", tf="1m", bars=duka_bars, base_resolution="1m", aggregated=False, source="Dukascopy (EURUSD ticks)")
            return _annotate(pack, score, provider="dukascopy", history_source="dukascopy")
    except Exception as exc:
        record_health("dukascopy", state="FAILED", quality="FAILED", last_failure=str(exc)[:180])

    real = await load_last_good("EUR/USD", "1m", "real")
    if real and real.get("bars"):
        score = score_ohlc(list(real["bars"]), last_n=120)
        if score["grade"] == "HEALTHY":
            out = dict(real)
            out["cache"] = "persistent"
            out["stale"] = True
            out["source_status"] = "cached"
            return _annotate(out, score, provider=str(out.get("provider") or "dukascopy"), history_source=str(out.get("history_provider") or out.get("provider") or "real_last_good"))

    t0 = time.monotonic()
    yahoo = await yahoo_factory()
    latency = int((time.monotonic() - t0) * 1000)
    bars = list(yahoo.get("bars") or [])
    score = score_ohlc(bars, last_n=120)
    record_health(
        "yahoo",
        state="OPEN" if str(yahoo.get("source_status") or "") == "rate_limited" else ("DEGRADED" if bars else "FAILED"),
        quality=score["grade"],
        latency_ms=latency,
        http_status=429 if str(yahoo.get("source_status") or "") == "rate_limited" else 200,
        last_failure=yahoo.get("message") if score["grade"] != "HEALTHY" else None,
    )
    annotated = _annotate(yahoo, score, provider="yahoo", history_source="yahoo")
    annotated["live_quote_provider"] = "yahoo"
    if score["grade"] != "HEALTHY":
        annotated["display_mode"] = "DEGRADED_LINE"
        annotated["history_kind"] = "quote_only"
        annotated["degraded_reason"] = "Источник дает только минутные ценовые точки без полного OHLC"
    return annotated
