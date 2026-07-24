"""Tests — Enterprise Workflow & Business Process Engine (Sprint 19.5)."""

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


def test_version_workflow_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "6.0.0-rc6"
    assert health["enterprise_foundation"] == "Enterprise Platform v6.0.0-rc5"
    assert health["enterprise_workflow_ready"] is True
    assert health["workflow_builder_ready"] is True
    assert health["approval_engine_ready"] is True
    assert health["workflow_scheduler_ready"] is True
    assert health["enterprise_communications_ready"] is True
    assert health["engines"]["workflow"] == "1.0"


def test_builder_engine_approval_scheduler():
    suite = enterprise_hub.workflow
    wf = suite.manager.create(
        name="QA Flow",
        trigger="api",
        blocks=[
            {"type": "start"},
            {"type": "approval", "config": {"mode": "auto"}},
            {"type": "notification", "config": {"channel": "email", "target": "qa@bidex.io"}},
            {"type": "finish"},
        ],
    )
    suite.manager.publish(workflow_id=wf["workflow_id"])
    assert suite.validator.validate(workflow_id=wf["workflow_id"])["valid"] is True
    run = suite.engine.run(workflow_id=wf["workflow_id"], executor="qa", context={"status": "open"})
    assert run["result"] == "completed"
    sched = suite.scheduler.schedule(workflow_id=wf["workflow_id"], kind="cron", expression="0 * * * *")
    assert suite.scheduler.fire(schedule_id=sched["schedule_id"])["fire_id"]
    with pytest.raises(ValidationError):
        suite.manager.create(name="", trigger="api")


def test_templates_optimization_bootstrap():
    suite = enterprise_hub.workflow
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "6.0.0-rc6"
    assert boot["template_invoice_id"] and boot["optimization_id"] and boot["fire_id"]
    tpl = suite.templates.instantiate(kind="customer_support")
    assert tpl["workflow_id"]
    opt = suite.optimization.analyze(workflow_id=boot["workflow_lead_id"])
    assert "suggestions" in opt
    for dtype in ("performance", "approvals", "scheduler", "templates", "optimization"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_workflow(client):
    health = await client.get(f"{WF}/health")
    body = await health.json()
    assert body["application_version"] == "6.0.0-rc6"
    assert body["enterprise_workflow_ready"] is True
    assert body["workflow_builder_ready"] is True

    boot = await client.post(f"{WF}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    created = await client.post(
        f"{WF}/manager",
        json={"name": "API Flow", "trigger": "webhook"},
    )
    assert created.status == 201

    for prefix in (HUB, ORCH, KG, AA, CM):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "6.0.0-rc6"

    assert boot_body["engine_run_lead_id"]


def test_docs_and_regression_19_5():
    for name in (
        "ENTERPRISE_WORKFLOW.md",
        "WORKFLOW_BUILDER.md",
        "WORKFLOW_APPROVALS.md",
        "WORKFLOW_TEMPLATES.md",
        "WORKFLOW_SCHEDULER.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_WORKFLOW.md").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "workflow" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "workflow" / "actions" / "email.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "workflow" / "conditions" / "ai.py").exists()

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
    assert "6.0.0-rc6" in manifest
    assert "21.6" in manifest
