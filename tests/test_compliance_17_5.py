"""Tests — Compliance Platform (Sprint 17.5)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.legal_enterprise import legal_enterprise
from applications.legal_enterprise.api.register import register_legal_enterprise_routes
from applications.legal_enterprise.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/legal-enterprise/v1"
LI = "/api/legal-li/v1"
JI = "/api/legal-ji/v1"
CM = "/api/legal-cm/v1"
DI = "/api/legal-di/v1"
CP = "/api/legal-cp/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_legal_enterprise_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    legal_enterprise.reset()
    yield
    legal_enterprise.reset()


def test_version_compliance_ready():
    health = legal_enterprise.health()
    assert health["application_version"] == "4.9.7-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.9.6-enterprise"
    assert health["compliance_platform_ready"] is True
    assert health["corporate_governance_ready"] is True
    assert health["legal_risk_management_ready"] is True
    assert health["ai_compliance_intelligence_ready"] is True
    assert health["document_intelligence_ready"] is True


def test_compliance_and_corporate():
    suite = legal_enterprise.compliance_platform
    co = suite.governance.register_company(name="QA Corp", jurisdiction="US")
    fw = suite.compliance.register_framework(name="QA Framework")
    req = suite.compliance.register_requirement(
        framework_id=fw["framework_id"], code="QA-1", title="Control A"
    )
    assert co["company_id"] and req["requirement_id"]
    with pytest.raises(ValidationError):
        suite.governance.register_company(name="")


def test_aml_risk_ai_bootstrap():
    suite = legal_enterprise.compliance_platform
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "4.9.7-enterprise"
    assert boot["company_id"] and boot["aml_id"] and boot["health_id"]
    assert suite.aml.aml_score(name="Test Entity", score=55)["risk_level"] == "medium"
    assert suite.ai.compliance_health_score()["kind"] == "compliance_health"
    for dtype in ("compliance", "corporate", "license", "risk", "ai_compliance"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_compliance(client):
    health = await client.get(f"{CP}/health")
    body = await health.json()
    assert body["application_version"] == "4.9.7-enterprise"
    assert body["compliance_platform_ready"] is True
    assert body["corporate_governance_ready"] is True

    boot = await client.post(f"{CP}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    aml = await client.post(
        f"{CP}/aml",
        json={"action": "score", "counterparty_id": boot_body["partner_id"], "score": 80},
    )
    assert aml.status == 201

    ai = await client.post(f"{CP}/ai", json={"action": "report", "audience": "board"})
    assert ai.status == 201

    for prefix in (PREFIX, LI, JI, CM, DI):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "4.9.7-enterprise"


def test_docs_and_regression_17_5():
    for name in (
        "COMPLIANCE_PLATFORM.md",
        "CORPORATE_GOVERNANCE.md",
        "LEGAL_RISK_MANAGEMENT.md",
        "AML_KYC_KYB.md",
        "AI_COMPLIANCE_INTELLIGENCE.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "COMPLIANCE_PLATFORM.md").exists()
    assert (ROOT / "applications" / "legal_enterprise" / "compliance" / "facade.py").exists()
    assert (ROOT / "applications" / "legal_enterprise" / "document_intelligence" / "facade.py").exists()

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT
    from applications.auto_marketplace.config import DEFAULT_CONFIG as AUTO
    from applications.agro_enterprise.config import DEFAULT_CONFIG as AGRO
    from applications.port_enterprise.config import DEFAULT_CONFIG as PORT
    from applications.port_erp.config import DEFAULT_CONFIG as PORT_ERP
    from applications.crypto_enterprise.config import DEFAULT_CONFIG as CRYPTO

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AUTO.application_version == "4.2.0-enterprise"
    assert AGRO.application_version == "4.4.0-enterprise"
    assert PORT.application_version == "4.6.0-enterprise"
    assert PORT_ERP.application_version == "2.0.0"
    assert CRYPTO.application_version == "4.8.0-enterprise"
    manifest = (ROOT / "applications" / "legal_enterprise" / "manifest.json").read_text()
    assert "4.9.7-enterprise" in manifest
    assert "17.7" in manifest
