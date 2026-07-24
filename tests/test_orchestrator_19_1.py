"""Tests — AI Orchestrator & Workflow Engine (Sprint 19.1)."""

from __future__ import annotations

import time
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


def test_version_orchestrator_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "5.4.10-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v5.4.9-enterprise"
    assert health["ai_orchestrator_ready"] is True
    assert health["workflow_engine_ready"] is True
    assert health["cross_platform_routing_ready"] is True
    assert health["ai_decision_engine_ready"] is True
    assert health["enterprise_hub_foundation_ready"] is True
    assert health["engines"]["orchestrator"] == "1.0"


def test_workflow_and_routing():
    suite = enterprise_hub.orchestrator
    wf = suite.core.register_workflow(name="QA Flow", kind="sequential", steps=["a", "b"])
    plan = suite.core.plan(workflow_id=wf["workflow_id"])
    exe = suite.core.execute(workflow_id=wf["workflow_id"], plan_id=plan["plan_id"])
    route = suite.routing.route(platform="finance", action="payment_post")
    assert exe["execution_id"] and route["route_id"]
    with pytest.raises(ValidationError):
        suite.core.register_workflow(name="", kind="sequential")


def test_decisions_bootstrap():
    suite = enterprise_hub.orchestrator
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "5.4.10-enterprise"
    assert boot["execution_id"] and boot["coordination_id"] and boot["explain_nl_id"]
    assert suite.decisions.decide(
        decision_type="recommendation", subject="QA"
    )["decision_type"] == "recommendation"
    for dtype in ("orchestrator", "workflow", "execution", "platform_activity", "ai_decision"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_orchestrator(client):
    health = await client.get(f"{ORCH}/health")
    body = await health.json()
    assert body["application_version"] == "5.4.10-enterprise"
    assert body["ai_orchestrator_ready"] is True
    assert body["ai_decision_engine_ready"] is True

    boot = await client.post(f"{ORCH}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    rt = await client.post(
        f"{ORCH}/routing",
        json={"platform": "legal", "task": "contract_billing"},
    )
    assert rt.status == 201

    dec = await client.post(
        f"{ORCH}/decisions",
        json={"decision_type": "platform_selection", "subject": "QA", "selected": "finance"},
    )
    assert dec.status == 201

    hub = await client.get(f"{HUB}/health")
    assert hub.status == 200
    assert (await hub.json())["application_version"] == "5.4.10-enterprise"
    assert boot_body["intent_id"]


def test_performance_bootstrap():
    suite = enterprise_hub.orchestrator
    started = time.perf_counter()
    boot = suite.bootstrap()
    elapsed = time.perf_counter() - started
    assert boot["bootstrap"] is True
    assert elapsed < 2.0


def test_docs_and_regression_19_1():
    for name in (
        "AI_ORCHESTRATOR.md",
        "WORKFLOW_ENGINE.md",
        "CROSS_PLATFORM_ROUTING.md",
        "EXECUTION_ENGINE.md",
        "AI_DECISION_ENGINE.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "AI_ORCHESTRATOR.md").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "orchestrator" / "facade.py").exists()

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
    assert "5.4.10-enterprise" in manifest
    assert "20.10" in manifest
