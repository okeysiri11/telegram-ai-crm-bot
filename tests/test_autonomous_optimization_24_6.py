"""Tests — Enterprise Autonomous Optimization Engine (Sprint 24.6 / v7.6.0)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from applications.enterprise_hub.shared.exceptions import ValidationError
from platform_enterprise_autonomous_optimization.models import (
    CATEGORIES,
    COUNCIL_ROLES,
    INTEGRATION_TARGETS,
    KPI_TARGETS,
    PRINCIPLES,
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
]
EOE = "/api/enterprise-eoe/v1"


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


def test_version_eoe_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "7.6.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v7.5.0"
    assert health["autonomous_optimization_ready"] is True
    assert health["process_optimizer_ready"] is True
    assert health["revenue_optimizer_ready"] is True
    assert health["owner_optimization_ready"] is True
    assert health["engines"]["autonomous_optimization"] == "1.0"
    # prior suites remain
    assert health["enterprise_digital_twin_ready"] is True
    assert health["enterprise_ai_orchestrator_ready"] is True
    assert "process" in CATEGORIES
    assert "product" in COUNCIL_ROLES
    assert "enterprise_digital_twin" in INTEGRATION_TARGETS
    assert KPI_TARGETS["no_autonomous_critical_changes"] is True
    assert set(PRINCIPLES)


def test_optimizers_council_owner_verify():
    suite = enterprise_hub.autonomous_optimization
    scan = suite.scan(
        signals={
            "redundant_steps": 2,
            "bottleneck_ms": 2000,
            "unused_licenses": 2,
            "avg_ticket": 30,
            "target_ticket": 50,
            "journey_dropoffs": 1,
            "staff_idle_pct": 0.3,
        }
    )
    assert scan["process"]["category"] == "process"
    assert scan["revenue"]["category"] == "revenue"
    assert scan["ai_may_act"] is False

    proposed = suite.propose(
        opportunity_id="opp_test_1",
        category="cost",
        title="Retire unused licenses",
        priority="high",
        business_value=500,
        expected_roi=0.6,
        confidence=0.85,
        risk_score=0.2,
    )
    assert proposed["council"]["unified"] is True
    assert proposed["council"]["requires_owner"] is True
    assert proposed["opportunity"]["owner_status"] == "awaiting_owner"
    assert proposed["opportunity"]["ranked"] is True
    assert proposed["ai_may_act"] is False

    decision = suite.owner_decide(
        action="approve",
        actor="platform_owner",
        opportunity_id="opp_test_1",
    )
    assert decision["status"] == "approved"
    assert decision["autonomous_deploy"] is False

    with pytest.raises(ValidationError):
        suite.owner_decide(action="approve", actor="agent", opportunity_id="opp_test_1")

    blocked = suite.verify(opportunity_id="opp_test_1", expected=500, actual=480, confirmed=False)
    assert blocked["verified"] is False
    assert blocked["requires_confirmed"] is True

    verified = suite.verify(opportunity_id="opp_test_1", expected=500, actual=480, confirmed=True)
    assert verified["verified"] is True
    assert verified["success"] is True
    assert verified["confirmed_only"] is True

    ranked = suite.list_opportunities()
    assert ranked["ranked"] is True
    assert ranked["count"] >= 1

    dash = suite.owner_dashboard()
    assert dash["ai_may_act"] is False
    assert "projected_savings" in dash


def test_bootstrap_eoe():
    suite = enterprise_hub.autonomous_optimization
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "7.6.0"
    assert boot["autonomous_optimization_ready"] is True
    assert boot["process_optimizer_ready"] is True
    assert boot["revenue_optimizer_ready"] is True
    assert boot["owner_optimization_ready"] is True
    assert boot["ai_may_act"] is False
    assert boot["autonomous_deploy"] is False
    assert boot["council_reviewed"] is True
    assert boot["ranked"] is True
    assert boot["verified_confirmed_only"] is True
    assert boot["duplicates_core_logic"] is False
    assert boot["integrations"]["linked"] is True


@pytest.mark.asyncio
async def test_api_eoe(client):
    health = await client.get(f"{EOE}/health")
    body = await health.json()
    assert body["application_version"] == "7.6.0"
    assert body["autonomous_optimization_ready"] is True

    boot = await client.post(f"{EOE}/bootstrap", json={})
    assert boot.status == 201
    assert (await boot.json())["owner_optimization_ready"] is True

    for prefix in PREFIXES:
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        payload = await resp.json()
        version = payload.get("application_version") or payload.get("data", {}).get("application_version")
        assert version == "7.6.0"


def test_docs_and_regression_24_6():
    for name in (
        "ENTERPRISE_AUTONOMOUS_OPTIMIZATION.md",
        "EOE_REGISTRY_OPTIMIZERS.md",
        "EOE_COUNCIL_SCORING.md",
        "EOE_VERIFY_OWNER.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_AUTONOMOUS_OPTIMIZATION.md").exists()
    assert (ROOT / "platform_enterprise_autonomous_optimization" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "autonomous_optimization" / "facade.py").exists()

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
    assert '"application_version": "7.6.0"' in manifest
    assert "24.6" in manifest
