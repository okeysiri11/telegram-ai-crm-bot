"""Tests — Enterprise Certification & Production Release (Sprint 13.9)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.register import register_auto_marketplace_routes


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/enterprise-certification/v1"
MP = "/api/mobility-platform/v1"
CC = "/api/connected-cars/v1"
AE = "/api/automotive-erp/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_auto_marketplace_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    auto_marketplace.reset()
    yield
    auto_marketplace.reset()


def test_version_production_release():
    health = auto_marketplace.health()
    assert health["application_version"] == "4.2.0-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.1.8-enterprise"
    assert health["release_status"] == "Production Ready"
    assert health["production_ready"] is True
    assert health["architecture_certified"] is True
    assert health["security_certified"] is True
    assert health["performance_certified"] is True
    assert health["documentation_certified"] is True
    assert health["enterprise_release_ready"] is True
    assert health["automotive_enterprise_suite_released"] is True


def test_full_certification_pack():
    suite = auto_marketplace.enterprise_certification
    result = suite.run_all()
    assert result["architecture_certified"] is True
    assert result["security_certified"] is True
    assert result["performance_certified"] is True
    assert result["documentation_certified"] is True
    assert result["enterprise_release_ready"] is True
    assert result["executive"]["enterprise_readiness_score"] >= 90.0
    assert result["executive"]["status"] == "Production Ready"
    assert result["version_manifest"]["application_version"] == "4.2.0-enterprise"
    assert result["module_registry"]["count"] >= 10


def test_commercial_release_certify():
    cert = auto_marketplace.enterprise.release.certify()
    assert cert["application_version"] == "4.2.0-enterprise"
    assert cert["production_ready"] is True
    assert cert["certified"] is True
    assert cert["notes_present"] is True


@pytest.mark.asyncio
async def test_api_enterprise_certification(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "4.2.0-enterprise"
    assert body["architecture_certified"] is True
    assert body["enterprise_release_ready"] is True

    assert (await client.get(f"{MP}/health")).status == 200
    assert (await client.get(f"{CC}/health")).status == 200
    assert (await client.get(f"{AE}/health")).status == 200

    boot = await client.post(f"{PREFIX}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()
    assert boot_body["enterprise_release_ready"] is True

    assert (await client.get(f"{PREFIX}/architecture")).status == 200
    assert (await client.get(f"{PREFIX}/integration")).status == 200
    assert (await client.get(f"{PREFIX}/performance")).status == 200
    assert (await client.get(f"{PREFIX}/security")).status == 200
    assert (await client.get(f"{PREFIX}/documentation")).status == 200
    assert (await client.get(f"{PREFIX}/quality")).status == 200
    assert (await client.get(f"{PREFIX}/release?kind=registry")).status == 200
    assert (await client.get(f"{PREFIX}/executive")).status == 200


def test_docs_and_regression_13_9():
    for name in (
        "ENTERPRISE_AUTOMOTIVE_CERTIFICATION.md",
        "ARCHITECTURE_VALIDATION_REPORT.md",
        "PERFORMANCE_CERTIFICATION_REPORT.md",
        "SECURITY_CERTIFICATION_REPORT.md",
        "QUALITY_ASSURANCE_REPORT.md",
        "DOCUMENTATION_INDEX.md",
        "DEVELOPER_HANDBOOK.md",
        "ADMINISTRATOR_HANDBOOK.md",
        "USER_HANDBOOK.md",
        "AUTOMOTIVE_CHANGELOG.md",
        "MODULE_REGISTRY.md",
        "VERSION_MANIFEST.md",
        "DEPLOYMENT_GUIDE.md",
        "UPGRADE_GUIDE.md",
        "BACKUP_GUIDE.md",
        "DISASTER_RECOVERY_GUIDE.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_AUTOMOTIVE_CERTIFICATION.md").exists()
    assert (ROOT / "applications" / "auto_marketplace" / "enterprise_certification" / "facade.py").exists()
    for pkg in (
        "mobility_platform",
        "connected_cars",
        "automotive_erp",
        "seller_ai",
        "buyer_ai",
        "dealer_crm",
        "inspection_ai",
        "vin_intelligence",
        "enterprise_automotive",
    ):
        assert (ROOT / "applications" / "auto_marketplace" / pkg / "facade.py").exists()
    manifest = (ROOT / "applications" / "auto_marketplace" / "manifest.json").read_text()
    assert "4.2.0-enterprise" in manifest
    assert "13.9" in manifest
    notes = (ROOT / "applications" / "auto_marketplace" / "release" / "RELEASE_NOTES.md").read_text()
    assert "4.2.0-enterprise" in notes

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
