"""Tests — Enterprise Simulation & Decision Intelligence (Sprint 20.9)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from applications.enterprise_hub.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
HUB = "/api/enterprise-hub/v1"
ORCH = "/api/enterprise-orch/v1"
KG = "/api/enterprise-kg/v1"
AA = "/api/enterprise-agents/v1"
CM = "/api/enterprise-comms/v1"
WF = "/api/enterprise-workflow/v1"
EIP = "/api/enterprise-eip/v1"
EDP = "/api/enterprise-edp/v1"
ISAM = "/api/enterprise-isam/v1"
OBS = "/api/enterprise-obs/v1"
TN = "/api/enterprise-tenancy/v1"
AOP = "/api/enterprise-aop/v1"
ATS = "/api/enterprise-ats/v1"
EKP = "/api/enterprise-ekp/v1"
AIOS = "/api/enterprise-aios/v1"
EVP = "/api/enterprise-evp/v1"
SDP = "/api/enterprise-sdp/v1"
EDF = "/api/enterprise-edf/v1"
EDT = "/api/enterprise-edt/v1"
ESI = "/api/enterprise-esi/v1"


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


def test_version_esi_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "6.6.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v6.5.0"
    assert health["simulation_engine_ready"] is True
    assert health["decision_intelligence_ready"] is True
    assert health["forecasting_ready"] is True
    assert health["risk_engine_ready"] is True
    assert health["recommendation_engine_ready"] is True
    assert health["digital_twin_ready"] is True
    assert health["engines"]["simulation_engine"] == "1.0"


def test_scenario_decision_monte_carlo():
    suite = enterprise_hub.simulation_engine
    scn = suite.finance.build(
        question="What if cost rises 10%?",
        kind="resource_cost_change",
        parameters={"cost_pct": 10},
    )
    run = suite.scenarios.run(scenario_id=scn["scenario_id"])
    assert run["run_id"]
    dec = suite.decisions.evaluate(
        options=[
            {"option_id": "a", "label": "A", "profit": 70, "cost": 40, "risk": 30, "time": 20, "efficiency": 60, "success_probability": 80},
            {"option_id": "b", "label": "B", "profit": 40, "cost": 20, "risk": 50, "time": 10, "efficiency": 50, "success_probability": 90},
        ]
    )
    assert dec["best_option"]
    mc = suite.monte_carlo.run(iterations=50, mean=100, stdev=10, seed=1)
    assert mc["p50"]
    sens = suite.sensitivity.analyze(parameters={"fuel_cost": 1.0, "demand": 1.0})
    assert sens["top_driver"] == "fuel_cost"
    rec = suite.recommendation_engine.generate(scenario_id=scn["scenario_id"], decision_id=dec["decision_id"])
    assert rec["top_action"] in (
        "increase_inventory",
        "reschedule_delivery",
        "redistribute_workforce",
        "change_production_schedule",
        "acquire_equipment",
    )
    with pytest.raises(ValidationError):
        suite.decisions.evaluate(options=[{"option_id": "only"}])


def test_bootstrap_dashboard():
    suite = enterprise_hub.simulation_engine
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "6.6.0"
    assert boot["schedule_completed"] is True
    assert boot["event_triggered"] is True
    assert boot["continuous_ticks"] >= 1
    assert boot["top_recommendation"]
    assert boot["integrations_linked"] == 7
    assert boot["best_option"]
    assert boot["critical_risks"]
    assert boot["top_driver"]
    dash = boot["dashboard"]
    assert dash["confidence_id"]
    assert dash["executive_id"]
    assert "success_probability" in dash
    assert "potential_profit" in dash
    assert "potential_loss" in dash
    assert "ai_recommendations" in dash
    assert "decision_history" in dash
    assert dash["active_scenario_count"] >= 1


@pytest.mark.asyncio
async def test_api_esi(client):
    health = await client.get(f"{ESI}/health")
    body = await health.json()
    assert body["application_version"] == "6.6.0"
    assert body["simulation_engine_ready"] is True
    assert body["recommendation_engine_ready"] is True

    boot = await client.post(f"{ESI}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    created = await client.post(
        f"{ESI}/scenarios",
        json={"domain": "custom", "question": "What if X?", "kind": "what_if", "parameters": {"shock_pct": 5}},
    )
    assert created.status == 201

    rec = await client.post(
        f"{ESI}/recommendations",
        json={"scenario_id": boot_body["scenario_ids"][2], "decision_id": boot_body["decision_id"]},
    )
    assert rec.status == 201

    for prefix in (HUB, ORCH, KG, AA, CM, WF, EIP, EDP, ISAM, OBS, TN, AOP, ATS, EKP, AIOS, EVP, SDP, EDF, EDT):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "6.6.0"

    assert boot_body["decision_id"]
    assert boot_body["recommendation_id"]


def test_docs_and_regression_20_9():
    for name in (
        "ENTERPRISE_SIMULATION.md",
        "ESI_SCENARIOS.md",
        "ESI_FORECAST_OPT.md",
        "ESI_RISK_MC.md",
        "ESI_RECOMMENDATIONS_DASHBOARD.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_SIMULATION.md").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "simulation_engine" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "simulation_engine" / "recommendation_engine.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "simulation_engine" / "integrations.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "simulation_engine" / "scenarios" / "maritime.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "simulation_engine" / "optimization" / "engine.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "digital_twin").exists()

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
    assert "6.6.0" in manifest
    assert "22.5" in manifest
    assert "recommendation_engine" in manifest
