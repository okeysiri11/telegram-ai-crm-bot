"""Tests — internal platform event bus."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from events.base_event import BaseEvent
from events.event_bus import PlatformEventBus, publish, reset_subscribers, subscribe
from events.handlers import register_platform_event_handlers, reset_handler_registration
from events.handlers.audit_handler import AuditEventHandler
from events.handlers.metrics_handler import MetricsEventHandler
from events.handlers.notification_handler import NotificationEventHandler
from events.handlers.sla_handler import SLAEventHandler
from events.request_events import RequestCreatedEvent


@pytest.fixture(autouse=True)
def _clean_bus():
    reset_subscribers()
    reset_handler_registration()
    yield
    reset_subscribers()
    reset_handler_registration()


@pytest.mark.asyncio
async def test_publish_subscribe_async_handler():
    seen: list[BaseEvent] = []

    async def handler(event: BaseEvent) -> None:
        seen.append(event)

    subscribe(RequestCreatedEvent, handler, handler_id="test_handler")
    event = RequestCreatedEvent(
        request_id="id-1",
        request_number="REALTY-00001",
        vertical="realty",
        request_type="REALTY_RENT",
    )

    await publish(event, wait=True)
    assert len(seen) == 1
    assert seen[0].request_number == "REALTY-00001"


@pytest.mark.asyncio
async def test_handler_failure_does_not_break_others():
    calls: list[str] = []

    async def bad_handler(_event: BaseEvent) -> None:
        calls.append("bad")
        raise RuntimeError("boom")

    async def good_handler(_event: BaseEvent) -> None:
        calls.append("good")

    subscribe(RequestCreatedEvent, bad_handler, handler_id="bad")
    subscribe(RequestCreatedEvent, good_handler, handler_id="good")

    event = RequestCreatedEvent(
        request_id="id-2",
        request_number="AGRO-00001",
        vertical="agro",
        request_type="AGRO_REQUEST",
    )
    result = await publish(event, wait=True)

    assert "good" in calls
    assert len(result["errors"]) == 1


@pytest.mark.asyncio
async def test_request_created_triggers_all_handlers():
    register_platform_event_handlers()

    with patch(
        "services.notification_service.notification_service.notify_managers_new_request",
        new=AsyncMock(),
    ) as notify, patch(
        "services.pg_platform_audit_engine.PlatformAuditEngineV1.lead_created",
        new=AsyncMock(),
    ) as audit, patch(
        "services.platform_metrics_service.platform_metrics_service.track_request_created",
        new=AsyncMock(),
    ) as metrics, patch(
        "services.pg_lead_sla_engine.LeadSlaEngineV1.on_lead_created",
        new=AsyncMock(),
    ) as sla:
        await publish(
            RequestCreatedEvent(
                request_id="00000000-0000-0000-0000-000000000001",
                request_number="REALTY-00010",
                vertical="realty",
                request_type="REALTY_RENT",
                client_telegram_id=123,
                client_name="Test",
                description="Rent apt",
                manager_telegram_id=456,
            ),
            wait=True,
        )
        await asyncio.sleep(0.05)

    notify.assert_awaited_once()
    audit.assert_awaited_once()
    metrics.assert_awaited_once()
    sla.assert_awaited_once()


@pytest.mark.asyncio
async def test_request_service_create_only_publishes_event(client_user_id):
    from services.request_service import request_service

    row = AsyncMock()
    row.id = "00000000-0000-0000-0000-000000000099"
    row.request_number = "REALTY-00099"
    row.request_type = "REALTY_RENT"
    row.status = "NEW"
    row.client_telegram_id = client_user_id
    row.client_first_name = "Test"
    row.client_username = None
    row.description = "rent"
    row.manager_id = None
    row.created_at = None

    with patch(
        "services.manager_service.manager_service.resolve_manager_for_vertical",
        new=AsyncMock(return_value={"user_id": "00000000-0000-0000-0000-000000000001", "telegram_id": 1}),
    ), patch(
        "repositories.request_repository.RequestRepository.next_crm_number",
        new=AsyncMock(return_value="REALTY-00099"),
    ), patch(
        "repositories.request_repository.RequestRepository.create_crm",
        new=AsyncMock(return_value=row),
    ), patch(
        "services.request_service.RequestService._publish_request_created",
        new=AsyncMock(),
    ) as publish_mock, patch(
        "services.notification_service.notification_service.notify_managers_new_request",
        new=AsyncMock(),
    ) as notify_mock:
        await request_service.create_request(
            vertical="realty",
            client_telegram_id=client_user_id,
            product="rent",
            description="Kyiv",
        )

    publish_mock.assert_awaited_once()
    notify_mock.assert_not_called()


@pytest.mark.asyncio
async def test_handlers_registered():
    register_platform_event_handlers()
    subs = PlatformEventBus.list_subscribers("RequestCreatedEvent")["RequestCreatedEvent"]
    assert "notification" in subs
    assert "audit" in subs
    assert "metrics" in subs
    assert "sla" in subs


def test_event_types():
    assert NotificationEventHandler.__name__ == "NotificationEventHandler"
    assert AuditEventHandler.__name__ == "AuditEventHandler"
    assert MetricsEventHandler.__name__ == "MetricsEventHandler"
    assert SLAEventHandler.__name__ == "SLAEventHandler"
