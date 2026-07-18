"""Tests — Smart Assignment Engine."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp.test_utils import TestClient, TestServer

from events.event_bus import reset_subscribers
from events.handlers import reset_handler_registration
from events.smart_assignment_events import (
    SmartAssignmentCalculatedEvent,
    SmartAssignmentCompletedEvent,
)
from models.assignment_score import (
    AssignmentSegment,
    AssignmentStrategy,
    ManagerCandidateMetrics,
    ScoreWeights,
    segment_from_vertical,
)
from models.manager_pool import ManagerPoolSnapshot
from routers.admin.assignment_router import register_assignment_admin_routes
from services.smart_assignment_service import SmartAssignmentService, smart_assignment_service


def _candidate(
    *,
    pool_id: str | None = None,
    telegram_id: int = 100,
    name: str = "Manager",
    vertical: str = "auto",
    specialization: str = "AUTO",
    priority: int = 100,
    current_load: int = 0,
    avg_response: float | None = 300.0,
    completed: int = 10,
) -> ManagerCandidateMetrics:
    return ManagerCandidateMetrics(
        pool_id=pool_id or str(uuid.uuid4()),
        telegram_id=telegram_id,
        name=name,
        vertical=vertical,
        specialization=specialization,
        priority=priority,
        current_load=current_load,
        average_response_seconds=avg_response,
        completed_requests=completed,
    )


def _pool_entry(**kwargs) -> ManagerPoolSnapshot:
    defaults = dict(
        entry_id=str(uuid.uuid4()),
        telegram_id=100,
        name="Manager",
        vertical="auto",
        priority=100,
        weight=100,
        is_active=True,
        current_load=0,
        last_assigned_at=None,
        specialization="AUTO",
    )
    defaults.update(kwargs)
    return ManagerPoolSnapshot(
        id=defaults.pop("entry_id"),
        telegram_id=defaults["telegram_id"],
        name=defaults["name"],
        vertical=defaults["vertical"],
        priority=defaults["priority"],
        weight=defaults["weight"],
        is_active=defaults["is_active"],
        current_load=defaults["current_load"],
        last_assigned_at=defaults["last_assigned_at"],
        specialization=defaults["specialization"],
    )


@pytest.fixture(autouse=True)
def _clean_bus():
    reset_subscribers()
    reset_handler_registration()
    yield
    reset_subscribers()
    reset_handler_registration()


@pytest.fixture
def mock_session_cm():
    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = AsyncMock()
    mock_cm.__aexit__.return_value = None
    return mock_cm


def test_segment_detection_auto():
    assert segment_from_vertical("auto") == AssignmentSegment.AUTO
    assert SmartAssignmentService.detect_segment(vertical="agro") == AssignmentSegment.AGRO
    assert SmartAssignmentService.detect_segment(request_type="REALTY_RENT") == AssignmentSegment.REALTY


def test_score_calculation_prefers_low_load():
    heavy = _candidate(name="Heavy", current_load=8, specialization="AUTO")
    light = _candidate(name="Light", current_load=1, specialization="AUTO")
    heavy_score = SmartAssignmentService.calculate_score(heavy, AssignmentSegment.AUTO)
    light_score = SmartAssignmentService.calculate_score(light, AssignmentSegment.AUTO)
    assert light_score.total_score > heavy_score.total_score


def test_specialization_bonus():
    specialist = _candidate(specialization="AUTO", current_load=2)
    generalist = _candidate(specialization="AGRO", current_load=2)
    spec_score = SmartAssignmentService.calculate_score(specialist, AssignmentSegment.AUTO)
    gen_score = SmartAssignmentService.calculate_score(generalist, AssignmentSegment.AUTO)
    assert spec_score.total_score > gen_score.total_score


def test_multi_specialization_gets_bonus():
    multi = _candidate(specialization="MULTI")
    other = _candidate(specialization="LEGAL")
    multi_score = SmartAssignmentService.calculate_score(multi, AssignmentSegment.AUTO)
    other_score = SmartAssignmentService.calculate_score(other, AssignmentSegment.AUTO)
    assert multi_score.total_score > other_score.total_score


def test_score_weights_configurable():
    weights = ScoreWeights(load=0.8, response=0.05, completed=0.05, priority=0.05, specialization=0.05)
    low_load = _candidate(current_load=0, specialization="AUTO")
    high_load = _candidate(current_load=9, specialization="AUTO")
    low = SmartAssignmentService.calculate_score(
        low_load, AssignmentSegment.AUTO, weights=weights
    )
    high = SmartAssignmentService.calculate_score(
        high_load, AssignmentSegment.AUTO, weights=weights
    )
    assert low.total_score > high.total_score


@pytest.mark.asyncio
async def test_smart_strategy_selects_highest_score(mock_session_cm):
    e1 = _pool_entry(name="Low", telegram_id=1, current_load=5, specialization="AUTO")
    e2 = _pool_entry(name="High", telegram_id=2, current_load=1, specialization="AUTO")

    mock_pool = AsyncMock()
    mock_pool.get_available_for_segment.return_value = [e1, e2]
    mock_pool.update_load.side_effect = lambda pid, **kw: e2
    mock_pool.touch_last_assigned.side_effect = lambda pid: e2

    mock_score = AsyncMock()
    mock_score.create_record.return_value = MagicMock(
        id=uuid.uuid4(),
        request_id=None,
        request_number=None,
        manager_pool_id=e2.id,
        manager_user_id=str(uuid.uuid4()),
        manager_telegram_id=2,
        segment="AUTO",
        score=0.9,
        strategy="SMART",
        assignment_time=datetime.now(timezone.utc),
        completed=False,
        response_time_seconds=None,
        resolution_time_seconds=None,
        specialization="AUTO",
    )
    mock_score.count_completed_for_manager.return_value = 5
    mock_score.average_response_from_metrics.return_value = 200.0
    mock_score.average_response_for_manager.return_value = None

    mock_user = MagicMock()
    mock_user.id = uuid.uuid4()
    mock_user.telegram_id = 2

    published: list = []

    async def _capture(event, *, wait=False):
        published.append(event)
        return {"handlers": 0, "errors": []}

    with patch("services.smart_assignment_service.get_session", return_value=mock_session_cm), patch(
        "services.smart_assignment_service.ManagerPoolRepository",
        return_value=mock_pool,
    ), patch(
        "services.smart_assignment_service.AssignmentScoreRepository",
        return_value=mock_score,
    ), patch(
        "services.smart_assignment_service.UserRepository",
        return_value=AsyncMock(get_by_telegram_id=AsyncMock(return_value=mock_user)),
    ), patch(
        "services.smart_assignment_service._strategy",
        return_value=AssignmentStrategy.SMART,
    ), patch(
        "services.smart_assignment_service.publish",
        side_effect=_capture,
    ):
        result = await smart_assignment_service.assign_for_request(
            vertical="auto",
            request_number="AUTO-00001",
        )

    assert result is not None
    assert result["telegram_id"] == 2
    assert any(isinstance(e, SmartAssignmentCalculatedEvent) for e in published)
    assert any(isinstance(e, SmartAssignmentCompletedEvent) for e in published)


@pytest.mark.asyncio
async def test_fallback_strategy_least_loaded(mock_session_cm):
    e1 = _pool_entry(name="Heavy", telegram_id=1, current_load=5)
    e2 = _pool_entry(name="Light", telegram_id=2, current_load=1)

    mock_pool = AsyncMock()
    mock_pool.get_available_for_segment.return_value = [e1, e2]
    mock_pool.update_load.side_effect = lambda pid, **kw: e2
    mock_pool.touch_last_assigned.side_effect = lambda pid: e2

    mock_score = AsyncMock()
    mock_score.create_record.return_value = MagicMock(id=uuid.uuid4())
    mock_user = MagicMock(id=uuid.uuid4(), telegram_id=2)

    with patch("services.smart_assignment_service.get_session", return_value=mock_session_cm), patch(
        "services.smart_assignment_service.ManagerPoolRepository",
        return_value=mock_pool,
    ), patch(
        "services.smart_assignment_service.AssignmentScoreRepository",
        return_value=mock_score,
    ), patch(
        "services.smart_assignment_service.UserRepository",
        return_value=AsyncMock(get_by_telegram_id=AsyncMock(return_value=mock_user)),
    ), patch(
        "services.smart_assignment_service._strategy",
        return_value=AssignmentStrategy.LEAST_LOADED,
    ), patch("services.smart_assignment_service.publish", new=AsyncMock()):
        result = await smart_assignment_service.assign_for_request(vertical="auto")

    assert result is not None
    assert result["telegram_id"] == 2


@pytest.mark.asyncio
async def test_unavailable_managers(mock_session_cm):
    mock_pool = AsyncMock()
    mock_pool.get_available_for_segment.return_value = []

    published: list = []

    async def _capture(event, *, wait=False):
        published.append(event)
        return {"handlers": 0, "errors": []}

    with patch("services.smart_assignment_service.get_session", return_value=mock_session_cm), patch(
        "services.smart_assignment_service.ManagerPoolRepository",
        return_value=mock_pool,
    ), patch(
        "services.smart_assignment_service._strategy",
        return_value=AssignmentStrategy.SMART,
    ), patch(
        "services.smart_assignment_service.publish",
        side_effect=_capture,
    ):
        result = await smart_assignment_service.assign_for_request(vertical="legal")

    assert result is None


@pytest.mark.asyncio
async def test_statistics_endpoint():
    stats_payload = {
        "assignment_strategy": "SMART",
        "average_score": 0.75,
        "average_assignment_latency_ms": 12.5,
        "segment_distribution": {"AUTO": 10},
        "manager_utilization": {},
        "kpi": {
            "average_assignment_score": 0.75,
            "smart_assignment_latency": 12.5,
            "specialization_accuracy": 0.8,
            "manager_utilization": {},
            "segment_distribution": {"AUTO": 10},
            "assignment_failures": 0,
        },
    }

    with patch.object(
        smart_assignment_service,
        "get_statistics",
        new=AsyncMock(return_value=stats_payload),
    ):
        from aiohttp import web

        app = web.Application()
        register_assignment_admin_routes(app)
        async with TestClient(TestServer(app)) as client:
            resp = await client.get("/api/v1/assignment/statistics")
            assert resp.status == 200
            body = await resp.json()
            assert body["assignment_strategy"] == "SMART"
            assert "kpi" in body


@pytest.mark.asyncio
async def test_manager_service_delegates_to_smart_assignment():
    from services.manager_service import manager_service

    expected = {
        "user_id": str(uuid.uuid4()),
        "telegram_id": 555,
        "display_name": "Smart Manager",
        "pool_id": str(uuid.uuid4()),
        "assignment_score": 0.88,
    }
    with patch.object(
        smart_assignment_service,
        "assign_for_request",
        new=AsyncMock(return_value=expected),
    ) as assign:
        mgr = await manager_service.resolve_manager_for_vertical("auto", request_type="AUTO_PARTS")
        assert mgr == expected
        assign.assert_awaited_once()


@pytest.mark.asyncio
async def test_kpi_updates_in_statistics(mock_session_cm):
    mock_score = AsyncMock()
    mock_score.get_statistics.return_value = {
        "total_assignments": 5,
        "average_score": 0.82,
        "completed_assignments": 3,
        "assignment_failures": 1,
        "segment_distribution": {"AUTO": 3, "AGRO": 2},
        "strategy_counts": {"SMART": 5},
        "specialization_efficiency": {"AUTO": {"count": 3, "average_score": 0.9}},
        "manager_utilization": {"abc": {"assignments": 2, "average_score": 0.7}},
        "specialization_accuracy": 0.6,
    }

    with patch("services.smart_assignment_service.get_session", return_value=mock_session_cm), patch(
        "services.smart_assignment_service.AssignmentScoreRepository",
        return_value=mock_score,
    ):
        stats = await smart_assignment_service.get_statistics()

    assert stats["kpi"]["average_assignment_score"] == 0.82
    assert stats["kpi"]["segment_distribution"]["AUTO"] == 3
    assert stats["kpi"]["assignment_failures"] >= 0


@pytest.mark.asyncio
@pytest.mark.skipif(
    os.getenv("RUN_SMART_ASSIGNMENT_PG_INTEGRATION") != "1",
    reason="PostgreSQL integration — set RUN_SMART_ASSIGNMENT_PG_INTEGRATION=1",
)
async def test_postgres_statistics_integration():
    stats = await smart_assignment_service.get_statistics()
    assert "assignment_strategy" in stats
    assert "kpi" in stats
    assert "average_assignment_score" in stats["kpi"]
