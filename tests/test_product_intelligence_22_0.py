"""Tests — Enterprise Product Intelligence (Sprint 22.0 / v6.2.0)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from applications.enterprise_hub.shared.exceptions import ValidationError
from platform_product_intelligence.models import FEEDBACK_SOURCES, OWNER_DECISIONS, PRINCIPLES


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
]
EPI = "/api/enterprise-epi/v1"


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


def test_version_epi_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "6.2.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v6.1.0"
    assert health["product_intelligence_ready"] is True
    assert health["feedback_collector_ready"] is True
    assert health["expert_board_ready"] is True
    assert health["owner_approval_ready"] is True
    assert health["production_ready"] is True
    assert health["engines"]["product_intelligence"] == "1.0"
    assert set(PRINCIPLES)


def test_ingest_analyze_owner_gate():
    suite = enterprise_hub.product_intelligence
    fb = suite.ingest(
        source="bug",
        title="Export fails on large datasets",
        module="data_fabric",
    )
    assert fb["normalized"] is True
    assert fb["fingerprint"]
    suite.ingest(source="support", title="Export fails on large datasets", module="data_fabric")
    analysis = suite.analyze()
    assert analysis["passed"] is True
    assert analysis["recurring_problems"]
    report = suite.generate_report(
        problem="Export fails on large datasets",
        proposal="Add chunked export with progress and retries",
    )
    assert report["requires_owner_decision"] is True
    assert report["ai_autonomous_change"] is False
    assert report["kpi"]
    rejected = suite.owner_decide(
        report_id=report["report_id"],
        decision="reject",
        owner_id="platform_owner",
    )
    assert rejected["development_allowed"] is False
    assert "pipeline_id" not in rejected
    approved = suite.owner_decide(
        report_id=report["report_id"],
        decision="approve",
        owner_id="platform_owner",
    )
    assert approved["development_allowed"] is True
    assert approved["pipeline_id"]
    validation = suite.validate_release(report_id=report["report_id"])
    assert validation["passed"] is True
    with pytest.raises(ValidationError):
        suite.ingest(source="unknown", title="x")
    assert set(OWNER_DECISIONS)
    assert set(FEEDBACK_SOURCES)


def test_bootstrap_knowledge():
    suite = enterprise_hub.product_intelligence
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "6.2.0"
    assert boot["ai_never_modifies_system"] is True
    assert boot["universal_intake"] is True
    assert boot["pipeline_artifacts"] == 7
    assert boot["owner_decision"] == "approve"
    assert boot["status"] == "ready"
    kb = suite.knowledge_history()
    assert kb["count"] >= 1


@pytest.mark.asyncio
async def test_api_epi(client):
    health = await client.get(f"{EPI}/health")
    body = await health.json()
    assert body["application_version"] == "6.2.0"
    assert body["product_intelligence_ready"] is True

    boot = await client.post(f"{EPI}/bootstrap", json={})
    assert boot.status == 201
    assert (await boot.json())["ai_never_modifies_system"] is True

    kb = await client.get(f"{EPI}/knowledge")
    assert kb.status == 200
    assert (await kb.json())["count"] >= 1

    for prefix in PREFIXES:
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        payload = await resp.json()
        version = payload.get("application_version") or payload.get("data", {}).get("application_version")
        assert version == "6.2.0"


def test_docs_and_regression_22_0():
    for name in (
        "ENTERPRISE_PRODUCT_INTELLIGENCE.md",
        "EPI_FEEDBACK_ANALYSIS.md",
        "EPI_EXPERT_BOARD_REPORTS.md",
        "EPI_OWNER_PIPELINE_VALIDATION.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_PRODUCT_INTELLIGENCE.md").exists()
    assert (ROOT / "platform_product_intelligence" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "product_intelligence" / "facade.py").exists()

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
    assert '"application_version": "6.2.0"' in manifest
    assert "22.1" in manifest
