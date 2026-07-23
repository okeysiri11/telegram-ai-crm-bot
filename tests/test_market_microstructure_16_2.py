"""Tests — Market Microstructure (Sprint 16.2)."""

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


def test_version_market_microstructure_ready():
    health = crypto_enterprise.health()
    assert health["application_version"] == "4.7.5-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.7.4-enterprise"
    assert health["order_book_intelligence_ready"] is True
    assert health["trade_flow_analytics_ready"] is True
    assert health["derivatives_intelligence_ready"] is True
    assert health["liquidity_intelligence_ready"] is True
    assert health["ai_market_interpretation_ready"] is True
    assert health["technical_analysis_ready"] is True


def test_order_book_and_trade_flow():
    suite = crypto_enterprise.market_microstructure
    book = suite.order_book.snapshot(symbol="ETHUSDT")
    assert book["book_id"] and book["spread"] >= 0
    imb = suite.order_book.imbalance(symbol="ETHUSDT", bid_volume=100, ask_volume=80)
    assert imb["bias"] == "bid"
    ts = suite.trade_flow.time_and_sales(symbol="ETHUSDT", price=3500, size=1.2, side="buy")
    assert ts["trade_id"]
    cvd = suite.trade_flow.cvd(symbol="ETHUSDT", cumulative=500)
    assert cvd["trend"] == "rising"
    with pytest.raises(ValidationError):
        suite.order_book.bid_ask(symbol="ETHUSDT", bid=10, ask=5)


def test_derivatives_and_liquidity():
    suite = crypto_enterprise.market_microstructure
    oi = suite.derivatives.open_interest(symbol="BTCUSDT", oi=1e9, change_pct=1.5)
    assert oi["open_interest"] == 1e9
    fund = suite.derivatives.funding_rate(symbol="BTCUSDT", rate=0.0001)
    assert fund["bias"] == "longs_pay"
    long_liq = suite.liquidations.liquidation(symbol="BTCUSDT", side="long", size=5, price=67000)
    assert long_liq["side"] == "long"
    zone = suite.liquidity.zone(symbol="BTCUSDT", price_low=66000, price_high=67000, strength=0.8)
    assert zone["zone_id"]
    hunt = suite.liquidity.stop_hunt(symbol="BTCUSDT", direction="below", swept_price=65990)
    assert hunt["direction"] == "below"


def test_ai_market_and_bootstrap():
    suite = crypto_enterprise.market_microstructure
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "4.7.5-enterprise"
    assert boot["bias_id"] and boot["confidence_id"]
    bias = suite.ai.trade_bias(symbol="SOLUSDT", bias="short", confidence=0.61)
    assert bias["bias"] == "short"
    for dtype in ("order_flow", "derivatives", "liquidity", "liquidation", "ai_market"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_market_microstructure(client):
    health = await client.get(f"{MM}/health")
    body = await health.json()
    assert body["application_version"] == "4.7.5-enterprise"
    assert body["order_book_intelligence_ready"] is True
    assert body["ai_market_interpretation_ready"] is True

    boot = await client.post(f"{MM}/bootstrap", json={})
    assert boot.status == 201

    ob = await client.post(f"{MM}/order-book", json={"action": "snapshot", "symbol": "BTCUSDT"})
    assert ob.status == 201

    der = await client.post(
        f"{MM}/derivatives",
        json={"action": "open_interest", "symbol": "BTCUSDT", "oi": 2e9},
    )
    assert der.status == 201

    ai = await client.post(
        f"{MM}/ai",
        json={"action": "bias", "symbol": "BTCUSDT", "bias": "long", "confidence": 0.7},
    )
    assert ai.status == 201

    ce = await client.get(f"{PREFIX}/health")
    assert ce.status == 200
    assert (await ce.json())["application_version"] == "4.7.5-enterprise"

    ta = await client.get(f"{TA}/health")
    assert ta.status == 200


def test_docs_and_regression_16_2():
    for name in (
        "ORDER_BOOK_INTELLIGENCE.md",
        "TRADE_FLOW_ANALYSIS.md",
        "DERIVATIVES_INTELLIGENCE.md",
        "LIQUIDATION_ANALYTICS.md",
        "MARKET_MICROSTRUCTURE.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "CRYPTO_MARKET_MICROSTRUCTURE.md").exists()
    assert (ROOT / "applications" / "crypto_enterprise" / "market_microstructure" / "facade.py").exists()

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
    assert "4.7.5-enterprise" in manifest
    assert "16.5" in manifest
    assert (ROOT / "applications" / "crypto_enterprise" / "technical_analysis" / "facade.py").exists()
    assert (ROOT / "applications" / "crypto_enterprise" / "exchanges.py").exists()
