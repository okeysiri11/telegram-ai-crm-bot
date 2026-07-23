"""Tests — Market Intelligence (Sprint 16.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.crypto_enterprise import crypto_enterprise
from applications.crypto_enterprise.api.register import register_crypto_enterprise_routes
from applications.crypto_enterprise.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/crypto-enterprise/v1"
TA = "/api/crypto-ta/v1"
MM = "/api/crypto-mm/v1"
MI = "/api/crypto-mi/v1"


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
def reset_store():
    crypto_enterprise.reset()
    yield
    crypto_enterprise.reset()


def test_version_market_intelligence_ready():
    health = crypto_enterprise.health()
    assert health["application_version"] == "4.8.0-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.7.7-enterprise"
    assert health["news_intelligence_ready"] is True
    assert health["sentiment_intelligence_ready"] is True
    assert health["macro_intelligence_ready"] is True
    assert health["ai_correlation_engine_ready"] is True
    assert health["ai_decision_engine_ready"] is True
    assert health["order_book_intelligence_ready"] is True


def test_news_and_sentiment():
    suite = crypto_enterprise.market_intelligence
    news = suite.news.aggregate(source="reuters", headline="BTC rallies on ETF demand")
    assert news["news_id"]
    cls = suite.news.classify(news_id=news["news_id"], category="etf")
    assert cls["category"] == "etf"
    fg = suite.sentiment.fear_greed(value=80)
    assert fg["band"] == "extreme_greed"
    idx = suite.sentiment.market_index(score=65)
    assert idx["label"] == "bullish"
    with pytest.raises(ValidationError):
        suite.news.classify(news_id="missing", category="etf")


def test_macro_and_correlation():
    suite = crypto_enterprise.market_intelligence
    fed = suite.macro.fed(title="FOMC", scheduled_at="2026-07-30T18:00:00Z")
    assert fed["event_type"] == "fed"
    corr = suite.correlation.correlate(
        correlation_type="news_price",
        symbol="BTCUSDT",
        coefficient=0.7,
    )
    assert corr["strength"] == "strong"
    with pytest.raises(ValidationError):
        suite.correlation.correlate(
            correlation_type="news_price",
            symbol="BTCUSDT",
            coefficient=1.5,
        )


def test_ai_decision_and_bootstrap():
    suite = crypto_enterprise.market_intelligence
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "4.8.0-enterprise"
    assert boot["summary_id"] and boot["correlation_id"]
    opp = suite.decision.opportunity(symbol="ETHUSDT", score=66)
    assert opp["score"] == 66
    for dtype in ("news", "sentiment", "macro", "correlation", "ai_market"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_market_intelligence(client):
    health = await client.get(f"{MI}/health")
    body = await health.json()
    assert body["application_version"] == "4.8.0-enterprise"
    assert body["news_intelligence_ready"] is True
    assert body["ai_decision_engine_ready"] is True

    boot = await client.post(f"{MI}/bootstrap", json={})
    assert boot.status == 201

    news = await client.post(
        f"{MI}/news",
        json={"action": "aggregate", "source": "bloomberg", "headline": "Macro bid"},
    )
    assert news.status == 201

    sent = await client.post(f"{MI}/sentiment", json={"action": "index", "score": 55})
    assert sent.status == 201

    corr = await client.post(
        f"{MI}/correlation",
        json={"correlation_type": "sentiment_volume", "symbol": "BTCUSDT", "coefficient": 0.5},
    )
    assert corr.status == 201

    decision = await client.post(
        f"{MI}/decision",
        json={"action": "summary", "symbol": "BTCUSDT", "summary": "Constructive bias"},
    )
    assert decision.status == 201

    for path in (PREFIX, TA, MM):
        resp = await client.get(f"{path}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "4.8.0-enterprise"


def test_docs_and_regression_16_3():
    for name in (
        "AI_MARKET_INTELLIGENCE.md",
        "SENTIMENT_ANALYSIS.md",
        "NEWS_ENGINE.md",
        "MACRO_ANALYSIS.md",
        "CORRELATION_ENGINE.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "CRYPTO_MARKET_INTELLIGENCE.md").exists()
    assert (ROOT / "applications" / "crypto_enterprise" / "market_intelligence" / "facade.py").exists()

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT
    from applications.auto_marketplace.config import DEFAULT_CONFIG as AUTO
    from applications.agro_enterprise.config import DEFAULT_CONFIG as AGRO
    from applications.port_enterprise.config import DEFAULT_CONFIG as PORT
    from applications.port_erp.config import DEFAULT_CONFIG as PORT_ERP

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AUTO.application_version == "4.2.0-enterprise"
    assert AGRO.application_version == "4.4.0-enterprise"
    assert PORT.application_version == "4.6.0-enterprise"
    assert PORT_ERP.application_version == "2.0.0"
    manifest = (ROOT / "applications" / "crypto_enterprise" / "manifest.json").read_text()
    assert "4.8.0-enterprise" in manifest
    assert "16.8" in manifest
    assert (ROOT / "applications" / "crypto_enterprise" / "market_microstructure" / "facade.py").exists()
    assert (ROOT / "applications" / "crypto_enterprise" / "technical_analysis" / "facade.py").exists()
