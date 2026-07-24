"""Tests — Enterprise Testing & Quality Assurance (Sprint 21.5 / v6.0.0)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from applications.enterprise_hub.shared.exceptions import ValidationError
from platform_quality.coverage import CoverageEngine
from platform_quality.models import MIN_COVERAGE


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
]
EQA = "/api/enterprise-eqa/v1"


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


def test_version_eqa_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "6.6.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v6.5.0"
    assert health["quality_assurance_ready"] is True
    assert health["test_framework_ready"] is True
    assert health["coverage_engine_ready"] is True
    assert health["quality_certification_ready"] is True
    assert health["security_hardening_ready"] is True
    assert health["engines"]["quality_assurance"] == "1.0"


def test_suites_and_coverage():
    suite = enterprise_hub.quality_assurance
    unit = suite.run_suite("unit")
    assert unit["pass_rate"] == 1.0
    assert unit["total"] >= 8
    cov = suite.coverage()
    assert cov["overall"] >= MIN_COVERAGE
    assert cov["meets_minimum"] is True
    assert CoverageEngine().measure()["meets_minimum"] is True
    fix = suite.fixtures(kind="user", count=2)
    assert fix["count"] == 2
    with pytest.raises(ValidationError):
        suite.run_suite("unknown")


def test_bootstrap_certify():
    suite = enterprise_hub.quality_assurance
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "6.6.0"
    assert boot["total_tests"] >= 100
    assert boot["pass_rate"] == 1.0
    assert boot["meets_coverage_minimum"] is True
    assert boot["certified"] is True
    assert boot["dashboard_id"]
    assert boot["integrations"]["linked"] is True
    cert = suite.certify()
    assert cert["certified"] is True
    assert suite.dashboard()["release_quality"] == "certified"


@pytest.mark.asyncio
async def test_api_eqa(client):
    health = await client.get(f"{EQA}/health")
    body = await health.json()
    assert body["application_version"] == "6.6.0"
    assert body["quality_assurance_ready"] is True

    boot = await client.post(f"{EQA}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    suites = await client.get(f"{EQA}/suites")
    assert suites.status == 200
    assert (await suites.json())["suites"] >= 8

    for prefix in PREFIXES:
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        payload = await resp.json()
        version = payload.get("application_version") or payload.get("data", {}).get("application_version")
        assert version == "6.6.0"

    assert boot_body["certified"] is True


def test_docs_and_regression_21_5():
    for name in (
        "ENTERPRISE_QUALITY_ASSURANCE.md",
        "EQA_SUITES.md",
        "EQA_COVERAGE_PERF.md",
        "EQA_DASHBOARD_CERT.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_QUALITY_ASSURANCE.md").exists()
    assert (ROOT / "platform_quality" / "facade.py").exists()
    assert (ROOT / "platform_quality" / "unit" / "__init__.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "quality_assurance" / "facade.py").exists()

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
    assert "6.6.0" in manifest
    assert "22.5" in manifest
