"""Tests — Enterprise Simulation Lab & Scenario Engine (Sprint 24.5 / v7.5.0)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from applications.enterprise_hub.shared.exceptions import ValidationError
from platform_enterprise_simulation_lab.models import (
    KPI_TARGETS,
    PRINCIPLES,
    SCENARIO_KINDS,
    WHAT_IF_QUESTIONS,
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
]
ESL = "/api/enterprise-esl/v1"


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


def test_version_esl_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "7.5.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v7.4.0"
    assert health["simulation_lab_ready"] is True
    assert health["what_if_ready"] is True
    assert health["multi_scenario_ready"] is True
    assert health["owner_simulation_ready"] is True
    assert health["engines"]["simulation_lab"] == "1.0"
    # legacy simulation engine remains
    assert health["simulation_engine_ready"] is True
    assert "increase_prices" in WHAT_IF_QUESTIONS
    assert set(SCENARIO_KINDS) == {"optimistic", "realistic", "conservative", "crisis"}
    assert KPI_TARGETS["forecast_before_rollout"] is True
    assert set(PRINCIPLES)


def test_what_if_simulate_compare_owner():
    suite = enterprise_hub.simulation_lab
    scn = suite.create_scenario(scenario_id="scn_hire", name="Hire more staff", models=["predictive_intelligence"])
    assert scn["status"] == "draft"

    wi = suite.what_if(question="hire_staff", intensity=1.0)
    assert wi["sandbox"] is True
    assert wi["ai_may_act"] is False
    assert "workforce" in wi["domain_deltas"]

    run = suite.simulate(scenario_id="scn_hire", question="hire_staff", intensity=1.0)
    assert run["sandbox"] is True
    assert run["mutates_production"] is False
    assert run["ai_may_act"] is False
    assert run["debate"]["unified_report"] is True
    assert run["debate"]["requires_owner"] is True
    assert len(run["multi_scenarios"]["scenarios"]) == 4

    cmp_ = suite.compare(
        options=[
            {"option_id": "hire", "pros": ["capacity"], "cons": ["cost"], "cost": 500, "risks": 0.2, "expected_profit": 1200, "payback_days": 60},
            {"option_id": "overtime", "pros": ["fast"], "cons": ["burnout"], "cost": 200, "risks": 0.35, "expected_profit": 400, "payback_days": 20},
        ]
    )
    assert cmp_["best"]["option_id"] in ("hire", "overtime")

    owner = suite.owner_decide(action="approve", actor="platform_owner", scenario_id="scn_hire")
    assert owner["approved"] is True
    assert owner["deployed"] is False
    assert owner["ai_may_act"] is False

    with pytest.raises(ValidationError):
        suite.what_if(question="teleport_branch")


def test_bootstrap_esl():
    suite = enterprise_hub.simulation_lab
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "7.5.0"
    assert boot["simulation_lab_ready"] is True
    assert boot["sandbox"] is True
    assert boot["ai_may_act"] is False
    assert boot["council_debated"] is True
    assert boot["duplicates_core_logic"] is False
    assert boot["integrations"]["linked"] is True


@pytest.mark.asyncio
async def test_api_esl(client):
    health = await client.get(f"{ESL}/health")
    body = await health.json()
    assert body["application_version"] == "7.5.0"
    assert body["simulation_lab_ready"] is True

    boot = await client.post(f"{ESL}/bootstrap", json={})
    assert boot.status == 201
    assert (await boot.json())["what_if_ready"] is True

    for prefix in PREFIXES:
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        payload = await resp.json()
        version = payload.get("application_version") or payload.get("data", {}).get("application_version")
        assert version == "7.5.0"


def test_docs_and_regression_24_4():
    for name in (
        "ENTERPRISE_SIMULATION_LAB.md",
        "ESL_REGISTRY_ENGINE.md",
        "ESL_IMPACT_COMPARE.md",
        "ESL_DEBATE_OWNER.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_SIMULATION_LAB.md").exists()
    assert (ROOT / "platform_enterprise_simulation_lab" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "simulation_lab" / "facade.py").exists()

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
    assert '"application_version": "7.5.0"' in manifest
    assert "24.5" in manifest
