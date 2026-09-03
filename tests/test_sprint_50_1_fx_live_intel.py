"""Sprint 50.1 — live FX intelligence runtime."""

from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.crypto_enterprise.api.register import register_crypto_enterprise_routes
from services.fx_market_intel.evaluation import compute_move_metrics, direction_label, due_horizons
from services.fx_market_intel.memory import reset_memory_for_tests
from services.fx_market_intel.news import dedupe_articles
from services.fx_market_intel.providers import (
    DxyStubProvider,
    NullMacroCalendarProvider,
    NullMarketDataProvider,
    NullNewsProvider,
)
from services.fx_market_intel.rss_news import assess_news_impact
from services.fx_market_intel.service import FxMarketIntelService, reset_fx_market_intel_for_tests
from services.fx_market_intel.signals import assert_no_trade_execution
from services.fx_market_intel.symbols import normalize_symbol
from services.fx_market_intel.technical import compute_indicators
from services.fx_market_intel.yahoo_feed import normalize_yahoo_bars

FX = "/api/crypto-mi/v1/fx-intel"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_crypto_enterprise_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def _reset():
    reset_memory_for_tests()
    reset_fx_market_intel_for_tests()
    yield
    reset_memory_for_tests()
    reset_fx_market_intel_for_tests()


def test_symbol_normalization_eurusd_dxy():
    assert normalize_symbol("EURUSD") == "EUR/USD"
    assert normalize_symbol("DX-Y.NYB") == "DXY" or normalize_symbol("DXY") == "DXY"


def test_yahoo_candle_normalization():
    result = {
        "timestamp": [1_700_000_000, 1_700_003_600, 1_700_007_200],
        "indicators": {
            "quote": [
                {
                    "open": [1.1, 1.11, None],
                    "high": [1.12, 1.13, 1.14],
                    "low": [1.09, 1.10, 1.11],
                    "close": [1.11, 1.12, None],
                    "volume": [1, 2, 3],
                }
            ]
        },
    }
    bars = normalize_yahoo_bars(result, timeframe="1H")
    assert len(bars) == 2
    assert bars[0]["c"] == 1.11
    assert "o" in bars[0] and "h" in bars[0]


def test_technical_indicators_extended():
    bars = [{"c": 1.08 + i * 0.001, "h": 1.09 + i * 0.001, "l": 1.07 + i * 0.001} for i in range(40)]
    ind = compute_indicators(bars)
    assert ind["status"] == "ok"
    assert ind["ema_fast"] is not None
    assert ind["rsi"] is not None
    assert ind["macd"] is not None
    assert ind["atr"] is not None
    assert ind["bollinger"]["mid"] is not None


def test_news_assessment_not_trade_advice():
    assert assess_news_impact("x") == "Недостаточно данных"
    assert "DXY" in assess_news_impact("Fed announces hawkish hike", "Federal Reserve") or assess_news_impact(
        "Fed announces hawkish hike", "Federal Reserve"
    ) in {"Поддерживает DXY", "Нейтрально", "Недостаточно данных"}


def test_evaluation_metrics_no_profit_claim():
    m = compute_move_metrics(price_at=1.10, price_after=1.12, predicted_direction="WATCH_BUY")
    assert m["direction_correct"] is True
    assert m["evaluation_status"] == "evaluated"
    assert "profit" not in m
    assert direction_label("WATCH_SELL") == "bearish"


def test_macro_event_normalization_keys():
    from services.fx_market_intel.macro import normalize_macro_event

    ev = normalize_macro_event({"event": "CPI", "country": "USD", "scheduled_at": "2026-08-11"})
    assert ev["event"] == "cpi"
    assert "EUR/USD" in ev["affected_instruments"]


@pytest.mark.asyncio
async def test_full_analysis_persists_memory_and_no_trade():
    svc = FxMarketIntelService(
        eurusd_provider=NullMarketDataProvider(),
        dxy_provider=DxyStubProvider(),
        news_provider=NullNewsProvider(),
        macro_provider=NullMacroCalendarProvider(),
    )
    result = await svc.run_full_analysis(preset_id="morning", tenant_id="tenant-a")
    assert result["ok"] is True
    assert result["signal"]["trade_execution"] is False
    assert_no_trade_execution(result["signal"])
    assert "display" in result
    assert result["display"]["direction_ru"]
    assert result["persistence"]["status"] in {"postgres", "memory"}
    # tenant isolation on in-memory signal list fallback
    other = await svc.list_signals("tenant-b")
    own = await svc.list_signals("tenant-a")
    assert any(s.get("tenant_id") == "tenant-a" for s in own)
    assert all(s.get("tenant_id") != "tenant-a" for s in other) or not other


@pytest.mark.asyncio
async def test_http_candles_history_routes(client: TestClient):
    health = await client.get(f"{FX}/health")
    assert health.status == 200
    candles = await client.get(f"{FX}/candles?symbol=EUR/USD&timeframe=1H")
    assert candles.status == 200
    hist = await client.get(f"{FX}/history?tenant_id=http-50-1")
    assert hist.status == 200
    run = await client.post(
        f"{FX}/run",
        json={"preset_id": "morning", "tenant_id": "http-50-1", "timeframe": "1H"},
    )
    assert run.status == 201
    payload = await run.json()
    assert payload["ok"] is True
    assert payload["signal"]["analytics_only"] is True


@pytest.mark.asyncio
async def test_telegram_path_uses_service():
    svc = FxMarketIntelService(
        eurusd_provider=NullMarketDataProvider(),
        dxy_provider=DxyStubProvider(),
        news_provider=NullNewsProvider(),
        macro_provider=NullMacroCalendarProvider(),
    )
    text = await svc.telegram_brief("EURUSD", tenant_id="tg_1")
    assert "EUR/USD" in text or "нет данных" in text
    text2 = await svc.telegram_brief("Утренний обзор", tenant_id="tg_1")
    assert "AI-анализ" in text2


@pytest.mark.asyncio
async def test_quote_annotates_provider_and_dxy_mid():
    class LiveDxy:
        id = "yahoo_dxy"
        label = "Yahoo Finance (DX-Y.NYB)"

        async def status(self):
            return {"provider_id": self.id, "status": "connected"}

        async def get_quote(self, symbol: str):
            return {
                "symbol": "DXY",
                "bid": "99.860",
                "ask": "99.880",
                "mid": "99.870",
                "source": self.label,
                "status": "connected",
                "fetched_at": "2026-09-02T12:00:00+00:00",
            }

    class LiveEur:
        id = "nbu_cross"
        label = "НБУ (кросс EUR/USD)"

        async def status(self):
            return {"provider_id": self.id, "status": "connected"}

        async def get_quote(self, symbol: str):
            return {
                "symbol": "EUR/USD",
                "bid": "1.0850",
                "ask": "1.0850",
                "mid": "1.0850",
                "source": self.label,
                "status": "connected",
                "fetched_at": "2026-09-02T12:00:00+00:00",
            }

    svc = FxMarketIntelService(eurusd_provider=LiveEur(), dxy_provider=LiveDxy())
    e = await svc.quote("EUR/USD")
    d = await svc.quote("DXY")
    assert e["provider"] == "nbu_cross"
    assert e["mid"] == "1.0850"
    assert e["status"] == "delayed"
    assert e["price"] == 1.085
    assert d["provider"] == "yahoo_dxy"
    assert d["mid"] == "99.870"
    assert d["status"] == "connected"


def test_classify_fx_quote_status_never_fakes_live():
    import time

    from services.fx_market_intel.service import classify_fx_quote_status

    now = time.time()
    assert (
        classify_fx_quote_status(
            {"mid": "1.08", "provider": "yahoo_eurusd", "status": "connected", "market_time": now}
        )
        == "live"
    )
    assert (
        classify_fx_quote_status(
            {
                "mid": "1.08",
                "provider": "yahoo_eurusd",
                "status": "connected",
                "market_time": now - 3600,
            }
        )
        == "delayed"
    )
    assert (
        classify_fx_quote_status(
            {"mid": "1.08", "provider": "nbu_cross", "status": "connected", "market_time": now}
        )
        == "delayed"
    )
    assert classify_fx_quote_status({"mid": None, "provider": "yahoo_eurusd", "status": "error"}) == "error"


@pytest.mark.asyncio
async def test_eurusd_yahoo_primary_skips_nbu_when_yahoo_works():
    from services.fx_market_intel.yahoo_feed import EurUsdMarketQuoteProvider

    class Primary:
        id = "yahoo_eurusd"

        async def get_quote(self, symbol: str):
            return {"symbol": symbol, "mid": "1.1710", "status": "connected", "source": "Yahoo"}

    class Fallback:
        id = "nbu_cross"

        async def get_quote(self, symbol: str):
            raise AssertionError("NBU must not run when Yahoo quote is present")

    svc = FxMarketIntelService(
        eurusd_provider=EurUsdMarketQuoteProvider(primary=Primary(), fallback=Fallback()),
        dxy_provider=DxyStubProvider(),
    )
    q = await svc.quote("EUR/USD")
    assert q["provider"] == "yahoo_eurusd"
    assert q["mid"] == "1.1710"
    assert q["status"] == "delayed"  # no market_time → cannot claim live
    assert q["price"] == 1.171


@pytest.mark.asyncio
async def test_eurusd_falls_back_to_nbu_when_yahoo_fails():
    from services.fx_market_intel.yahoo_feed import EurUsdMarketQuoteProvider

    class Primary:
        id = "yahoo_eurusd"

        async def get_quote(self, symbol: str):
            return {"symbol": symbol, "mid": None, "status": "error", "source": "Yahoo"}

    class Fallback:
        id = "nbu_cross"

        async def get_quote(self, symbol: str):
            return {"symbol": symbol, "mid": "1.1577", "status": "connected", "source": "НБУ"}

    svc = FxMarketIntelService(
        eurusd_provider=EurUsdMarketQuoteProvider(primary=Primary(), fallback=Fallback()),
        dxy_provider=DxyStubProvider(),
    )
    q = await svc.quote("EUR/USD")
    assert q["provider"] == "nbu_cross"
    assert q["mid"] == "1.1577"
    assert q["status"] == "delayed"
    assert q["fallback_from"] == "yahoo_eurusd"
