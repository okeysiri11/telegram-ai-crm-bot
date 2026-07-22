"""Tests — AI Agronomist, Decision Support & Autonomous Planning (Sprint 14.7)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.agro_enterprise import agro_enterprise
from applications.agro_enterprise.api.register import register_agro_enterprise_routes
from applications.agro_enterprise.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/ai-agronomist/v1"
AF = "/api/agro-finance/v1"
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


def test_version_ai_agronomist_ready():
    health = agro_enterprise.health()
    assert health["application_version"] == "4.4.0-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.3.7-enterprise"
    assert health["ai_agronomist_ready"] is True
    assert health["enterprise_decision_support_ready"] is True
    assert health["autonomous_planning_ready"] is True
    assert health["executive_intelligence_ready"] is True


def test_agronomist_and_decision_engine():
    suite = agro_enterprise.ai_agronomist
    consult = suite.agronomist.consult(query="Need pest advisory for maize", farm_id="f1")
    assert consult["topic"] == "pest"
    adv = suite.agronomist.advise(advisory_type="nutrition", farm_id="f1")
    assert adv["recommendations"]
    decision = suite.decisions.decide(
        intent="cost", farm_id="f1", options=["cheap", "premium"], cost=10, profit=5
    )
    assert decision["chosen"] == "cheap"
    with pytest.raises(ValidationError):
        suite.agronomist.advise(advisory_type="astrology", farm_id="f1")


def test_planning_forecast_optimization():
    suite = agro_enterprise.ai_agronomist
    boot = suite.bootstrap()
    assert boot["plan_id"] and boot["forecast_id"] and boot["optimization_id"]
    plan = suite.planning.create_plan(
        plan_type="irrigation", farm_id="f2", title="Pivot B", window_start="2026-08-01"
    )
    active = suite.planning.activate(plan["plan_id"])
    assert active["status"] == "active"
    fc = suite.forecasts.forecast(forecast_type="yield", farm_id="f2", baseline=5.0)
    assert fc["predicted"] > 0
    opt = suite.optimization.optimize(opt_type="water", farm_id="f2", current_cost=20000)
    assert opt["projected_cost"] < 20000
    briefing = suite.executive.daily_briefing(farm_id="f2")
    assert briefing["business_health_score"] > 0
    with pytest.raises(ValidationError):
        suite.forecasts.forecast(forecast_type="magic", farm_id="f2")
    for dtype in (
        "agronomist",
        "decision_support",
        "forecast",
        "optimization",
        "executive_intelligence",
    ):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_ai_agronomist(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "4.4.0-enterprise"
    assert body["ai_agronomist_ready"] is True
    assert body["executive_intelligence_ready"] is True

    for prefix in (AF, SC, CE, CA, SI, PA, AE):
        assert (await client.get(f"{prefix}/health")).status == 200

    boot = await client.post(f"{PREFIX}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    decide = await client.post(
        f"{PREFIX}/decisions",
        json={"intent": "risk", "farm_id": "f1", "options": ["a", "b"], "risk_score": 0.8},
    )
    assert decide.status == 201

    forecast = await client.post(
        f"{PREFIX}/forecast",
        json={"forecast_type": "market", "farm_id": "f1", "baseline": 100},
    )
    assert forecast.status == 201

    exec_resp = await client.post(
        f"{PREFIX}/executive",
        json={"action": "briefing", "farm_id": boot_body.get("plan_id", "f1")},
    )
    assert exec_resp.status == 201

    dash = await client.get(f"{PREFIX}/dashboard?type=forecast")
    assert dash.status == 200


def test_docs_and_regression_14_7():
    for name in (
        "AI_AGRONOMIST.md",
        "DECISION_SUPPORT.md",
        "AUTONOMOUS_PLANNING.md",
        "PREDICTIVE_INTELLIGENCE.md",
        "EXECUTIVE_AI.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "AI_AGRONOMIST.md").exists()
    assert (ROOT / "applications" / "agro_enterprise" / "ai_agronomist" / "facade.py").exists()
    for pkg in (
        "agro_finance",
        "supply_chain",
        "controlled_environment",
        "crop_ai",
        "smart_irrigation",
        "precision_agriculture",
    ):
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
