"""Tests — Enterprise Operations Center & Pilot Release (Sprint 24.2 / v7.2.0)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from applications.enterprise_hub.shared.exceptions import ValidationError
from platform_enterprise_operations.models import (
    KPI_TARGETS,
    OWNER_ACTIONS,
    PRINCIPLES,
    TENANT_HEALTH_DIMS,
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
]
EOC = "/api/enterprise-eoc/v1"


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


def test_version_eoc_pilot_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "7.2.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v7.1.0"
    assert health["operations_center_ready"] is True
    assert health["pilot_release_ready"] is True
    assert health["tenant_health_ready"] is True
    assert health["owner_command_ready"] is True
    assert health["engines"]["enterprise_operations"] == "1.0"
    assert set(TENANT_HEALTH_DIMS)
    assert "approve_release" in OWNER_ACTIONS
    assert KPI_TARGETS["pilot_success"] is True
    assert set(PRINCIPLES)


def test_dashboard_health_feedback_owner():
    suite = enterprise_hub.operations_center
    dash = suite.dashboard(
        companies=[
            {"company_id": "a", "stage": "pilot", "status": "Active"},
            {"company_id": "b", "stage": "onboarding", "status": "Onboarding", "new_registration": True},
        ],
        users=10,
        ai_agents=3,
        releases=[{"version": "7.2.0"}],
    )
    assert dash["pilot"] == 1
    assert dash["onboarding"] == 1
    assert dash["stage"] == "pilot_release"

    health = suite.tenant_health(
        company_id="a",
        dimensions={d: 1.0 for d in TENANT_HEALTH_DIMS},
        performance=0.95,
    )
    assert health["health_score"] >= 0.8
    assert health["status"] == "healthy"

    mon = suite.platform_monitoring()
    assert mon["all_ok"] is True

    pilot = suite.pilot_profile(
        company_id="a",
        readiness_pct=80,
        staff_trained=True,
        daily_users=5,
        feedback=["great"],
        issues=[],
        improvements=["faster booking"],
    )
    assert pilot["pilot"] is True

    fb = suite.collect_feedback(role="master", message="Calendar lag", company_id="a", kind="error")
    assert fb["routed_to"] == "product_intelligence"
    assert fb["epi_routed"] is True

    usage = suite.usage_analytics(
        events=[
            {"feature": "booking", "duration_ms": 500},
            {"feature": "pos", "duration_ms": 700, "error": True},
            {"feature": "ai", "ai_recommendation": "upsell"},
        ]
    )
    assert "booking" in usage["most_used"]
    assert usage["user_errors"] == 1

    report = suite.daily_ops_report(dashboard=dash, pilots=[pilot], usage=usage, monitoring=mon)
    assert report["proposes_only"] is True
    assert report["ai_may_act"] is False
    assert report["requires_owner_approval"] is True

    rel = suite.record_release(version="7.2.0", changelog=["eoc"], test_results={"passed": True})
    assert rel["version"] == "7.2.0"

    inc = suite.open_incident(title="API timeout", severity="high")
    resolved = suite.resolve_incident(incident_id=inc["incident_id"], investigation="lb", fix="restart")
    assert resolved["status"] == "resolved"

    ok = suite.owner_approve(action="promote_to_production", actor="platform_owner", payload={"company_id": "a"})
    assert ok["approved"] is True

    with pytest.raises(ValidationError):
        suite.owner_approve(action="approve_release", actor="admin")


def test_bootstrap_ops():
    suite = enterprise_hub.operations_center
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "7.2.0"
    assert boot["operations_center_ready"] is True
    assert boot["pilot_release"] is True
    assert boot["pilot_release_ready"] is True
    assert boot["ai_may_act"] is False
    assert boot["feedback_to_epi"] is True
    assert boot["requires_owner_approval"] is True
    assert boot["duplicates_core_logic"] is False
    assert boot["integrations"]["linked"] is True
    assert boot["release_stage"] == "pilot_release"


@pytest.mark.asyncio
async def test_api_eoc(client):
    health = await client.get(f"{EOC}/health")
    body = await health.json()
    assert body["application_version"] == "7.2.0"
    assert body["operations_center_ready"] is True
    assert body["release_stage"] == "pilot_release"

    boot = await client.post(f"{EOC}/bootstrap", json={})
    assert boot.status == 201
    assert (await boot.json())["pilot_release"] is True

    for prefix in PREFIXES:
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        payload = await resp.json()
        version = payload.get("application_version") or payload.get("data", {}).get("application_version")
        assert version == "7.2.0"


def test_docs_and_regression_23_0():
    for name in (
        "ENTERPRISE_OPERATIONS_CENTER.md",
        "EOC_DASHBOARD_HEALTH.md",
        "EOC_PILOT_FEEDBACK_USAGE.md",
        "EOC_ADVISOR_OWNER.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_OPERATIONS_CENTER.md").exists()
    assert (ROOT / "platform_enterprise_operations" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "operations_center" / "facade.py").exists()

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
    assert '"application_version": "7.2.0"' in manifest
    assert "24.2" in manifest
    assert "pilot_release" in manifest
