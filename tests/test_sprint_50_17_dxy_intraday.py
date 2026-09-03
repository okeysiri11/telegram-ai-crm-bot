"""Sprint 50.17 — DXY native 1m/5m/15m; never aggregate 60m down to intraday."""

from __future__ import annotations

import pytest

from services.fx_market_intel.bars import aggregate_bars, can_aggregate
from services.fx_market_intel.candle_feed import get_candles, reset_fx_market_cache
from services.fx_market_intel.yahoo_feed import yahoo_interval_range


def _yahoo_chart(closes: list[float], *, step: int, start: int = 1_700_000_000) -> dict:
    n = len(closes)
    pad = 0.02
    return {
        "timestamp": [start + i * step for i in range(n)],
        "indicators": {
            "quote": [
                {
                    "open": [c - pad / 2 for c in closes],
                    "high": [c + pad for c in closes],
                    "low": [c - pad for c in closes],
                    "close": list(closes),
                    "volume": [1.0] * n,
                }
            ]
        },
    }


@pytest.fixture(autouse=True)
def _reset():
    reset_fx_market_cache()
    yield
    reset_fx_market_cache()


def test_can_aggregate_allowed_pairs():
    assert can_aggregate("1m", "5m") is True
    assert can_aggregate("1m", "15m") is True
    assert can_aggregate("5m", "15m") is True
    assert can_aggregate("1m", "1H") is True
    assert can_aggregate("1H", "4H") is True
    assert can_aggregate("1D", "1W") is True


def test_can_aggregate_forbids_downsample():
    assert can_aggregate("60m", "5m") is False
    assert can_aggregate("60m", "1m") is False
    assert can_aggregate("60m", "15m") is False
    assert can_aggregate("15m", "5m") is False
    assert can_aggregate("15m", "1m") is False
    assert can_aggregate("5m", "1m") is False
    assert can_aggregate("1D", "1H") is False


def test_1m_to_5m_ohlc_aggregation():
    start = (1_700_000_000 // 300) * 300
    bars = []
    for i in range(5):
        t = start + i * 60
        bars.append({"time": t, "open": 99.0 + i * 0.01, "high": 99.2 + i * 0.01, "low": 98.9, "close": 99.05 + i * 0.01, "v": 1})
    out = aggregate_bars(bars, "5m", instrument="DXY", source_resolution="1m")
    assert len(out) == 1
    assert out[0]["open"] == bars[0]["open"]
    assert out[0]["close"] == bars[-1]["close"]
    assert out[0]["high"] == max(b["high"] for b in bars)
    assert out[0]["low"] == min(b["low"] for b in bars)
    assert out[0]["v"] == 5


def test_1m_to_15m_ohlc_aggregation():
    start = (1_700_000_000 // 900) * 900
    bars = [{"time": start + i * 60, "open": 99.0, "high": 99.3, "low": 98.8, "close": 99.1, "v": 2} for i in range(15)]
    bars[0]["open"] = 99.01
    bars[-1]["close"] = 99.19
    out = aggregate_bars(bars, "15m", instrument="DXY", source_resolution="1m")
    assert len(out) == 1
    assert out[0]["open"] == 99.01
    assert out[0]["close"] == 99.19
    assert out[0]["high"] == 99.3
    assert out[0]["low"] == 98.8


def test_duplicate_timestamps_removed():
    bars = [
        {"time": 1_700_000_000, "open": 99.1, "high": 99.2, "low": 99.0, "close": 99.15},
        {"time": 1_700_000_000, "open": 99.15, "high": 99.25, "low": 99.05, "close": 99.2},
        {"time": 1_700_000_060, "open": 99.2, "high": 99.3, "low": 99.1, "close": 99.22},
    ]
    from services.fx_market_intel.bars import normalize_canonical_bars

    out = normalize_canonical_bars(bars, instrument="DXY")
    times = [b["time"] for b in out]
    assert times == sorted(set(times))
    assert len(times) == 2


def test_invalid_ohlc_rejected():
    from services.fx_market_intel.bars import normalize_canonical_bars

    out = normalize_canonical_bars(
        [
            {"time": 1_700_000_000, "open": 99.1, "high": 99.0, "low": 99.2, "close": 99.15},
            {"time": 1_700_000_060, "open": float("nan"), "high": 99.2, "low": 99.0, "close": 99.1},
            {"time": 1_700_000_120, "open": 99.1, "high": 99.2, "low": 99.0, "close": 99.15},
        ],
        instrument="DXY",
    )
    assert len(out) == 1
    assert out[0]["close"] == 99.15


def test_dxy_cache_key_includes_timeframe():
    from services.fx_market_intel.candle_feed import _key

    assert "1m" in _key("DXY", "1m")
    assert "5m" in _key("DXY", "5m")
    assert _key("DXY", "1m") != _key("DXY", "5m")
    assert _key("DXY", "1m") != _key("DXY", "1H")
    assert "v2" in _key("DXY", "1m")
    assert "v2" not in _key("EUR/USD", "1m")


@pytest.mark.asyncio
async def test_dxy_1m_uses_native_yahoo_1m(monkeypatch):
    from services.fx_market_intel import yahoo_feed as yf

    async def fake(symbol_yahoo: str, *, interval: str, range_: str):
        assert symbol_yahoo == "DX-Y.NYB"
        assert interval == "1m"
        return _yahoo_chart([99.2 + i * 0.01 for i in range(90)], step=60)

    monkeypatch.setattr(yf, "fetch_yahoo_chart", fake)
    pack = await get_candles("DXY", "1m")
    assert pack["bar_count"] >= 60
    assert pack["source_resolution"] == "1m"
    assert pack["transformation"] == "native"
    assert pack["source_status"] != "UNAVAILABLE_AT_SOURCE_RESOLUTION"
    assert pack["requested_timeframe"] == "1m"


@pytest.mark.asyncio
async def test_dxy_never_requests_60m_for_intraday(monkeypatch):
    from services.fx_market_intel import yahoo_feed as yf

    seen: list[tuple[str, str]] = []

    async def fake(symbol_yahoo: str, *, interval: str, range_: str):
        seen.append((interval, range_))
        step = {"1m": 60, "5m": 300, "15m": 900, "60m": 3600}[interval]
        return _yahoo_chart([99.2 + (i % 4) * 0.01 for i in range(80)], step=step)

    monkeypatch.setattr(yf, "fetch_yahoo_chart", fake)
    for tf in ("1m", "5m", "15m"):
        pack = await get_candles("DXY", tf)
        assert pack["bars"], tf
        assert pack.get("source_resolution") != "60m"
    assert all(interval != "60m" for interval, _ in seen)


@pytest.mark.asyncio
async def test_dxy_rejects_60m_payload_as_1m(monkeypatch):
    from services.fx_market_intel import yahoo_feed as yf

    async def coarse(symbol_yahoo: str, *, interval: str, range_: str):
        return _yahoo_chart([99.2, 99.3, 99.25, 99.4], step=3600)

    monkeypatch.setattr(yf, "fetch_yahoo_chart", coarse)
    pack = await get_candles("DXY", "1m")
    assert pack["bars"] == []
    assert pack["source_status"] == "UNAVAILABLE_AT_SOURCE_RESOLUTION"
    assert pack["source_resolution"] != "60m" or pack["transformation"].startswith("none") or "не предоставляет" in str(pack.get("message"))
    assert "60m ->" not in str(pack.get("transformation") or "")
    assert pack.get("aggregated") is False


@pytest.mark.asyncio
async def test_derived_from_cannot_downsample_60m_to_5m():
    from services.fx_market_intel.candle_feed import _derived_from

    hourly = {
        "bars": [
            {"time": 1_700_000_000 + i * 3600, "open": 99.1, "high": 99.3, "low": 99.0, "close": 99.2, "o": 99.1, "h": 99.3, "l": 99.0, "c": 99.2}
            for i in range(8)
        ],
        "source_resolution": "60m",
        "provider": "yahoo",
    }
    pack = _derived_from(hourly, symbol="DXY", tf="5m", base_resolution="60m")
    assert pack["bars"] == []
    assert pack["source_status"] == "UNAVAILABLE_AT_SOURCE_RESOLUTION"


@pytest.mark.asyncio
async def test_eurusd_1m_router_untouched(monkeypatch):
    from services.fx_market_intel import provider_router as pr
    from services.fx_market_intel import yahoo_feed as yf

    async def duka(*_a, **_k):
        start = 1_700_000_000
        bars = []
        for i in range(80):
            o = 1.1600 + (i % 5) * 0.0001
            c = o + 0.00012
            t = start + i * 60
            bars.append({"time": t, "open": o, "high": c + 0.00008, "low": o - 0.00006, "close": c, "o": o, "h": c + 0.00008, "l": o - 0.00006, "c": c})
        return bars

    async def boom(*_a, **_k):
        raise AssertionError("EURUSD 1m must still prefer Dukascopy")

    monkeypatch.setattr(pr, "dukascopy_eurusd_1m", duka)
    monkeypatch.setattr(yf, "fetch_yahoo_chart", boom)
    pack = await get_candles("EUR/USD", "1m")
    assert pack["display_mode"] == "CANDLES"
    assert pack["data_quality"] == "HEALTHY"
    assert pack["bar_count"] >= 60
    assert pack["provider"] == "dukascopy"


def test_yahoo_interval_map_dxy_intraday_is_native():
    assert yahoo_interval_range("DXY", "1m") == ("1m", "1d")
    assert yahoo_interval_range("DXY", "5m") == ("5m", "5d")
    assert yahoo_interval_range("DXY", "15m") == ("15m", "5d")
    assert yahoo_interval_range("EUR/USD", "1m") == ("1m", "1d")
