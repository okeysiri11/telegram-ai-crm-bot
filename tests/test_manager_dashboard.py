"""Tests — Manager Dashboard service and router."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.dashboard_service import dashboard_service
from services.request_service import request_service


def _crm_row(**kwargs):
    row = MagicMock()
    row.id = kwargs.get("id", uuid.uuid4())
    row.request_number = kwargs.get("request_number", "REALTY-00001")
    row.request_type = kwargs.get("request_type", "REALTY_RENT_APARTMENT")
    row.status = kwargs.get("status", "NEW")
    row.client_telegram_id = kwargs.get("client_telegram_id", 900001)
    row.client_first_name = kwargs.get("client_first_name", "Client")
    row.client_username = kwargs.get("client_username", None)
    row.description = kwargs.get("description", "Rent apartment")
    row.manager_id = kwargs.get("manager_id", None)
    row.created_at = kwargs.get("created_at", datetime.now(timezone.utc))
    row.updated_at = row.created_at
    return row


@pytest.mark.asyncio
async def test_dashboard_get_new_requests():
    manager_id = uuid.uuid4()
    row = _crm_row()

    with patch(
        "services.request_service.RequestRepository.list_new_for_manager",
        new=AsyncMock(return_value=([row], [])),
    ):
        items = await dashboard_service.get_new_requests(manager_id)

    assert len(items) == 1
    assert items[0]["request_number"] == "REALTY-00001"
    assert items[0]["status"] == "NEW"


@pytest.mark.asyncio
async def test_dashboard_get_active_requests():
    manager_id = uuid.uuid4()
    row = _crm_row(status="IN_PROGRESS", manager_id=manager_id)

    with patch(
        "services.request_service.RequestRepository.list_active_for_manager",
        new=AsyncMock(return_value=([row], [])),
    ):
        items = await dashboard_service.get_active_requests(manager_id)

    assert items[0]["status"] == "IN_PROGRESS"


@pytest.mark.asyncio
async def test_dashboard_get_overdue_requests():
    manager_id = uuid.uuid4()
    row = _crm_row(status="ASSIGNED", manager_id=manager_id)

    with patch(
        "services.request_service.RequestRepository.list_overdue_for_manager",
        new=AsyncMock(return_value=([row], [])),
    ):
        items = await dashboard_service.get_overdue_requests(manager_id)

    assert len(items) == 1


@pytest.mark.asyncio
async def test_dashboard_get_completed_requests():
    manager_id = uuid.uuid4()
    row = _crm_row(status="COMPLETED", manager_id=manager_id)

    with patch(
        "services.request_service.RequestRepository.list_completed_for_manager",
        new=AsyncMock(return_value=([row], [])),
    ):
        items = await dashboard_service.get_completed_requests(manager_id)

    assert items[0]["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_take_request_via_request_service():
    manager_id = uuid.uuid4()
    with patch(
        "services.pg_client_request_crm_engine.ClientRequestCrmEngineV1.assign_manager",
        new=AsyncMock(
            return_value={
                "id": str(uuid.uuid4()),
                "request_number": "AGRO-00010",
                "request_type": "AGRO_REQUEST",
                "status": "ASSIGNED",
                "client_telegram_id": 1,
                "client_username": "client",
                "description": "wheat",
            }
        ),
    ), patch(
        "services.request_service.RequestService._resolve_request_number",
        new=AsyncMock(return_value="AGRO-00010"),
    ):
        result = await request_service.take_request("AGRO-00010", manager_id)

    assert result is not None
    assert result["request_number"] == "AGRO-00010"
    assert result["status"] == "ASSIGNED"


@pytest.mark.asyncio
async def test_complete_request_via_request_service():
    with patch(
        "services.pg_client_request_crm_engine.ClientRequestCrmEngineV1.update_status",
        new=AsyncMock(
            return_value={
                "id": str(uuid.uuid4()),
                "request_number": "REALTY-00005",
                "request_type": "REALTY_BUY_HOUSE",
                "status": "COMPLETED",
                "client_telegram_id": 1,
                "client_username": "client",
                "description": "buy",
            }
        ),
    ), patch(
        "services.request_service.RequestService._resolve_request_number",
        new=AsyncMock(return_value="REALTY-00005"),
    ):
        result = await request_service.complete_request("REALTY-00005")

    assert result is not None
    assert result["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_reassign_request_delegates_to_take():
    manager_id = uuid.uuid4()
    with patch(
        "services.request_service.RequestService.get_request",
        new=AsyncMock(return_value={"manager_id": "old-id"}),
    ), patch(
        "services.request_service.RequestService._assign_request_to_manager",
        new=AsyncMock(return_value={"id": "1", "request_number": "AUTO-0001", "status": "ASSIGNED", "vertical": "auto", "request_type": "AUTO_SEARCH"}),
    ), patch(
        "services.request_service.RequestService._publish_manager_reassigned",
        new=AsyncMock(),
    ) as publish_mock:
        result = await dashboard_service.reassign_request("AUTO-0001", manager_id)

    publish_mock.assert_awaited_once()
    assert result["request_number"] == "AUTO-0001"


@pytest.mark.asyncio
async def test_dashboard_tabs_keyboard():
    from routers.manager_dashboard_router import TAB_ACTIVE, TAB_NEW, dashboard_tabs_keyboard

    kb = dashboard_tabs_keyboard()
    callbacks = [btn.callback_data for row in kb.inline_keyboard for btn in row]
    assert TAB_NEW in callbacks
    assert TAB_ACTIVE in callbacks


@pytest.mark.asyncio
async def test_dashboard_new_callback():
    from routers.manager_dashboard_router import dashboard_new

    callback = AsyncMock()
    callback.from_user = MagicMock(id=123)
    callback.message = AsyncMock()
    callback.answer = AsyncMock()

    manager_uuid = uuid.uuid4()
    with patch(
        "routers.manager_dashboard_router._require_manager",
        new=AsyncMock(return_value=True),
    ), patch(
        "routers.manager_dashboard_router._manager_uuid",
        new=AsyncMock(return_value=manager_uuid),
    ), patch(
        "routers.manager_dashboard_router.dashboard_service.get_new_requests",
        new=AsyncMock(return_value=[{"request_number": "REALTY-1", "status": "NEW", "vertical": "realty", "request_type": "RENT", "description": "x"}]),
    ):
        await dashboard_new(callback)

    callback.message.edit_text.assert_awaited_once()
    callback.answer.assert_awaited_once()


def test_format_request_lines_empty():
    text = dashboard_service.format_request_lines("📥 Новые", [])
    assert "Нет заявок" in text
