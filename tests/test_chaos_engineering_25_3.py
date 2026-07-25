"""Tests — Enterprise Chaos Engineering & Fault Tolerance (Sprint 25.4 / v8.4.0)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from applications.enterprise_hub.shared.exceptions import ValidationError
from platform_chaos.models import (
    FAILURE_TYPES,
    INTEGRATION_TARGETS,
    KPI_TARGETS,
    PRINCIPLES,
    RETRY_STRATEGIES,
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
]
ECE = "/api/enterprise-ece/v1"


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


def test_version_ece_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "8.4.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v8.3.0"
    assert health["chaos_engineering_ready"] is True
    assert health["failure_injection_ready"] is True
    assert health["recovery_engine_ready"] is True
    assert health["circuit_breaker_ready"] is True
    assert health["engines"]["chaos_engineering"] == "1.0"
    assert health["performance_testing_ready"] is True
    assert "postgresql_offline" in FAILURE_TYPES
    assert "exponential_backoff" in RETRY_STRATEGIES
    assert "performance_testing" in INTEGRATION_TARGETS
    assert KPI_TARGETS["required_before_production"] is True
    assert "simulate_never_destroy_data" in PRINCIPLES


def test_chaos_scenario_resilience_flow():
    suite = enterprise_hub.chaos_engineering
    scenario = suite.create_scenario(
        scenario_id="chs_redis",
        name="Redis Offline",
        target_service="redis",
        failure_type="redis_offline",
        duration_sec=15,
        validation_rules=["no_data_loss", "auto_recover"],
    )
    assert scenario["status"] == "ready"

    with pytest.raises(ValidationError):
        suite.create_scenario(
            scenario_id="chs_bad",
            name="Bad",
            target_service="x",
            failure_type="explode_everything",
        )

    run = suite.run_scenario(scenario_id="chs_redis", retry_strategy="exponential_backoff", fallback="local_cache")
    assert run["injection"]["simulated"] is True
    assert run["injection"]["data_loss"] is False
    assert run["recovery"]["recovered"] is True
    assert run["recovery"]["automatic"] is True
    assert run["recovery"]["user_intervention_required"] is False
    assert run["circuit"]["verified"] is True
    assert run["retry"]["success"] is True
    assert run["fallback"]["activated"] is True
    assert run["reports"]["auto_generated"] is True

    circuit = suite.circuit_check(failure_count=5, success_after_open=0)
    assert circuit["state"] == "open"
    half = suite.circuit_check(failure_count=5, success_after_open=1)
    assert half["state"] == "half_open"
    closed = suite.circuit_check(failure_count=5, success_after_open=3)
    assert closed["state"] == "closed"

    retry = suite.retry_check(strategy="fixed_delay", max_attempts=3)
    assert retry["attempts"] == 3
    with pytest.raises(ValidationError):
        suite.retry_check(strategy="magic")

    fb = suite.fallback_check(preferred="backup_ai_provider")
    assert fb["service_continued"] is True

    deps = suite.dependency_map(failed_service="event_bus")
    assert deps["blast_radius"] >= 1
    assert "database" in deps["chain"]

    health = suite.health_monitor(services=["enterprise_hub", "event_bus"], incidents={"event_bus": 2})
    assert health["count"] == 2

    incidents = suite.list_incidents()
    assert incidents["count"] >= 1

    dash = suite.dashboard()
    assert dash["ci_cd_required"] is True
    assert "recovery_time_ms" in dash


def test_bootstrap_ece():
    suite = enterprise_hub.chaos_engineering
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "8.4.0"
    assert boot["chaos_engineering_ready"] is True
    assert boot["failure_injection_ready"] is True
    assert boot["recovery_engine_ready"] is True
    assert boot["circuit_breaker_ready"] is True
    assert boot["no_data_loss"] is True
    assert boot["automatic_recovery"] is True
    assert boot["ci_cd_required"] is True
    assert boot["required_before_production"] is True
    assert boot["duplicates_core_logic"] is False
    assert boot["integrations"]["linked"] is True


@pytest.mark.asyncio
async def test_api_ece(client):
    health = await client.get(f"{ECE}/health")
    body = await health.json()
    assert body["application_version"] == "8.4.0"
    assert body["chaos_engineering_ready"] is True

    boot = await client.post(f"{ECE}/bootstrap", json={})
    assert boot.status == 201
    assert (await boot.json())["failure_injection_ready"] is True

    for prefix in PREFIXES:
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        payload = await resp.json()
        version = payload.get("application_version") or payload.get("data", {}).get("application_version")
        assert version == "8.4.0"


def test_docs_and_regression_25_3():
    for name in (
        "ENTERPRISE_CHAOS_ENGINEERING.md",
        "ECE_CONTROLLER_INJECTION.md",
        "ECE_RECOVERY_RESILIENCE.md",
        "ECE_DASHBOARD_REPORTS.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_CHAOS_ENGINEERING.md").exists()
    assert (ROOT / "platform_chaos" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "chaos_engineering" / "facade.py").exists()

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
    assert '"application_version": "8.4.0"' in manifest
    assert "25.4" in manifest
