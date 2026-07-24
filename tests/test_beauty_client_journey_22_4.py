"""Tests — Beauty Client Journey & Smart Booking (Sprint 22.4 / v6.7.0)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from applications.enterprise_hub.shared.exceptions import ValidationError
from platform_beauty_client_journey.models import BOOKING_CHANNELS, KPI_TARGETS, PRINCIPLES


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
]
BCJ = "/api/enterprise-bcj/v1"


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


def test_version_bcj_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "6.7.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v6.6.0"
    assert health["beauty_client_journey_ready"] is True
    assert health["smart_booking_ready"] is True
    assert health["waitlist_ready"] is True
    assert health["loyalty_triggers_ready"] is True
    assert health["beauty_os_ready"] is True
    assert health["beauty_workspace_ready"] is True
    assert health["engines"]["beauty_client_journey"] == "1.0"
    assert set(PRINCIPLES)
    assert KPI_TARGETS["booking_under_30s"] is True


def test_booking_waitlist_loyalty_assistant():
    suite = enterprise_hub.beauty_client_journey
    enterprise_hub.beauty_os.bootstrap()
    avail = suite.suggest_availability(service_ids=["haircut", "color"])
    assert avail["requires_confirmation"] is True
    assert avail["ai_may_book"] is False
    assert avail["optimal"]
    booking = suite.smart_book(
        channel="administrator",
        customer_id="c_flow",
        service_ids=["haircut", "color"],
        auto_pick=True,
    )
    assert booking["under_30s"] is True
    assert booking["multi_service"] is True
    assert booking["ai_auto_executed"] is False
    journey = suite.create_journey(customer_id="c_loyal", source="referral")
    wait = suite.join_waitlist(customer_id="c_wait2", service_ids=["manicure"])
    assert wait["status"] == "waiting"
    offer = suite.offer_waitlist_slot(
        customer_id="c_wait2",
        slot={"start": "2026-07-27T11:00:00Z", "end": "2026-07-27T12:00:00Z"},
    )
    assert offer["offered"] is True
    assert offer["auto_booked"] is False
    loyalty = suite.loyalty_scan(journey_id=journey["journey_id"])
    assert loyalty["count"] >= 1
    assert all(o["auto_sent"] is False for o in loyalty["offers"])
    assistant = suite.booking_assistant(service_ids=["facial"], customer_id="c_loyal")
    assert assistant["proposes_only"] is True
    assert assistant["ai_may_execute"] is False
    with pytest.raises(ValidationError):
        suite.smart_book(channel="unknown", customer_id="x", service_ids=["y"])
    assert set(BOOKING_CHANNELS)


def test_bootstrap_lifecycle():
    suite = enterprise_hub.beauty_client_journey
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "6.7.0"
    assert boot["lifecycle_ready"] is True
    assert boot["ai_may_execute"] is False
    assert boot["booking_under_30s"] is True
    assert boot["duplicates_core_logic"] is False
    assert boot["integrations"]["linked"] is True
    assert boot["reminders"] >= 4
    assert boot["waitlist_offered"] is True


@pytest.mark.asyncio
async def test_api_bcj(client):
    health = await client.get(f"{BCJ}/health")
    body = await health.json()
    assert body["application_version"] == "6.7.0"
    assert body["beauty_client_journey_ready"] is True

    boot = await client.post(f"{BCJ}/bootstrap", json={})
    assert boot.status == 201
    assert (await boot.json())["lifecycle_ready"] is True

    avail = await client.post(f"{BCJ}/availability", json={"service_ids": ["haircut"]})
    assert avail.status == 201
    assert (await avail.json())["requires_confirmation"] is True

    for prefix in PREFIXES:
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        payload = await resp.json()
        version = payload.get("application_version") or payload.get("data", {}).get("application_version")
        assert version == "6.7.0"


def test_docs_and_regression_22_4():
    for name in (
        "ENTERPRISE_BEAUTY_CLIENT_JOURNEY.md",
        "BCJ_SMART_BOOKING_AVAILABILITY.md",
        "BCJ_JOURNEY_WAITLIST_REMINDERS.md",
        "BCJ_LOYALTY_AI_ASSISTANT.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_BEAUTY_CLIENT_JOURNEY.md").exists()
    assert (ROOT / "platform_beauty_client_journey" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "beauty_client_journey" / "facade.py").exists()

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
    assert '"application_version": "6.7.0"' in manifest
    assert "22.6" in manifest
