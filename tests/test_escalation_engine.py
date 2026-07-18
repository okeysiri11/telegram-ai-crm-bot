"""Tests — platform Escalation Engine."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from events.event_bus import publish, reset_subscribers
from events.handlers import register_platform_event_handlers, reset_handler_registration
from events.request_events import ManagerEscalationEvent, RequestAssignedEvent, RequestOverdueEvent
from models.request_sla import RequestEscalationContext
from repositories.escalation_repository import EscalationRepository
from services.escalation_service import EscalationService
from services.sla_timer_service import SlaTimerService
from workers.escalation_worker import EscalationWorker


@pytest.fixture(autouse=True)
def _clean():
    reset_subscribers()
    reset_handler_registration()
    yield
    reset_subscribers()
    reset_handler_registration()


def _sla_row(
    *,
    request_id: str | None = None,
    escalation_level: int = 0,
    overdue_minutes: int = 5,
) -> MagicMock:
    now = datetime.now(timezone.utc)
    row = MagicMock()
    row.request_id = uuid.UUID(request_id or str(uuid.uuid4()))
    row.manager_id = 12345
    row.first_response_deadline = now - timedelta(minutes=overdue_minutes)
    row.completion_deadline = now + timedelta(hours=48)
    row.escalation_level = escalation_level
    row.first_response_at = None
    row.completed_at = None
    row.created_at = now - timedelta(hours=1)
    return row


def _context(**kwargs) -> RequestEscalationContext:
    return RequestEscalationContext(
        request_id=kwargs.get("request_id", str(uuid.uuid4())),
        request_number=kwargs.get("request_number", "AUTO-00001"),
        vertical=kwargs.get("vertical", "auto"),
        request_type=kwargs.get("request_type", "AUTO_PARTS"),
        manager_uuid=kwargs.get("manager_uuid", str(uuid.uuid4())),
        manager_telegram_id=kwargs.get("manager_telegram_id", 111),
        client_telegram_id=kwargs.get("client_telegram_id", 999),
    )


@pytest.mark.asyncio
async def test_sla_timer_creates_record_on_assigned():
    mock_repo = AsyncMock()
    mock_repo.create_sla.return_value = MagicMock()

    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = AsyncMock()
    mock_cm.__aexit__.return_value = None

    with patch("services.sla_timer_service.get_session", return_value=mock_cm), patch(
        "services.sla_timer_service.EscalationRepository",
        return_value=mock_repo,
    ):
        await SlaTimerService._on_assigned(
            RequestAssignedEvent(
                request_id=str(uuid.uuid4()),
                request_number="REALTY-00001",
                vertical="realty",
                request_type="REALTY_RENT",
                manager_id=str(uuid.uuid4()),
                manager_telegram_id=555,
            )
        )

    mock_repo.create_sla.assert_awaited_once()


@pytest.mark.asyncio
async def test_sla_timer_idempotent_create():
    mock_repo = AsyncMock()
    mock_repo.create_sla.return_value = MagicMock()

    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = AsyncMock()
    mock_cm.__aexit__.return_value = None

    event = RequestAssignedEvent(
        request_id=str(uuid.uuid4()),
        request_number="AUTO-00002",
        vertical="auto",
        request_type="AUTO_PARTS",
        manager_id=str(uuid.uuid4()),
        manager_telegram_id=555,
    )

    with patch("services.sla_timer_service.get_session", return_value=mock_cm), patch(
        "services.sla_timer_service.EscalationRepository",
        return_value=mock_repo,
    ):
        await SlaTimerService._on_assigned(event)
        await SlaTimerService._on_assigned(event)

    assert mock_repo.create_sla.await_count == 2


@pytest.mark.asyncio
async def test_level1_publishes_request_overdue_event():
    row = _sla_row(escalation_level=0, overdue_minutes=10)
    context = _context(request_id=str(row.request_id))

    mock_repo = AsyncMock()
    mock_repo.lock_due_for_escalation.return_value = [row]
    mock_repo.load_request_context.return_value = context
    mock_repo.advance_escalation_level.return_value = True
    mock_repo.overdue_seconds.return_value = 600

    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = AsyncMock()
    mock_cm.__aexit__.return_value = None

    with patch("services.escalation_service.get_session", return_value=mock_cm), patch(
        "services.escalation_service.EscalationRepository",
        return_value=mock_repo,
    ), patch("services.escalation_service.publish", new=AsyncMock()) as publish_mock:
        result = await EscalationService.process_due_escalations()

    assert result["acted"] == 1
    publish_mock.assert_awaited_once()
    event = publish_mock.await_args.args[0]
    assert isinstance(event, RequestOverdueEvent)
    assert event.escalation_level == 1


@pytest.mark.asyncio
async def test_repeated_escalation_does_not_republish_level1():
    row = _sla_row(escalation_level=1, overdue_minutes=20)
    context = _context(request_id=str(row.request_id))

    mock_repo = AsyncMock()
    mock_repo.lock_due_for_escalation.return_value = [row]
    mock_repo.load_request_context.return_value = context
    mock_repo.advance_escalation_level.return_value = False

    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = AsyncMock()
    mock_cm.__aexit__.return_value = None

    with patch("services.escalation_service.get_session", return_value=mock_cm), patch(
        "services.escalation_service.EscalationRepository",
        return_value=mock_repo,
    ), patch("services.escalation_service.publish", new=AsyncMock()) as publish_mock:
        result = await EscalationService.process_due_escalations()

    assert result["acted"] == 0
    publish_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_level2_publishes_manager_escalation_event():
    row = _sla_row(escalation_level=1, overdue_minutes=60)
    context = _context(request_id=str(row.request_id))

    mock_repo = AsyncMock()
    mock_repo.lock_due_for_escalation.return_value = [row]
    mock_repo.load_request_context.return_value = context
    mock_repo.advance_escalation_level.return_value = True
    mock_repo.overdue_seconds.return_value = 3600

    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = AsyncMock()
    mock_cm.__aexit__.return_value = None

    with patch("services.escalation_service.get_session", return_value=mock_cm), patch(
        "services.escalation_service.EscalationRepository",
        return_value=mock_repo,
    ), patch("services.escalation_service.publish", new=AsyncMock()) as publish_mock:
        result = await EscalationService.process_due_escalations()

    assert result["acted"] == 1
    event = publish_mock.await_args.args[0]
    assert isinstance(event, ManagerEscalationEvent)
    assert event.escalation_level == 2


@pytest.mark.asyncio
async def test_level3_automatic_reassignment():
    row = _sla_row(escalation_level=2, overdue_minutes=120)
    context = _context(request_id=str(row.request_id))
    new_manager = {"user_id": str(uuid.uuid4()), "telegram_id": 777}

    mock_repo = AsyncMock()
    mock_repo.lock_due_for_escalation.return_value = [row]
    mock_repo.load_request_context.return_value = context
    mock_repo.advance_escalation_level.return_value = True
    mock_repo.overdue_seconds.return_value = 7200

    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = AsyncMock()
    mock_cm.__aexit__.return_value = None

    with patch("services.escalation_service.get_session", return_value=mock_cm), patch(
        "services.escalation_service.EscalationRepository",
        return_value=mock_repo,
    ), patch(
        "services.manager_service.manager_service.resolve_alternate_manager_for_vertical",
        new=AsyncMock(return_value=new_manager),
    ), patch(
        "services.request_service.request_service.reassign_request",
        new=AsyncMock(return_value={"id": context.request_id, "request_number": context.request_number}),
    ) as reassign_mock, patch(
        "services.escalation_service.publish",
        new=AsyncMock(),
    ) as publish_mock:
        result = await EscalationService.process_due_escalations()

    assert result["acted"] == 1
    reassign_mock.assert_awaited_once()
    publish_mock.assert_not_awaited()
    mock_repo.advance_escalation_level.assert_awaited()


@pytest.mark.asyncio
async def test_worker_start_is_idempotent():
    worker = EscalationWorker(interval_sec=30)
    await worker.start()
    first_task = worker._task
    await worker.start()
    assert worker._task is first_task
    assert worker.is_running
    await worker.stop()
    assert not worker.is_running


@pytest.mark.asyncio
async def test_double_worker_tick_serializes():
    worker = EscalationWorker(interval_sec=30)
    calls = 0

    async def counting_process(**kwargs):
        nonlocal calls
        calls += 1
        await asyncio.sleep(0.02)
        return {"acted": 0}

    with patch(
        "services.escalation_service.escalation_service.process_due_escalations",
        side_effect=counting_process,
    ):
        await asyncio.gather(worker.tick(), worker.tick())

    assert calls == 2


@pytest.mark.asyncio
async def test_double_process_same_level_idempotent():
    row = _sla_row(escalation_level=0, overdue_minutes=10)
    context = _context(request_id=str(row.request_id))

    mock_repo = AsyncMock()
    mock_repo.lock_due_for_escalation.return_value = [row]
    mock_repo.load_request_context.return_value = context
    mock_repo.overdue_seconds.return_value = 600

    async def advance_side_effect(_row, *, new_level, manager_telegram_id=None):
        if _row.escalation_level >= new_level:
            return False
        _row.escalation_level = new_level
        return True

    mock_repo.advance_escalation_level.side_effect = advance_side_effect

    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = AsyncMock()
    mock_cm.__aexit__.return_value = None

    with patch("services.escalation_service.get_session", return_value=mock_cm), patch(
        "services.escalation_service.EscalationRepository",
        return_value=mock_repo,
    ), patch("services.escalation_service.publish", new=AsyncMock()) as publish_mock:
        await EscalationService.process_due_escalations()
        row.escalation_level = 1
        result = await EscalationService.process_due_escalations()

    assert publish_mock.await_count == 1
    assert result["acted"] == 0


@pytest.mark.asyncio
async def test_escalation_handlers_registered():
    register_platform_event_handlers()
    from events.event_bus import PlatformEventBus

    subs = PlatformEventBus.list_subscribers("RequestAssignedEvent")["RequestAssignedEvent"]
    assert "sla_timer_RequestAssignedEvent" in subs


@pytest.mark.asyncio
async def test_advance_escalation_level_guard():
    row = MagicMock()
    row.escalation_level = 2

    repo = EscalationRepository(AsyncMock())
    assert await repo.advance_escalation_level(row, new_level=1) is False
    row.escalation_level = 1
    assert await repo.advance_escalation_level(row, new_level=2) is True
