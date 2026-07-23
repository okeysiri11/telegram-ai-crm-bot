"""Tests — AI Crypto Trader (Sprint 16.7)."""

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
SE = "/api/crypto-se/v1"
RM = "/api/crypto-rm/v1"
OC = "/api/crypto-oc/v1"
AT = "/api/crypto-at/v1"


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


def test_version_ai_trader_ready():
    health = crypto_enterprise.health()
    assert health["application_version"] == "4.7.7-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.7.6-enterprise"
    assert health["ai_crypto_trader_ready"] is True
    assert health["decision_support_ready"] is True
    assert health["trade_recommendation_engine_ready"] is True
    assert health["executive_intelligence_ready"] is True
    assert health["ai_explainability_ready"] is True
    assert health["onchain_intelligence_ready"] is True


def test_ai_decision_and_recommendations():
    suite = crypto_enterprise.ai_trader
    decision = suite.decision.decide(symbol="BTCUSDT", bullish=0.6, bearish=0.2, confidence=0.8)
    assert decision["bias"] == "bullish"
    rec = suite.recommendations.recommend(
        symbol="BTCUSDT",
        side="long",
        entry_low=100,
        entry_high=102,
        stop=95,
        targets=[110, 120],
        size=1.0,
    )
    assert rec["risk_reward"] > 0
    with pytest.raises(ValidationError):
        suite.decision.decide(symbol="BTCUSDT", confidence=1.5)


def test_portfolio_intel_and_explainability():
    suite = crypto_enterprise.ai_trader
    health = suite.portfolio_intel.health(portfolio_id="pf1", score=85)
    assert health["status"] == "healthy"
    decision = suite.decision.decide(symbol="ETHUSDT", bullish=0.5, bearish=0.3, confidence=0.7)
    trace = suite.explainability.trace(decision_id=decision["decision_id"], steps=["a", "b"])
    assert trace["trace_id"]
    alert = suite.alerts.raise_alert(
        alert_type="risk",
        symbol="ETHUSDT",
        severity="warning",
        message="Elevated risk",
    )
    assert alert["alert_id"]


def test_bootstrap_and_executive():
    suite = crypto_enterprise.ai_trader
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "4.7.7-enterprise"
    assert boot["decision_id"] and boot["recommendation_id"] and boot["report_id"]
    overview = suite.executive.market_overview(summary="Constructive", bias="bullish")
    assert overview["bias"] == "bullish"
    for dtype in ("ai_trader", "decision", "portfolio_intel", "executive", "alert"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_ai_trader(client):
    health = await client.get(f"{AT}/health")
    body = await health.json()
    assert body["application_version"] == "4.7.7-enterprise"
    assert body["ai_crypto_trader_ready"] is True
    assert body["ai_explainability_ready"] is True

    boot = await client.post(f"{AT}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    decision = await client.post(
        f"{AT}/decision",
        json={"symbol": "BTCUSDT", "bullish": 0.55, "bearish": 0.25, "confidence": 0.7},
    )
    assert decision.status == 201

    expl = await client.post(
        f"{AT}/explainability",
        json={
            "action": "report",
            "decision_id": boot_body["decision_id"],
            "narrative": "Explainable long bias",
        },
    )
    assert expl.status == 201

    for path in (PREFIX, TA, MM, MI, SE, RM, OC):
        resp = await client.get(f"{path}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "4.7.7-enterprise"


def test_docs_and_regression_16_7():
    for name in (
        "AI_CRYPTO_TRADER.md",
        "DECISION_SUPPORT.md",
        "TRADE_RECOMMENDATION_ENGINE.md",
        "AI_EXPLAINABILITY.md",
        "EXECUTIVE_MARKET_BRIEFING.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "CRYPTO_AI_TRADER.md").exists()
    assert (ROOT / "applications" / "crypto_enterprise" / "ai_trader" / "facade.py").exists()

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
    assert "4.7.7-enterprise" in manifest
    assert "16.7" in manifest
    assert (ROOT / "applications" / "crypto_enterprise" / "onchain_intelligence" / "facade.py").exists()
    assert (ROOT / "applications" / "crypto_enterprise" / "risk_management" / "facade.py").exists()
