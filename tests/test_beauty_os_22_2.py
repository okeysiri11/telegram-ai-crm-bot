"""Tests — Beauty Operating System (Sprint 22.2 / v7.7.0)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from applications.enterprise_hub.shared.exceptions import ValidationError
from platform_beauty_os.models import FUTURE_INDUSTRIES, PRINCIPLES


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
]
BOS = "/api/enterprise-bos/v1"


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


def test_version_bos_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "7.7.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v7.6.0"
    assert health["beauty_os_ready"] is True
    assert health["beauty_appointments_ready"] is True
    assert health["beauty_dashboard_ready"] is True
    assert health["beauty_integrations_ready"] is True
    assert health["ai_business_advisor_ready"] is True
    assert health["product_intelligence_ready"] is True
    assert health["engines"]["beauty_os"] == "1.0"
    assert set(PRINCIPLES)
    assert "cafe" in FUTURE_INDUSTRIES


def test_salon_flow_and_conflicts():
    suite = enterprise_hub.beauty_os
    company = suite.create_company(name="Glow Studio", currency="EUR", timezone="Europe/Berlin")
    assert company["industry"] == "beauty"
    branch = suite.create_branch(name="Downtown")
    assert branch["uses_enterprise_services"] is True
    employee = suite.create_employee(name="Ivy", role="nail_tech", specialization="nails")
    service = suite.create_service(name="Gel Polish", category="nails", duration_min=50, price=45.0)
    customer = suite.create_customer(name="Alex", preferences=["evening"])
    assert customer["uses_enterprise_crm"] is True
    appt = suite.book_appointment(
        customer_id=customer["customer_id"],
        service_id=service["service_id"],
        employee_id=employee["employee_id"],
        branch_id=branch["branch_id"],
        start="2026-07-26T12:00:00Z",
        end="2026-07-26T12:50:00Z",
        resource_id="chair-1",
    )
    assert appt["status"] == "booked"
    assert appt["calendar_ref"] == "enterprise_calendar"
    confirmed = suite.transition_appointment(appointment_id=appt["appointment_id"], status="confirmed")
    assert confirmed["status"] == "confirmed"
    with pytest.raises(ValidationError):
        suite.book_appointment(
            customer_id=customer["customer_id"],
            service_id=service["service_id"],
            employee_id=employee["employee_id"],
            branch_id=branch["branch_id"],
            start="2026-07-26T12:10:00Z",
            end="2026-07-26T12:40:00Z",
            resource_id="chair-1",
        )
    with pytest.raises(ValidationError):
        suite.create_company(name="")


def test_bootstrap_dashboard_integrations():
    suite = enterprise_hub.beauty_os
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "7.7.0"
    assert boot["pilot_ready"] is True
    assert boot["duplicates_core_logic"] is False
    assert boot["services"] == 3
    assert boot["integrations"]["linked"] is True
    assert boot["integrations"]["ai_business_advisor"] == "ai_business_advisor"
    assert boot["integrations"]["product_intelligence"] == "product_intelligence"
    dash = suite.dashboard()
    assert dash["status"] == "ready"
    assert "revenue" in dash
    assert dash["advisor_ref"] == "ai_business_advisor"


@pytest.mark.asyncio
async def test_api_bos(client):
    health = await client.get(f"{BOS}/health")
    body = await health.json()
    assert body["application_version"] == "7.7.0"
    assert body["beauty_os_ready"] is True

    boot = await client.post(f"{BOS}/bootstrap", json={})
    assert boot.status == 201
    assert (await boot.json())["pilot_ready"] is True

    dash = await client.get(f"{BOS}/dashboard")
    assert dash.status == 200
    assert (await dash.json())["status"] == "ready"

    for prefix in PREFIXES:
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        payload = await resp.json()
        version = payload.get("application_version") or payload.get("data", {}).get("application_version")
        assert version == "7.7.0"


def test_docs_and_regression_22_2():
    for name in (
        "ENTERPRISE_BEAUTY_OS.md",
        "BOS_COMPANY_BRANCHES.md",
        "BOS_STAFF_SERVICES_RESOURCES.md",
        "BOS_APPOINTMENTS_DASHBOARD.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_BEAUTY_OS.md").exists()
    assert (ROOT / "platform_beauty_os" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "beauty_os" / "facade.py").exists()

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
    assert '"application_version": "7.7.0"' in manifest
    assert "24.7" in manifest
