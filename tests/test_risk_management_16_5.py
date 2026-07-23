"""Tests — Risk Management (Sprint 16.5)."""

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


def test_version_risk_management_ready():
    health = crypto_enterprise.health()
    assert health["application_version"] == "4.8.0-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.7.7-enterprise"
    assert health["risk_management_ready"] is True
    assert health["portfolio_optimization_ready"] is True
    assert health["position_sizing_ready"] is True
    assert health["ai_risk_intelligence_ready"] is True
    assert health["capital_protection_ready"] is True
    assert health["strategy_builder_ready"] is True


def test_risk_engine_and_sizing():
    suite = crypto_enterprise.risk_management
    size = suite.sizing.size(
        method="kelly",
        symbol="BTCUSDT",
        capital=100000,
        risk_pct=1,
        stop_distance=500,
        win_rate=0.55,
        payoff=2.0,
    )
    assert size["quantity"] > 0
    risk = suite.analytics.risk_per_trade(symbol="BTCUSDT", risk_amount=1000, capital=100000)
    assert risk["risk_pct"] == 1.0
    limit = suite.analytics.loss_limit(period="daily", limit_pct=2, realized_pct=2.5)
    assert limit["breached"] is True
    with pytest.raises(ValidationError):
        suite.sizing.size(method="unknown", symbol="BTCUSDT", capital=1000)


def test_portfolio_and_exposure():
    suite = crypto_enterprise.risk_management
    alloc = suite.optimization.asset_allocation(name="Core", weights={"BTC": 60, "ETH": 40})
    assert alloc["allocation_id"]
    var = suite.models.var(portfolio_id="pf1", confidence=0.95, var_pct=2.5)
    assert var["var_pct"] == 2.5
    stop = suite.protection.dynamic_stop(symbol="ETHUSDT", stop=3200)
    assert stop["kind"] == "dynamic_stop"
    with pytest.raises(ValidationError):
        suite.models.var(portfolio_id="pf1", confidence=1.5, var_pct=1)


def test_ai_risk_and_bootstrap():
    suite = crypto_enterprise.risk_management
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "4.8.0-enterprise"
    assert boot["sizing_id"] and boot["approval_id"] and boot["var_id"]
    health = suite.ai.portfolio_health(portfolio_id=boot["portfolio_id"], score=90)
    assert health["status"] == "healthy"
    for dtype in ("risk", "portfolio", "exposure", "capital", "ai_risk"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_risk_management(client):
    health = await client.get(f"{RM}/health")
    body = await health.json()
    assert body["application_version"] == "4.8.0-enterprise"
    assert body["risk_management_ready"] is True
    assert body["capital_protection_ready"] is True

    boot = await client.post(f"{RM}/bootstrap", json={})
    assert boot.status == 201

    size = await client.post(
        f"{RM}/sizing",
        json={"method": "percentage", "symbol": "BTCUSDT", "capital": 50000, "risk_pct": 1, "stop_distance": 400},
    )
    assert size.status == 201

    ai = await client.post(
        f"{RM}/ai",
        json={"action": "market_risk", "symbol": "BTCUSDT", "score": 55},
    )
    assert ai.status == 201

    for path in (PREFIX, TA, MM, MI, SE):
        resp = await client.get(f"{path}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "4.8.0-enterprise"


def test_docs_and_regression_16_5():
    for name in (
        "RISK_MANAGEMENT.md",
        "POSITION_SIZING.md",
        "PORTFOLIO_OPTIMIZATION.md",
        "AI_RISK_INTELLIGENCE.md",
        "CAPITAL_MANAGEMENT.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "CRYPTO_RISK_MANAGEMENT.md").exists()
    assert (ROOT / "applications" / "crypto_enterprise" / "risk_management" / "facade.py").exists()

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
    assert (ROOT / "applications" / "crypto_enterprise" / "strategy_engine" / "facade.py").exists()
    assert (ROOT / "applications" / "crypto_enterprise" / "market_intelligence" / "facade.py").exists()
