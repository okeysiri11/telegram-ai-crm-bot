"""Tests — Enterprise AI Orchestration Platform (Sprint 20.1)."""

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


def test_version_aop_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "5.4.8-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v5.4.7-enterprise"
    assert health["ai_orchestration_ready"] is True
    assert health["agent_registry_ready"] is True
    assert health["task_planning_ready"] is True
    assert health["result_aggregation_ready"] is True
    assert health["multi_tenant_ready"] is True
    assert health["engines"]["ai_orchestrator"] == "1.0"
    assert health["engines"]["orchestrator"] == "1.0"


def test_registry_orchestrate_policy():
    suite = enterprise_hub.ai_orchestrator
    legal = suite.registry.register(name="Legal", specialization="legal", cost_per_task=0.04)
    suite.registry.register(name="Finance", specialization="finance")
    suite.registry.register(name="CRM", specialization="crm")
    suite.registry.register(name="Writer", specialization="writer")
    suite.registry.register(name="Agg", specialization="aggregator")
    suite.policy.define(kind="cost_quality", name="cap", rules={"max_cost": 50})
    run = suite.orchestrator.orchestrate(
        request="Подготовить коммерческое предложение.", strategy="sequential"
    )
    assert run["task_id"] and run["aggregation_id"] and run["result"]["ok"] is True
    with pytest.raises(ValidationError):
        suite.registry.register(name="", specialization="x")
    assert legal["agent_id"]


def test_bootstrap_analytics():
    suite = enterprise_hub.ai_orchestrator
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "5.4.8-enterprise"
    assert boot["execution_id"] and boot["performance_id"] and boot["cost_id"]
    assert "sequential" in boot["strategies"]


@pytest.mark.asyncio
async def test_api_aop(client):
    health = await client.get(f"{AOP}/health")
    body = await health.json()
    assert body["application_version"] == "5.4.8-enterprise"
    assert body["ai_orchestration_ready"] is True

    boot = await client.post(f"{AOP}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    created = await client.post(
        f"{AOP}/agents",
        json={"name": "Ops", "specialization": "ops"},
    )
    assert created.status == 201

    for prefix in (HUB, ORCH, KG, AA, CM, WF, EIP, EDP, ISAM, OBS, TN):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "5.4.8-enterprise"

    assert boot_body["aggregation_id"]


def test_docs_and_regression_20_1():
    for name in (
        "ENTERPRISE_AI_ORCHESTRATION.md",
        "AOP_AGENTS.md",
        "AOP_PLANNING.md",
        "AOP_CONTEXT_MEMORY.md",
        "AOP_ANALYTICS.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_AI_ORCHESTRATION.md").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "ai_orchestrator" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "ai_orchestrator" / "agents" / "registry.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "ai_orchestrator" / "strategies" / "parallel.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "ai_orchestrator" / "analytics" / "costs.py").exists()

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
    assert "5.4.8-enterprise" in manifest
    assert "20.8" in manifest
