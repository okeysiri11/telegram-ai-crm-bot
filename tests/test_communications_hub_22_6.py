"""Tests — Enterprise Communications Hub (Sprint 22.6 / v6.7.0)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from applications.enterprise_hub.shared.exceptions import ValidationError
from platform_communications_hub.models import AUTOMATION_SCENARIOS, INDUSTRIES, PRINCIPLES


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
]
ECH = "/api/enterprise-ech/v1"


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


def test_version_ech_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "6.7.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v6.6.0"
    assert health["communications_hub_ready"] is True
    assert health["unified_messaging_ready"] is True
    assert health["comms_automation_ready"] is True
    assert health["comms_analytics_ready"] is True
    assert health["engines"]["communications_hub"] == "1.0"
    assert health["engines"]["communications"] == "1.0"
    assert set(PRINCIPLES)
    assert "beauty" in INDUSTRIES and "port" in INDUSTRIES


def test_send_gate_templates_automation_assistant():
    suite = enterprise_hub.communications_hub
    with pytest.raises(ValidationError):
        suite.send_message(channel="sms", recipient="+1", body="hi")
    msg = suite.send_message(
        channel="sms",
        recipient="+7000",
        body="Confirmed",
        approved=True,
        customer_id="cust1",
        industry="beauty",
    )
    assert msg["gateway"] == "enterprise_communications_hub"
    assert msg["ai_sent"] is False
    tmpl = suite.create_template(
        name="thanks",
        category="post_visit",
        body="Thanks {{name}}",
        variables=["name"],
    )
    assert tmpl["version"] == 1
    auto = suite.create_automation(scenario="birthday", channel="telegram", pre_approved=True)
    assert auto["enabled"] is True
    assert "birthday" in AUTOMATION_SCENARIOS
    timeline = suite.timeline(customer_id="cust1")
    assert timeline["count"] >= 1
    assistant = suite.assistant(purpose="open_slot", customer_id="cust1")
    assert assistant["proposes_only"] is True
    assert assistant["ai_may_send"] is False
    delivery = suite.enqueue_campaign(
        campaign_id="c1", recipients=["a", "b"], channel="email", body="Promo"
    )
    assert delivery["auto_sent_by_ai"] is False
    analytics = suite.analytics(delivered=10, opened=4, clicks=2, conversions=1, bookings=1, sales=20)
    assert analytics["ctr"] == 0.5


def test_bootstrap_hub():
    suite = enterprise_hub.communications_hub
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "6.7.0"
    assert boot["communications_hub_ready"] is True
    assert boot["no_module_sends_independently"] is True
    assert boot["ai_may_send"] is False
    assert boot["universal_api"] is True
    assert boot["duplicates_core_logic"] is False
    assert boot["integrations"]["linked"] is True
    assert boot["integrations"]["existing_comms_ref"] == "enterprise_comms"


@pytest.mark.asyncio
async def test_api_ech(client):
    health = await client.get(f"{ECH}/health")
    body = await health.json()
    assert body["application_version"] == "6.7.0"
    assert body["communications_hub_ready"] is True

    boot = await client.post(f"{ECH}/bootstrap", json={})
    assert boot.status == 201
    assert (await boot.json())["no_module_sends_independently"] is True

    for prefix in PREFIXES:
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        payload = await resp.json()
        version = payload.get("application_version") or payload.get("data", {}).get("application_version")
        assert version == "6.7.0"


def test_docs_and_regression_22_6():
    for name in (
        "ENTERPRISE_COMMUNICATIONS_HUB.md",
        "ECH_CENTER_TEMPLATES_AUTOMATION.md",
        "ECH_TIMELINE_ASSISTANT_DELIVERY.md",
        "ECH_ANALYTICS_INDUSTRIES.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_COMMUNICATIONS_HUB.md").exists()
    assert (ROOT / "platform_communications_hub" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "communications_hub" / "facade.py").exists()

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
