"""Tests — Enterprise Platform Release Candidate RC1 (Sprint 26.8 / v9.1.0-rc1)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from platform_enterprise_release_candidate.models import (
    ARCHITECTURE,
    INTEGRATION_MODULES,
    KPI_TARGETS,
    PRINCIPLES,
    RELEASE_CODE,
    VERSION,
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
    "/api/enterprise-wfi/v1",
    "/api/enterprise-ekg/v1",
    "/api/enterprise-pin/v1",
    "/api/enterprise-esl/v1",
    "/api/enterprise-etw/v1",
    "/api/enterprise-eoe/v1",
    "/api/enterprise-est/v1",
    "/api/enterprise-ele/v1",
    "/api/enterprise-aph/v1",
    "/api/enterprise-ees/v1",
    "/api/enterprise-eti/v1",
    "/api/enterprise-epl/v1",
    "/api/enterprise-ece/v1",
    "/api/enterprise-emr/v1",
    "/api/enterprise-esv/v1",
    "/api/enterprise-epd/v1",
    "/api/enterprise-ecf/v1",
    "/api/enterprise-ewf/v1",
    "/api/enterprise-eds/v1",
    "/api/enterprise-eic/v1",
    "/api/enterprise-ews/v1",
    "/api/enterprise-enp/v1",
    "/api/enterprise-command/v1",
    "/api/enterprise-navigation/v1",
]
RC = "/api/release/v1"


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


def test_version_release_candidate_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "9.1.0-rc1"
    assert health["release_candidate_ready"] is True
    assert health["platform_integrated"] is True
    assert health["platform_health_report_ready"] is True
    assert health["engines"]["release_candidate"] == "1.0"
    assert VERSION == "9.1.0-rc1"
    assert RELEASE_CODE == "RC1"
    assert len(INTEGRATION_MODULES) >= 30
    assert "platform_integration_auditor" in ARCHITECTURE
    assert KPI_TARGETS["release_candidate_ready"] is True
    assert "phase3_release_candidate" in PRINCIPLES


def test_integration_registry_routes_security_performance_docs_health():
    suite = enterprise_hub.release_candidate
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["hub_version"] == "9.1.0-rc1"
    assert boot["version"] == "9.1.0-rc1"
    assert boot["release_code"] == "RC1"
    assert boot["release_candidate_ready"] is True
    assert boot["platform_integrated"] is True
    assert boot["overall_readiness_pct"] >= 90
    assert boot["release_path_exists"] is True
    assert boot["dashboard_page_exists"] is True
    assert boot["docs_rc_exists"] is True
    assert boot["docs_health_exists"] is True

    integration = suite.integration()
    assert integration["integrated_count"] == integration["total"]
    assert integration["score"] >= 90
    assert integration["status"] == "pass"

    registry = suite.registry()
    assert registry["application_count"] >= 10
    assert registry["platform_package_count"] >= 40
    assert "auto_marketplace" in registry["applications"]

    routes = suite.routes()
    assert routes["react_route_count"] >= 10
    assert routes["navigation_ready"] is True
    assert routes["breadcrumbs_ready"] is True
    assert "/api/release/v1" in routes["api_prefixes"]

    security = suite.security()
    assert security["score"] >= 90
    assert security["status"] == "pass"
    assert security["checks"]["rbac"] is True
    assert security["checks"]["authentication"] is True

    performance = suite.performance()
    assert performance["score"] >= 85
    assert performance["checks"]["command_center"] is True
    assert performance["checks"]["search"] is True

    documentation = suite.documentation()
    assert "docs/RELEASE_CANDIDATE.md" in documentation["present"]
    assert "docs/PLATFORM_HEALTH_REPORT.md" in documentation["present"]
    assert documentation["missing"] == []

    report = suite.health_report()
    assert report["overall_readiness_pct"] >= 90
    assert report["release_candidate_ready"] is True
    assert report["critical_issues"] == []
    assert "coverage" in report
    assert report["applications"]["count"] >= 10

    dash = suite.dashboard()
    assert dash["title"] == "Release Candidate Dashboard"
    assert dash["overall_readiness_pct"] >= 90


@pytest.mark.asyncio
async def test_api_release_candidate(client):
    health = await client.get(f"{RC}/health")
    body = await health.json()
    assert body["application_version"] == "9.1.0-rc1"
    assert body["release_candidate_ready"] is True

    boot = await client.post(f"{RC}/bootstrap", json={})
    assert boot.status == 201
    payload = await boot.json()
    assert payload["release_candidate_ready"] is True

    for path in (
        "/inventory",
        "/dashboard",
        "/health-report",
        "/integration",
        "/registry",
        "/routes",
        "/security",
        "/performance",
        "/documentation",
    ):
        resp = await client.get(f"{RC}{path}")
        assert resp.status == 200

    # prior platform APIs still healthy at RC version
    for prefix in (
        "/api/enterprise-navigation/v1",
        "/api/enterprise-command/v1",
        "/api/enterprise-enp/v1",
        "/api/enterprise-ews/v1",
    ):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "9.1.0-rc1"

    for prefix in PREFIXES:
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        data = await resp.json()
        version = data.get("application_version") or data.get("data", {}).get("application_version")
        assert version == "9.1.0-rc1"


def test_docs_and_regression_26_8():
    assert (ROOT / "docs" / "RELEASE_CANDIDATE.md").exists()
    assert (ROOT / "docs" / "PLATFORM_HEALTH_REPORT.md").exists()
    assert (ROOT / "platform_enterprise_release_candidate" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "release_candidate" / "facade.py").exists()
    assert (ROOT / "src" / "web" / "release" / "pages" / "ReleaseCandidatePage.tsx").exists()
    assert (ROOT / "knowledge" / "applications" / "enterprise_hub" / "release_candidate" / "README.md").exists()

    docs = (ROOT / "docs" / "RELEASE_CANDIDATE.md").read_text()
    assert "RC1" in docs
    assert "/api/release/v1" in docs

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
    assert '"application_version": "9.1.0-rc1"' in manifest
    assert "26.8" in manifest
