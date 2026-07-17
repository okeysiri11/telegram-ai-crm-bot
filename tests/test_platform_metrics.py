"""Unit tests — PlatformMetricsService lifecycle and aggregates."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.platform_metrics_service import PlatformMetricsService, _infer_vertical


def test_infer_vertical_from_request_number():
    assert _infer_vertical("AUTO-001", "buy_car") == "auto"
    assert _infer_vertical("AGRO-002", "request") == "agro"
    assert _infer_vertical("REQ-003", "AGRO_SEED", vertical="agro") == "agro"


@pytest.mark.asyncio
async def test_track_request_created_is_non_blocking():
    with patch.object(
        PlatformMetricsService,
        "_write_request_created",
        new=AsyncMock(),
    ) as write_mock, patch(
        "services.platform_metrics_service.asyncio.get_running_loop",
    ) as get_loop:
        task = MagicMock()
        loop = MagicMock()
        loop.create_task.return_value = task
        get_loop.return_value = loop

        await PlatformMetricsService.track_request_created(
            request_number="AUTO-100",
            request_type="buy_car",
            manager_id=str(uuid.uuid4()),
        )

        loop.create_task.assert_called_once()
        coro = loop.create_task.call_args[0][0]
        assert hasattr(coro, "__await__")


@pytest.mark.asyncio
async def test_write_request_created_persists_metrics():
    manager_id = uuid.uuid4()
    request_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    mock_repo = AsyncMock()
    mock_repo.get_request_metric.return_value = None
    mock_repo.insert_request_metric.return_value = MagicMock()
    mock_repo.mark_assigned.return_value = (MagicMock(), True)

    mock_session = AsyncMock()
    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_session
    mock_cm.__aexit__.return_value = None

    with patch("services.platform_metrics_service.get_session", return_value=mock_cm), patch(
        "services.platform_metrics_service.PlatformMetricsRepository",
        return_value=mock_repo,
    ):
        await PlatformMetricsService._write_request_created(
            request_number="AUTO-200",
            request_type="buy_car",
            vertical="auto",
            request_id=request_id,
            manager_id=manager_id,
            request_created_at=now,
        )

    mock_repo.insert_request_metric.assert_called_once()
    mock_repo.bump_platform_daily.assert_called()
    mock_repo.mark_assigned.assert_called_once()
    mock_repo.bump_manager_daily.assert_called_once()


@pytest.mark.asyncio
async def test_write_manager_first_response_idempotent():
    mock_repo = AsyncMock()
    mock_repo.mark_first_response.return_value = (MagicMock(), False)

    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = AsyncMock()
    mock_cm.__aexit__.return_value = None

    with patch("services.platform_metrics_service.get_session", return_value=mock_cm), patch(
        "services.platform_metrics_service.PlatformMetricsRepository",
        return_value=mock_repo,
    ):
        await PlatformMetricsService._write_manager_first_response(
            request_number="AUTO-300",
            status="IN_PROGRESS",
        )

    mock_repo.bump_platform_daily.assert_not_called()
    mock_repo.bump_manager_daily.assert_not_called()


@pytest.mark.asyncio
async def test_aggregate_methods_delegate_to_repository():
    mock_repo = AsyncMock()
    mock_repo.average_response_time.return_value = 42.0
    mock_repo.requests_per_day.return_value = [{"date": "2026-07-17", "count": 5}]
    mock_repo.requests_per_vertical.return_value = [{"vertical": "auto", "count": 5}]
    mock_repo.conversion_to_deal.return_value = 0.2

    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = AsyncMock()
    mock_cm.__aexit__.return_value = None

    with patch("services.platform_metrics_service.get_session", return_value=mock_cm), patch(
        "services.platform_metrics_service.PlatformMetricsRepository",
        return_value=mock_repo,
    ):
        assert await PlatformMetricsService.average_response_time() == 42.0
        assert await PlatformMetricsService.requests_per_day() == [{"date": "2026-07-17", "count": 5}]
        assert await PlatformMetricsService.requests_per_vertical() == [{"vertical": "auto", "count": 5}]
        assert await PlatformMetricsService.conversion_to_deal() == 0.2
