"""Sprint 50.15 — EURUSD chart stability v2: aggregation, breaker, persist, 1m quality."""

from __future__ import annotations

import asyncio

import pytest

from services.fx_market_intel.bars import aggregate_bars, ohlc_range_stats
from services.fx_market_intel.candle_feed import (
    get_candles,
    reset_fx_market_cache,
    yahoo_provider_state,
    yahoo_upstream_calls,
)
from services.fx_market_intel.last_good_store import memory_get, memory_put, persistent_backend_name
from services.fx_market_intel.yahoo_feed import YahooHttpError, normalize_yahoo_bars


def _chart(closes: list[float], *, step: int = 3600, start: int = 1_700_000_000, ranges: bool = True) -> dict:
    n = len(closes)
    pad = 0.0002 if ranges else 0.0
    return {
        "timestamp": [start + i * step for i in range(n)],
        "indicators": {
            "quote": [
                {
                    "open": [c - pad / 2 for c in closes],
                    "high": [c + pad for c in closes],
                    "low": [c - pad for c in closes],
                    "close": list(closes),
                    "volume": [0] * n,
                }
            ]
        },
    }


def _hourly(days: int = 25) -> dict:
    n = 24 * days
    closes = [1.16 + (i % 9) * 0.00015 for i in range(n)]
    return _chart(closes, step=3600, start=1_700_000_000)


def _minutes(count: int = 180) -> dict:
    closes = [1.161 + (i % 11) * 0.00012 for i in range(count)]
    return _chart(closes, step=60, start=1_700_000_000)


@pytest.fixture(autouse=True)
def _reset():
    reset_fx_market_cache()
    yield
    reset_fx_market_cache()


def test_quote_only_yahoo_rows_are_dropped():
    result = {
        "timestamp": [1_700_000_000, 1_700_000_060, 1_700_000_120],
        "indicators": {
            "quote": [
                {
                    "open": [None, 1.1610, 1.1612],
                    "high": [None, 1.1614, 1.1615],
                    "low": [None, 1.1608, 1.1610],
                    "close": [1.1610, 1.1611, 1.1613],
                    "volume": [0, 0, 0],
                }
            ]
        },
    }
    bars = normalize_yahoo_bars(result, timeframe="1m", instrument="EUR/USD")
    assert len(bars) == 2
    assert all(b["h"] > b["l"] for b in bars)


def test_aggregate_4h_from_hourly_not_relabel():
    hourly = []
    start = 1_700_006_400  # aligned-ish
    start = (start // 14400) * 14400
    for i in range(12):
        t = start + i * 3600
        o = 1.1600 + i * 0.0001
        hourly.append({"time": t, "open": o, "high": o + 0.0004, "low": o - 0.0002, "close": o + 0.0001, "source": "yahoo"})
    out = aggregate_bars(hourly, "4H", instrument="EUR/USD", source_resolution="60m")
    assert len(out) == 3
    assert all(int(b["time"]) % 14400 == 0 for b in out)
    first = out[0]
    assert first["open"] == hourly[0]["open"]
    assert first["close"] == hourly[3]["close"]
    assert first["high"] == max(b["high"] for b in hourly[:4])
    assert first["low"] == min(b["low"] for b in hourly[:4])


def test_aggregate_skips_empty_buckets_and_uses_true_ohlc():
    bars = [
        {"time": 1_700_000_000, "open": 1.16, "high": 1.162, "low": 1.159, "close": 1.161},
        {"time": 1_700_007_200, "open": 1.161, "high": 1.164, "low": 1.160, "close": 1.163},
    ]
    out = aggregate_bars(bars, "1H", instrument="EUR/USD")
    assert len(out) == 2
    assert out[0]["open"] == 1.16
    assert out[0]["close"] == 1.161


@pytest.mark.asyncio
async def test_eurusd_4h_is_aggregated_from_1h(monkeypatch):
    from services.fx_market_intel import yahoo_feed as yf

    async def fake(symbol_yahoo: str, *, interval: str, range_: str):
        assert interval == "60m"
        return _hourly(3)

    monkeypatch.setattr(yf, "fetch_yahoo_chart", fake)
    pack = await get_candles("EUR/USD", "4H")
    assert pack["aggregated"] is True
    assert pack["displayed_timeframe"] == "4H"
    assert pack["base_resolution"] == "60m"
    assert pack["aggregation"] == "60m -> aggregated 4H"
    times = [int(b["time"]) for b in pack["bars"]]
    assert times == sorted(times)
    assert len(times) > 1
    deltas = [times[i] - times[i - 1] for i in range(1, len(times))]
    assert min(deltas) >= 14400
    assert all(t % 14400 == 0 for t in times)


@pytest.mark.asyncio
async def test_upstream_requests_per_full_eurusd_tf_cycle(monkeypatch):
    from services.fx_market_intel import yahoo_feed as yf

    async def fake(symbol_yahoo: str, *, interval: str, range_: str):
        if interval == "1m":
            return _minutes(180)
        return _hourly(25)

    monkeypatch.setattr(yf, "fetch_yahoo_chart", fake)
    await get_candles("EUR/USD", "1m")
    await get_candles("EUR/USD", "1H")
    baseline = yahoo_upstream_calls()
    for tf in ("5m", "15m", "1H", "4H", "1D", "1W"):
        pack = await get_candles("EUR/USD", tf)
        assert pack["bars"], tf
        if tf == "4H":
            assert pack["aggregated"] is True
            assert pack["displayed_timeframe"] == "4H"
    extra = yahoo_upstream_calls() - baseline
    assert extra == 0
    assert yahoo_upstream_calls() <= 2
    assert baseline <= 2


@pytest.mark.asyncio
async def test_yahoo_circuit_breaker_opens_on_429(monkeypatch):
    from services.fx_market_intel import yahoo_feed as yf

    calls = {"n": 0}

    async def boom(symbol_yahoo: str, *, interval: str, range_: str):
        calls["n"] += 1
        raise YahooHttpError(429, "60")

    monkeypatch.setattr(yf, "fetch_yahoo_chart", boom)
    first = await get_candles("EUR/USD", "1H")
    assert yahoo_provider_state() == "OPEN"
    assert first["source_status"] in {"rate_limited", "error"}
    second = await get_candles("EUR/USD", "1H")
    third = await get_candles("EUR/USD", "4H")
    assert calls["n"] == 1
    assert yahoo_provider_state() == "OPEN"
    assert second.get("provider_state") == "OPEN"
    assert third.get("provider_state") == "OPEN"


@pytest.mark.asyncio
async def test_persistent_last_good_survives_process_cache_reset(monkeypatch):
    from services.fx_market_intel import yahoo_feed as yf

    async def ok(symbol_yahoo: str, *, interval: str, range_: str):
        return _hourly(2)

    monkeypatch.setattr(yf, "fetch_yahoo_chart", ok)
    live = await get_candles("EUR/USD", "1H")
    await asyncio.sleep(0.05)
    stored = memory_get("EUR/USD", "1H")
    if not stored:
        from services.fx_market_intel import candle_feed as cf

        stored = cf._candle_last_good["candle:EUR/USD:1H"]["payload"]
    assert stored and stored.get("bars")
    reset_fx_market_cache()
    memory_put("EUR/USD", "1H", stored)

    async def boom(symbol_yahoo: str, *, interval: str, range_: str):
        raise AssertionError("hydrated last-good must be served first")

    monkeypatch.setattr(yf, "fetch_yahoo_chart", boom)
    pack = await get_candles("EUR/USD", "1H")
    assert pack.get("bars")
    assert pack.get("bar_count") == live["bar_count"]
    assert pack.get("cache") == "persistent"
    assert persistent_backend_name() in {"redis", "memory"}


@pytest.mark.asyncio
async def test_1m_quality_stats_and_non_zero_ranges(monkeypatch):
    from services.fx_market_intel import yahoo_feed as yf

    async def fake(symbol_yahoo: str, *, interval: str, range_: str):
        return _minutes(180)

    monkeypatch.setattr(yf, "fetch_yahoo_chart", fake)
    pack = await get_candles("EUR/USD", "1m")
    sample = pack["bars"][-120:]
    stats = ohlc_range_stats(sample, 120)
    assert pack["bar_count"] >= 60
    assert stats["visible_non_zero_range_bars"] > 20
    assert pack["visible_non_zero_range_bars"] > 20
    assert pack["data_quality"] == "HEALTHY"
    assert pack["zero_range_bars"] == 0


@pytest.mark.asyncio
async def test_1d_and_1w_aggregate_from_hourly(monkeypatch):
    from services.fx_market_intel import yahoo_feed as yf

    async def fake(symbol_yahoo: str, *, interval: str, range_: str):
        assert interval == "60m"
        return _hourly(25)

    monkeypatch.setattr(yf, "fetch_yahoo_chart", fake)
    daily = await get_candles("EUR/USD", "1D")
    weekly = await get_candles("EUR/USD", "1W")
    assert daily["aggregated"] is True
    assert weekly["aggregated"] is True
    assert daily["displayed_timeframe"] == "1D"
    assert weekly["displayed_timeframe"] == "1W"
    assert len(daily["bars"]) >= 20
    assert weekly["bars"]
    yahoo_calls = yahoo_upstream_calls()
    assert yahoo_calls == 1
