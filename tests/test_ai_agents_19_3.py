"""Tests — Enterprise AI Agents & Autonomous Automation (Sprint 19.3)."""

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


def test_version_agents_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "5.4.3-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v5.4.2-enterprise"
    assert health["enterprise_ai_agents_ready"] is True
    assert health["autonomous_automation_ready"] is True
    assert health["multi_agent_collaboration_ready"] is True
    assert health["ai_agent_governance_ready"] is True
    assert health["unified_knowledge_graph_ready"] is True
    assert health["ai_orchestrator_ready"] is True
    assert health["engines"]["ai_agents"] == "1.0"


def test_agent_automation_collaboration():
    suite = enterprise_hub.ai_agents
    agent = suite.registry.register_agent(
        name="QA Agent",
        agent_type="general",
        capabilities=["qa"],
        permissions=["hub_coordinate"],
    )
    suite.registry.set_lifecycle(agent_id=agent["agent_id"], lifecycle="active")
    task = suite.execution.assign_task(
        agent_id=agent["agent_id"], title="QA run", priority=1, mode="sequential"
    )
    exec_rec = suite.execution.execute(task_id=task["task_id"])
    auto = suite.automation.create(
        name="QA schedule", kind="scheduled", agent_id=agent["agent_id"], schedule="0 * * * *"
    )
    peer = suite.registry.register_agent(name="Peer", agent_type="finance", permissions=["view_treasury"])
    msg = suite.collaboration.communicate(
        from_agent_id=agent["agent_id"],
        to_agent_id=peer["agent_id"],
        message="sync",
    )
    assert exec_rec["execution_id"] and auto["automation_id"] and msg["message_id"]
    with pytest.raises(ValidationError):
        suite.registry.register_agent(name="", agent_type="general")


def test_governance_performance_bootstrap():
    suite = enterprise_hub.ai_agents
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "5.4.3-enterprise"
    assert boot["agent_general_id"] and boot["emergency_stop_id"] and boot["consensus_id"]
    health = suite.governance.health_check(agent_id=boot["agent_general_id"])
    assert health["status"] == "healthy"
    intel = suite.intelligence.insight(
        insight_type="task_optimization", subject="qa", detail="batch"
    )
    assert intel["insight_id"]
    for dtype in ("agents", "automation", "execution", "performance", "governance"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_ai_agents(client):
    health = await client.get(f"{AA}/health")
    body = await health.json()
    assert body["application_version"] == "5.4.3-enterprise"
    assert body["enterprise_ai_agents_ready"] is True
    assert body["autonomous_automation_ready"] is True

    boot = await client.post(f"{AA}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    reg = await client.post(
        f"{AA}/registry",
        json={"name": "API Agent", "agent_type": "legal", "permissions": ["read_cases"]},
    )
    assert reg.status == 201

    for prefix in (HUB, ORCH, KG):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "5.4.3-enterprise"

    assert boot_body["agent_finance_id"]


def test_docs_and_regression_19_3():
    for name in (
        "AI_AGENTS.md",
        "AUTONOMOUS_AUTOMATION.md",
        "MULTI_AGENT_COLLABORATION.md",
        "AI_AGENT_GOVERNANCE.md",
        "ENTERPRISE_AUTOMATION.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "AI_AGENTS.md").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "ai_agents" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "knowledge" / "facade.py").exists()

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT
    from applications.auto_marketplace.config import DEFAULT_CONFIG as AUTO
    from applications.agro_enterprise.config import DEFAULT_CONFIG as AGRO
    from applications.port_enterprise.config import DEFAULT_CONFIG as PORT
    from applications.port_erp.config import DEFAULT_CONFIG as PORT_ERP
    from applications.crypto_enterprise.config import DEFAULT_CONFIG as CRYPTO
    from applications.legal_enterprise.config import DEFAULT_CONFIG as LEGAL
    from applications.finance_enterprise.config import DEFAULT_CONFIG as FINANCE

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AUTO.application_version == "4.2.0-enterprise"
    assert AGRO.application_version == "4.4.0-enterprise"
    assert PORT.application_version == "4.6.0-enterprise"
    assert PORT_ERP.application_version == "2.0.0"
    assert CRYPTO.application_version == "4.8.0-enterprise"
    assert LEGAL.application_version == "5.0.0-enterprise"
    assert FINANCE.application_version == "5.2.0-enterprise"
    manifest = (ROOT / "applications" / "enterprise_hub" / "manifest.json").read_text()
    assert "5.4.3-enterprise" in manifest
    assert "20.3" in manifest
