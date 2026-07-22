"""Tests — Agro Enterprise Certification & Production Release (Sprint 14.8)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.agro_enterprise import agro_enterprise
from applications.agro_enterprise.api.register import register_agro_enterprise_routes


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/agro-enterprise-certification/v1"
AA = "/api/ai-agronomist/v1"
AF = "/api/agro-finance/v1"
SC = "/api/agro-supply-chain/v1"
CE = "/api/controlled-environment/v1"
CA = "/api/crop-ai/v1"
SI = "/api/smart-irrigation/v1"
PA = "/api/precision-agriculture/v1"
AE = "/api/agro-enterprise/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_agro_enterprise_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    agro_enterprise.reset()
    yield
    agro_enterprise.reset()


def test_version_production_release():
    health = agro_enterprise.health()
    assert health["application_version"] == "4.4.0-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.3.7-enterprise"
    assert health["release_status"] == "Production Ready"
    assert health["architecture_certified"] is True
    assert health["integration_certified"] is True
    assert health["performance_certified"] is True
    assert health["security_certified"] is True
    assert health["documentation_certified"] is True
    assert health["agro_enterprise_ready"] is True
    assert health["production_ready"] is True
    assert health["enterprise_release_ready"] is True
    assert health["agro_enterprise_suite_released"] is True
    assert health["all_enterprise_tests_passed"] is True


def test_full_certification_pack():
    suite = agro_enterprise.enterprise_certification
    result = suite.run_all()
    assert result["architecture_certified"] is True
    assert result["integration_certified"] is True
    assert result["security_certified"] is True
    assert result["performance_certified"] is True
    assert result["documentation_certified"] is True
    assert result["quality_certified"] is True
    assert result["enterprise_release_ready"] is True
    assert result["all_enterprise_tests_passed"] is True
    assert result["executive"]["enterprise_readiness_score"] >= 90.0
    assert result["executive"]["status"] == "Production Ready"
    assert result["version_manifest"]["application_version"] == "4.4.0-enterprise"
    assert result["module_registry"]["count"] >= 9


@pytest.mark.asyncio
async def test_api_agro_enterprise_certification(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "4.4.0-enterprise"
    assert body["architecture_certified"] is True
    assert body["enterprise_release_ready"] is True
    assert body["agro_enterprise_suite_released"] is True

    for prefix in (AA, AF, SC, CE, CA, SI, PA, AE):
        assert (await client.get(f"{prefix}/health")).status == 200

    boot = await client.post(f"{PREFIX}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()
    assert boot_body["enterprise_release_ready"] is True
    assert boot_body["all_enterprise_tests_passed"] is True

    assert (await client.get(f"{PREFIX}/architecture")).status == 200
    assert (await client.get(f"{PREFIX}/integration")).status == 200
    assert (await client.get(f"{PREFIX}/performance")).status == 200
    assert (await client.get(f"{PREFIX}/security")).status == 200
    assert (await client.get(f"{PREFIX}/documentation")).status == 200
    assert (await client.get(f"{PREFIX}/quality")).status == 200
    assert (await client.get(f"{PREFIX}/release?kind=registry")).status == 200
    assert (await client.get(f"{PREFIX}/executive")).status == 200
    assert (await client.get(f"{PREFIX}/dashboard?type=security")).status == 200


def test_docs_and_regression_14_8():
    for name in (
        "AGRO_ENTERPRISE_ARCHITECTURE.md",
        "AGRO_ENTERPRISE_DEPLOYMENT.md",
        "AGRO_API_REFERENCE.md",
        "AGRO_RELEASE_NOTES_v4.4.0.md",
        "AGRO_CHANGELOG.md",
        "AGRO_MODULE_REGISTRY.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "AGRO_ENTERPRISE_CERTIFICATION.md").exists()
    assert (ROOT / "applications" / "agro_enterprise" / "enterprise_certification" / "facade.py").exists()
    for pkg in (
        "ai_agronomist",
        "agro_finance",
        "supply_chain",
        "controlled_environment",
        "crop_ai",
        "smart_irrigation",
        "precision_agriculture",
    ):
        assert (ROOT / "applications" / "agro_enterprise" / pkg / "facade.py").exists()
    for artifact in (
        "VERSION_MANIFEST.json",
        "DEPLOYMENT_MANIFEST.json",
        "config.template.env",
        "PRODUCTION_CHECKLIST.md",
        "INSTALLATION_GUIDE.md",
        "ADMINISTRATOR_GUIDE.md",
        "OPERATIONS_MANUAL.md",
        "RELEASE_NOTES.md",
    ):
        assert (ROOT / "applications" / "agro_enterprise" / "release" / artifact).exists()

    manifest = (ROOT / "applications" / "agro_enterprise" / "manifest.json").read_text()
    assert "4.4.0-enterprise" in manifest
    assert "14.8" in manifest
    notes = (ROOT / "applications" / "agro_enterprise" / "release" / "RELEASE_NOTES.md").read_text()
    assert "4.4.0-enterprise" in notes

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT
    from applications.auto_marketplace.config import DEFAULT_CONFIG as AUTO
    from applications.agro_marketplace.config import DEFAULT_CONFIG as AGRO

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AUTO.application_version == "4.2.0-enterprise"
    assert AGRO.application_version == "2.0.0"
