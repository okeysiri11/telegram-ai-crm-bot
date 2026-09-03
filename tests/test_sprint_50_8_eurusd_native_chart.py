"""Sprint 50.8 — EURUSD native candles (Yahoo EURUSD=X, no TradingView)."""

from __future__ import annotations

import math

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.crypto_enterprise.api.register import register_crypto_enterprise_routes
from services.fx_market_intel.yahoo_feed import (
    SUPPORTED_TIMEFRAMES,
    aggregate_ohlc_4h,
    normalize_timeframe,
)


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_crypto_enterprise_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


def test_eurusd_timeframe_map():
    assert normalize_timeframe("1m") == "1m"
    assert normalize_timeframe("5m") == "5m"
    assert normalize_timeframe("15m") == "15m"
    assert normalize_timeframe("1h") == "1H"
    assert normalize_timeframe("4h") == "4H"
    assert normalize_timeframe("1D") == "1D"
    assert normalize_timeframe("1W") == "1W"
    assert list(SUPPORTED_TIMEFRAMES) == ["1m", "5m", "15m", "1H", "4H", "1D", "1W"]


def test_normalize_skips_non_finite_and_dedupes():
    from services.fx_market_intel.yahoo_feed import normalize_yahoo_bars

    result = {
        "timestamp": [1_700_000_000, 1_700_000_000, 1_700_003_600, 1_700_007_200],
        "indicators": {
            "quote": [
                {
                    "open": [1.10, 1.101, 1.11, float("nan")],
                    "high": [1.12, 1.121, 1.13, 1.14],
                    "low": [1.09, 1.091, 1.10, 1.11],
                    "close": [1.11, 1.111, 1.12, float("inf")],
                    "volume": [1, 2, 3, 4],
                }
            ]
        },
    }
    bars = normalize_yahoo_bars(result, timeframe="1H")
    assert len(bars) == 2
    assert all(math.isfinite(float(b[k])) for b in bars for k in ("o", "h", "l", "c"))
    times = [b["t"] for b in bars]
    assert times == sorted(times)
    assert len(set(times)) == len(times)


def test_aggregate_real_1h_into_4h():
    bars = [
        {
            "t": "2026-08-12T10:00:00+00:00",
            "o": 1.10,
            "h": 1.12,
            "l": 1.09,
            "c": 1.11,
            "v": 10,
            "timeframe": "1H",
        },
        {
            "t": "2026-08-12T11:00:00+00:00",
            "o": 1.11,
            "h": 1.14,
            "l": 1.10,
            "c": 1.13,
            "v": 20,
            "timeframe": "1H",
        },
        {
            "t": "2026-08-12T12:00:00+00:00",
            "o": 1.13,
            "h": 1.15,
            "l": 1.12,
            "c": 1.14,
            "v": 5,
            "timeframe": "1H",
        },
    ]
    out = aggregate_ohlc_4h(bars)
    assert len(out) == 2
    first = out[0]
    assert first["o"] == 1.10
    assert first["h"] == 1.14
    assert first["l"] == 1.09
    assert first["c"] == 1.13
    assert first["timeframe"] == "4H"


@pytest.mark.asyncio
async def test_fetch_bars_eurusd_metadata_and_4h_uses_1h_yahoo(monkeypatch):
    from services.fx_market_intel import yahoo_feed as yf

    seen: list[tuple[str, str, str]] = []

    async def fake_chart(symbol_yahoo: str, *, interval: str, range_: str):
        seen.append((symbol_yahoo, interval, range_))
        assert symbol_yahoo == "EURUSD=X"
        n = 8
        return {
            "timestamp": [1_700_000_000 + i * 3600 for i in range(n)],
            "indicators": {
                "quote": [
                    {
                        "open": [1.10 + i * 0.001 for i in range(n)],
                        "high": [1.11 + i * 0.001 for i in range(n)],
                        "low": [1.09 + i * 0.001 for i in range(n)],
                        "close": [1.105 + i * 0.001 for i in range(n)],
                        "volume": [1] * n,
                    }
                ]
            },
        }

    monkeypatch.setattr(yf, "fetch_yahoo_chart", fake_chart)
    pack = await yf.fetch_bars("EUR/USD", "4H")
    assert pack["status"] == "connected"
    assert pack["chart_ready"] is True
    assert pack["provider"] == "yahoo"
    assert pack["provider_symbol"] == "EURUSD=X"
    assert pack["chart_engine"] == "lightweight_charts"
    assert pack["supported_timeframes"] == ["1m", "5m", "15m", "1H", "4H", "1D", "1W"]
    assert seen == [("EURUSD=X", "60m", "30d")]
    assert pack["bar_count"] > 0
    assert pack["bar_count"] < 8
    assert all(math.isfinite(float(b["c"])) for b in pack["bars"])


@pytest.mark.asyncio
async def test_fetch_bars_empty_and_error(monkeypatch):
    from services.fx_market_intel import yahoo_feed as yf

    async def empty_chart(symbol_yahoo: str, *, interval: str, range_: str):
        return {"timestamp": [], "indicators": {"quote": [{"open": [], "high": [], "low": [], "close": [], "volume": []}]}}

    monkeypatch.setattr(yf, "fetch_yahoo_chart", empty_chart)
    empty = await yf.fetch_bars("EUR/USD", "1H")
    assert empty["chart_ready"] is False
    assert empty["bars"] == []
    assert empty["status"] == "insufficient_data"

    async def boom(symbol_yahoo: str, *, interval: str, range_: str):
        raise RuntimeError("Yahoo HTTP 503")

    monkeypatch.setattr(yf, "fetch_yahoo_chart", boom)
    err = await yf.fetch_bars("EUR/USD", "1m")
    assert err["chart_ready"] is False
    assert err["status"] == "error"
    assert err["bars"] == []
    assert "503" in str(err["message"])


@pytest.mark.asyncio
async def test_http_eurusd_candles_native_metadata(client: TestClient, monkeypatch):
    from services.fx_market_intel import yahoo_feed as yf

    async def fake_chart(symbol_yahoo: str, *, interval: str, range_: str):
        return {
            "timestamp": [1_700_000_000],
            "indicators": {
                "quote": [{"open": [1.16], "high": [1.17], "low": [1.15], "close": [1.161], "volume": [0]}]
            },
        }

    monkeypatch.setattr(yf, "fetch_yahoo_chart", fake_chart)
    candles = await client.get("/api/crypto-mi/v1/fx-intel/candles?symbol=EUR/USD&timeframe=1H")
    assert candles.status == 200
    body = await candles.json()
    assert body.get("symbol") == "EUR/USD"
    assert body.get("provider_symbol") == "EURUSD=X"
    assert body.get("chart_engine") == "lightweight_charts"
    assert body.get("chart_ready") is True
    assert body.get("bars")
    assert math.isfinite(float(body["bars"][0]["c"]))
