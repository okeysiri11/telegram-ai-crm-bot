"""Tests — Enterprise AI Tools & Skills (Sprint 20.2)."""

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


def test_version_ats_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "6.0.0-rc6"
    assert health["enterprise_foundation"] == "Enterprise Platform v6.0.0-rc5"
    assert health["ai_tools_ready"] is True
    assert health["skill_engine_ready"] is True
    assert health["tool_sandbox_ready"] is True
    assert health["tool_marketplace_ready"] is True
    assert health["ai_orchestration_ready"] is True
    assert health["engines"]["ai_tools"] == "1.0"


def test_tools_skills_policy():
    suite = enterprise_hub.ai_tools
    suite.policy.define(name="qa", max_cost=1.0)
    tool = suite.tools.register(name="crm.ping", domain="crm", cost_per_call=0.01)
    skill = suite.skills.register(
        name="Ping Flow",
        steps=[{"tool_id": tool["tool_id"]}],
    )
    run = suite.executor.execute(tool_id=tool["tool_id"], params={"x": 1}, agent_id="qa")
    assert run["status"] == "completed"
    skill_run = suite.skills.run(skill_id=skill["skill_id"], agent_id="qa")
    assert skill_run["status"] == "completed"
    with pytest.raises(ValidationError):
        suite.tools.register(name="", domain="crm")


def test_bootstrap_marketplace():
    suite = enterprise_hub.ai_tools
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "6.0.0-rc6"
    assert boot["skill_contract_id"] and boot["install_id"] and boot["analytics_id"]


@pytest.mark.asyncio
async def test_api_ats(client):
    health = await client.get(f"{ATS}/health")
    body = await health.json()
    assert body["application_version"] == "6.0.0-rc6"
    assert body["ai_tools_ready"] is True

    boot = await client.post(f"{ATS}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    created = await client.post(
        f"{ATS}/tools",
        json={"name": "custom.api", "domain": "custom"},
    )
    assert created.status == 201

    for prefix in (HUB, ORCH, KG, AA, CM, WF, EIP, EDP, ISAM, OBS, TN, AOP):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "6.0.0-rc6"

    assert boot_body["execution_context_id"]


def test_docs_and_regression_20_2():
    for name in (
        "ENTERPRISE_AI_TOOLS.md",
        "ATS_TOOLS.md",
        "ATS_SKILLS.md",
        "ATS_SANDBOX_POLICY.md",
        "ATS_MARKETPLACE.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_AI_TOOLS.md").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "ai_tools" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "ai_tools" / "tools" / "crm" / "actions.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "ai_tools" / "skills" / "contract_review.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "ai_tools" / "marketplace" / "installer.py").exists()

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
