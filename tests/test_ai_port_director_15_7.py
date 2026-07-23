"""Tests — AI Port Director, Predictive & Autonomous Ops (Sprint 15.7)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.port_enterprise import port_enterprise
from applications.port_enterprise.api.register import register_port_enterprise_routes
from applications.port_enterprise.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/port-ai-director/v1"
FM = "/api/port-freight/v1"
WD = "/api/port-warehouse/v1"
CT = "/api/port-customs/v1"
ML = "/api/port-multimodal/v1"
CM = "/api/port-containers/v1"
NAV = "/api/port-navigation/v1"
PE = "/api/port-enterprise/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_port_enterprise_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    port_enterprise.reset()
    yield
    port_enterprise.reset()


def test_version_ai_director_ready():
    health = port_enterprise.health()
    assert health["application_version"] == "4.6.0-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.5.7-enterprise"
    assert health["ai_port_director_ready"] is True
    assert health["predictive_logistics_ready"] is True
    assert health["autonomous_operations_ready"] is True
    assert health["executive_intelligence_ready"] is True


def test_director_and_decisions():
    suite = port_enterprise.ai_port_director
    ask = suite.director.ask(prompt="Status?", context="port")
    suite.director.advise(advisory_type="cargo", subject="Lot A")
    decision = suite.decisions.decide(topic="Priority berth", options=["A", "B"])
    suite.decisions.scenario(name="Peak day")
    assert ask["assistant_id"] and decision["decision_id"]
    with pytest.raises(ValidationError):
        suite.director.advise(advisory_type="orbit", subject="X")


def test_predictive_autonomous_executive():
    suite = port_enterprise.ai_port_director
    boot = suite.bootstrap()
    assert boot["arrival_id"] and boot["yard_id"] and boot["briefing_id"]
    assert suite.predictive.status()["arrivals"] >= 1
    assert suite.autonomous.status()["dock_schedules"] >= 1
    assert suite.intelligence.status()["risks"] >= 1
    assert suite.executive.status()["briefings"] >= 1
    with pytest.raises(ValidationError):
        suite.executive.health_score(score=150)
    for dtype in (
        "ai_director",
        "decision_support",
        "predictive_logistics",
        "autonomous_operations",
        "executive_intelligence",
    ):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_ai_director(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "4.6.0-enterprise"
    assert body["ai_port_director_ready"] is True
    assert body["executive_intelligence_ready"] is True

    assert (await client.get(f"{FM}/health")).status == 200
    assert (await client.get(f"{WD}/health")).status == 200
    assert (await client.get(f"{CT}/health")).status == 200
    assert (await client.get(f"{ML}/health")).status == 200
    assert (await client.get(f"{CM}/health")).status == 200
    assert (await client.get(f"{NAV}/health")).status == 200
    assert (await client.get(f"{PE}/health")).status == 200

    boot = await client.post(f"{PREFIX}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    auto = await client.post(
        f"{PREFIX}/autonomous",
        json={"action": "yard", "yard_ref": "Yard North"},
    )
    assert auto.status == 201

    exec_resp = await client.post(
        f"{PREFIX}/executive",
        json={"action": "health", "score": 90},
    )
    assert exec_resp.status == 201
    assert boot_body["decision_id"]

    dash = await client.get(f"{PREFIX}/dashboard?type=predictive_logistics")
    assert dash.status == 200


def test_docs_and_regression_15_7():
    for name in (
        "AI_PORT_DIRECTOR.md",
        "PREDICTIVE_LOGISTICS.md",
        "AUTONOMOUS_PORT_OPERATIONS.md",
        "EXECUTIVE_INTELLIGENCE.md",
        "DECISION_SUPPORT.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "PORT_AI_DIRECTOR.md").exists()
    assert (ROOT / "applications" / "port_enterprise" / "ai_port_director" / "facade.py").exists()
    assert (ROOT / "applications" / "port_enterprise" / "freight_marketplace" / "facade.py").exists()

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT
    from applications.auto_marketplace.config import DEFAULT_CONFIG as AUTO
    from applications.agro_enterprise.config import DEFAULT_CONFIG as AGRO
    from applications.port_erp.config import DEFAULT_CONFIG as PORT_ERP

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AUTO.application_version == "4.2.0-enterprise"
    assert AGRO.application_version == "4.4.0-enterprise"
    assert PORT_ERP.application_version == "2.0.0"
    manifest = (ROOT / "applications" / "port_enterprise" / "manifest.json").read_text()
    assert "4.6.0-enterprise" in manifest
    assert "15.8" in manifest
