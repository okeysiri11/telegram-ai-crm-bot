"""Sprint 50.16 — real EURUSD 1m OHLC via provider router; Yahoo quote-only is DEGRADED_LINE."""

from __future__ import annotations

import lzma
import struct
from datetime import datetime, timezone

import pytest

from services.fx_market_intel.candle_feed import get_candles, reset_fx_market_cache
from services.fx_market_intel.dukascopy_feed import decode_bi5_ticks, ticks_to_1m_bars
from services.fx_market_intel.last_good_store import memory_get, memory_put, save_last_good
from services.fx_market_intel.provider_router import reset_provider_health, resolve_eurusd_1m
from services.fx_market_intel.quality import score_ohlc


def _flat_bars(n: int = 120, start: int = 1_700_000_000) -> list[dict]:
    bars = []
    for i in range(n):
        px = 1.161
        t = start + i * 60
        bars.append({"time": t, "open": px, "high": px, "low": px, "close": px, "o": px, "h": px, "l": px, "c": px, "t": datetime.fromtimestamp(t, tz=timezone.utc).isoformat()})
    return bars


async def _no_keyed():
    return None


def _real_bars(n: int = 120, start: int = 1_700_000_000) -> list[dict]:
    bars = []
    for i in range(n):
        o = 1.1600 + (i % 7) * 0.00005
        c = o + 0.00012
        h = max(o, c) + 0.00008
        l = min(o, c) - 0.00006
        t = start + i * 60
        bars.append({"time": t, "open": o, "high": h, "low": l, "close": c, "o": o, "h": h, "l": l, "c": c, "t": datetime.fromtimestamp(t, tz=timezone.utc).isoformat()})
    return bars


@pytest.fixture(autouse=True)
def _reset():
    reset_fx_market_cache()
    reset_provider_health()
    yield
    reset_fx_market_cache()
    reset_provider_health()


def test_yahoo_flat_1m_is_degraded_not_healthy():
    score = score_ohlc(_flat_bars(120), last_n=120)
    assert score["grade"] == "DEGRADED"
    assert score["zero_range_ratio"] >= 0.80
    assert score["display_mode"] == "DEGRADED_LINE"
    assert score["real_body_bars"] == 0
    assert score["real_wick_bars"] == 0


def test_real_ohlc_is_healthy_with_wicks_and_bodies():
    score = score_ohlc(_real_bars(120), last_n=120)
    assert score["grade"] == "HEALTHY"
    assert score["real_body_bars"] > 10
    assert score["real_wick_bars"] > 5
    assert score["zero_range_ratio"] < 0.80
    assert score["display_mode"] == "CANDLES"


def test_dukascopy_ticks_aggregate_true_ohlc():
    hour = datetime(2026, 9, 3, 9, tzinfo=timezone.utc)
    ticks = []
    for i in range(60):
        ts = hour.timestamp() + i * 0.25
        ticks.append((ts, 1.1600 + i * 0.000001, 1.1601 + i * 0.000001))
    # synthesize bi5 for first 4 ticks then decode
    payload = b""
    for i in range(8):
        tms = i * 1000
        bid_i = int(round((1.1600 + i * 0.00001) * 100000))
        ask_i = bid_i + 1
        payload += struct.pack(">IIIff", tms, ask_i, bid_i, 1.0, 1.0)
    raw = lzma.compress(payload)
    decoded = decode_bi5_ticks(raw, hour)
    assert len(decoded) == 8
    bars = ticks_to_1m_bars(decoded, source="Dukascopy (EURUSD ticks)")
    assert bars
    b = bars[0]
    assert b["h"] >= max(b["o"], b["c"])
    assert b["l"] <= min(b["o"], b["c"])
    assert b["h"] > b["l"]


@pytest.mark.asyncio
async def test_router_prefers_healthy_dukascopy_over_flat_yahoo():
    async def duka():
        return _real_bars(90)

    async def yahoo():
        return {"bars": _flat_bars(90), "provider": "yahoo", "timeframe": "1m"}

    def factory(**kwargs):
        return {"bars": kwargs["bars"], "timeframe": "1m", "symbol": "EUR/USD", **kwargs}

    pack = await resolve_eurusd_1m(pack_factory=factory, yahoo_factory=yahoo, dukascopy_factory=duka, keyed_factory=_no_keyed)
    assert pack["display_mode"] == "CANDLES"
    assert pack["data_quality"] == "HEALTHY"
    assert pack["provider"] == "dukascopy"
    assert pack["real_body_bars"] > 10


@pytest.mark.asyncio
async def test_router_uses_degraded_line_when_only_yahoo_flat():
    async def duka():
        return []

    async def yahoo():
        return {"bars": _flat_bars(90), "provider": "yahoo", "timeframe": "1m", "source_status": "live"}

    def factory(**kwargs):
        return {"bars": kwargs["bars"], "timeframe": "1m", "symbol": "EUR/USD", **kwargs}

    pack = await resolve_eurusd_1m(pack_factory=factory, yahoo_factory=yahoo, dukascopy_factory=duka, keyed_factory=_no_keyed)
    assert pack["display_mode"] == "DEGRADED_LINE"
    assert pack["data_quality"] == "DEGRADED"
    assert "OHLC" in str(pack.get("degraded_reason") or "")


@pytest.mark.asyncio
async def test_degraded_does_not_overwrite_real_last_good():
    real = {"bars": _real_bars(40), "data_quality": "HEALTHY", "display_mode": "CANDLES", "provider": "dukascopy"}
    memory_put("EUR/USD", "1m", real, tier="real")
    await save_last_good("EUR/USD", "1m", {"bars": _flat_bars(40), "data_quality": "DEGRADED", "provider": "yahoo"}, tier="degraded")
    kept = memory_get("EUR/USD", "1m", "real")
    assert kept and kept["bars"]
    assert float(kept["bars"][0]["h"]) > float(kept["bars"][0]["l"])


@pytest.mark.asyncio
async def test_get_candles_1m_uses_router_not_yahoo_when_dukascopy_healthy(monkeypatch):
    from services.fx_market_intel import provider_router as pr

    async def duka(*_a, **_k):
        return _real_bars(80)

    async def boom(*_a, **_k):
        raise AssertionError("yahoo 1m must not run when dukascopy is HEALTHY")

    monkeypatch.setattr(pr, "dukascopy_eurusd_1m", duka)
    monkeypatch.setattr("services.fx_market_intel.yahoo_feed.fetch_yahoo_chart", boom)
    pack = await get_candles("EUR/USD", "1m")
    assert pack["display_mode"] == "CANDLES"
    assert pack["data_quality"] == "HEALTHY"
    assert pack["bar_count"] >= 60
    assert pack["real_body_bars"] > 10
    assert pack["real_wick_bars"] > 5
    assert pack["zero_range_ratio"] < 0.80
    assert pack.get("provider_health")


@pytest.mark.asyncio
async def test_dxy_1m_unavailable_flag_not_fabricated():
    pack = await get_candles("DXY", "1m")
    assert pack["source_status"] == "UNAVAILABLE_AT_SOURCE_RESOLUTION"
    assert pack["DXY_SOURCE_UNAVAILABLE"] == "yes"
    assert pack["bars"] == []

