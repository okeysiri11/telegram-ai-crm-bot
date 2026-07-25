"""Tests — Enterprise Certification (Sprint 26.1 / v9.0.0)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from platform_enterprise_certification.models import (
    INTEGRATION_TARGETS,
    KPI_TARGETS,
    PRINCIPLES,
    QUALITY_GATES,
    STAGE_25_COMPLETE,
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
]
ECF = "/api/enterprise-ecf/v1"


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


def test_version_ecf_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "9.0.4"
    assert health["enterprise_foundation"] == "Enterprise Platform v8.7.0"
    assert health["certification_ready"] is True
    assert health["quality_gates_ready"] is True
    assert health["release_builder_ready"] is True
    assert health["enterprise_certified"] is True
    assert health["enterprise_ready"] is True
    assert health["release_approved"] is True
    assert health["ready_for_enterprise_web_platform"] is True
    assert health["engines"]["certification"] == "1.0"
    assert health["production_platform_ready"] is True
    assert "security_verification" in QUALITY_GATES
    assert "production_readiness" in INTEGRATION_TARGETS
    assert "enterprise_certification" in STAGE_25_COMPLETE
    assert KPI_TARGETS["block_release_on_critical"] is True
    assert "enterprise_ready_status" in PRINCIPLES


def test_certification_gate_blocks_on_failures():
    suite = enterprise_hub.certification
    clean = suite.run_gate(release="9.0.4")
    assert clean["release_blocked"] is False
    assert clean["enterprise_certified"] is True
    assert clean["production_ready"] is True
    assert clean["release_approved"] is True
    assert clean["ready_for_enterprise_web_platform"] is True
    assert clean["status"] == "ENTERPRISE READY"
    assert clean["reports"]["unified_certification_report"] is True
    assert clean["package"]["package_ready"] is True
    assert clean["readiness"]["overall_readiness_percent"] == 100.0
    assert clean["versions"]["full_history"] is True

    blocked = suite.run_gate(
        release="9.0.4",
        failed_gates=["chaos_tests", "security_verification"],
        missing_architecture=["event_bus"],
        missing_docs=["deployment_guide"],
        readiness_scores={"security": 50.0},
    )
    assert blocked["release_blocked"] is True
    assert blocked["enterprise_certified"] is False
    assert blocked["status"] == "NOT READY"
    assert blocked["quality"]["blocks_release"] is True
    assert blocked["architecture"]["blocks_release"] is True
    assert blocked["documentation"]["blocks_release"] is True

    dash = suite.dashboard()
    assert "overall_readiness" in dash
    assert "final_certification" in dash


def test_bootstrap_ecf():
    suite = enterprise_hub.certification
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "9.0.4"
    assert boot["certification_ready"] is True
    assert boot["quality_gates_ready"] is True
    assert boot["release_builder_ready"] is True
    assert boot["enterprise_certified"] is True
    assert boot["enterprise_ready"] is True
    assert boot["status"] == "ENTERPRISE READY"
    assert boot["phase3_ready"] is True
    assert boot["next_phase"] == "enterprise_web_platform"
    assert boot["next_version"] == "9.0.4"
    assert boot["duplicates_core_logic"] is False
    assert boot["duplicates_erl_logic"] is False
    assert boot["integrations"]["linked"] is True
    assert "enterprise_certification" in boot["integrations"]["stage_25_complete"]


@pytest.mark.asyncio
async def test_api_ecf(client):
    health = await client.get(f"{ECF}/health")
    body = await health.json()
    assert body["application_version"] == "9.0.4"
    assert body["certification_ready"] is True
    assert body["enterprise_ready"] is True

    boot = await client.post(f"{ECF}/bootstrap", json={})
    assert boot.status == 201
    payload = await boot.json()
    assert payload["enterprise_certified"] is True
    assert payload["ready_for_enterprise_web_platform"] is True

    # legacy ERL / EPD remain
    erl = await client.get("/api/enterprise-erl/v1/health")
    assert erl.status == 200
    epd = await client.get("/api/enterprise-epd/v1/health")
    assert epd.status == 200

    for prefix in PREFIXES:
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        payload = await resp.json()
        version = payload.get("application_version") or payload.get("data", {}).get("application_version")
        assert version == "9.0.4"


def test_docs_and_regression_25_7():
    for name in (
        "ENTERPRISE_CERTIFICATION.md",
        "ECF_QUALITY_GATES.md",
        "ECF_ARCHITECTURE_DOCS.md",
        "ECF_RELEASE_DASHBOARD.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_CERTIFICATION.md").exists()
    assert (ROOT / "platform_enterprise_certification" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "certification" / "facade.py").exists()

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
    assert '"enterprise_ready": true' in manifest or '"enterprise_certified": true' in manifest
