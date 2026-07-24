"""Tests — Client Portal & Mobile Experience (Sprint 24.3 / v7.3.0)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from applications.enterprise_hub.shared.exceptions import ValidationError
from platform_client_portal.models import INTEGRATION_TARGETS, KPI_TARGETS, MOBILE_PLATFORMS, PRINCIPLES


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
]
CPL = "/api/enterprise-cpl/v1"


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


def test_version_cpl_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "7.3.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v7.2.0"
    assert health["client_portal_ready"] is True
    assert health["online_booking_ready"] is True
    assert health["mobile_experience_ready"] is True
    assert health["portal_security_ready"] is True
    assert health["engines"]["client_portal"] == "1.0"
    assert set(PRINCIPLES)
    assert KPI_TARGETS["booking_under_60s"] is True
    assert set(MOBILE_PLATFORMS) == {"android", "ios", "pwa"}
    assert "smart_booking" in INTEGRATION_TARGETS


def test_account_booking_loyalty_assistant_security():
    suite = enterprise_hub.client_portal
    # seed commerce for enrichment
    enterprise_hub.commerce_core.issue_certificate(face_value=40, customer_id="c_portal")
    enterprise_hub.commerce_core.create_membership(customer_id="c_portal", visits_limit=4)
    enterprise_hub.commerce_core.loyalty_profile(customer_id="c_portal", points=80)

    account = suite.create_account(customer_id="c_portal", name="Portal Client", phone="+7999")
    assert account["customer_id"] == "c_portal"
    assert account["bonuses"] == 80
    assert len(account["certificates"]) >= 1
    assert len(account["memberships"]) >= 1

    booking = suite.online_book(
        customer_id="c_portal",
        branch_id="b1",
        service_ids=["cut", "color"],
        employee_id="e1",
        start="2026-07-28T10:00:00Z",
        end="2026-07-28T12:00:00Z",
    )
    assert booking["under_60s"] is True
    assert booking["self_service"] is True
    assert booking["multi_service"] is True
    assert booking["smart_booking_ref"] == "beauty_client_journey"

    waitlist = suite.online_book(
        customer_id="c_portal",
        branch_id="b1",
        service_ids=["cut"],
        waitlist=True,
    )
    assert waitlist["status"] == "waitlist"

    cal = suite.personal_calendar(customer_id="c_portal")
    assert "upcoming" in cal or "past" in cal or "cancelled" in cal

    loy = suite.loyalty_center(customer_id="c_portal")
    assert loy["balance"] == 80

    certs = suite.certificates(customer_id="c_portal")
    assert certs["count"] >= 1

    mems = suite.memberships(customer_id="c_portal")
    assert len(mems["active"]) >= 1

    advice = suite.assistant(customer_id="c_portal")
    assert advice["proposes_only"] is True
    assert advice["ai_may_act"] is False

    notes = suite.notifications(customer_id="c_portal")
    assert notes["count"] >= 1

    sec = suite.secure_account(customer_id="c_portal", device_id="iphone1", platform="ios")
    assert sec["two_factor"]["two_factor"] is True
    assert sec["consent"]["personal_data_consent"] is True
    assert sec["login"]["success"] is True

    with pytest.raises(ValidationError):
        suite.create_account(customer_id="", name="x")


def test_bootstrap_portal():
    suite = enterprise_hub.client_portal
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "7.3.0"
    assert boot["client_portal_ready"] is True
    assert boot["booking_under_60s"] is True
    assert boot["ai_may_act"] is False
    assert boot["mobile_first"] is True
    assert boot["duplicates_core_logic"] is False
    assert boot["integrations"]["linked"] is True
    assert set(boot["platforms"]) == {"android", "ios", "pwa"}


@pytest.mark.asyncio
async def test_api_cpl(client):
    health = await client.get(f"{CPL}/health")
    body = await health.json()
    assert body["application_version"] == "7.3.0"
    assert body["client_portal_ready"] is True

    boot = await client.post(f"{CPL}/bootstrap", json={})
    assert boot.status == 201
    assert (await boot.json())["client_portal_ready"] is True

    for prefix in PREFIXES:
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        payload = await resp.json()
        version = payload.get("application_version") or payload.get("data", {}).get("application_version")
        assert version == "7.3.0"


def test_docs_and_regression_22_8():
    for name in (
        "ENTERPRISE_CLIENT_PORTAL.md",
        "CPL_ACCOUNT_BOOKING.md",
        "CPL_LOYALTY_CALENDAR.md",
        "CPL_ASSISTANT_MOBILE_SECURITY.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_CLIENT_PORTAL.md").exists()
    assert (ROOT / "platform_client_portal" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "client_portal" / "facade.py").exists()

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
    assert '"application_version": "7.3.0"' in manifest
    assert "24.3" in manifest
