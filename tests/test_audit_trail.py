"""Tests — platform audit trail."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from audit.audit_event import AuditEventType, audit_record_from_event
from audit.audit_service import AuditService, audit_service
from events.event_bus import publish, reset_subscribers
from events.handlers import register_platform_event_handlers, reset_handler_registration
from events.request_events import (
    ManagerReassignedEvent,
    RequestAssignedEvent,
    RequestCompletedEvent,
    RequestCreatedEvent,
    RequestOverdueEvent,
)


@pytest.fixture(autouse=True)
def _clean():
    reset_subscribers()
    reset_handler_registration()
    yield
    reset_subscribers()
    reset_handler_registration()


def test_audit_record_from_request_created():
    event = RequestCreatedEvent(
        request_id="00000000-0000-0000-0000-000000000001",
        request_number="REALTY-00001",
        vertical="realty",
        request_type="REALTY_RENT",
        client_telegram_id=12345,
        client_name="Alice",
        description="Kyiv",
    )
    record = audit_record_from_event(event)
    assert record is not None
    assert record.event_type == AuditEventType.REQUEST_CREATED.value
    assert record.entity_id == event.request_id
    assert record.new_value["status"] == "NEW"
    assert record.metadata_json["request_id"] == event.request_id
    assert record.metadata_json["request_number"] == "REALTY-00001"


def test_audit_record_manager_reassigned():
    event = ManagerReassignedEvent(
        request_id="00000000-0000-0000-0000-000000000002",
        request_number="AUTO-00010",
        vertical="auto",
        request_type="AUTO_PARTS",
        previous_manager_id="mgr-old",
        manager_id="mgr-new",
        manager_telegram_id=999,
    )
    record = audit_record_from_event(event)
    assert record is not None
    assert record.event_type == AuditEventType.MANAGER_REASSIGNED.value
    assert record.old_value["manager_id"] == "mgr-old"
    assert record.new_value["manager_id"] == "mgr-new"
    assert record.metadata_json["manager_id"] == "mgr-new"


@pytest.mark.asyncio
async def test_handle_event_is_non_blocking():
    record_mock = AsyncMock(return_value={"id": "1"})
    with patch.object(AuditService, "record", record_mock):
        await AuditService.handle_event(
            RequestCreatedEvent(
                request_id="id-1",
                request_number="AGRO-00001",
                vertical="agro",
                request_type="AGRO_REQUEST",
            )
        )
        await asyncio.sleep(0.05)
    record_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_record_failure_does_not_raise():
    with patch(
        "audit.audit_service.get_session",
        side_effect=RuntimeError("db down"),
    ):
        result = await AuditService.record(
            audit_record_from_event(
                RequestCreatedEvent(
                    request_id="id-1",
                    request_number="AGRO-00001",
                    vertical="agro",
                    request_type="AGRO_REQUEST",
                )
            )
        )
    assert result is None


@pytest.mark.asyncio
async def test_event_bus_audit_does_not_break_publish():
    register_platform_event_handlers()

    with patch(
        "audit.audit_service.AuditService._record_from_event",
        new=AsyncMock(side_effect=RuntimeError("audit boom")),
    ), patch(
        "services.notification_service.notification_service.notify_managers_new_request",
        new=AsyncMock(),
    ) as notify:
        result = await publish(
            RequestCreatedEvent(
                request_id="00000000-0000-0000-0000-000000000001",
                request_number="REALTY-00010",
                vertical="realty",
                request_type="REALTY_RENT",
            ),
            wait=True,
        )
        await asyncio.sleep(0.05)

    notify.assert_awaited_once()
    assert result["handlers"] >= 3


@pytest.mark.asyncio
async def test_full_request_history_reconstruction():
    request_id = "00000000-0000-0000-0000-000000000099"
    manager_id = "00000000-0000-0000-0000-000000000001"
    stored_rows: list[MagicMock] = []

    async def fake_insert(record):
        row = MagicMock()
        row.id = f"evt-{len(stored_rows) + 1}"
        row.event_type = record.event_type
        row.entity_type = record.entity_type
        row.entity_id = record.entity_id
        row.actor_id = record.actor_id
        row.old_value = record.old_value
        row.new_value = record.new_value
        row.metadata_json = record.metadata_json
        row.created_at = datetime.now(timezone.utc)
        stored_rows.append(row)
        return row

    mock_session = AsyncMock()
    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_session
    mock_cm.__aexit__.return_value = None

    with patch("audit.audit_service.get_session", return_value=mock_cm), patch(
        "audit.audit_repository.AuditRepository.insert",
        side_effect=fake_insert,
    ), patch(
        "audit.audit_repository.AuditRepository.list_by_request_id",
        new=AsyncMock(side_effect=lambda _rid, limit=200: list(stored_rows)),
    ):
        for event in (
            RequestCreatedEvent(
                request_id=request_id,
                request_number="REALTY-00099",
                vertical="realty",
                request_type="REALTY_RENT",
                client_telegram_id=111,
            ),
            RequestAssignedEvent(
                request_id=request_id,
                request_number="REALTY-00099",
                vertical="realty",
                request_type="REALTY_RENT",
                manager_id=manager_id,
                manager_telegram_id=222,
            ),
            RequestOverdueEvent(
                request_id=request_id,
                request_number="REALTY-00099",
                vertical="realty",
                request_type="REALTY_RENT",
                manager_id=manager_id,
                overdue_seconds=3600,
            ),
            RequestCompletedEvent(
                request_id=request_id,
                request_number="REALTY-00099",
                vertical="realty",
                request_type="REALTY_RENT",
                manager_id=manager_id,
            ),
        ):
            await AuditService.record(audit_record_from_event(event))

        history = await AuditService.get_request_history(request_id=request_id)

    assert len(history) == 4
    assert [h["event_type"] for h in history] == [
        AuditEventType.REQUEST_CREATED.value,
        AuditEventType.REQUEST_ASSIGNED.value,
        AuditEventType.REQUEST_OVERDUE.value,
        AuditEventType.REQUEST_COMPLETED.value,
    ]
    assert all(h["metadata_json"]["request_id"] == request_id for h in history)


@pytest.mark.asyncio
async def test_filter_by_manager_id():
    manager_id = "00000000-0000-0000-0000-000000000010"
    rows = []

    for idx in range(2):
        row = MagicMock()
        row.id = f"evt-{idx}"
        row.event_type = AuditEventType.REQUEST_ASSIGNED.value
        row.entity_type = "client_request"
        row.entity_id = f"req-{idx}"
        row.actor_id = "222"
        row.old_value = None
        row.new_value = {"manager_id": manager_id}
        row.metadata_json = {"request_id": f"req-{idx}", "manager_id": manager_id}
        row.created_at = datetime.now(timezone.utc)
        rows.append(row)

    mock_session = AsyncMock()
    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_session
    mock_cm.__aexit__.return_value = None

    with patch("audit.audit_service.get_session", return_value=mock_cm), patch(
        "audit.audit_repository.AuditRepository.list_by_manager_id",
        new=AsyncMock(return_value=rows),
    ):
        history = await AuditService.get_manager_history(manager_id)

    assert len(history) == 2
    assert all(h["metadata_json"]["manager_id"] == manager_id for h in history)


def test_audit_service_subscribed_on_register():
    register_platform_event_handlers()
    from events.event_bus import PlatformEventBus

    subs = PlatformEventBus.list_subscribers("RequestOverdueEvent")["RequestOverdueEvent"]
    assert "audit_trail_RequestOverdueEvent" in subs
