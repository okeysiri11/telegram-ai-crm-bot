"""Tests — Enterprise Release Platform (Sprint 21.8 / v6.0.0 LTS)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from platform_release.models import CERTIFICATION_DOMAINS, LTS_VERSION, PRODUCTION_STATUSES


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
]
ERL = "/api/enterprise-erl/v1"


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


def test_version_erl_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "6.4.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v6.3.0"
    assert health["release_certification_ready"] is True
    assert health["production_ready"] is True
    assert health["disaster_recovery_ready"] is True
    assert health["lts_baseline_ready"] is True
    assert health["performance_platform_ready"] is True
    assert health["engines"]["release_platform"] == "1.0"


def test_certify_migrate_dr():
    suite = enterprise_hub.release_platform
    cert = suite.certify()
    assert cert["passed"] is True
    assert cert["certificate"] == "ENTERPRISE-CORE-V6-CERTIFIED"
    assert cert["count"] == len(CERTIFICATION_DOMAINS)
    mig = suite.migrate()
    assert mig["passed"] is True
    assert mig["to_version"] == LTS_VERSION
    dr = suite.disaster_recovery()
    assert dr["passed"] is True
    assert dr["rpo_met"] is True
    assert dr["rto_met"] is True


def test_bootstrap_approve_manifest():
    suite = enterprise_hub.release_platform
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "6.4.0"
    assert boot["production_ready"] is True
    assert boot["enterprise_certified"] is True
    assert boot["lts_baseline"] is True
    assert boot["lts_version"] == "6.0.0"
    assert boot["manifest_published"] is True
    assert boot["approved"] is True
    assert boot["status"] == "production_ready"
    assert boot["integrations"]["linked"] is True
    assert set(boot["statuses"]) == set(PRODUCTION_STATUSES)
    notes = suite.release_notes()
    assert notes["version"] == "6.0.0"
    approval = suite.approve()
    assert approval["approved"] is True
    manifest = suite.production_manifest()
    assert manifest["published"] is True
    assert manifest["channel"] == "stable-lts"


@pytest.mark.asyncio
async def test_api_erl(client):
    health = await client.get(f"{ERL}/health")
    body = await health.json()
    assert body["application_version"] == "6.4.0"
    assert body["production_ready"] is True
    assert body["lts_baseline_ready"] is True

    boot = await client.post(f"{ERL}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()
    assert boot_body["production_ready"] is True

    manifest = await client.get(f"{ERL}/manifest")
    assert manifest.status == 200
    assert (await manifest.json())["manifest_version"] == "6.0.0"

    for prefix in PREFIXES:
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        payload = await resp.json()
        version = payload.get("application_version") or payload.get("data", {}).get("application_version")
        assert version == "6.4.0"


def test_docs_and_regression_21_8():
    for name in (
        "ENTERPRISE_RELEASE_PLATFORM.md",
        "ERL_CERTIFICATION_READINESS.md",
        "ERL_DEPLOYMENT_MIGRATION.md",
        "ERL_BACKUP_DR_MONITORING.md",
        "ERL_LTS_APPROVAL.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_RELEASE_PLATFORM.md").exists()
    assert (ROOT / "platform_release" / "facade.py").exists()
    assert (ROOT / "platform_release" / "certification" / "__init__.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "release_platform" / "facade.py").exists()

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
    assert "6.4.0" in manifest
    assert '"application_version": "6.4.0"' in manifest
    assert "22.3" in manifest
