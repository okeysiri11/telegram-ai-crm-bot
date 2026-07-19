"""Tests — platform KPI engine."""

from __future__ import annotations

import asyncio
import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from events.event_bus import publish, reset_subscribers
from events.handlers import register_platform_event_handlers, reset_handler_registration
from events.request_events import (
    ManagerFirstResponseEvent,
    RequestAssignedEvent,
    RequestCompletedEvent,
    RequestCreatedEvent,
    RequestOverdueEvent,
)
from models.manager_kpi import KpiTotals, period_bounds
from services.kpi_service import KpiService, kpi_service


@pytest.fixture(autouse=True)
def _clean():
    reset_subscribers()
    reset_handler_registration()
    KpiService.invalidate_cache()
    yield
    reset_subscribers()
    reset_handler_registration()
    KpiService.invalidate_cache()


def test_period_bounds_day_week_month():
    anchor = date(2026, 7, 17)
    assert period_bounds("day", anchor=anchor) == (anchor, anchor)
    assert period_bounds("week", anchor=anchor) == (date(2026, 7, 11), anchor)
    assert period_bounds("month", anchor=anchor) == (date(2026, 7, 1), anchor)
    assert period_bounds("all_time", anchor=anchor)[0] is None


def test_kpi_totals_metrics():
    totals = KpiTotals(
        requests_assigned=10,
        requests_first_response=8,
        requests_completed=6,
        requests_converted=2,
        requests_overdue=1,
        sla_compliant_count=7,
        sla_total_count=8,
        total_first_response_seconds=800,
        total_response_seconds=800,
        total_resolution_seconds=3600,
        response_count=8,
    )
    metrics = totals.to_metrics_dict()
    assert metrics["first_response_time_seconds"] == 100.0
    assert metrics["sla_compliance_percent"] == 87.5
    assert metrics["conversion_rate"] == round(2 / 6, 4)
    assert metrics["overdue_requests_count"] == 1


@pytest.mark.asyncio
async def test_handle_event_is_non_blocking():
    with patch.object(KpiService, "_process_event", new=AsyncMock()) as process_mock:
        await KpiService.handle_event(
            RequestCreatedEvent(
                request_id="id-1",
                request_number="AUTO-00001",
                vertical="auto",
                request_type="AUTO_PARTS",
            )
        )
        await asyncio.sleep(0.05)
    process_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_kpi_failure_does_not_break_event_bus():
    register_platform_event_handlers()

    with patch(
        "services.kpi_service.KpiService._process_event",
        new=AsyncMock(side_effect=RuntimeError("kpi down")),
    ), patch(
        "services.notification_service.notification_service.notify_managers_new_request",
        new=AsyncMock(),
    ) as notify:
        result = await publish(
            RequestCreatedEvent(
                request_id=str(uuid.uuid4()),
                request_number="REALTY-00001",
                vertical="realty",
                request_type="REALTY_RENT",
            ),
            wait=True,
        )
        await asyncio.sleep(0.05)

    notify.assert_awaited_once()
    assert result["handlers"] >= 3


@pytest.mark.asyncio
async def test_get_manager_kpi_uses_cache():
    payload = {"manager_id": "m1", "period": "month", "requests_assigned": 5}
    with patch.object(
        KpiService,
        "_cache_get",
        side_effect=[None, payload],
    ), patch.object(
        KpiService,
        "_cache_set",
    ) as cache_set, patch(
        "services.kpi_service.get_session",
    ) as get_session:
        mock_cm = AsyncMock()
        mock_cm.__aenter__.return_value = AsyncMock()
        mock_cm.__aexit__.return_value = None
        get_session.return_value = mock_cm

        mock_repo = AsyncMock()
        mock_repo.aggregate_manager_kpi.return_value = (KpiTotals(requests_assigned=5), {})
        with patch("services.kpi_service.KpiRepository", return_value=mock_repo):
            first = await kpi_service.get_manager_kpi("m1", period="month")
            second = await kpi_service.get_manager_kpi("m1", period="month")

    assert first["requests_assigned"] == 5
    assert second == payload
    cache_set.assert_called_once()


@pytest.mark.asyncio
async def test_platform_kpi_includes_manager_rankings():
    totals = KpiTotals(requests_created=20, requests_completed=10)
    rankings = [{"manager_id": "m1", "rank": 1, "score": 100.0}]

    mock_repo = AsyncMock()
    mock_repo.aggregate_platform_kpi.return_value = (totals, {"auto": totals.to_metrics_dict()})
    mock_repo.manager_rankings.return_value = rankings

    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = AsyncMock()
    mock_cm.__aexit__.return_value = None

    with patch("services.kpi_service.get_session", return_value=mock_cm), patch(
        "services.kpi_service.KpiRepository",
        return_value=mock_repo,
    ), patch(
        "services.owner_escalation_service.owner_escalation_service.get_owner_escalation_kpi",
        new=AsyncMock(return_value={"total": 0}),
    ):
        payload = await kpi_service.get_platform_kpi(period="week")

    assert payload["period"] == "week"
    assert payload["manager_rankings"][0]["manager_id"] == "m1"
    assert "auto" in payload["by_vertical"]


@pytest.mark.asyncio
async def test_event_lifecycle_updates_kpi():
    manager_id = str(uuid.uuid4())
    request_id = str(uuid.uuid4())
    mock_repo = AsyncMock()
    metric_row = MagicMock()
    metric_row.time_to_first_response_seconds = 120
    metric_row.time_to_close_seconds = 3600

    mock_repo.ensure_request_metric.return_value = metric_row
    mock_repo.mark_assigned.return_value = (metric_row, True)
    mock_repo.mark_first_response.return_value = (metric_row, True)
    mock_repo.mark_closed.return_value = (metric_row, True)

    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = AsyncMock()
    mock_cm.__aexit__.return_value = None

    with patch("services.kpi_service.get_session", return_value=mock_cm), patch(
        "services.kpi_service.KpiRepository",
        return_value=mock_repo,
    ):
        await KpiService._on_request_created(
            RequestCreatedEvent(
                request_id=request_id,
                request_number="AUTO-00050",
                vertical="auto",
                request_type="AUTO_PARTS",
            )
        )
        await KpiService._on_request_assigned(
            RequestAssignedEvent(
                request_id=request_id,
                request_number="AUTO-00050",
                vertical="auto",
                request_type="AUTO_PARTS",
                manager_id=manager_id,
            )
        )
        await KpiService._on_manager_first_response(
            ManagerFirstResponseEvent(
                request_id=request_id,
                request_number="AUTO-00050",
                vertical="auto",
                request_type="AUTO_PARTS",
                manager_id=manager_id,
                response_time_seconds=120,
            )
        )
        await KpiService._on_request_completed(
            RequestCompletedEvent(
                request_id=request_id,
                request_number="AUTO-00050",
                vertical="auto",
                request_type="AUTO_PARTS",
                manager_id=manager_id,
                converted_to_deal=True,
            )
        )
        await KpiService._on_request_overdue(
            RequestOverdueEvent(
                request_id=request_id,
                request_number="AUTO-00051",
                vertical="auto",
                request_type="AUTO_PARTS",
                manager_id=manager_id,
            )
        )

    assert mock_repo.bump_vertical.call_count >= 4
    assert mock_repo.bump_manager.call_count >= 3


def test_kpi_subscribed_on_register():
    register_platform_event_handlers()
    from events.event_bus import PlatformEventBus

    subs = PlatformEventBus.list_subscribers("ManagerFirstResponseEvent")["ManagerFirstResponseEvent"]
    assert "kpi_ManagerFirstResponseEvent" in subs
