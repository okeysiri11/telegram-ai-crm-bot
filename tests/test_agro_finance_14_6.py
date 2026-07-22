"""Tests — Agro Finance, Exchange, Insurance & Risk (Sprint 14.6)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.agro_enterprise import agro_enterprise
from applications.agro_enterprise.api.register import register_agro_enterprise_routes
from applications.agro_enterprise.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/agro-finance/v1"
SC = "/api/agro-supply-chain/v1"
CE = "/api/controlled-environment/v1"
CA = "/api/crop-ai/v1"
SI = "/api/smart-irrigation/v1"
PA = "/api/precision-agriculture/v1"
AE = "/api/agro-enterprise/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_agro_enterprise_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    agro_enterprise.reset()
    yield
    agro_enterprise.reset()


def test_version_agro_finance_ready():
    health = agro_enterprise.health()
    assert health["application_version"] == "4.4.0-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.3.7-enterprise"
    assert health["agro_finance_ready"] is True
    assert health["commodity_exchange_ready"] is True
    assert health["risk_intelligence_ready"] is True
    assert health["crop_insurance_ready"] is True
    assert health["market_intelligence_ready"] is True


def test_finance_trading_insurance():
    suite = agro_enterprise.agro_finance
    cmd = suite.exchange.register_commodity(symbol="BARLEY", name="Feed Barley")
    buy = suite.exchange.place_order(
        commodity_id=cmd["commodity_id"], side="buy", quantity=100, price=180, trade_type="spot"
    )
    sell = suite.exchange.place_order(
        commodity_id=cmd["commodity_id"], side="sell", quantity=100, price=182, trade_type="spot"
    )
    trade = suite.exchange.execute_trade(buy_order_id=buy["order_id"], sell_order_id=sell["order_id"])
    assert trade["price"] == 181.0
    suite.finance.create_budget(farm_id="f1", year=2026, revenue=100, costs=40)
    assert suite.finance.profitability("f1")["margin"] == 60.0
    insurer = suite.insurance.register_insurer(name="InsureAg")
    policy = suite.insurance.create_policy(
        insurer_id=insurer["insurer_id"], farm_id="f1", crop="barley", coverage=10000, premium=400
    )
    claim = suite.insurance.claim(policy_id=policy["policy_id"], amount=2000, damage_pct=55)
    assert claim["assessment"] == "severe"
    with pytest.raises(ValidationError):
        suite.exchange.place_order(
            commodity_id=cmd["commodity_id"], side="hold", quantity=1, price=1
        )


def test_risk_and_market_analytics():
    suite = agro_enterprise.agro_finance
    boot = suite.bootstrap()
    assert boot["trade_id"] and boot["policy_id"]
    suite.risk.assess(risk_type="supply_chain", entity_id="farm_bootstrap", severity=0.7)
    score = suite.risk.portfolio_score("farm_bootstrap")
    assert score["risk_count"] >= 1
    insight = suite.market.trading_insight(commodity="wheat")
    assert insight["action"] in ("accumulate", "hedge", "hold")
    with pytest.raises(ValidationError):
        suite.risk.assess(risk_type="alien", entity_id="x", severity=0.5)
    for dtype in ("finance", "commodity_exchange", "risk", "insurance", "market_intelligence"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_agro_finance(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "4.4.0-enterprise"
    assert body["agro_finance_ready"] is True
    assert body["market_intelligence_ready"] is True

    for prefix in (SC, CE, CA, SI, PA, AE):
        assert (await client.get(f"{prefix}/health")).status == 200

    boot = await client.post(f"{PREFIX}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    risk = await client.post(
        f"{PREFIX}/risk",
        json={"risk_type": "operational", "entity_id": "farm_bootstrap", "severity": 0.5},
    )
    assert risk.status == 201

    market = await client.post(
        f"{PREFIX}/market",
        json={"action": "forecast", "commodity": "wheat", "horizon_days": 10},
    )
    assert market.status == 201

    depth = await client.get(f"{PREFIX}/exchange?view=depth&commodity_id={boot_body['commodity_id']}")
    assert depth.status == 200

    dash = await client.get(f"{PREFIX}/dashboard?type=risk")
    assert dash.status == 200


def test_docs_and_regression_14_6():
    for name in (
        "AGRO_FINANCE.md",
        "COMMODITY_EXCHANGE.md",
        "RISK_MANAGEMENT.md",
        "CROP_INSURANCE.md",
        "MARKET_INTELLIGENCE.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "AGRO_FINANCE.md").exists()
    assert (ROOT / "applications" / "agro_enterprise" / "agro_finance" / "facade.py").exists()
    for pkg in ("supply_chain", "controlled_environment", "crop_ai", "smart_irrigation", "precision_agriculture"):
        assert (ROOT / "applications" / "agro_enterprise" / pkg / "facade.py").exists()

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT
    from applications.auto_marketplace.config import DEFAULT_CONFIG as AUTO
    from applications.agro_marketplace.config import DEFAULT_CONFIG as AGRO

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AUTO.application_version == "4.2.0-enterprise"
    assert AGRO.application_version == "2.0.0"
    manifest = (ROOT / "applications" / "agro_enterprise" / "manifest.json").read_text()
    assert "4.4.0-enterprise" in manifest
    assert "14.8" in manifest
