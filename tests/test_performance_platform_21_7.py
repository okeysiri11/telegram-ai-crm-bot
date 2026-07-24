"""Tests — Enterprise Performance Platform (Sprint 21.7 / v6.0.0)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from applications.enterprise_hub.shared.exceptions import ValidationError
from platform_performance.models import LOAD_TARGETS, PROFILE_TARGETS, SLA


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
]
EPF = "/api/enterprise-epf/v1"


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


def test_version_epf_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "6.5.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v6.4.0"
    assert health["performance_platform_ready"] is True
    assert health["load_testing_ready"] is True
    assert health["autoscaling_ready"] is True
    assert health["performance_certification_ready"] is True
    assert health["documentation_platform_ready"] is True
    assert health["engines"]["performance_platform"] == "1.0"


def test_profile_load_cache():
    suite = enterprise_hub.performance_platform
    profile = suite.profile("api")
    assert profile["count"] == 1
    load = suite.load_test(concurrent_users=250)
    assert load["pass_rate"] == 1.0
    assert set(LOAD_TARGETS)
    cache = suite.cache_put(key="k1", value={"x": 1}, ttl=30, backend="redis")
    assert cache["backend"] == "redis"
    with pytest.raises(ValidationError):
        suite.profile("unknown-target")
    with pytest.raises(ValidationError):
        suite.cache_put(key="k", value=1, backend="memcached")


def test_bootstrap_certify():
    suite = enterprise_hub.performance_platform
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "6.5.0"
    assert boot["benchmark_passed"] is True
    assert boot["certified"] is True
    assert boot["production_validated"] is True
    assert boot["status"] == "production_ready"
    assert boot["hpa_enabled"] is True
    assert boot["load_pass_rate"] == 1.0
    assert boot["recovery_time_s"] <= SLA["recovery_time_s"]
    assert boot["dashboard_id"]
    assert boot["certification_id"]
    assert boot["integrations"]["linked"] is True
    assert suite.dashboard()["status"] == "production_ready"
    cert = suite.certify()
    assert cert["certified"] is True
    assert set(PROFILE_TARGETS)


@pytest.mark.asyncio
async def test_api_epf(client):
    health = await client.get(f"{EPF}/health")
    body = await health.json()
    assert body["application_version"] == "6.5.0"
    assert body["performance_platform_ready"] is True

    boot = await client.post(f"{EPF}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()
    assert boot_body["certified"] is True

    dash = await client.get(f"{EPF}/dashboard")
    assert dash.status == 200
    assert (await dash.json())["status"] == "production_ready"

    for prefix in PREFIXES:
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        payload = await resp.json()
        version = payload.get("application_version") or payload.get("data", {}).get("application_version")
        assert version == "6.5.0"


def test_docs_and_regression_21_7():
    for name in (
        "ENTERPRISE_PERFORMANCE_PLATFORM.md",
        "EPF_PROFILING_BENCHMARK.md",
        "EPF_CACHE_DB_OPTIMIZATION.md",
        "EPF_LOAD_STRESS_SCALING.md",
        "EPF_MONITORING_CERTIFICATION.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_PERFORMANCE_PLATFORM.md").exists()
    assert (ROOT / "platform_performance" / "facade.py").exists()
    assert (ROOT / "platform_performance" / "profiler" / "__init__.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "performance_platform" / "facade.py").exists()

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
    assert "6.5.0" in manifest
    assert "22.4" in manifest
