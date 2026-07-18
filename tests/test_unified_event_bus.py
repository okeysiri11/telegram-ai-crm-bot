"""Tests — unified PlatformEventBus (all events pass through)."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from events.event_bus import PlatformEventBus, publish, reset_subscribers
from events.generic_events import GenericPlatformEvent
from events.handlers import register_platform_event_handlers, reset_handler_registration
from events.request_events import RequestCreatedEvent
from platform_events_legacy import EventBus, PlatformEvent, reset_event_bus_for_tests


@pytest.fixture(autouse=True)
def _clean():
    reset_subscribers()
    reset_handler_registration()
    reset_event_bus_for_tests()
    from events.adapters.legacy_adapter import reset_legacy_bridge_registration

    reset_legacy_bridge_registration()
    yield
    reset_subscribers()
    reset_handler_registration()
    reset_event_bus_for_tests()
    reset_legacy_bridge_registration()


@pytest.mark.asyncio
async def test_typed_event_passes_platform_bus():
    seen: list[str] = []

    async def handler(event: RequestCreatedEvent) -> None:
        seen.append(event.request_number)

    PlatformEventBus.subscribe(RequestCreatedEvent, handler, handler_id="test")
    await publish(
        RequestCreatedEvent(
            request_id="id-1",
            request_number="AUTO-001",
            vertical="auto",
            request_type="AUTO_SEARCH",
        ),
        wait=True,
    )
    assert seen == ["AUTO-001"]


@pytest.mark.asyncio
async def test_legacy_event_passes_platform_bus():
    seen: list[str] = []

    async def handler(event: GenericPlatformEvent) -> None:
        seen.append(event.name)

    PlatformEventBus.subscribe("DEAL_CREATED", handler, handler_id="test")

    from events.adapters.legacy_adapter import publish_legacy_to_platform_bus
    from platform_events_legacy import PlatformEvent

    await publish_legacy_to_platform_bus(
        PlatformEvent(
            event_type="DEAL_CREATED",
            module="deals",
            entity_type="deal",
            entity_id=100,
            user_id=42,
            payload={"title": "Test deal"},
            event_id=1,
        ),
        wait=True,
    )

    assert seen == ["DEAL_CREATED"]


def test_legacy_event_bus_routes_through_platform_adapter(monkeypatch):
    routed: list[PlatformEvent] = []

    def _capture(event: PlatformEvent, *, wait: bool = False) -> dict:
        routed.append(event)
        return {"event_type": event.event_type, "handlers": 1, "errors": []}

    monkeypatch.setattr(
        "events.adapters.legacy_adapter.publish_legacy_to_platform_bus_sync",
        _capture,
    )
    monkeypatch.setattr("database.insert_platform_event", lambda event, replay_of=None: 99, raising=False)
    monkeypatch.setattr("database.update_platform_event_status", lambda *args, **kwargs: None, raising=False)
    monkeypatch.setattr("database.log_audit", lambda *args, **kwargs: None, raising=False)

    EventBus.publish(
        "DEAL_CREATED",
        user_id=42,
        entity_id=100,
        payload={"title": "Test deal"},
    )

    assert len(routed) == 1
    assert routed[0].event_type == "DEAL_CREATED"


@pytest.mark.asyncio
async def test_crm_event_passes_platform_bus():
    seen: list[GenericPlatformEvent] = []

    async def handler(event: GenericPlatformEvent) -> None:
        seen.append(event)

    PlatformEventBus.subscribe("client_request.created", handler, handler_id="test")

    from events.adapters.crm_adapter import publish_crm_to_platform_bus

    agg_id = uuid.uuid4()
    await publish_crm_to_platform_bus(
        "client_request.created",
        "client_request",
        agg_id,
        {"request_number": "CRM-001"},
        crm_event_id=uuid.uuid4(),
        wait=True,
    )

    assert len(seen) == 1
    assert seen[0].source == "crm"
    assert seen[0].aggregate_id == str(agg_id)


@pytest.mark.asyncio
async def test_ai_event_uses_publisher():
    from platform_ai.ai_events import AIRequestCompletedEvent, publish_ai_event

    seen: list[str] = []

    async def handler(event: AIRequestCompletedEvent) -> None:
        seen.append(event.request_id)

    PlatformEventBus.subscribe(AIRequestCompletedEvent, handler, handler_id="test")
    await publish_ai_event(
        AIRequestCompletedEvent(request_id="req-1", provider_id="openai", model_id="gpt-4")
    )
    assert seen == ["req-1"]


@pytest.mark.asyncio
async def test_plugin_event_uses_publisher():
    from platform_plugins.plugin_events import PluginInstalledEvent, publish_plugin_event

    seen: list[str] = []

    async def handler(event: PluginInstalledEvent) -> None:
        seen.append(event.plugin_id)

    PlatformEventBus.subscribe(PluginInstalledEvent, handler, handler_id="test")
    await publish_plugin_event(PluginInstalledEvent(plugin_id="auto", version="1.0.0"))
    assert seen == ["auto"]


@pytest.mark.asyncio
async def test_legacy_handlers_registered_on_platform_bus():
    register_platform_event_handlers()
    subs = PlatformEventBus.list_subscribers("AGRO_REQUEST_CREATED").get("AGRO_REQUEST_CREATED", [])
    assert any(s.startswith("legacy_") for s in subs)


def test_generic_event_from_legacy():
    pe = PlatformEvent(
        event_type="DEAL_CREATED",
        module="deals",
        entity_type="deal",
        entity_id=1,
        user_id=42,
        payload={"x": 1},
        created_at="2026-01-01 00:00:00",
        status="PUBLISHED",
        event_id=99,
    )
    generic = GenericPlatformEvent.from_legacy(
        event_type=pe.event_type,
        user_id=pe.user_id,
        module=pe.module,
        entity_type=pe.entity_type,
        entity_id=pe.entity_id,
        payload=pe.payload,
        legacy_event_id=pe.event_id,
    )
    assert generic.event_type == "DEAL_CREATED"
    assert generic.source == "legacy"
