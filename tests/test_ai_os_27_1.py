"""Tests — Enterprise Multi-Agent Operating System (Sprint 27.2 / v9.4.0)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from platform_ai_os.models import (
    ARCHITECTURE,
    BUS_MESSAGE_TYPES,
    COLLABORATION_ACTIONS,
    KPI_TARGETS,
    MEMORY_LAYERS,
    ORCHESTRATOR_MODES,
    PRINCIPLES,
    VERSION,
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
    "/api/enterprise-est/v1",
    "/api/enterprise-ele/v1",
    "/api/enterprise-aph/v1",
    "/api/enterprise-ees/v1",
    "/api/enterprise-eti/v1",
    "/api/enterprise-epl/v1",
    "/api/enterprise-ece/v1",
    "/api/enterprise-emr/v1",
    "/api/enterprise-esv/v1",
    "/api/enterprise-epd/v1",
    "/api/enterprise-ecf/v1",
    "/api/enterprise-ewf/v1",
    "/api/enterprise-eds/v1",
    "/api/enterprise-eic/v1",
    "/api/enterprise-ews/v1",
    "/api/enterprise-enp/v1",
    "/api/enterprise-command/v1",
    "/api/enterprise-navigation/v1",
    "/api/release/v1",
]
AIOS = "/api/ai-os/v1"
MAOS = f"{AIOS}/maos"


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


def test_version_enterprise_ai_os_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "9.4.0"
    assert health["enterprise_ai_os_ready"] is True
    assert health["executive_ai_ready"] is True
    assert health["agent_registry_v2_ready"] is True
    assert health["task_orchestrator_ready"] is True
    assert health["ai_collaboration_ready"] is True
    assert health["engines"]["enterprise_ai_os"] == "1.0"
    assert VERSION == "9.4.0"
    assert "executive_ai_director" in ARCHITECTURE
    assert "request" in BUS_MESSAGE_TYPES
    assert "parallel" in ORCHESTRATOR_MODES
    assert "semantic" in MEMORY_LAYERS
    assert "vote" in COLLABORATION_ACTIONS
    assert KPI_TARGETS["executive_ai_ready"] is True
    assert "phase4_enterprise_ai_os" in PRINCIPLES


def test_executive_registry_bus_orchestrator_memory_collaboration():
    suite = enterprise_hub.enterprise_ai_os
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["hub_version"] == "9.4.0"
    assert boot["executive_ai_ready"] is True
    assert boot["agent_registry_ready"] is True
    assert boot["communication_bus_ready"] is True
    assert boot["task_orchestrator_ready"] is True
    assert boot["memory_manager_ready"] is True
    assert boot["collaboration_ready"] is True
    assert boot["ai_os_path_exists"] is True
    assert boot["dashboard_page_exists"] is True
    assert boot["hub_bridge_exists"] is True

    exec_result = suite.executive("Prepare CRM sales weekly report with finance summary")
    assert exec_result["status"] == "completed"
    assert exec_result["controlled"] is True
    assert len(exec_result["assignments"]) >= 2
    assert exec_result["merged"]["consensus"] is True

    registry = suite.agents()
    assert registry["version"] == "2.0"
    assert registry["count"] >= 8
    agent = registry["agents"][0]
    for key in ("name", "role", "status", "load", "capabilities", "cost", "speed", "memory", "models"):
        assert key in agent

    bus_msg = suite.bus_publish(
        "broadcast",
        sender="agent_director",
        payload={"hello": True},
        priority=1,
    )
    assert bus_msg["ok"] is True
    bus = suite.bus()
    assert bus["queue_depth"] >= 1
    assert "priority_queue_depth" in bus

    orch = suite.orchestrate(name="pipeline", mode="parallel", retry=1, timeout_ms=5000)
    assert orch["ok"] is True
    assert orch["mode"] == "parallel"
    assert set(orch["policies"]) >= {"retry", "rollback", "timeout"}

    mem = suite.memory_write(layer="workspace", content="workspace note")
    assert mem["ok"] is True
    snap = suite.memory()
    assert snap["counts"]["workspace"] >= 1

    collab = suite.collaborate(topic="best pricing strategy", action="merge")
    assert collab["ok"] is True
    assert collab["best"]
    assert collab["merged"]

    dash = suite.dashboard()
    assert dash["title"] == "AI Executive Dashboard"
    assert "active_agents" in dash
    assert "task_history" in dash


@pytest.mark.asyncio
async def test_api_enterprise_ai_os(client):
    health = await client.get(f"{MAOS}/health")
    body = await health.json()
    assert body["application_version"] == "9.4.0"
    assert body["enterprise_ai_os_ready"] is True

    boot = await client.post(f"{MAOS}/bootstrap", json={})
    assert boot.status == 201
    assert (await boot.json())["executive_ai_ready"] is True

    inv = await client.get(f"{MAOS}/inventory")
    assert inv.status == 200

    agents = await client.get(f"{AIOS}/agents")
    assert agents.status == 200
    assert (await agents.json())["count"] >= 8

    exe = await client.post(f"{AIOS}/executive", json={"goal": "Open CRM and summarize leads"})
    assert exe.status == 200
    assert (await exe.json())["status"] == "completed"

    tasks = await client.post(
        f"{AIOS}/tasks",
        json={"name": "seq", "mode": "sequential", "retry": 1},
    )
    assert tasks.status == 200
    assert (await tasks.json())["ok"] is True

    bus = await client.post(
        f"{AIOS}/agent-bus",
        json={"type": "event", "sender": "agent_ops", "payload": {"ping": True}},
    )
    assert bus.status == 200

    mem = await client.post(
        f"{AIOS}/memory-layers",
        json={"layer": "short", "content": "hello"},
    )
    assert mem.status == 200

    collab = await client.post(
        f"{AIOS}/collaborate",
        json={"topic": "architecture", "action": "vote"},
    )
    assert collab.status == 200

    dash = await client.get(f"{AIOS}/exec-dashboard")
    assert dash.status == 200

    # prior platforms healthy
    for prefix in ("/api/release/v1", "/api/enterprise-navigation/v1", "/api/enterprise-command/v1", "/api/enterprise-aios/v1"):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "9.4.0"

    for prefix in PREFIXES:
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        data = await resp.json()
        version = data.get("application_version") or data.get("data", {}).get("application_version")
        assert version == "9.4.0"


def test_docs_and_regression_27_1():
    assert (ROOT / "docs" / "ENTERPRISE_AI_OS.md").exists()
    assert (ROOT / "platform_ai_os" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "enterprise_ai_os" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "ai_os" / "enterprise_multi_agent.py").exists()
    assert (ROOT / "src" / "web" / "ai-os" / "pages" / "AIOSPage.tsx").exists()
    assert (ROOT / "knowledge" / "applications" / "enterprise_hub" / "ai_os" / "README.md").exists()

    docs = (ROOT / "docs" / "ENTERPRISE_AI_OS.md").read_text()
    for key in ("Executive AI", "Agent Registry 2.0", "Task Orchestrator", "Collaboration"):
        assert key in docs

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS_CFG
    from applications.enterprise.config import DEFAULT_CONFIG as ENT
    from applications.auto_marketplace.config import DEFAULT_CONFIG as AUTO

    assert AIOS_CFG.api_prefix == "/api/ai-os/v1"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AUTO.application_version == "4.2.0-enterprise"
    manifest = (ROOT / "applications" / "enterprise_hub" / "manifest.json").read_text()
    assert '"application_version": "9.4.0"' in manifest
    assert "27.3" in manifest
