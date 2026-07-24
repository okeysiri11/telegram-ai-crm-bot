"""Tests — Enterprise Communications & Notifications (Sprint 19.4)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from applications.enterprise_hub.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
HUB = "/api/enterprise-hub/v1"
ORCH = "/api/enterprise-orch/v1"
KG = "/api/enterprise-kg/v1"
AA = "/api/enterprise-agents/v1"
CM = "/api/enterprise-comms/v1"


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


def test_version_communications_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "7.3.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v7.2.0"
    assert health["enterprise_communications_ready"] is True
    assert health["notification_center_ready"] is True
    assert health["multi_channel_delivery_ready"] is True
    assert health["corporate_chat_ready"] is True
    assert health["enterprise_ai_agents_ready"] is True
    assert health["engines"]["communications"] == "1.0"


def test_center_router_priority_queue():
    suite = enterprise_hub.communications
    evt = suite.center.publish(
        source="crm",
        event="new_lead",
        recipient="sales@bidex.io",
        subject="New Lead",
        body="Acme",
    )
    prio = suite.priority.classify(subject="Server Down", event="outage")
    assert prio["priority"] == "critical"
    assert "telegram" in prio["channels"]
    route = suite.router.route(event_id=evt["event_id"])
    assert route["route_id"] and route["delivery_ids"]
    q = suite.queue.enqueue(
        event_id=evt["event_id"],
        recipient="sales@bidex.io",
        channel="email",
        priority="medium",
        mode="fifo",
    )
    assert q["status"] == "pending"
    with pytest.raises(ValidationError):
        suite.center.publish(source="", event="x", recipient="a")


def test_templates_chat_delivery_bootstrap():
    suite = enterprise_hub.communications
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "7.3.0"
    assert boot["route_critical_id"] and boot["chat_ai_id"] and boot["audit_id"]
    tpl = suite.templates.register(kind="lead", name="QA Lead", fmt="plain")
    rend = suite.templates.render(
        template_id=tpl["template_id"],
        variables={"name": "Sam", "company": "Bidex", "project": "Hub", "date": "2026-07-23", "status": "open"},
    )
    assert "Sam" in rend["body"]
    chat = suite.chat.ai_to_ai(from_agent="a1", to_agent="a2", message="ping")
    assert chat["party_type"] == "ai_agent"
    for dtype in ("delivery", "queue", "channels", "audit", "analytics"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_communications(client):
    health = await client.get(f"{CM}/health")
    body = await health.json()
    assert body["application_version"] == "7.3.0"
    assert body["enterprise_communications_ready"] is True
    assert body["notification_center_ready"] is True

    boot = await client.post(f"{CM}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    center = await client.post(
        f"{CM}/center",
        json={
            "source": "agro",
            "event": "harvest_alert",
            "recipient": "agro@bidex.io",
            "subject": "Harvest ready",
        },
    )
    assert center.status == 201

    for prefix in (HUB, ORCH, KG, AA):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "7.3.0"

    assert boot_body["template_invoice_id"]


def test_docs_and_regression_19_4():
    for name in (
        "ENTERPRISE_COMMUNICATIONS.md",
        "NOTIFICATION_CENTER.md",
        "NOTIFICATION_CHANNELS.md",
        "NOTIFICATION_TEMPLATES.md",
        "CORPORATE_CHAT.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_COMMUNICATIONS.md").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "communications" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "communications" / "channels" / "telegram.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "communications" / "templates" / "engine.py").exists()

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT
    from applications.auto_marketplace.config import DEFAULT_CONFIG as AUTO
    from applications.agro_enterprise.config import DEFAULT_CONFIG as AGRO
    from applications.port_enterprise.config import DEFAULT_CONFIG as PORT
    from applications.port_erp.config import DEFAULT_CONFIG as PORT_ERP
    from applications.crypto_enterprise.config import DEFAULT_CONFIG as CRYPTO
    from applications.legal_enterprise.config import DEFAULT_CONFIG as LEGAL
    from applications.finance_enterprise.config import DEFAULT_CONFIG as FINANCE

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AUTO.application_version == "4.2.0-enterprise"
    assert AGRO.application_version == "4.4.0-enterprise"
    assert PORT.application_version == "4.6.0-enterprise"
    assert PORT_ERP.application_version == "2.0.0"
    assert CRYPTO.application_version == "4.8.0-enterprise"
    assert LEGAL.application_version == "5.0.0-enterprise"
    assert FINANCE.application_version == "5.2.0-enterprise"
    manifest = (ROOT / "applications" / "enterprise_hub" / "manifest.json").read_text()
    assert "7.3.0" in manifest
    assert "24.3" in manifest
