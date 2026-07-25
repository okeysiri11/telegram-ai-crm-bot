"""Tests — Enterprise Test Infrastructure Foundation (Sprint 26.1 / v9.0.0)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from applications.enterprise_hub.shared.exceptions import ValidationError
from platform_testing.models import (
    ENVIRONMENTS,
    INTEGRATION_TARGETS,
    KPI_TARGETS,
    PIPELINE_STAGES,
    PRINCIPLES,
    TEST_CATEGORIES,
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
]
ETI = "/api/enterprise-eti/v1"


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


def test_version_eti_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "9.0.4"
    assert health["enterprise_foundation"] == "Enterprise Platform v8.7.0"
    assert health["test_infrastructure_ready"] is True
    assert health["test_registry_ready"] is True
    assert health["test_runner_ready"] is True
    assert health["test_dashboard_ready"] is True
    assert health["engines"]["test_infrastructure"] == "1.0"
    assert health["extension_sdk_ready"] is True
    assert health["quality_assurance_ready"] is True
    assert "smoke" in TEST_CATEGORIES
    assert "chaos" in TEST_CATEGORIES
    assert "discovery" in PIPELINE_STAGES
    assert "production_mirror" in ENVIRONMENTS
    assert "ai_provider_hub" in INTEGRATION_TARGETS
    assert KPI_TARGETS["unified_test_runner"] is True
    assert "single_test_center" in PRINCIPLES


def test_registry_runner_pipeline_reports():
    suite = enterprise_hub.test_infrastructure
    t1 = suite.register_test(
        test_id="tst_unit_1",
        name="Unit sample",
        module="enterprise_hub",
        category="unit",
        tags=["unit", "hub"],
    )
    suite.register_test(
        test_id="tst_smoke_1",
        name="Smoke sample",
        module="enterprise_hub",
        category="smoke",
        tags=["smoke"],
    )
    suite.register_test(
        test_id="tst_api_1",
        name="API sample",
        module="extension_sdk",
        category="api",
        tags=["api"],
    )
    assert t1["last_result"] is None

    by_module = suite.run(module="enterprise_hub", environment="ci")
    assert by_module["pipeline"]["completed"] is True
    assert by_module["execution"]["passed"] == 2
    assert by_module["environment"]["isolated"] is True
    assert set(by_module["reports"]["formats"]) == {"html", "json", "xml", "console"}

    by_tag = suite.run(tag="api")
    assert by_tag["execution"]["total"] == 1

    full = suite.run(full=True, fail_ids=["tst_unit_1"])
    assert full["execution"]["failed"] == 1
    assert full["execution"]["success"] is False

    smoke = suite.smoke(modules=["enterprise_hub"])
    assert smoke["passed"] is True
    assert suite.integration_check()["passed"] is True
    assert suite.regression(baseline_pass_rate=1.0, current_pass_rate=1.0)["passed"] is True
    assert suite.validate_contracts(
        contracts=[{"contract_id": "c1", "required_fields": ["a"], "payload": {"a": 1}}]
    )["passed"] is True

    data = suite.generate_data(entity="clients", count=3)
    assert data["auto_generated"] is True
    assert data["count"] == 3

    with pytest.raises(ValidationError):
        suite.generate_data(entity="aliens")

    with pytest.raises(ValidationError):
        suite.provision_env(environment="prod")

    env = suite.provision_env(environment="docker")
    assert env["isolated"] is True

    cov = suite.coverage(covered_lines=80, total_lines=100)
    assert cov["coverage_pct"] == 0.8

    dash = suite.dashboard()
    assert "quality_score" in dash
    assert "coverage" in dash

    analytics = suite.analytics()
    assert "avg_duration_ms" in analytics
    assert "run_history" in analytics


def test_bootstrap_eti():
    suite = enterprise_hub.test_infrastructure
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "9.0.4"
    assert boot["test_infrastructure_ready"] is True
    assert boot["test_registry_ready"] is True
    assert boot["test_runner_ready"] is True
    assert boot["test_dashboard_ready"] is True
    assert boot["isolated_environments"] is True
    assert boot["auto_reports"] is True
    assert boot["duplicates_core_logic"] is False
    assert boot["integrations"]["linked"] is True
    assert boot["integrations"]["duplicates_eqa_logic"] is False


@pytest.mark.asyncio
async def test_api_eti(client):
    health = await client.get(f"{ETI}/health")
    body = await health.json()
    assert body["application_version"] == "9.0.4"
    assert body["test_infrastructure_ready"] is True

    boot = await client.post(f"{ETI}/bootstrap", json={})
    assert boot.status == 201
    assert (await boot.json())["test_runner_ready"] is True

    for prefix in PREFIXES:
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        payload = await resp.json()
        version = payload.get("application_version") or payload.get("data", {}).get("application_version")
        assert version == "9.0.4"


def test_docs_and_regression_25_1():
    for name in (
        "ENTERPRISE_TEST_INFRASTRUCTURE.md",
        "ETI_REGISTRY_RUNNER.md",
        "ETI_ENV_DATA_ENGINES.md",
        "ETI_DASHBOARD_REPORTS.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_TEST_INFRASTRUCTURE.md").exists()
    assert (ROOT / "platform_testing" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "test_infrastructure" / "facade.py").exists()

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
