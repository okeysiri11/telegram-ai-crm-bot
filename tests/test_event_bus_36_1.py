"""Tests — Enterprise Event Bus (Sprint 36.1)."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from events.event_bus import PlatformEventBus
from platform_enterprise_event_bus.bus import EnterpriseEventBus, enterprise_event_bus
from platform_enterprise_event_bus.models import EnterpriseEvent, EventPriority
from platform_enterprise_event_bus.router import register_enterprise_event_bus_routes
from platform_enterprise_event_bus.service import enterprise_event_bus_service
from platform_management.permissions import ManagementRole


@pytest.fixture
def bus() -> EnterpriseEventBus:
    enterprise_event_bus.reset()
    PlatformEventBus.reset_subscribers()
    yield enterprise_event_bus
    enterprise_event_bus.reset()
    PlatformEventBus.reset_subscribers()


@pytest.mark.asyncio
async def test_publish_subscribe(bus: EnterpriseEventBus):
    received: list[EnterpriseEvent] = []

    async def handler(event: EnterpriseEvent) -> None:
        received.append(event)

    bus.subscribe(
        subscriber_id="crm-worker",
        topic="crm",
        event_type="crm.lead.created",
        handler=handler,
    )
    result = await bus.publish(
        {
            "event_type": "crm.lead.created",
            "category": "crm",
            "topic": "crm",
            "source_service": "enterprise_crm",
            "priority": "high",
            "payload": {"lead_id": "L1"},
        },
        wait=True,
    )
    assert result["delivered"] >= 1
    assert len(received) == 1
    assert received[0].payload["lead_id"] == "L1"
    assert received[0].signature


@pytest.mark.asyncio
async def test_routing_wildcards_filters(bus: EnterpriseEventBus):
    hits: list[str] = []

    async def h(event: EnterpriseEvent) -> None:
        hits.append(event.event_type)

    bus.subscribe(subscriber_id="ai", topic="ai", wildcard="ai.*", handler=h)
    bus.subscribe(subscriber_id="all", regex=r"^workflow\.", handler=h)
    bus.subscribe(
        subscriber_id="critical-only",
        topic="security",
        priority_min=EventPriority.CRITICAL,
        handler=h,
    )

    await bus.publish(
        {
            "event_type": "ai.infer",
            "category": "ai",
            "topic": "ai",
            "source_service": "ai_runtime",
            "payload": {},
        },
        wait=True,
    )
    await bus.publish(
        {
            "event_type": "workflow.started",
            "category": "workflow",
            "topic": "workflow",
            "source_service": "workflow_runtime",
            "payload": {},
        },
        wait=True,
    )
    await bus.publish(
        {
            "event_type": "security.alert",
            "category": "security",
            "topic": "security",
            "source_service": "security",
            "priority": "low",
            "payload": {},
        },
        wait=True,
    )
    assert "ai.infer" in hits
    assert "workflow.started" in hits
    assert hits.count("security.alert") == 0  # filtered by priority


@pytest.mark.asyncio
async def test_dead_letter_and_retry(bus: EnterpriseEventBus):
    async def boom(_event: EnterpriseEvent) -> None:
        raise RuntimeError("handler exploded")

    bus.retry.max_attempts = 2
    bus.retry.base_delay_sec = 0.001
    bus.subscribe(subscriber_id="fragile", topic="platform", wildcard="*", handler=boom)
    await bus.publish(
        {
            "event_type": "platform.ping",
            "category": "platform",
            "topic": "platform",
            "source_service": "test",
            "payload": {"n": 1},
        },
        wait=True,
    )
    items = bus.dlq.list_items()
    assert len(items) >= 1
    dlq_id = items[-1].dlq_id

    # replace handler with healthy one for retry
    bus._handlers.clear()
    ok: list[str] = []

    async def healthy(event: EnterpriseEvent) -> None:
        ok.append(event.event_id)

    bus.subscribe(subscriber_id="fragile", topic="platform", wildcard="*", handler=healthy)
    result = await bus.retry_dead_letter(dlq_id)
    assert result["new_event_id"]
    assert ok


@pytest.mark.asyncio
async def test_replay(bus: EnterpriseEventBus):
    seen: list[str] = []

    async def h(event: EnterpriseEvent) -> None:
        seen.append(event.event_id)

    bus.subscribe(subscriber_id="replayer", topic="analytics", wildcard="*", handler=h)
    first = await bus.publish(
        {
            "event_type": "analytics.metric",
            "category": "analytics",
            "topic": "analytics",
            "source_service": "analytics",
            "payload": {"v": 1},
        },
        wait=True,
    )
    event_id = first["event_id"]
    replayed = await bus.replay_engine.replay(event_id=event_id)
    assert replayed["replayed"] == 1
    assert len(seen) >= 2


@pytest.mark.asyncio
async def test_delayed_delivery(bus: EnterpriseEventBus):
    received: list[str] = []

    async def h(event: EnterpriseEvent) -> None:
        received.append(event.event_id)

    bus.subscribe(subscriber_id="delayed", topic="platform", handler=h)
    import time

    future = time.time() + 3600
    result = await bus.publish(
        {
            "event_type": "platform.later",
            "category": "platform",
            "topic": "platform",
            "source_service": "scheduler",
            "payload": {},
            "deliver_at": future,
        }
    )
    assert result["status"] == "scheduled"
    assert received == []
    # force due
    bus._scheduled[0].deliver_at = time.time() - 1
    n = await bus.process_scheduled()
    assert n == 1
    assert len(received) == 1


@pytest.mark.asyncio
async def test_security_signing_and_tenant_filter(bus: EnterpriseEventBus):
    got: list[EnterpriseEvent] = []

    async def h(event: EnterpriseEvent) -> None:
        got.append(event)

    bus.subscribe(subscriber_id="tenant-a", topic="crm", tenant_id="t1", handler=h)
    await bus.publish(
        {
            "event_type": "crm.deal.updated",
            "category": "crm",
            "topic": "crm",
            "source_service": "crm",
            "tenant_id": "t2",
            "payload": {"deal": 1},
        },
        wait=True,
    )
    assert got == []
    await bus.publish(
        {
            "event_type": "crm.deal.updated",
            "category": "crm",
            "topic": "crm",
            "source_service": "crm",
            "tenant_id": "t1",
            "payload": {"deal": 2},
        },
        wait=True,
    )
    assert len(got) == 1
    assert got[0].signature
    assert bus.validator.verify_signature(got[0])


@pytest.mark.asyncio
async def test_bridges_platform_event_bus(bus: EnterpriseEventBus):
    bridged: list[str] = []

    async def platform_handler(event) -> None:
        bridged.append(event.event_type)

    PlatformEventBus.subscribe("EnterpriseBusEvent", platform_handler, handler_id="bridge_test")
    await bus.publish(
        {
            "event_type": "agents.spawned",
            "category": "agents",
            "topic": "agents",
            "source_service": "multi_agent",
            "payload": {},
        },
        wait=True,
    )
    await asyncio.sleep(0.05)
    assert "EnterpriseBusEvent" in bridged


@pytest.mark.asyncio
async def test_performance_batch(bus: EnterpriseEventBus):
    count = 0

    async def h(_e: EnterpriseEvent) -> None:
        nonlocal count
        count += 1

    bus.subscribe(subscriber_id="perf", topic="platform", wildcard="*", handler=h)
    for i in range(50):
        await bus.publish(
            {
                "event_type": "platform.perf",
                "category": "platform",
                "topic": "platform",
                "source_service": "bench",
                "payload": {"i": i},
            },
            wait=True,
            bridge=False,
        )
    assert count == 50
    snap = bus.metrics.snapshot(subscribers=1)
    assert snap["published"] >= 50
    assert snap["delivered"] >= 50


@pytest.mark.asyncio
async def test_api_routes(auth_headers, monkeypatch):
    enterprise_event_bus.reset()

    async def _admin(_tid):
        return ManagementRole.ADMINISTRATOR

    monkeypatch.setattr("platform_management.permissions.resolve_role", _admin)
    app = web.Application()
    register_enterprise_event_bus_routes(app)

    with patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(app)) as client:
            res = await client.get("/api/event-bus/topics", headers=auth_headers)
            assert res.status == 200
            topics = (await res.json())["data"]["topics"]
            assert any(t["name"] == "workflow" for t in topics)

            res = await client.post(
                "/api/event-bus/publish",
                headers=auth_headers,
                json={
                    "event_type": "platform.api",
                    "category": "platform",
                    "topic": "platform",
                    "source_service": "api_test",
                    "payload": {"ok": True},
                },
            )
            assert res.status == 201
            event_id = (await res.json())["data"]["event_id"]

            res = await client.get("/api/event-bus/events", headers=auth_headers)
            assert res.status == 200
            assert (await res.json())["data"]["count"] >= 1

            res = await client.get(f"/api/event-bus/events/{event_id}", headers=auth_headers)
            assert res.status == 200
            body = await res.json()
            assert body["data"]["event"]["event_id"] == event_id

            res = await client.post(
                "/api/event-bus/subscribe",
                headers=auth_headers,
                json={"subscriber_id": "api-sub", "topic": "platform"},
            )
            assert res.status == 201
            sub_id = (await res.json())["data"]["subscription_id"]

            res = await client.post(
                "/api/event-bus/unsubscribe",
                headers=auth_headers,
                json={"subscription_id": sub_id},
            )
            assert res.status == 200

            res = await client.post(
                "/api/event-bus/replay",
                headers=auth_headers,
                json={"event_id": event_id},
            )
            assert res.status == 200

            res = await client.get("/api/event-bus/statistics", headers=auth_headers)
            assert res.status == 200

            res = await client.get("/api/event-bus/dead-letter", headers=auth_headers)
            assert res.status == 200

            res = await client.get("/management/v1/event-bus/topics", headers=auth_headers)
            assert res.status == 200

    enterprise_event_bus.reset()


@pytest.mark.asyncio
async def test_websocket_live_stream():
    enterprise_event_bus.reset()
    app = web.Application()
    register_enterprise_event_bus_routes(app)

    async with TestClient(TestServer(app)) as client:
        async with client.ws_connect("/api/event-bus/ws") as ws:
            welcome = await ws.receive_json()
            assert welcome["type"] == "welcome"
            await enterprise_event_bus_service.publish(
                {
                    "event_type": "platform.ws",
                    "category": "platform",
                    "topic": "platform",
                    "source_service": "ws_test",
                    "payload": {"live": True},
                }
            )
            msg = await asyncio.wait_for(ws.receive_json(), timeout=2.0)
            assert msg["type"] == "event"
            assert msg["data"]["event_type"] == "platform.ws"

    enterprise_event_bus.reset()


def test_ui_module_present():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    page = root / "src/web/src/event-bus/EventBusPage.tsx"
    assert page.exists()
    text = page.read_text(encoding="utf-8")
    for label in (
        "Live Events",
        "Topics",
        "Subscribers",
        "Dead Letter Queue",
        "Replay",
        "Statistics",
        "Traffic Monitor",
        "Event Inspector",
    ):
        assert label in text


def test_package_exports_and_canonical():
    from platform_architecture.canonical_services import CANONICAL_SERVICES
    from platform_enterprise_event_bus import (
        DeadLetterQueue,
        EnterpriseEvent,
        EnterpriseEventBus,
        EventBroker,
        EventDispatcher,
        EventFilter,
        EventPriority,
        EventPublisher,
        EventReplayEngine,
        EventRouter,
        EventSerializer,
        EventStore,
        EventSubscriber,
        EventValidator,
        RetryManager,
        TopicManager,
    )

    assert EnterpriseEventBus is not None
    assert EnterpriseEvent is not None
    assert EventPriority.CRITICAL.value == "critical"
    assert EventPublisher and EventSubscriber and EventDispatcher
    assert EventRouter and EventBroker and EventStore and EventReplayEngine
    assert EventFilter and EventValidator and EventSerializer
    assert DeadLetterQueue and RetryManager and TopicManager
    assert CANONICAL_SERVICES["event_bus"]["canonical"].endswith("PlatformEventBus")
    assert "enterprise_event_bus" in CANONICAL_SERVICES


def test_orm_tables():
    from database.models.enterprise_event_bus import (
        DeadLetterQueueRow,
        EnterpriseEventStoreRow,
        EventDeliveryRow,
        EventReplayRow,
        EventStatisticsRow,
        EventSubscriberRow,
        EventTopicRow,
    )

    assert EnterpriseEventStoreRow.__tablename__ == "event_store"
    assert EventTopicRow.__tablename__ == "event_topics"
    assert EventSubscriberRow.__tablename__ == "event_subscribers"
    assert EventDeliveryRow.__tablename__ == "event_delivery"
    assert DeadLetterQueueRow.__tablename__ == "dead_letter_queue"
    assert EventStatisticsRow.__tablename__ == "event_statistics"
    assert EventReplayRow.__tablename__ == "event_replay"


def test_default_topics(bus: EnterpriseEventBus):
    names = {t.name for t in bus.topics.list_topics()}
    for required in ("system", "security", "workflow", "crm", "ai", "agents", "creative", "platform"):
        assert required in names
