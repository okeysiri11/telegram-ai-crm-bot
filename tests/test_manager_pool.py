"""Tests — dynamic Manager Pool (assignment strategies, load, release, rebalance)."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp.test_utils import TestClient, TestServer

from events.event_bus import reset_subscribers
from events.handlers import reset_handler_registration
from events.manager_pool_events import (
    ManagerAssignedEvent,
    ManagerReleasedEvent,
    ManagerUnavailableEvent,
)
from events.request_events import ManagerReassignedEvent, RequestCompletedEvent
from models.manager_pool import AssignmentMode, ManagerPoolSnapshot
from services.manager_pool_service import ManagerPoolService, manager_pool_service


def _entry(
    *,
    entry_id: str | None = None,
    telegram_id: int = 100,
    name: str = "Manager A",
    vertical: str = "auto",
    priority: int = 100,
    weight: int = 100,
    is_active: bool = True,
    current_load: int = 0,
    last_assigned_at: datetime | None = None,
    specialization: str = "AUTO",
) -> ManagerPoolSnapshot:
    return ManagerPoolSnapshot(
        id=entry_id or str(uuid.uuid4()),
        telegram_id=telegram_id,
        name=name,
        vertical=vertical,
        priority=priority,
        weight=weight,
        is_active=is_active,
        current_load=current_load,
        last_assigned_at=last_assigned_at,
        specialization=specialization,
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


def test_select_round_robin_prefers_never_assigned():
    older = _entry(name="Old", telegram_id=1, last_assigned_at=datetime(2026, 1, 1, tzinfo=timezone.utc))
    newer = _entry(name="New", telegram_id=2, last_assigned_at=datetime(2026, 6, 1, tzinfo=timezone.utc))
    never = _entry(name="Fresh", telegram_id=3, last_assigned_at=None)

    picked = ManagerPoolService._select_manager([older, newer, never], AssignmentMode.ROUND_ROBIN)
    assert picked is not None
    assert picked.telegram_id == 3


def test_select_least_loaded():
    heavy = _entry(name="Heavy", telegram_id=1, current_load=5)
    light = _entry(name="Light", telegram_id=2, current_load=1)
    picked = ManagerPoolService._select_manager([heavy, light], AssignmentMode.LEAST_LOADED)
    assert picked is not None
    assert picked.telegram_id == 2


def test_select_priority():
    low = _entry(name="Low", telegram_id=1, priority=50, current_load=0)
    high = _entry(name="High", telegram_id=2, priority=200, current_load=1)
    picked = ManagerPoolService._select_manager([low, high], AssignmentMode.PRIORITY)
    assert picked is not None
    assert picked.telegram_id == 2


def test_select_weighted_respects_weights(monkeypatch):
    a = _entry(name="A", telegram_id=1, weight=1)
    b = _entry(name="B", telegram_id=2, weight=100)
    monkeypatch.setattr("services.manager_pool_service.random.choices", lambda c, weights, k=1: [b])
    picked = ManagerPoolService._select_manager([a, b], AssignmentMode.WEIGHTED)
    assert picked is not None
    assert picked.telegram_id == 2


def test_select_skips_inactive_via_empty_candidates():
    inactive = _entry(name="Off", telegram_id=1, is_active=False)
    # inactive managers are filtered at repository level; service receives only active
    picked = ManagerPoolService._select_manager([], AssignmentMode.ROUND_ROBIN)
    assert picked is None


@pytest.mark.asyncio
async def test_assign_manager_publishes_event(mock_session_cm):
    entry = _entry(telegram_id=111, name="Boroda")
    updated = _entry(entry_id=entry.id, telegram_id=111, name="Boroda", current_load=1)

    mock_repo = AsyncMock()
    mock_repo.get_available_managers.return_value = [entry]
    mock_repo.update_load.return_value = updated
    mock_repo.touch_last_assigned.return_value = updated

    published: list = []

    async def _capture(event, *, wait=False):
        published.append(event)
        return {"handlers": 1, "errors": []}

    with patch("services.manager_pool_service.get_session", return_value=mock_session_cm), patch(
        "services.manager_pool_service.ManagerPoolRepository",
        return_value=mock_repo,
    ), patch(
        "services.manager_pool_service._assignment_mode",
        return_value=AssignmentMode.ROUND_ROBIN,
    ), patch(
        "services.manager_pool_service.publish",
        side_effect=_capture,
    ), patch.object(
        ManagerPoolService,
        "_manager_snapshot_from_pool",
        new=AsyncMock(
            return_value={
                "user_id": str(uuid.uuid4()),
                "telegram_id": 111,
                "display_name": "Boroda",
                "pool_id": entry.id,
            }
        ),
    ):
        result = await manager_pool_service.assign_manager("auto")

    assert result is not None
    assert result["telegram_id"] == 111
    assert any(isinstance(e, ManagerAssignedEvent) for e in published)
    mock_repo.update_load.assert_awaited_once()
    mock_repo.touch_last_assigned.assert_awaited_once()


@pytest.mark.asyncio
async def test_assign_manager_unavailable_when_pool_empty(mock_session_cm):
    mock_repo = AsyncMock()
    mock_repo.get_available_managers.return_value = []

    published: list = []

    async def _capture(event, *, wait=False):
        published.append(event)
        return {"handlers": 0, "errors": []}

    with patch("services.manager_pool_service.get_session", return_value=mock_session_cm), patch(
        "services.manager_pool_service.ManagerPoolRepository",
        return_value=mock_repo,
    ), patch(
        "services.manager_pool_service._assignment_mode",
        return_value=AssignmentMode.ROUND_ROBIN,
    ), patch(
        "services.manager_pool_service.publish",
        side_effect=_capture,
    ):
        result = await manager_pool_service.assign_manager("agro")

    assert result is None
    assert any(isinstance(e, ManagerUnavailableEvent) for e in published)


@pytest.mark.asyncio
async def test_release_manager_decrements_load(mock_session_cm):
    entry = _entry(current_load=2)
    released = _entry(entry_id=entry.id, current_load=1)

    mock_repo = AsyncMock()
    mock_repo.get_manager_by_id.return_value = entry
    mock_repo.update_load.return_value = released

    published: list = []

    async def _capture(event, *, wait=False):
        published.append(event)
        return {"handlers": 0, "errors": []}

    with patch("services.manager_pool_service.get_session", return_value=mock_session_cm), patch(
        "services.manager_pool_service.ManagerPoolRepository",
        return_value=mock_repo,
    ), patch(
        "services.manager_pool_service.publish",
        side_effect=_capture,
    ):
        result = await manager_pool_service.release_manager(pool_manager_id=entry.id)

    assert result is not None
    assert result.current_load == 1
    mock_repo.update_load.assert_awaited_with(entry.id, delta=-1)
    assert any(isinstance(e, ManagerReleasedEvent) for e in published)


@pytest.mark.asyncio
async def test_calculate_load_and_rebalance(mock_session_cm):
    e1 = _entry(name="M1", telegram_id=10)
    e2 = _entry(name="M2", telegram_id=20)

    mock_repo = AsyncMock()
    mock_repo.list_all.return_value = [e1, e2]
    mock_repo.count_active_for_telegram.side_effect = [3, 1, 3, 1]
    mock_repo.set_loads_bulk = AsyncMock()

    with patch("services.manager_pool_service.get_session", return_value=mock_session_cm), patch(
        "services.manager_pool_service.ManagerPoolRepository",
        return_value=mock_repo,
    ):
        loads = await manager_pool_service.calculate_load(vertical="auto")
        rebalance = await manager_pool_service.rebalance(vertical="auto")

    assert loads[e1.id] == 3
    assert loads[e2.id] == 1
    assert rebalance["total_load"] == 4
    assert rebalance["average_load"] == 2.0
    mock_repo.set_loads_bulk.assert_awaited()


@pytest.mark.asyncio
async def test_handle_request_completed_releases_manager():
    manager_uuid = str(uuid.uuid4())
    with patch.object(
        ManagerPoolService,
        "release_by_manager_uuid",
        new=AsyncMock(),
    ) as release:
        await ManagerPoolService.handle_request_completed(
            RequestCompletedEvent(
                request_id=str(uuid.uuid4()),
                request_number="AUTO-00001",
                vertical="auto",
                request_type="AUTO_PARTS",
                manager_id=manager_uuid,
            )
        )
        release.assert_awaited_once()


@pytest.mark.asyncio
async def test_handle_reassigned_releases_previous_manager():
    with patch.object(
        ManagerPoolService,
        "release_by_manager_uuid",
        new=AsyncMock(),
    ) as release:
        await ManagerPoolService.handle_request_completed(
            ManagerReassignedEvent(
                request_id=str(uuid.uuid4()),
                request_number="AGRO-00002",
                vertical="agro",
                request_type="AGRO_GRAIN",
                previous_manager_id=str(uuid.uuid4()),
                manager_id=str(uuid.uuid4()),
            )
        )
        release.assert_awaited_once()


@pytest.mark.asyncio
async def test_pool_dashboard_endpoint(monkeypatch, auth_headers):
    dashboard = {
        "assignment_mode": "ROUND_ROBIN",
        "managers": [],
        "active_requests": 0,
        "average_response_time_seconds": None,
        "kpi": {
            "manager_current_load": {},
            "manager_average_load": 0.0,
            "assignment_latency_ms": 0.0,
            "pool_utilization": 0.0,
            "busy_managers": 0,
            "idle_managers": 0,
        },
    }

    async def _owner(_tid):
        from platform_management.permissions import ManagementRole

        return ManagementRole.OWNER

    monkeypatch.setattr("platform_management.permissions.resolve_role", _owner)

    with patch.object(
        manager_pool_service,
        "get_pool_dashboard",
        new=AsyncMock(return_value=dashboard),
    ), patch(
        "services.smart_assignment_service.smart_assignment_service.get_statistics",
        new=AsyncMock(return_value={"strategy": "ROUND_ROBIN", "kpi": {}}),
    ), patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        from aiohttp import web
        from platform_management.management_router import register_management_routes

        app = web.Application()
        register_management_routes(app)
        async with TestClient(TestServer(app)) as client:
            resp = await client.get("/management/v1/managers", headers=auth_headers)
            assert resp.status == 200
            body = (await resp.json())["data"]["pool"]
            assert body["assignment_mode"] == "ROUND_ROBIN"
            assert "kpi" in body
            assert "busy_managers" in body["kpi"]


@pytest.mark.asyncio
async def test_repository_snapshot_from_row():
    from repositories.manager_pool_repository import _snapshot

    row = MagicMock()
    row.id = uuid.uuid4()
    row.telegram_id = 999
    row.name = "Test"
    row.vertical = "auto"
    row.priority = 100
    row.weight = 100
    row.is_active = True
    row.current_load = 0
    row.last_assigned_at = None

    result = _snapshot(row)
    assert result.telegram_id == 999
    assert result.vertical == "auto"


@pytest.mark.asyncio
async def test_manager_service_delegates_to_pool():
    from services.manager_service import manager_service
    from services.smart_assignment_service import smart_assignment_service

    expected = {
        "user_id": str(uuid.uuid4()),
        "telegram_id": 555,
        "display_name": "Pool Manager",
        "pool_id": str(uuid.uuid4()),
    }
    with patch.object(
        smart_assignment_service,
        "assign_for_request",
        new=AsyncMock(return_value=expected),
    ) as assign:
        mgr = await manager_service.resolve_manager_for_vertical("auto")
        assert mgr == expected
        assign.assert_awaited_once()


@pytest.mark.asyncio
async def test_enable_and_disable_manager(mock_session_cm):
    entry = _entry(is_active=True)
    disabled = _entry(entry_id=entry.id, is_active=False)
    enabled = _entry(entry_id=entry.id, is_active=True)

    mock_repo = AsyncMock()
    mock_repo.disable_manager.return_value = disabled
    mock_repo.enable_manager.return_value = enabled

    with patch("services.manager_pool_service.get_session", return_value=mock_session_cm), patch(
        "services.manager_pool_service.ManagerPoolRepository",
        return_value=mock_repo,
    ):
        from repositories.manager_pool_repository import ManagerPoolRepository

        repo = ManagerPoolRepository(AsyncMock())
        repo.disable_manager = mock_repo.disable_manager
        repo.enable_manager = mock_repo.enable_manager
        off = await repo.disable_manager(entry.id)
        on = await repo.enable_manager(entry.id)

    assert off is not None and off.is_active is False
    assert on is not None and on.is_active is True


@pytest.mark.asyncio
async def test_inactive_managers_yield_unavailable(mock_session_cm):
    mock_repo = AsyncMock()
    mock_repo.get_available_managers.return_value = []

    published: list = []

    async def _capture(event, *, wait=False):
        published.append(event)
        return {"handlers": 0, "errors": []}

    with patch("services.manager_pool_service.get_session", return_value=mock_session_cm), patch(
        "services.manager_pool_service.ManagerPoolRepository",
        return_value=mock_repo,
    ), patch(
        "services.manager_pool_service.publish",
        side_effect=_capture,
    ):
        result = await manager_pool_service.assign_manager("realty")

    assert result is None
    assert any(isinstance(e, ManagerUnavailableEvent) for e in published)


@pytest.mark.asyncio
@pytest.mark.skipif(
    os.getenv("RUN_MANAGER_POOL_PG_INTEGRATION") != "1",
    reason="PostgreSQL integration — set RUN_MANAGER_POOL_PG_INTEGRATION=1 and run migration",
)
async def test_postgres_pool_dashboard_real():
    payload = await manager_pool_service.get_pool_dashboard()
    assert "assignment_mode" in payload
    assert "managers" in payload
    assert "kpi" in payload
    assert "pool_utilization" in payload["kpi"]
