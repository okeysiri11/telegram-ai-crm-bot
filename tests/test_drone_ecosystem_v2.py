"""Tests — Unified Drone AI Ecosystem & Enterprise Certification (Sprint 11.10)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.drone_platform import drone_platform
from applications.drone_platform.api.register import register_drone_platform_routes
from applications.drone_platform.ecosystem.lifecycle import LIFECYCLE_STAGES
from applications.drone_platform.ecosystem.unified_twin import TWIN_TYPES


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/drone/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_drone_platform_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    drone_platform.reset()
    yield
    drone_platform.reset()


def test_version_enterprise_certified():
    health = drone_platform.health()
    assert health["application_version"] == "2.0.0"
    assert health["unified_drone_ai_ecosystem_ready"] is True
    assert health["full_lifecycle_ready"] is True
    assert health["executive_dashboard_ready"] is True
    assert health["drone_platform_enterprise_certified"] is True
    assert health["enterprise_certification_passed"] is True
    assert health["engines"]["drone_ecosystem"] == "1.0"
    assert health["engines"]["ai"] == "2.0"
    assert health["drone_ecosystem_status"]["ready"] is True


def test_ecosystem_manager_integration_lifecycle_twins():
    eco = drone_platform.drone_ecosystem
    boot = eco.bootstrap()
    assert boot["integration"]["count"] >= 10
    reg = eco.manager.unified_registry()
    assert reg["count"] >= 10
    search = eco.manager.unified_search(query="cloud")
    assert search["count"] >= 1
    assert eco.manager.unified_knowledge()["nodes"]
    assert eco.manager.unified_dashboard()["modules_connected"] >= 10
    evt = eco.manager.publish_event(topic="test.ping", payload={"ok": True})
    assert evt["event_id"]
    sync = eco.manager.cross_module_sync()
    assert sync["status"] == "completed"
    assert eco.integration.verify()["ok"] is True

    life = eco.lifecycle.start(aircraft_id="AC-100", stage="design")
    for _ in range(3):
        life = eco.lifecycle.advance(life["lifecycle_id"])
    assert life["stage"] in LIFECYCLE_STAGES
    assert eco.lifecycle.timeline(life["lifecycle_id"])["history"]

    for twin_type in TWIN_TYPES:
        twin = eco.twins.create(twin_type=twin_type, name=f"{twin_type}-twin", source_id="src1")
        synced = eco.twins.sync(twin["twin_id"], state={"tick": 1})
        assert synced["synced"] is True
    assert eco.twins.sync_all()["synced"] == len(TWIN_TYPES)


def test_dashboards_reports_ai_certification():
    eco = drone_platform.drone_ecosystem
    boards = eco.dashboards.all_dashboards()
    assert boards["executive"]["type"] == "executive_dashboard"
    assert boards["ai"]["type"] == "ai_dashboard"
    assert boards["financial"]["type"] == "financial_dashboard"

    for report_type in ("executive", "engineering", "production", "mission", "maintenance", "fleet", "performance", "ai_decision"):
        rpt = eco.reporting.generate(report_type=report_type, period="monthly")
        assert rpt["status"] == "generated"
        assert rpt["sections"]

    caps = drone_platform.ai.capabilities()
    assert "chief_drone_ai" in caps
    assert "multi_agent_collaborate" in caps
    collab = drone_platform.ai.assist(
        agent="multi_agent_collaborate",
        query="prepare release",
        context={"agents": ["engineering", "mission", "fleet", "cloud"]},
    )
    assert collab["agent"] == "multi_agent_collaborate"
    assert len(collab["response"]["contributions"]) == 4
    chief = drone_platform.ai.assist(agent="chief_drone_ai", query="status")
    assert chief["response"]["role"] == "chief"

    cert = eco.certification.run(version="2.0.0")
    assert cert["passed"] is True
    assert cert["enterprise_certification_report"]["status"] == "passed"
    assert cert["coverage_report"]
    assert cert["architecture_report"]
    assert cert["performance_report"]
    failed = [c for c in cert["checks"] if not c["passed"]]
    assert failed == []


@pytest.mark.asyncio
async def test_api_ecosystem(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "2.0.0"
    assert body["drone_platform_enterprise_certified"] is True

    status = await client.get(f"{PREFIX}/ecosystem")
    assert status.status == 200
    assert (await status.json())["ready"] is True

    boot = await client.post(f"{PREFIX}/ecosystem/bootstrap", json={})
    assert boot.status == 201

    reg = await client.get(f"{PREFIX}/ecosystem/registry")
    assert reg.status == 200
    assert (await reg.json())["count"] >= 1

    search = await client.post(f"{PREFIX}/ecosystem/search", json={"query": "mission"})
    assert search.status == 200

    life = await client.post(f"{PREFIX}/ecosystem/lifecycle", json={"aircraft_id": "AC-1", "stage": "design"})
    assert life.status == 201

    twin = await client.post(f"{PREFIX}/ecosystem/twins", json={"twin_type": "aircraft", "name": "A1"})
    assert twin.status == 201

    exec_dash = await client.get(f"{PREFIX}/ecosystem/executive")
    assert exec_dash.status == 200
    assert "executive" in await exec_dash.json()

    rpt = await client.post(f"{PREFIX}/ecosystem/reports", json={"report_type": "executive"})
    assert rpt.status == 201

    cert = await client.post(f"{PREFIX}/ecosystem/certification", json={"version": "2.0.0"})
    assert cert.status == 201
    assert (await cert.json())["passed"] is True


def test_docs_and_knowledge_11_10():
    for name in ("DRONE_PLATFORM.md", "DRONE_ECOSYSTEM.md", "DRONE_AI.md", "ENTERPRISE_CERTIFICATION.md"):
        assert (ROOT / "docs" / name).exists()
    for name in (
        "KNOWLEDGE_GRAPH.md",
        "ARCHITECTURE_GRAPH.md",
        "DEPENDENCY_GRAPH.md",
        "AI_REGISTRY.md",
        "DRONE_REGISTRY.md",
        "ENTERPRISE_DASHBOARD.md",
        "DRONE_DASHBOARD.md",
    ):
        assert (ROOT / "knowledge" / "drone" / name).exists()
    manifest = (ROOT / "applications" / "drone_platform" / "manifest.json").read_text()
    assert "2.0.0" in manifest
    assert "11.10" in manifest
    assert "enterprise_certified" in manifest
