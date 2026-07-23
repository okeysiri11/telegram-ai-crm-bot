"""Tests — Finance Enterprise Certification & Production Release (Sprint 18.8)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.finance_enterprise import finance_enterprise
from applications.finance_enterprise.api.register import register_finance_enterprise_routes


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/finance-enterprise-certification/v1"
INT = "/api/finance-int/v1"
CFO = "/api/finance-cfo/v1"
RPT = "/api/finance-rpt/v1"
DA = "/api/finance-da/v1"
TR = "/api/finance-tr/v1"
BIL = "/api/finance-bil/v1"
PAY = "/api/finance-pay/v1"
CE = "/api/finance-enterprise/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_finance_enterprise_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    finance_enterprise.reset()
    yield
    finance_enterprise.reset()


def test_version_production_release():
    health = finance_enterprise.health()
    assert health["application_version"] == "5.2.0-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v5.1.7-enterprise"
    assert health["release_status"] == "Production Ready"
    assert health["architecture_certified"] is True
    assert health["integration_certified"] is True
    assert health["performance_certified"] is True
    assert health["security_certified"] is True
    assert health["financial_integrity_certified"] is True
    assert health["documentation_certified"] is True
    assert health["finance_enterprise_ready"] is True
    assert health["production_ready"] is True
    assert health["enterprise_release_ready"] is True
    assert health["bidex_finance_enterprise_suite_released"] is True
    assert health["all_enterprise_tests_passed"] is True


def test_full_certification_pack():
    suite = finance_enterprise.enterprise_certification
    result = suite.run_all()
    assert result["architecture_certified"] is True
    assert result["integration_certified"] is True
    assert result["security_certified"] is True
    assert result["performance_certified"] is True
    assert result["financial_integrity_certified"] is True
    assert result["documentation_certified"] is True
    assert result["quality_certified"] is True
    assert result["enterprise_release_ready"] is True
    assert result["all_enterprise_tests_passed"] is True
    assert result["executive"]["enterprise_readiness_score"] >= 90.0
    assert result["executive"]["status"] == "Production Ready"
    assert result["version_manifest"]["application_version"] == "5.2.0-enterprise"
    assert result["module_registry"]["count"] >= 9
    for dtype in ("enterprise_health", "certification", "performance", "security", "release"):
        assert suite.dashboard(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_finance_enterprise_certification(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "5.2.0-enterprise"
    assert body["architecture_certified"] is True
    assert body["enterprise_release_ready"] is True
    assert body["bidex_finance_enterprise_suite_released"] is True

    for prefix in (INT, CFO, RPT, DA, TR, BIL, PAY, CE):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "5.2.0-enterprise"

    boot = await client.post(f"{PREFIX}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()
    assert boot_body["enterprise_release_ready"] is True
    assert boot_body["all_enterprise_tests_passed"] is True
    assert boot_body["financial_integrity_certified"] is True

    assert (await client.get(f"{PREFIX}/architecture")).status == 200
    assert (await client.get(f"{PREFIX}/integration")).status == 200
    assert (await client.get(f"{PREFIX}/performance")).status == 200
    assert (await client.get(f"{PREFIX}/security")).status == 200
    assert (await client.get(f"{PREFIX}/integrity")).status == 200
    assert (await client.get(f"{PREFIX}/documentation")).status == 200
    assert (await client.get(f"{PREFIX}/quality")).status == 200
    assert (await client.get(f"{PREFIX}/release?kind=registry")).status == 200
    assert (await client.get(f"{PREFIX}/executive")).status == 200
    assert (await client.get(f"{PREFIX}/dashboard?type=security")).status == 200


def test_docs_and_regression_18_8():
    for name in (
        "FINANCE_ENTERPRISE_ARCHITECTURE.md",
        "FINANCE_ENTERPRISE_API.md",
        "FINANCE_ENTERPRISE_DEPLOYMENT.md",
        "FINANCE_ENTERPRISE_SECURITY.md",
        "FINANCE_ENTERPRISE_TEST_REPORT.md",
        "FINANCE_ENTERPRISE_RELEASE_NOTES.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "FINANCE_ENTERPRISE_CERTIFICATION.md").exists()
    assert (
        ROOT / "applications" / "finance_enterprise" / "enterprise_certification" / "facade.py"
    ).exists()
    for pkg in (
        "payments",
        "billing",
        "treasury",
        "digital_assets",
        "reporting",
        "ai_cfo",
        "integration",
        "enterprise_certification",
    ):
        assert (ROOT / "applications" / "finance_enterprise" / pkg / "facade.py").exists()
    for artifact in (
        "VERSION_MANIFEST.json",
        "DEPLOYMENT_MANIFEST.json",
        "config.template.env",
        "PRODUCTION_CHECKLIST.md",
        "DEPLOYMENT_CHECKLIST.md",
        "OPERATIONS_CHECKLIST.md",
        "INSTALLATION_GUIDE.md",
        "ADMINISTRATOR_GUIDE.md",
        "DEVELOPER_GUIDE.md",
        "MIGRATION_GUIDE.md",
        "RELEASE_NOTES.md",
    ):
        assert (ROOT / "applications" / "finance_enterprise" / "release" / artifact).exists()

    manifest = (ROOT / "applications" / "finance_enterprise" / "manifest.json").read_text()
    assert "5.2.0-enterprise" in manifest
    assert "18.8" in manifest
    notes = (ROOT / "applications" / "finance_enterprise" / "release" / "RELEASE_NOTES.md").read_text()
    assert "5.2.0-enterprise" in notes

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT
    from applications.auto_marketplace.config import DEFAULT_CONFIG as AUTO
    from applications.agro_enterprise.config import DEFAULT_CONFIG as AGRO
    from applications.port_enterprise.config import DEFAULT_CONFIG as PORT
    from applications.port_erp.config import DEFAULT_CONFIG as PORT_ERP
    from applications.crypto_enterprise.config import DEFAULT_CONFIG as CRYPTO
    from applications.legal_enterprise.config import DEFAULT_CONFIG as LEGAL

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AUTO.application_version == "4.2.0-enterprise"
    assert AGRO.application_version == "4.4.0-enterprise"
    assert PORT.application_version == "4.6.0-enterprise"
    assert PORT_ERP.application_version == "2.0.0"
    assert CRYPTO.application_version == "4.8.0-enterprise"
    assert LEGAL.application_version == "5.0.0-enterprise"
