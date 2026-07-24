"""Tests — Enterprise Strategy Intelligence (Sprint 24.8 / v7.8.0)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from applications.enterprise_hub.shared.exceptions import ValidationError
from platform_enterprise_strategy_intelligence.models import (
    FORECAST_HORIZONS,
    GOAL_TYPES,
    INTEGRATION_TARGETS,
    KPI_TARGETS,
    PRINCIPLES,
    SCENARIO_TYPES,
)


ROOT = Path(__file__).resolve().parents[1]
PREFIXES = [
    "/api/enterprise-hub/v1",
    "/api/enterprise-orch/v1",
    "/api/enterprise-kg/v1",
    "/api/enterprise-agents/v1",
    "/api/enterprise-comms/v1",
    "/api/enterprise-workflow/v1",
    "/api/enterprise-eip/v1",
    "/api/enterprise-edp/v1",
    "/api/enterprise-isam/v1",
    "/api/enterprise-obs/v1",
    "/api/enterprise-tenancy/v1",
    "/api/enterprise-aop/v1",
    "/api/enterprise-ats/v1",
    "/api/enterprise-ekp/v1",
    "/api/enterprise-aios/v1",
    "/api/enterprise-evp/v1",
    "/api/enterprise-sdp/v1",
    "/api/enterprise-edf/v1",
    "/api/enterprise-edt/v1",
    "/api/enterprise-esi/v1",
    "/api/enterprise-epm/v1",
    "/api/enterprise-ebc/v1",
    "/api/enterprise-ecc/v1",
    "/api/enterprise-eas/v1",
    "/api/enterprise-edc/v1",
    "/api/enterprise-esh/v1",
    "/api/enterprise-eqa/v1",
    "/api/enterprise-edo/v1",
    "/api/enterprise-epf/v1",
    "/api/enterprise-erl/v1",
    "/api/enterprise-epi/v1",
    "/api/enterprise-aba/v1",
    "/api/enterprise-bos/v1",
    "/api/enterprise-bws/v1",
    "/api/enterprise-bcj/v1",
    "/api/enterprise-amo/v1",
    "/api/enterprise-ech/v1",
    "/api/enterprise-eco/v1",
    "/api/enterprise-cpl/v1",
    "/api/enterprise-eon/v1",
    "/api/enterprise-eoc/v1",
    "/api/enterprise-epr/v1",
    "/api/enterprise-eao/v1",
    "/api/enterprise-wfi/v1",
    "/api/enterprise-ekg/v1",
    "/api/enterprise-pin/v1",
    "/api/enterprise-esl/v1",
    "/api/enterprise-etw/v1",
    "/api/enterprise-eoe/v1",
]
EST = "/api/enterprise-est/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_enterprise_hub_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    enterprise_hub.reset()
    yield
    enterprise_hub.reset()


def test_version_est_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "7.8.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v7.7.0"
    assert health["strategy_intelligence_ready"] is True
    assert health["strategic_goals_ready"] is True
    assert health["long_term_forecast_ready"] is True
    assert health["owner_strategy_ready"] is True
    assert health["engines"]["strategy_intelligence"] == "1.0"
    assert health["autonomous_optimization_ready"] is True
    assert "revenue_growth" in GOAL_TYPES
    assert "five_years" in FORECAST_HORIZONS
    assert "crisis" in SCENARIO_TYPES
    assert "autonomous_optimization" in INTEGRATION_TARGETS
    assert KPI_TARGETS["owner_final_decision"] is True
    assert set(PRINCIPLES)


def test_strategy_flow_council_owner():
    suite = enterprise_hub.strategy_intelligence
    goal = suite.define_goal(goal_type="profit_growth", target_value=18.0)
    assert goal["measurable"] is True

    strategy = suite.create_strategy(
        strategy_id="str_test_1",
        name="Expand north market",
        goal="profit_growth",
        horizon="year",
        kpis={"profit_growth_pct": 18.0},
    )
    assert strategy["status"] == "draft"

    fc = suite.forecast(baseline=500_000, growth_rate=0.15, horizon="year")
    assert fc["horizon"] == "year"
    assert fc["projected"] > 500_000

    scenarios = suite.build_scenarios(baseline_value=fc["projected"], strategy_id="str_test_1")
    assert len(scenarios["scenarios"]) == 4

    inv = suite.analyze_investment(investment=100_000, annual_return=40_000, profit_delta=35_000)
    assert inv["payback_years"] == 2.5

    expansion = suite.plan_expansion(items=[{"dimension": "countries", "name": "PL"}])
    assert expansion["count"] == 1

    risk = suite.assess_risk(scores={"market": 0.5, "financial": 0.4})
    assert "overall_risk" in risk

    council = suite.council_review(strategy_id="str_test_1", risk_score=risk["overall_risk"])
    assert council["unified"] is True
    assert council["requires_owner"] is True

    decision = suite.owner_decide(action="approve", actor="platform_owner", strategy_id="str_test_1")
    assert decision["status"] == "approved"
    assert decision["execution_workflow"] is True
    assert decision["autonomous_decide"] is False

    with pytest.raises(ValidationError):
        suite.owner_decide(action="approve", actor="agent", strategy_id="str_test_1")

    dash = suite.owner_dashboard(strategy_id="str_test_1")
    assert dash["ai_may_act"] is False
    assert "kpi_achievement_forecast" in dash


def test_bootstrap_est():
    suite = enterprise_hub.strategy_intelligence
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "7.8.0"
    assert boot["strategy_intelligence_ready"] is True
    assert boot["strategic_goals_ready"] is True
    assert boot["long_term_forecast_ready"] is True
    assert boot["owner_strategy_ready"] is True
    assert boot["ai_may_act"] is False
    assert boot["autonomous_decide"] is False
    assert boot["council_reviewed"] is True
    assert boot["measurable_goals"] is True
    assert boot["duplicates_core_logic"] is False
    assert boot["integrations"]["linked"] is True


@pytest.mark.asyncio
async def test_api_est(client):
    health = await client.get(f"{EST}/health")
    body = await health.json()
    assert body["application_version"] == "7.8.0"
    assert body["strategy_intelligence_ready"] is True

    boot = await client.post(f"{EST}/bootstrap", json={})
    assert boot.status == 201
    assert (await boot.json())["owner_strategy_ready"] is True

    for prefix in PREFIXES:
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        payload = await resp.json()
        version = payload.get("application_version") or payload.get("data", {}).get("application_version")
        assert version == "7.8.0"


def test_docs_and_regression_24_7():
    for name in (
        "ENTERPRISE_STRATEGY_INTELLIGENCE.md",
        "EST_REGISTRY_GOALS.md",
        "EST_FORECAST_SCENARIOS.md",
        "EST_RISK_OWNER.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_STRATEGY_INTELLIGENCE.md").exists()
    assert (ROOT / "platform_enterprise_strategy_intelligence" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "strategy_intelligence" / "facade.py").exists()

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS_CFG
    from applications.enterprise.config import DEFAULT_CONFIG as ENT
    from applications.auto_marketplace.config import DEFAULT_CONFIG as AUTO
    from applications.agro_enterprise.config import DEFAULT_CONFIG as AGRO
    from applications.port_enterprise.config import DEFAULT_CONFIG as PORT
    from applications.port_erp.config import DEFAULT_CONFIG as PORT_ERP
    from applications.crypto_enterprise.config import DEFAULT_CONFIG as CRYPTO
    from applications.legal_enterprise.config import DEFAULT_CONFIG as LEGAL
    from applications.finance_enterprise.config import DEFAULT_CONFIG as FINANCE

    assert AIOS_CFG.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AUTO.application_version == "4.2.0-enterprise"
    assert AGRO.application_version == "4.4.0-enterprise"
    assert PORT.application_version == "4.6.0-enterprise"
    assert PORT_ERP.application_version == "2.0.0"
    assert CRYPTO.application_version == "4.8.0-enterprise"
    assert LEGAL.application_version == "5.0.0-enterprise"
    assert FINANCE.application_version == "5.2.0-enterprise"
    manifest = (ROOT / "applications" / "enterprise_hub" / "manifest.json").read_text()
    assert '"application_version": "7.8.0"' in manifest
    assert "24.8" in manifest
