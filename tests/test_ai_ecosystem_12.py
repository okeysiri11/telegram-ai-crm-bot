"""Tests — Unified AI Ecosystem Integration (Sprint 12.0)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.ecosystem import ai_ecosystem
from applications.ecosystem.api.register import register_ai_ecosystem_routes


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/ai-ecosystem/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_ai_ecosystem_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    ai_ecosystem.reset()
    yield
    ai_ecosystem.reset()


def test_version_unified_ready():
    health = ai_ecosystem.health()
    assert health["application_version"] == "3.0.0-alpha"
    assert health["unified_ai_ecosystem_ready"] is True
    assert health["cross_platform_integration_ready"] is True
    assert health["global_knowledge_graph_ready"] is True
    assert health["chief_ai_ready"] is True
    assert health["executive_dashboard_ready"] is True
    assert health["engines"]["unified_ai"] == "1.0"


def test_bootstrap_registry_and_integration():
    boot = ai_ecosystem.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["applications"]["count"] >= 5
    reg = ai_ecosystem.manager.application_registry()
    ids = {a["app_id"] for a in reg["applications"]}
    for expected in ("crm", "auto_marketplace", "agro_marketplace", "port_erp", "drone_platform", "knowledge_system"):
        assert expected in ids
    assert ai_ecosystem.communication.status()["ready"] is True
    xchg = ai_ecosystem.communication.exchange(
        source_app="drone_platform",
        target_app="port_erp",
        exchange_type="events",
        payload={"note": "berth clearance"},
    )
    assert xchg["status"] == "delivered"
    mem = ai_ecosystem.memory.connect_application(app_id="auto_marketplace")
    assert mem["connected"] is True
    assert "semantic_memory" in mem["engines"]


def test_auth_dashboard_search_knowledge_ai():
    session = ai_ecosystem.identity.sso_login(principal="exec@example.com", role="executive")
    assert session["authenticated"] is True
    org = ai_ecosystem.identity.create_organization(name="Acme Group")
    dep = ai_ecosystem.identity.create_department(org_id=org["org_id"], name="Ops")
    team = ai_ecosystem.identity.create_team(department_id=dep["department_id"], name="Fleet")
    assert team["team_id"]
    ai_ecosystem.identity.grant_role(principal="exec@example.com", role="admin")
    assert ai_ecosystem.identity.list_audit()

    boards = ai_ecosystem.dashboard.all_dashboards()
    assert boards["executive"]["type"] == "executive_dashboard"
    assert boards["crm"]["type"] == "crm_dashboard"
    assert boards["port"]["type"] == "port_dashboard"

    hits = ai_ecosystem.search.global_search(query="drone")
    assert hits["count"] >= 1
    assert ai_ecosystem.search.semantic_search(query="warehouse")["mode"] == "semantic"

    graph = ai_ecosystem.knowledge.build_graph()
    assert len(graph["nodes"]) >= 8
    assert graph["source_count"] >= 1

    agents = ai_ecosystem.ai.list_agents()
    assert any(a["agent_id"] == "chief" for a in agents)
    assert any(a["status"] == "future" for a in agents)
    collab = ai_ecosystem.ai.chief(query="cross-platform status")
    assert collab["engine"] == "platform_multi_agent"
    assert collab["contributions"]

    rpt = ai_ecosystem.analytics.report(report_type="ai")
    assert rpt["status"] == "generated"
    assert ai_ecosystem.gateway.route(app_id="drone_platform")["routed"] is True


@pytest.mark.asyncio
async def test_api_ai_ecosystem(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "3.0.0-alpha"
    assert body["unified_ai_ecosystem_ready"] is True

    boot = await client.post(f"{PREFIX}/bootstrap", json={})
    assert boot.status == 201

    reg = await client.get(f"{PREFIX}/registry")
    assert reg.status == 200
    assert (await reg.json())["count"] >= 5

    agents = await client.post(f"{PREFIX}/agents", json={"action": "chief", "query": "hello"})
    assert agents.status == 200

    auth = await client.post(f"{PREFIX}/auth", json={"principal": "u1", "role": "operator"})
    assert auth.status == 201

    dash = await client.get(f"{PREFIX}/dashboard")
    assert dash.status == 200
    assert "executive" in await dash.json()

    search = await client.post(f"{PREFIX}/search", json={"query": "orders", "mode": "global"})
    assert search.status == 200

    know = await client.post(f"{PREFIX}/knowledge", json={})
    assert know.status == 201
    assert (await know.json())["nodes"]


def test_docs_and_manifest_12_0():
    for name in ("AI_ECOSYSTEM.md", "APPLICATIONS.md", "UNIFIED_DASHBOARD.md", "AI_AGENTS.md", "KNOWLEDGE_GRAPH.md"):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "UNIFIED_AI_ECOSYSTEM.md").exists()
    manifest = (ROOT / "applications" / "ecosystem" / "manifest.json").read_text()
    assert "3.0.0-alpha" in manifest
    assert "12.0" in manifest
    # Ensure we did not claim to modify platform core
    assert "does_not_modify" in manifest


def test_does_not_rewrite_existing_apps():
    # Integration-only: existing app versions remain independently owned
    from applications.drone_platform import drone_platform
    from applications.agro_marketplace import agro_marketplace

    assert drone_platform.health()["application_version"]
    assert agro_marketplace.health()["application_version"]
    # Top-level ecosystem untouched
    from ecosystem.config import DEFAULT_CONFIG as ECO_CFG

    assert ECO_CFG.ecosystem_version == "1.5.0-alpha"
