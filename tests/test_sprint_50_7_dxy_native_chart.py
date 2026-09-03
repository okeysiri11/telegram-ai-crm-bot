"""Sprint 50.7 — DXY native candles API metadata."""

from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.crypto_enterprise.api.register import register_crypto_enterprise_routes
from services.fx_market_intel.yahoo_feed import (
    DXY_SUPPORTED_TIMEFRAMES,
    SUPPORTED_TIMEFRAMES,
    aggregate_ohlc_4h,
    normalize_timeframe,
    normalize_yahoo_bars,
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


def test_normalize_timeframe_canonical():
    assert normalize_timeframe("1h") == "1H"
    assert normalize_timeframe("4H") == "4H"
    assert normalize_timeframe("15m") == "15m"
    assert normalize_timeframe("bogus") == "1H"
    assert list(DXY_SUPPORTED_TIMEFRAMES) == ["1m", "5m", "15m", "1H", "4H", "1D", "1W"]
    assert list(SUPPORTED_TIMEFRAMES) == ["1m", "5m", "15m", "1H", "4H", "1D", "1W"]
    assert normalize_timeframe("1m") == "1m"
    assert normalize_timeframe("1W") == "1W"
    assert normalize_timeframe("1m", "DXY") == "1m"


def test_normalize_yahoo_bars_skips_null_closes():
    result = {
        "timestamp": [1_700_000_000, 1_700_003_600],
        "indicators": {
            "quote": [
                {
                    "open": [100.0, None],
                    "high": [101.0, None],
                    "low": [99.0, None],
                    "close": [100.5, None],
                    "volume": [1, 2],
                }
            ]
        },
    }
    bars = normalize_yahoo_bars(result, timeframe="1H")
    assert len(bars) == 1
    assert bars[0]["c"] == 100.5
    assert bars[0]["o"] == 100.0


@pytest.mark.asyncio
async def test_fetch_bars_dxy_metadata(monkeypatch):
    from services.fx_market_intel import yahoo_feed as yf

    async def fake_chart(symbol_yahoo: str, *, interval: str, range_: str):
        assert symbol_yahoo == "DX-Y.NYB"
        return {
            "timestamp": [1_700_000_000 + i * 3600 for i in range(5)],
            "indicators": {
                "quote": [
                    {
                        "open": [99 + i * 0.01 for i in range(5)],
                        "high": [99.2 + i * 0.01 for i in range(5)],
                        "low": [98.8 + i * 0.01 for i in range(5)],
                        "close": [99.1 + i * 0.01 for i in range(5)],
                        "volume": [0] * 5,
                    }
                ]
            },
        }

    monkeypatch.setattr(yf, "fetch_yahoo_chart", fake_chart)
    pack = await yf.fetch_bars("DXY", "1H")
    assert pack["status"] == "connected"
    assert pack["chart_ready"] is True
    assert pack["provider"] == "yahoo"
    assert pack["provider_symbol"] == "DX-Y.NYB"
    assert pack["bar_count"] == 5
    assert pack["chart_engine"] == "lightweight_charts"
    assert "1H" in pack["supported_timeframes"]


@pytest.mark.asyncio
async def test_http_dxy_candles_and_snapshot(client: TestClient):
    candles = await client.get("/api/crypto-mi/v1/fx-intel/candles?symbol=DXY&timeframe=1H")
    assert candles.status == 200
    body = await candles.json()
    assert body.get("symbol") == "DXY"
    assert "supported_timeframes" in body
    assert "bars" in body and "bar_count" in body and "chart_ready" in body
    assert body.get("provider") == "yahoo"

    snap = await client.get("/api/crypto-mi/v1/fx-intel/snapshot?tenant_id=t507")
    assert snap.status == 200
    sj = await snap.json()
    assert sj.get("dxy_chart", {}).get("engine") == "ados_lightweight_charts"
    assert sj.get("tradingview", {}).get("DXY") is None
    assert sj.get("tradingview", {}).get("EUR/USD") is None
    assert sj.get("eurusd_chart", {}).get("engine") == "ados_lightweight_charts"
    assert sj.get("eurusd_chart", {}).get("yahoo_symbol") == "EURUSD=X"
