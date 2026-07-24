"""Tests — Workflow Intelligence & AI Execution Engine (Sprint 24.5 / v7.5.0)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from applications.enterprise_hub.shared.exceptions import ValidationError
from platform_workflow_intelligence.models import (
    DESIGNER_NODES,
    EXECUTION_POLICIES,
    INDUSTRY_LIBRARY,
    KPI_TARGETS,
    PRINCIPLES,
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
]
WFI = "/api/enterprise-wfi/v1"


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


def test_version_wfi_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "7.5.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v7.4.0"
    assert health["workflow_intelligence_ready"] is True
    assert health["visual_designer_ready"] is True
    assert health["ai_execution_ready"] is True
    assert health["workflow_library_ready"] is True
    assert health["engines"]["workflow_intelligence"] == "1.0"
    assert "start" in DESIGNER_NODES and "human_approval" in DESIGNER_NODES
    assert "requires_owner" in EXECUTION_POLICIES
    assert "beauty" in INDUSTRY_LIBRARY and "port" in INDUSTRY_LIBRARY
    assert KPI_TARGETS["success_rate_95pct"] is True
    assert set(PRINCIPLES)


def test_design_execute_policy_analytics():
    suite = enterprise_hub.workflow_intelligence
    wf = suite.from_library(industry="beauty", workflow_id="wf_test_beauty")
    assert wf["from_library"] is True
    assert wf["policy"] == "requires_owner"

    wf = suite.design_node(workflow_id="wf_test_beauty", node_type="payment")
    assert any(n["type"] == "payment" for n in wf["nodes"])
    assert wf["version"] != "1.0"

    blocked = suite.execute(workflow_id="wf_test_beauty", owner_approved=False)
    assert blocked["status"] == "blocked_awaiting_owner"
    assert blocked["executed"] is False
    assert blocked["ai_started"] is False

    sim = suite.execute(workflow_id="wf_test_beauty", simulate=True)
    assert sim["status"] == "simulated"

    ok = suite.execute(workflow_id="wf_test_beauty", owner_approved=True, actor="platform_owner", mode="async")
    assert ok["executed"] is True
    assert ok["ai_started"] is False

    analysis = suite.analyze(workflow_id="wf_test_beauty")
    assert analysis["proposes_only"] is True
    assert analysis["mutates_workflow"] is False
    assert analysis["ai_may_act"] is False

    stats = suite.analytics(workflow_id="wf_test_beauty")
    assert "optimization" in stats
    assert stats["optimization"]["proposes_only"] is True

    inv = suite.invoke_module(module="commerce", action="ping")
    assert inv["delegated"] is True

    cat = suite.catalog()
    assert cat["count"] == len(INDUSTRY_LIBRARY)

    with pytest.raises(ValidationError):
        suite.design_node(workflow_id="wf_test_beauty", node_type="unknown_node")


def test_bootstrap_wfi():
    suite = enterprise_hub.workflow_intelligence
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "7.5.0"
    assert boot["workflow_intelligence_ready"] is True
    assert boot["visual_designer_ready"] is True
    assert boot["blocked_without_owner"] is True
    assert boot["executed_after_owner"] is True
    assert boot["ai_may_act"] is False
    assert boot["success_rate_95pct"] is True
    assert boot["duplicates_core_logic"] is False
    assert boot["integrations"]["linked"] is True


@pytest.mark.asyncio
async def test_api_wfi(client):
    health = await client.get(f"{WFI}/health")
    body = await health.json()
    assert body["application_version"] == "7.5.0"
    assert body["workflow_intelligence_ready"] is True

    boot = await client.post(f"{WFI}/bootstrap", json={})
    assert boot.status == 201
    assert (await boot.json())["workflow_library_ready"] is True

    for prefix in PREFIXES:
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        payload = await resp.json()
        version = payload.get("application_version") or payload.get("data", {}).get("application_version")
        assert version == "7.5.0"


def test_docs_and_regression_24_1():
    for name in (
        "ENTERPRISE_WORKFLOW_INTELLIGENCE.md",
        "WFI_REGISTRY_DESIGNER.md",
        "WFI_EXECUTION_POLICIES.md",
        "WFI_ANALYTICS_LIBRARY.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_WORKFLOW_INTELLIGENCE.md").exists()
    assert (ROOT / "platform_workflow_intelligence" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "workflow_intelligence" / "facade.py").exists()

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
    assert '"application_version": "7.5.0"' in manifest
    assert "24.5" in manifest
