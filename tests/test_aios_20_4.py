"""Tests — Enterprise Autonomous AIOS (Sprint 20.4)."""

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


def test_version_aios_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "6.2.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v6.1.0"
    assert health["autonomous_aios_ready"] is True
    assert health["goal_manager_ready"] is True
    assert health["checkpoint_recovery_ready"] is True
    assert health["aios_governance_ready"] is True
    assert health["enterprise_knowledge_ready"] is True
    assert health["engines"]["aios"] == "1.0"


def test_run_goal_recovery_governance():
    suite = enterprise_hub.aios
    run = suite.aios.run_goal(title="QA autonomous goal", mode="sequential", budget=5.0)
    assert run["execution_id"] and run["status"] in ("completed", "partial")
    task = suite.queue.enqueue(title="to recover")
    suite.states.transition(task_id=task["task_id"], state="failed", note="boom")
    suite.checkpoints.save(task_id=task["task_id"])
    rec = suite.recovery.recover(task_id=task["task_id"], action="retry")
    assert rec["recovery_id"]
    blocked = suite.safety.evaluate(operation="drop_database")
    assert blocked["allowed"] is False
    with pytest.raises(ValidationError):
        suite.goals.create(title="")


def test_bootstrap_dashboard():
    suite = enterprise_hub.aios
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "6.2.0"
    assert boot["recovery_id"] and boot["dashboard"]["productivity_id"]
    assert "collaborative" in boot["modes"]


@pytest.mark.asyncio
async def test_api_aios(client):
    health = await client.get(f"{AIOS}/health")
    body = await health.json()
    assert body["application_version"] == "6.2.0"
    assert body["autonomous_aios_ready"] is True

    boot = await client.post(f"{AIOS}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    created = await client.post(f"{AIOS}/goals", json={"title": "API Goal", "priority": "high"})
    assert created.status == 201

    for prefix in (HUB, ORCH, KG, AA, CM, WF, EIP, EDP, ISAM, OBS, TN, AOP, ATS, EKP):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "6.2.0"

    assert boot_body["run_sequential"]["plan_id"]


def test_docs_and_regression_20_4():
    for name in (
        "ENTERPRISE_AIOS.md",
        "AIOS_GOALS.md",
        "AIOS_EXECUTION.md",
        "AIOS_RECOVERY.md",
        "AIOS_GOVERNANCE.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_AIOS.md").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "ai_os" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "ai_os" / "execution" / "parallel.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "ai_os" / "governance" / "safety.py").exists()
    # frozen platform AI OS untouched
    assert (ROOT / "applications" / "ai_os").exists()

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
    assert "6.2.0" in manifest
    assert "22.1" in manifest
