"""Sprint 50.14 — FX candle reliability: cache, 429, coalescing, validation."""

from __future__ import annotations

import asyncio

import pytest

from services.fx_market_intel.candle_feed import (
    CANDLE_TTL_SEC,
    QUOTE_TTL_SEC,
    alternative_provider_name,
    get_candles,
    reset_fx_market_cache,
)
from services.fx_market_intel.yahoo_feed import (
    YahooHttpError,
    normalize_yahoo_bars,
    yahoo_interval_range,
)


def _chart(closes: list[float], *, step: int = 3600, start: int = 1_700_000_000) -> dict:
    n = len(closes)
    return {
        "timestamp": [start + i * step for i in range(n)],
        "indicators": {
            "quote": [
                {
                    "open": list(closes),
                    "high": [c + 0.01 for c in closes],
                    "low": [c - 0.01 for c in closes],
                    "close": list(closes),
                    "volume": [0] * n,
                }
            ]
        },
    }


@pytest.fixture(autouse=True)
def _reset():
    reset_fx_market_cache()
    yield
    reset_fx_market_cache()


def test_dxy_maps_intraday_to_honest_yahoo_interval():
    assert yahoo_interval_range("DXY", "1m") == ("60m", "10d")
    assert yahoo_interval_range("DXY", "5m") == ("60m", "10d")
    assert yahoo_interval_range("DXY", "1W") == ("1wk", "2y")
    assert yahoo_interval_range("EUR/USD", "1m") == ("1m", "1d")
    assert yahoo_interval_range("EUR/USD", "4H") == ("60m", "30d")
    assert yahoo_interval_range("EUR/USD", "1H") == ("60m", "30d")


def test_normalize_drops_zero_low_and_unit_corruption():
    result = {
        "timestamp": [1_700_000_000, 1_700_003_600, 1_700_007_200],
        "indicators": {
            "quote": [
                {
                    "open": [1.16, 1.161, 11610],
                    "high": [1.17, 1.162, 11620],
                    "low": [0.0, 1.16, 11600],
                    "close": [1.161, 1.1615, 11610],
                    "volume": [0, 0, 0],
                }
            ]
        },
    }
    bars = normalize_yahoo_bars(result, timeframe="1H", instrument="EUR/USD")
    assert len(bars) == 1
    assert bars[0]["c"] == 1.1615
    assert bars[0]["l"] > 0
    times = [b["time"] for b in bars]
    assert times == sorted(times)
    assert len(times) == len(set(times))


def test_ttl_constants_match_sprint():
    assert QUOTE_TTL_SEC == 4.0
    assert CANDLE_TTL_SEC["1m"] == 30.0
    assert CANDLE_TTL_SEC["5m"] == 60.0
    assert CANDLE_TTL_SEC["15m"] == 120.0
    assert CANDLE_TTL_SEC["1H"] == 300.0
    assert CANDLE_TTL_SEC["4H"] == 600.0
    assert CANDLE_TTL_SEC["1D"] == 1800.0
    assert CANDLE_TTL_SEC["1W"] == 3600.0


def test_no_invented_alternative_provider():
    assert alternative_provider_name() in {None} or isinstance(alternative_provider_name(), str)


@pytest.mark.asyncio
async def test_ttl_cache_second_call_skips_yahoo(monkeypatch):
    from services.fx_market_intel import yahoo_feed as yf

    calls = {"n": 0}

    async def fake_chart(symbol_yahoo: str, *, interval: str, range_: str):
        calls["n"] += 1
        return _chart([1.16, 1.161, 1.162])

    monkeypatch.setattr(yf, "fetch_yahoo_chart", fake_chart)
    a = await get_candles("EUR/USD", "1H")
    b = await get_candles("EUR/USD", "1H")
    assert calls["n"] == 1
    assert a["bar_count"] == b["bar_count"] == 3
    assert b.get("cache") == "ttl"
    assert a["chart_ready"] is True


@pytest.mark.asyncio
async def test_single_flight_coalesces_ten_dxy_1h(monkeypatch):
    from services.fx_market_intel import yahoo_feed as yf

    calls = {"n": 0}

    async def slow_chart(symbol_yahoo: str, *, interval: str, range_: str):
        calls["n"] += 1
        await asyncio.sleep(0.05)
        return _chart([99.1, 99.2, 99.3, 99.4], start=1_700_000_000)

    monkeypatch.setattr(yf, "fetch_yahoo_chart", slow_chart)
    packs = await asyncio.gather(*[get_candles("DXY", "1H") for _ in range(10)])
    assert calls["n"] == 1
    assert all(p["bar_count"] == 4 for p in packs)
    assert packs[0]["source_resolution"] == "60m"
    assert packs[0]["requested_timeframe"] == "1H"


@pytest.mark.asyncio
async def test_dxy_1m_and_5m_unavailable_without_yahoo(monkeypatch):
    from services.fx_market_intel import yahoo_feed as yf

    async def boom(symbol_yahoo: str, *, interval: str, range_: str):
        raise AssertionError("DXY 1m/5m must not call Yahoo")

    monkeypatch.setattr(yf, "fetch_yahoo_chart", boom)
    one = await get_candles("DXY", "1m")
    five = await get_candles("DXY", "5m")
    assert one["source_status"] == "UNAVAILABLE_AT_SOURCE_RESOLUTION"
    assert five["source_status"] == "UNAVAILABLE_AT_SOURCE_RESOLUTION"
    assert one["bars"] == []
    assert five["bars"] == []


@pytest.mark.asyncio
async def test_yahoo_429_returns_last_good_not_empty(monkeypatch):
    from services.fx_market_intel import yahoo_feed as yf
    from services.fx_market_intel import candle_feed as cf

    async def ok_chart(symbol_yahoo: str, *, interval: str, range_: str):
        return _chart([99.2, 99.25, 99.3])

    monkeypatch.setattr(yf, "fetch_yahoo_chart", ok_chart)
    good = await get_candles("DXY", "1H")
    assert good["chart_ready"] is True
    assert good["bars"]

    async def boom(symbol_yahoo: str, *, interval: str, range_: str):
        raise YahooHttpError(429, "30")

    monkeypatch.setattr(yf, "fetch_yahoo_chart", boom)
    cf._candle_ttl.clear()
    stale = await get_candles("DXY", "1H")
    assert stale["bars"], "429 must not replace last-good with []"
    assert stale["chart_ready"] is True
    assert stale["source_status"] == "rate_limited"
    assert stale["stale"] is True
    assert stale["cache"] == "last_good"
    assert stale["bar_count"] == good["bar_count"]
    key = "candle:DXY:1H"
    assert cf._candle_last_good[key]["payload"]["bars"]
    assert len(cf._candle_last_good[key]["payload"]["bars"]) > 0

    again = await get_candles("DXY", "1H")
    assert again["bars"]
    assert again["source_status"] == "rate_limited"


@pytest.mark.asyncio
async def test_empty_yahoo_does_not_wipe_last_good(monkeypatch):
    from services.fx_market_intel import yahoo_feed as yf
    from services.fx_market_intel import candle_feed as cf

    async def ok_chart(symbol_yahoo: str, *, interval: str, range_: str):
        return _chart([1.16, 1.161])

    monkeypatch.setattr(yf, "fetch_yahoo_chart", ok_chart)
    await get_candles("EUR/USD", "4H")
    cf._candle_ttl.clear()

    async def empty(symbol_yahoo: str, *, interval: str, range_: str):
        return _chart([])

    monkeypatch.setattr(yf, "fetch_yahoo_chart", empty)
    pack = await get_candles("EUR/USD", "4H")
    assert pack["bars"]
    assert pack["chart_ready"] is True
    assert pack["cache"] == "last_good"


@pytest.mark.asyncio
async def test_provider_fallback_uses_alternative_when_present(monkeypatch):
    from services.fx_market_intel import yahoo_feed as yf
    from services.fx_market_intel import candle_feed as cf

    yahoo_calls = {"n": 0}

    async def boom(symbol_yahoo: str, *, interval: str, range_: str):
        yahoo_calls["n"] += 1
        raise AssertionError("yahoo should not run when alt has bars")

    async def alt(symbol: str, timeframe: str):
        return {
            "symbol": "EUR/USD",
            "timeframe": "1H",
            "requested_timeframe": "1H",
            "provider": "finnhub",
            "status": "connected",
            "source_status": "live",
            "bars": [
                {"t": "2026-01-01T00:00:00+00:00", "time": 1_767_225_600, "o": 1.16, "h": 1.17, "l": 1.15, "c": 1.161}
            ],
            "chart_engine": "lightweight_charts",
        }

    monkeypatch.setattr(yf, "fetch_yahoo_chart", boom)
    monkeypatch.setattr(cf, "fetch_alternative_candles", alt)
    pack = await get_candles("EUR/USD", "1H")
    assert yahoo_calls["n"] == 0
    assert pack["provider"] == "finnhub"
    assert pack["bars"]


@pytest.mark.asyncio
async def test_sorted_deduped_ohlc_on_get_candles(monkeypatch):
    from services.fx_market_intel import yahoo_feed as yf

    async def messy(symbol_yahoo: str, *, interval: str, range_: str):
        return {
            "timestamp": [1_700_003_600, 1_700_000_000, 1_700_000_000],
            "indicators": {
                "quote": [
                    {
                        "open": [1.17, 1.16, 1.16],
                        "high": [1.18, 1.17, 1.165],
                        "low": [1.16, 1.15, 1.155],
                        "close": [1.171, 1.161, 1.162],
                        "volume": [0, 0, 0],
                    }
                ]
            },
        }

    monkeypatch.setattr(yf, "fetch_yahoo_chart", messy)
    pack = await get_candles("EUR/USD", "1H")
    times = [int(b["time"]) for b in pack["bars"]]
    assert times == sorted(times)
    assert len(times) == len(set(times))
    for b in pack["bars"]:
        assert b["h"] >= max(b["o"], b["c"])
        assert b["l"] <= min(b["o"], b["c"])
        assert b["h"] >= b["l"]
