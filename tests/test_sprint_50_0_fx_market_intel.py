"""Sprint 50.0 — EUR/USD + DXY market intelligence."""

from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.crypto_enterprise.api.register import register_crypto_enterprise_routes
from services.fx_market_intel.consensus import build_consensus
from services.fx_market_intel.correlation import eurusd_dxy_correlation, pearson
from services.fx_market_intel.memory import reset_memory_for_tests
from services.fx_market_intel.news import dedupe_articles, normalize_article
from services.fx_market_intel.providers import NullMarketDataProvider, news_fingerprint
from services.fx_market_intel.service import FxMarketIntelService
from services.fx_market_intel.signals import assert_no_trade_execution, create_signal
from services.fx_market_intel.symbols import normalize_symbol
from services.fx_market_intel.technical import compute_indicators

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
def _reset_memory():
    reset_memory_for_tests()
    yield
    reset_memory_for_tests()


def test_symbol_normalization():
    assert normalize_symbol("EURUSD") == "EUR/USD"
    assert normalize_symbol("eur-usd") == "EUR/USD"
    assert normalize_symbol("DXY") == "DXY"
    assert normalize_symbol("USDX") == "DXY"


def test_news_deduplication():
    a = normalize_article({"title": "ECB holds rates", "url": "https://x/1", "published_at": "2026-08-10"})
    b = normalize_article({"title": "ECB holds rates", "url": "https://x/1", "published_at": "2026-08-10T12:00:00Z"})
    assert a["duplicate_group_id"] == b["duplicate_group_id"] == news_fingerprint("ECB holds rates", "https://x/1", "2026-08-10")
    items = dedupe_articles([a, b, {"title": "Other", "url": "https://y"}])
    assert len(items) == 2


def test_technical_no_fabricated_bars():
    empty = compute_indicators([])
    assert empty["status"] == "insufficient_data"
    assert empty["sma_fast"] is None
    bars = [{"c": 1.08 + i * 0.001, "h": 1.09, "l": 1.07} for i in range(20)]
    ok = compute_indicators(bars)
    assert ok["status"] == "ok"
    assert ok["rsi"] is not None


def test_correlation_insufficient_and_inverse():
    assert pearson([1, 2], [2, 1]) is None
    corr = eurusd_dxy_correlation([1.1, 1.2, 1.15, 1.18], [104, 103, 103.5, 102.8])
    assert corr["status"] == "ok"
    assert corr["coefficient"] is not None


def test_consensus_structured_not_concat():
    c = build_consensus(
        technical_vote="WATCH_BUY",
        dxy_vote="WATCH_SELL",
        macro_vote="NEUTRAL",
        news_vote="WAIT",
        session_vote="WATCH_BUY",
    )
    assert "overall_direction" in c
    assert "disagreement_score" in c
    assert "weights_used" in c
    assert isinstance(c["overall_confidence"], float)


def test_signal_no_trade_execution_invariant():
    sig = create_signal(
        instrument="EUR/USD",
        timeframe="1h",
        signal="WATCH_BUY",
        confidence=0.6,
        reasons=["test"],
    )
    assert sig["analytics_only"] is True
    assert sig["trade_execution"] is False
    assert_no_trade_execution(sig)
    with pytest.raises(RuntimeError):
        assert_no_trade_execution({**sig, "trade_execution": True})


@pytest.mark.asyncio
async def test_null_provider_no_fake_quote():
    q = await NullMarketDataProvider().get_quote("EUR/USD")
    assert q["mid"] is None
    assert q["status"] == "not_connected"


@pytest.mark.asyncio
async def test_service_run_specialist_and_tenant_signals():
    from services.fx_market_intel.providers import NullNewsProvider, NullMacroCalendarProvider, DxyStubProvider

    svc = FxMarketIntelService(
        eurusd_provider=NullMarketDataProvider(),
        dxy_provider=DxyStubProvider(),
        news_provider=NullNewsProvider(),
        macro_provider=NullMacroCalendarProvider(),
    )
    a = await svc.run_specialist(specialist_id="chief", tenant_id="t1")
    b = await svc.run_specialist(specialist_id="technical", tenant_id="t2")
    assert a["ok"] and b["ok"]
    assert a["signal"]["trade_execution"] is False
    sigs_t1 = await svc.list_signals("t1")
    assert len(sigs_t1) >= 1
    assert all(s["tenant_id"] in ("t1", "default", "") for s in sigs_t1)


async def test_fx_intel_http_snapshot_and_run(client: TestClient):
    snap = await client.get(f"{FX}/snapshot")
    assert snap.status == 200
    body = await snap.json()
    assert "EUR/USD" in body["core_instruments"]
    assert "DXY" in body["core_instruments"]
    assert "scheduler_message" in body

    run = await client.post(f"{FX}/run", json={"specialist_id": "chief", "tenant_id": "http-tenant"})
    assert run.status == 201
    payload = await run.json()
    assert payload["ok"] is True
    assert payload["signal"]["analytics_only"] is True
    assert payload["signal"]["trade_execution"] is False

    sigs = await client.get(f"{FX}/signals?tenant_id=http-tenant")
    assert sigs.status == 200
    items = (await sigs.json())["items"]
    assert items

    tech = await client.post(f"{FX}/technical", json={"bars": []})
    assert tech.status == 200
    assert (await tech.json())["status"] == "insufficient_data"

    news = await client.post(f"{FX}/news", json={"action": "ingest", "articles": []})
    assert news.status == 201
    assert (await news.json())["count"] == 0

    macro = await client.get(f"{FX}/macro")
    assert macro.status == 200
    body_m = await macro.json()
    assert "events" in body_m
