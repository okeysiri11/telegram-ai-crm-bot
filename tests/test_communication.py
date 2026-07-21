"""Tests — Cross-Application Communication & Event Bus (Sprint 7.2)."""

from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from ecosystem import ecosystem
from ecosystem.api.register import register_ecosystem_routes
from ecosystem.communication.models import DeliveryStatus, EventCategory, MessageType, SyncScope
from ecosystem.config import DEFAULT_CONFIG


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_ecosystem_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    ecosystem.reset()
    DEFAULT_CONFIG.registered_applications[:] = ["auto_marketplace"]
    yield
    ecosystem.reset()
    DEFAULT_CONFIG.registered_applications[:] = ["auto_marketplace"]


def test_version_and_communication_manifest():
    assert DEFAULT_CONFIG.ecosystem_version == "1.5.0-alpha"
    assert DEFAULT_CONFIG.communication_layer == "1.0"
    assert DEFAULT_CONFIG.event_bus == "1.0"


@pytest.mark.asyncio
async def test_service_registry_and_bridge():
    result = await ecosystem.engine.communication.bridge.connect_application(
        "auto_marketplace",
        version="2.0.0",
        capabilities=["crm", "catalog"],
    )
    assert result["connected"] is True

    await ecosystem.engine.communication.bridge.connect_application(
        "crm_hub",
        version="1.0.0",
        capabilities=["crm"],
        dependencies=["auto_marketplace"],
    )

    apps = ecosystem.engine.communication.registry.discover_capability("crm")
    assert len(apps) >= 2
    graph = ecosystem.engine.communication.registry.dependency_graph()
    assert any(e["from"] == "crm_hub" for e in graph["edges"])
    health = ecosystem.engine.communication.registry.health_report()
    assert health["connected"] >= 2


@pytest.mark.asyncio
async def test_event_bus_categories_and_store():
    bus = ecosystem.engine.communication.bus
    domain = await bus.publish_domain("LeadCreated", {"lead_id": "l1"}, source="auto_marketplace")
    await bus.publish_ai("AgentInvoked", {"agent": "sales"}, source="auto_marketplace")
    await bus.publish_workflow("DealAdvanced", {"deal_id": "d1"}, source="auto_marketplace")
    await bus.publish_system("Heartbeat", {}, source="ecosystem")

    events = bus.list_events(category=EventCategory.DOMAIN)
    assert any(e.event_id == domain.event_id for e in events)

    stored = ecosystem.engine.communication.store.get(domain.event_id)
    assert stored.event_name == "LeadCreated"
    replay = ecosystem.engine.communication.store.replay()
    assert len(replay) >= 4


@pytest.mark.asyncio
async def test_messaging_patterns():
    await ecosystem.engine.communication.bridge.connect_application("auto_marketplace", capabilities=["crm"])
    await ecosystem.engine.communication.bridge.connect_application("crm_hub", capabilities=["crm"])
    ecosystem.engine.communication.subscriptions.subscribe("crm_hub", "LeadCreated")

    router = ecosystem.engine.communication.router
    direct = await router.direct("auto_marketplace", "crm_hub", {"ping": True})
    assert direct.status == DeliveryStatus.DELIVERED

    req = await router.request("auto_marketplace", "crm_hub", {"q": "status"})
    assert req.message_type == MessageType.REQUEST

    broadcast = await router.broadcast("auto_marketplace", {"alert": True})
    assert broadcast.message_type == MessageType.BROADCAST

    cmd = await router.command("auto_marketplace", "crm_hub", "qualify_lead", {"lead_id": "l1"})
    assert cmd.payload["command"] == "qualify_lead"

    query = await router.query("auto_marketplace", "crm_hub", "pipeline", {})
    assert query.payload["query"] == "pipeline"

    confirmation = router.acknowledge(direct.message_id, "crm_hub")
    assert confirmation.status == DeliveryStatus.ACKNOWLEDGED


@pytest.mark.asyncio
async def test_pubsub_and_subscriptions():
    await ecosystem.engine.communication.bridge.connect_application("auto_marketplace")
    await ecosystem.engine.communication.bridge.connect_application("crm_hub")
    sub = ecosystem.engine.communication.subscriptions.subscribe("crm_hub", "LeadCreated")
    assert sub.is_active

    event = await ecosystem.engine.communication.bus.publish(
        "LeadCreated",
        {"lead_id": "l2"},
        source_application="auto_marketplace",
    )
    assert event.event_id

    pub = await ecosystem.engine.communication.router.publish_subscribe(
        "auto_marketplace",
        "LeadCreated",
        {"lead_id": "l3"},
    )
    assert pub.status == DeliveryStatus.DELIVERED


@pytest.mark.asyncio
async def test_synchronization():
    await ecosystem.engine.communication.bridge.connect_application("auto_marketplace")
    await ecosystem.engine.communication.bridge.connect_application("crm_hub")

    sync = ecosystem.engine.communication.sync
    user = await sync.sync_user("auto_marketplace", {"user_id": "u1"})
    assert user.scope == SyncScope.USER
    assert user.status == "completed"

    org = await sync.sync_organization("auto_marketplace", {"organization_id": "o1"})
    assert org.target_applications

    history = sync.history(source_application="auto_marketplace")
    assert len(history) >= 2


@pytest.mark.asyncio
async def test_ai_bridge_context_and_delegation():
    await ecosystem.engine.communication.bridge.connect_application("auto_marketplace")
    await ecosystem.engine.communication.bridge.connect_application("crm_hub")

    context = await ecosystem.engine.communication.bridge.share_context(
        "user-1",
        "auto_marketplace",
        {"prefs": {"ev": True}},
        shared_with=["crm_hub"],
    )
    assert context.context_id
    assert "crm_hub" in context.shared_with

    delegated = await ecosystem.engine.communication.bridge.delegate_task(
        "auto_marketplace",
        "qualify_lead",
        {"lead_id": "l1"},
        target_agent="sales-agent",
    )
    assert delegated["delegated"] is True

    knowledge = await ecosystem.engine.communication.bridge.exchange_knowledge(
        "auto_marketplace",
        "crm_hub",
        {"topic": "EV incentives"},
    )
    assert knowledge["exchanged"] is True


@pytest.mark.asyncio
async def test_dead_letter_on_unroutable():
    envelope = await ecosystem.engine.communication.router.send(
        message_type=MessageType.DIRECT,
        source_application="lonely_app",
        target_application="",
        payload={"x": 1},
    )
    for _ in range(4):
        envelope = await ecosystem.engine.communication.router._fail_or_retry(envelope, "No route")
    assert envelope.status == DeliveryStatus.DEAD_LETTER
    assert any(d.message_id == envelope.message_id for d in ecosystem.engine.communication.router.dead_letters())


@pytest.mark.asyncio
async def test_communication_api(client: TestClient):
    resp = await client.get("/api/ecosystem/v1/health")
    assert resp.status == 200
    health = await resp.json()
    assert health["ecosystem_version"] == "1.5.0-alpha"
    assert health["communication_layer"] == "1.0"

    resp = await client.post(
        "/api/ecosystem/v1/registry",
        json={"application_id": "auto_marketplace", "capabilities": ["crm"], "version": "2.0.0"},
    )
    assert resp.status == 201

    resp = await client.post(
        "/api/ecosystem/v1/events",
        json={
            "event_name": "LeadCreated",
            "payload": {"lead_id": "api-1"},
            "source_application": "auto_marketplace",
            "category": "domain",
        },
    )
    assert resp.status == 201

    resp = await client.post(
        "/api/ecosystem/v1/communication/messages",
        json={
            "message_type": "direct",
            "source_application": "auto_marketplace",
            "target_application": "auto_marketplace",
            "payload": {"ok": True},
        },
    )
    assert resp.status == 201
    msg = await resp.json()
    assert msg["status"] == "delivered"

    resp = await client.post(
        "/api/ecosystem/v1/sync",
        json={"scope": "user", "source_application": "auto_marketplace", "data": {"user_id": "u1"}},
    )
    assert resp.status == 201

    resp = await client.get("/api/ecosystem/v1/registry/health")
    assert resp.status == 200

    resp = await client.get("/api/ecosystem/v1/manifest")
    assert resp.status == 200
    manifest = await resp.json()
    assert manifest["ecosystem_version"] == "1.5.0-alpha"
    assert manifest["communication_layer"] == "1.0"
    assert manifest["event_bus"] == "1.0"
