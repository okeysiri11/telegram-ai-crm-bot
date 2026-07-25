"""Tests — Enterprise Performance & Load Testing (Sprint 26.1 / v9.0.0)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from applications.enterprise_hub.shared.exceptions import ValidationError
from platform_enterprise_performance_testing.models import (
    INTEGRATION_TARGETS,
    KPI_TARGETS,
    LOAD_USER_LEVELS,
    PRINCIPLES,
    SOAK_DURATIONS_HOURS,
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
]
EPL = "/api/enterprise-epl/v1"


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


def test_version_epl_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "9.0.4"
    assert health["enterprise_foundation"] == "Enterprise Platform v8.7.0"
    assert health["performance_testing_ready"] is True
    assert health["load_testing_ready"] is True
    assert health["stress_testing_ready"] is True
    assert health["bottleneck_advisor_ready"] is True
    assert health["engines"]["performance_testing"] == "1.0"
    assert health["test_infrastructure_ready"] is True
    assert health["performance_platform_ready"] is True
    assert 5000 in LOAD_USER_LEVELS
    assert 24 in SOAK_DURATIONS_HOURS
    assert "test_infrastructure" in INTEGRATION_TARGETS
    assert KPI_TARGETS["required_before_production"] is True
    assert "ci_cd_gate" in PRINCIPLES


def test_load_stress_spike_soak_analyze():
    suite = enterprise_hub.performance_testing
    load = suite.load_test(users=500)
    assert load["users"] == 500
    assert "throughput_rps" in load
    assert "cpu_pct" in load

    with pytest.raises(ValidationError):
        suite.load_test(users=42)

    stress = suite.stress_test(start_users=100, step=500, max_users=2500)
    assert stress["pushed_to_failure"] is True
    assert "api" in stress["limits"]
    assert stress["degradation_point_users"] is not None

    spike = suite.spike_test(pattern=[100, 1000, 5000, 100])
    assert spike["recovered"] is True
    assert "recovery_ms" in spike

    soak = suite.soak_test(hours=1, users=100)
    assert soak["stable"] is True

    with pytest.raises(ValidationError):
        suite.soak_test(hours=2)

    api = suite.benchmark_api(endpoint="/api/enterprise-hub/v1/health")
    assert "p95_ms" in api
    assert "p99_ms" in api
    db = suite.benchmark_database()
    assert db["kind"] == "database"
    ai = suite.benchmark_ai()
    assert ai["kind"] == "ai"
    wf = suite.benchmark_workflow()
    assert wf["kind"] == "workflow"

    mon = suite.monitor(load_users=1000)
    assert "cpu" in mon["metrics"]

    analysis = suite.analyze(load_users=2000)
    assert "bottlenecks" in analysis
    assert "advice" in analysis
    assert analysis["advice"]["count"] >= 1

    dash = suite.dashboard()
    assert dash["ci_cd_required"] is True
    assert "recommendations" in dash


def test_bootstrap_epl():
    suite = enterprise_hub.performance_testing
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "9.0.4"
    assert boot["performance_testing_ready"] is True
    assert boot["load_testing_ready"] is True
    assert boot["stress_testing_ready"] is True
    assert boot["bottleneck_advisor_ready"] is True
    assert boot["ci_cd_required"] is True
    assert boot["required_before_production"] is True
    assert boot["duplicates_core_logic"] is False
    assert boot["duplicates_epf_logic"] is False
    assert boot["integrations"]["linked"] is True


@pytest.mark.asyncio
async def test_api_epl(client):
    health = await client.get(f"{EPL}/health")
    body = await health.json()
    assert body["application_version"] == "9.0.4"
    assert body["performance_testing_ready"] is True

    boot = await client.post(f"{EPL}/bootstrap", json={})
    assert boot.status == 201
    assert (await boot.json())["load_testing_ready"] is True

    epf = await client.get("/api/enterprise-epf/v1/health")
    assert epf.status == 200
    epf_body = await epf.json()
    epf_version = epf_body.get("application_version") or epf_body.get("data", {}).get("application_version")
    assert epf_version == "9.0.4"

    for prefix in PREFIXES:
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        payload = await resp.json()
        version = payload.get("application_version") or payload.get("data", {}).get("application_version")
        assert version == "9.0.4"


def test_docs_and_regression_25_2():
    for name in (
        "ENTERPRISE_PERFORMANCE_TESTING.md",
        "EPL_LOAD_STRESS.md",
        "EPL_BENCHMARKS.md",
        "EPL_BOTTLENECK_DASHBOARD.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_PERFORMANCE_TESTING.md").exists()
    assert (ROOT / "platform_enterprise_performance_testing" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "performance_testing" / "facade.py").exists()
    assert (ROOT / "platform_performance" / "facade.py").exists()  # legacy EPF untouched

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
    assert '"application_version": "9.0.4"' in manifest
    assert "26.5" in manifest
