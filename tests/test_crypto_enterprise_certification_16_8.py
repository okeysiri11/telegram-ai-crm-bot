"""Tests — Crypto Enterprise Certification & Production Release (Sprint 16.8)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.crypto_enterprise import crypto_enterprise
from applications.crypto_enterprise.api.register import register_crypto_enterprise_routes


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/crypto-enterprise-certification/v1"
AT = "/api/crypto-at/v1"
OC = "/api/crypto-oc/v1"
RM = "/api/crypto-rm/v1"
SE = "/api/crypto-se/v1"
MI = "/api/crypto-mi/v1"
MM = "/api/crypto-mm/v1"
TA = "/api/crypto-ta/v1"
CE = "/api/crypto-enterprise/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_crypto_enterprise_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    crypto_enterprise.reset()
    yield
    crypto_enterprise.reset()


def test_version_production_release():
    health = crypto_enterprise.health()
    assert health["application_version"] == "4.8.0-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.7.7-enterprise"
    assert health["release_status"] == "Production Ready"
    assert health["architecture_certified"] is True
    assert health["integration_certified"] is True
    assert health["performance_certified"] is True
    assert health["security_certified"] is True
    assert health["documentation_certified"] is True
    assert health["crypto_enterprise_ready"] is True
    assert health["production_ready"] is True
    assert health["enterprise_release_ready"] is True
    assert health["crypto_enterprise_suite_released"] is True
    assert health["all_enterprise_tests_passed"] is True


def test_full_certification_pack():
    suite = crypto_enterprise.enterprise_certification
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
    assert result["version_manifest"]["application_version"] == "4.8.0-enterprise"
    assert result["module_registry"]["count"] >= 9


@pytest.mark.asyncio
async def test_api_crypto_enterprise_certification(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "4.8.0-enterprise"
    assert body["architecture_certified"] is True
    assert body["enterprise_release_ready"] is True
    assert body["crypto_enterprise_suite_released"] is True

    for prefix in (AT, OC, RM, SE, MI, MM, TA, CE):
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


def test_docs_and_regression_16_8():
    for name in (
        "CRYPTO_ENTERPRISE_ARCHITECTURE.md",
        "CRYPTO_ENTERPRISE_DEPLOYMENT.md",
        "CRYPTO_API_REFERENCE.md",
        "CRYPTO_RELEASE_NOTES_v4.8.0.md",
        "CRYPTO_CHANGELOG.md",
        "CRYPTO_MODULE_REGISTRY.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "CRYPTO_ENTERPRISE_CERTIFICATION.md").exists()
    assert (ROOT / "applications" / "crypto_enterprise" / "enterprise_certification" / "facade.py").exists()
    for pkg in (
        "technical_analysis",
        "market_microstructure",
        "market_intelligence",
        "strategy_engine",
        "risk_management",
        "onchain_intelligence",
        "ai_trader",
        "enterprise_certification",
    ):
        assert (ROOT / "applications" / "crypto_enterprise" / pkg / "facade.py").exists()
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
        assert (ROOT / "applications" / "crypto_enterprise" / "release" / artifact).exists()

    manifest = (ROOT / "applications" / "crypto_enterprise" / "manifest.json").read_text()
    assert "4.8.0-enterprise" in manifest
    assert "16.8" in manifest
    notes = (ROOT / "applications" / "crypto_enterprise" / "release" / "RELEASE_NOTES.md").read_text()
    assert "4.8.0-enterprise" in notes

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT
    from applications.auto_marketplace.config import DEFAULT_CONFIG as AUTO
    from applications.agro_enterprise.config import DEFAULT_CONFIG as AGRO
    from applications.port_enterprise.config import DEFAULT_CONFIG as PORT
    from applications.port_erp.config import DEFAULT_CONFIG as PORT_ERP

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AUTO.application_version == "4.2.0-enterprise"
    assert AGRO.application_version == "4.4.0-enterprise"
    assert PORT.application_version == "4.6.0-enterprise"
    assert PORT_ERP.application_version == "2.0.0"
