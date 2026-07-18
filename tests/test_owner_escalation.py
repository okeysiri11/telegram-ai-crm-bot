"""Tests — Owner Escalation (Level 4)."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from audit.audit_event import AuditEventType, audit_record_from_event
from events.event_bus import reset_subscribers
from events.handlers import register_platform_event_handlers, reset_handler_registration
from events.owner_events import OwnerEscalationEvent
from repositories.owner_repository import OwnerRepository
from routers.admin.sla_router import register_sla_admin_routes
from services.owner_escalation_service import OwnerEscalationService, owner_escalation_service


@pytest.fixture(autouse=True)
def _clean():
    reset_subscribers()
    reset_handler_registration()
    yield
    reset_subscribers()
    reset_handler_registration()


def _sla_row(**kwargs) -> MagicMock:
    now = datetime.now(timezone.utc)
    row = MagicMock()
    row.request_id = kwargs.get("request_id", uuid.uuid4())
    row.manager_id = kwargs.get("manager_id", 111)
    row.first_response_deadline = now - timedelta(hours=2)
    row.completion_deadline = now - timedelta(hours=5)
    row.escalation_level = kwargs.get("escalation_level", 3)
    row.first_response_at = kwargs.get("first_response_at")
    row.completed_at = kwargs.get("completed_at")
    row.owner_escalated = kwargs.get("owner_escalated", False)
    row.owner_escalated_at = kwargs.get("owner_escalated_at")
    row.owner_notification_sent = False
    return row


def _context(**kwargs):
    ctx = MagicMock()
    ctx.request_id = kwargs.get("request_id", str(uuid.uuid4()))
    ctx.request_number = kwargs.get("request_number", "AUTO-00153")
    ctx.vertical = kwargs.get("vertical", "auto")
    ctx.request_type = kwargs.get("request_type", "AUTO_PARTS")
    ctx.manager_uuid = kwargs.get("manager_uuid", str(uuid.uuid4()))
    ctx.manager_telegram_id = kwargs.get("manager_telegram_id", 222)
    ctx.client_telegram_id = 999
    return ctx


@pytest.mark.asyncio
async def test_owner_escalation_occurs():
    row = _sla_row()
    context = _context(request_id=str(row.request_id))

    sla_repo = AsyncMock()
    sla_repo._resolve_manager_name.return_value = "Lucifer"

    mock_session = AsyncMock()

    with patch.object(OwnerRepository, "is_enabled", return_value=True), patch.object(
        OwnerRepository,
        "mark_owner_escalated",
        new=AsyncMock(return_value=True),
    ), patch(
        "services.owner_escalation_service.SLARepository",
        return_value=sla_repo,
    ), patch(
        "services.owner_escalation_service.publish",
        new=AsyncMock(),
    ) as publish_mock:
        result = await OwnerEscalationService.escalate_request(
            row,
            context=context,
            session=mock_session,
        )

    assert result is True
    publish_mock.assert_awaited_once()
    event = publish_mock.await_args.args[0]
    assert isinstance(event, OwnerEscalationEvent)
    assert event.request_number == "AUTO-00153"
    assert event.minutes_overdue >= 300
    assert event.manager_name == "Lucifer"


@pytest.mark.asyncio
async def test_owner_escalation_disabled():
    with patch.object(OwnerRepository, "is_enabled", return_value=False):
        result = await owner_escalation_service.check_overdue_requests()

    assert result["acted"] == 0
    assert result["skipped"] is True


@pytest.mark.asyncio
async def test_duplicate_escalation_prevented():
    row = _sla_row(owner_escalated=True)

    with patch(
        "services.owner_escalation_service.publish",
        new=AsyncMock(),
    ) as publish_mock:
        result = await OwnerEscalationService.escalate_request(
            row,
            context=_context(),
            session=AsyncMock(),
        )

    assert result is False
    publish_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_completed_requests_ignored():
    row = _sla_row(completed_at=datetime.now(timezone.utc))

    with patch(
        "services.owner_escalation_service.publish",
        new=AsyncMock(),
    ) as publish_mock:
        result = await OwnerEscalationService.escalate_request(
            row,
            context=_context(),
            session=AsyncMock(),
        )

    assert result is False
    publish_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_notification_sent():
    event = OwnerEscalationEvent(
        request_id=str(uuid.uuid4()),
        request_number="AUTO-00153",
        vertical="auto",
        request_type="AUTO_PARTS",
        manager_id=str(uuid.uuid4()),
        manager_name="Lucifer",
        owner_id="900001",
        owner_name="Platform Owner",
        minutes_overdue=263,
    )

    mock_repo = AsyncMock()
    mock_repo.mark_owner_notification_sent.return_value = True
    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = AsyncMock()
    mock_cm.__aexit__.return_value = None

    with patch(
        "services.owner_escalation_service.OwnerRepository.owner_config",
        return_value={"telegram_id": 900001, "name": "Platform Owner"},
    ), patch(
        "services.notification_service.notification_service.notify_managers_new_request",
        new=AsyncMock(),
    ) as notify_mock, patch(
        "services.owner_escalation_service.get_session",
        return_value=mock_cm,
    ), patch(
        "services.owner_escalation_service.OwnerRepository",
        return_value=mock_repo,
    ):
        sent = await owner_escalation_service.notify_owner(event)

    assert sent is True
    notify_mock.assert_awaited_once()
    mock_repo.mark_owner_notification_sent.assert_awaited_once()


@pytest.mark.asyncio
async def test_audit_written_for_owner_escalation():
    event = OwnerEscalationEvent(
        request_id=str(uuid.uuid4()),
        request_number="AUTO-00153",
        vertical="auto",
        manager_id="mgr-1",
        manager_name="Lucifer",
        owner_id="900001",
        minutes_overdue=263,
        completion_deadline=datetime.now(timezone.utc).isoformat(),
    )
    record = audit_record_from_event(event)
    assert record is not None
    assert record.event_type == AuditEventType.OWNER_ESCALATED.value
    assert record.metadata_json["manager_before"] == "mgr-1"
    assert record.metadata_json["minutes_overdue"] == 263


@pytest.mark.asyncio
async def test_kpi_updated_on_owner_escalation_event():
    mock_repo = AsyncMock()
    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = AsyncMock()
    mock_cm.__aexit__.return_value = None

    with patch("services.kpi_service.get_session", return_value=mock_cm), patch(
        "services.kpi_service.KpiRepository",
        return_value=mock_repo,
    ):
        from services.kpi_service import KpiService

        await KpiService._on_owner_escalation(
            OwnerEscalationEvent(
                request_id=str(uuid.uuid4()),
                request_number="AUTO-00153",
                vertical="auto",
            )
        )

    assert mock_repo.bump_vertical.await_count >= 2


@pytest.mark.asyncio
async def test_eventbus_handlers_registered():
    register_platform_event_handlers()
    from events.event_bus import PlatformEventBus

    subs = PlatformEventBus.list_subscribers("OwnerEscalationEvent")["OwnerEscalationEvent"]
    assert "owner_notification" in subs
    assert "metrics_owner_escalation" in subs
    assert "audit_trail_OwnerEscalationEvent" in subs
    assert "kpi_OwnerEscalationEvent" in subs


@pytest.mark.asyncio
async def test_check_overdue_requests_batch():
    row = _sla_row()
    context = _context(request_id=str(row.request_id))

    owner_repo = AsyncMock()
    owner_repo.lock_owner_escalation_candidates.return_value = [row]

    esc_repo = AsyncMock()
    esc_repo.load_request_context.return_value = context

    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = AsyncMock()
    mock_cm.__aexit__.return_value = None

    with patch.object(OwnerRepository, "is_enabled", return_value=True), patch(
        "services.owner_escalation_service.get_session",
        return_value=mock_cm,
    ), patch(
        "services.owner_escalation_service.OwnerRepository",
        return_value=owner_repo,
    ), patch(
        "services.owner_escalation_service.EscalationRepository",
        return_value=esc_repo,
    ), patch.object(
        OwnerEscalationService,
        "escalate_request",
        new=AsyncMock(return_value=True),
    ) as escalate_mock:
        result = await owner_escalation_service.check_overdue_requests()

    assert result["acted"] == 1
    escalate_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_dashboard_owner_escalated_endpoint():
    items = [
        {
            "request_number": "AUTO-00153",
            "manager": "Lucifer",
            "vertical": "AUTO",
            "minutes_overdue": 263,
            "owner_escalated_at": datetime.now(timezone.utc).isoformat(),
        }
    ]

    app = web.Application()
    register_sla_admin_routes(app)

    with patch(
        "services.sla_dashboard_service.sla_dashboard_service.get_owner_escalated",
        new=AsyncMock(return_value=items),
    ):
        async with TestClient(TestServer(app)) as client:
            resp = await client.get("/api/v1/sla/owner-escalated")
            assert resp.status == 200
            data = await resp.json()
            assert data[0]["request_number"] == "AUTO-00153"


@pytest.mark.asyncio
async def test_owner_escalation_kpi_metrics():
    mock_repo = AsyncMock()
    mock_repo.get_owner_escalation_kpi.return_value = {
        "owner_escalations_total": 5,
        "owner_escalations_today": 1,
        "owner_escalations_this_week": 3,
        "owner_escalations_this_month": 4,
    }
    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = AsyncMock()
    mock_cm.__aexit__.return_value = None

    with patch("services.owner_escalation_service.get_session", return_value=mock_cm), patch(
        "services.owner_escalation_service.OwnerRepository",
        return_value=mock_repo,
    ):
        kpi = await owner_escalation_service.get_owner_escalation_kpi()

    assert kpi["owner_escalations_total"] == 5
    assert kpi["owner_escalations_today"] == 1


@pytest.mark.asyncio
@pytest.mark.skipif(
    os.getenv("RUN_OWNER_PG_INTEGRATION") != "1",
    reason="PostgreSQL integration — set RUN_OWNER_PG_INTEGRATION=1",
)
async def test_postgres_owner_repository_kpi_shape():
    kpi = await owner_escalation_service.get_owner_escalation_kpi()
    assert "owner_escalations_total" in kpi
