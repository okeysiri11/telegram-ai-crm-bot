"""Integration tests — manager assignment rules."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from config import DEFAULT_AGRO_MANAGER_ID, DEFAULT_AUTO_MANAGER_ID, OWNER_ID
from services.manager_service import manager_service
from services.system_roles import Vertical


@pytest.mark.asyncio
async def test_auto_manager_is_boroda():
    with patch.object(
        manager_service,
        "resolve_manager_for_vertical",
        wraps=manager_service.resolve_manager_for_vertical,
    ), patch(
        "repositories.manager_repository.ManagerRepository.get_primary_for_vertical",
        new=AsyncMock(return_value=None),
    ), patch(
        "repositories.user_repository.UserRepository.get_by_telegram_id",
        new=AsyncMock(),
    ) as get_user:
        user = AsyncMock()
        user.id = "uuid"
        user.telegram_id = DEFAULT_AUTO_MANAGER_ID
        user.full_name = "Boroda_0003"
        user.username = "Boroda_0003"
        user.role = "AUTO_MANAGER"
        get_user.return_value = user

        if DEFAULT_AUTO_MANAGER_ID is None:
            pytest.skip("DEFAULT_AUTO_MANAGER_ID not configured")

        mgr = await manager_service.resolve_manager_for_vertical(Vertical.AUTO.value)
        assert mgr is not None
        assert mgr["telegram_id"] == DEFAULT_AUTO_MANAGER_ID


@pytest.mark.asyncio
async def test_agro_manager_is_christopher():
    if DEFAULT_AGRO_MANAGER_ID is None:
        pytest.skip("DEFAULT_AGRO_MANAGER_ID not configured")

    with patch(
        "repositories.manager_repository.ManagerRepository.get_primary_for_vertical",
        new=AsyncMock(return_value=None),
    ), patch(
        "repositories.user_repository.UserRepository.get_by_telegram_id",
        new=AsyncMock(),
    ) as get_user:
        user = AsyncMock()
        user.id = "uuid"
        user.telegram_id = DEFAULT_AGRO_MANAGER_ID
        user.full_name = "Christopher Moltisanti"
        user.username = None
        user.role = "AGRO_MANAGER"
        get_user.return_value = user

        mgr = await manager_service.resolve_manager_for_vertical(Vertical.AGRO.value)
        assert mgr is not None
        assert mgr["telegram_id"] == DEFAULT_AGRO_MANAGER_ID


@pytest.mark.asyncio
async def test_super_admin_not_auto_assigned():
    if OWNER_ID is None:
        pytest.skip("OWNER_ID not configured")

    fake_mgr = {
        "user_id": "00000000-0000-0000-0000-000000000001",
        "telegram_id": DEFAULT_AUTO_MANAGER_ID or 999,
        "display_name": "Boroda_0003",
    }
    with patch(
        "services.manager_service.ManagerRepository.get_primary_for_vertical",
        new=AsyncMock(return_value=None),
    ), patch(
        "services.manager_service.UserRepository.get_by_telegram_id",
        new=AsyncMock(),
    ) as get_user:
        user = AsyncMock()
        user.id = "uuid"
        user.telegram_id = fake_mgr["telegram_id"]
        user.full_name = "Boroda_0003"
        user.username = "Boroda_0003"
        user.role = "AUTO_MANAGER"
        get_user.return_value = user

        mgr = await manager_service.resolve_manager_for_vertical(Vertical.AUTO.value)
        assert mgr is not None
        assert mgr["telegram_id"] != OWNER_ID


@pytest.mark.asyncio
async def test_request_service_uses_manager_for_agro(client_user_id):
    from services.request_service import request_service

    with patch(
        "services.manager_service.manager_service.resolve_manager_for_vertical",
        new=AsyncMock(
            return_value={
                "user_id": "00000000-0000-0000-0000-000000000001",
                "telegram_id": DEFAULT_AGRO_MANAGER_ID or 1,
                "display_name": "Christopher Moltisanti",
            }
        ),
    ), patch(
        "repositories.request_repository.RequestRepository.next_crm_number",
        new=AsyncMock(return_value="AGRO-00099"),
    ), patch(
        "repositories.request_repository.RequestRepository.create_crm",
        new=AsyncMock(),
    ) as create, patch(
        "services.notification_service.notification_service.notify_managers_new_request",
        new=AsyncMock(),
    ):
        row = AsyncMock()
        row.id = "00000000-0000-0000-0000-000000000099"
        row.request_number = "AGRO-00099"
        row.request_type = "AGRO_REQUEST"
        row.status = "NEW"
        row.client_telegram_id = client_user_id
        row.client_first_name = "Test"
        row.client_username = None
        row.description = "wheat"
        row.manager_id = None
        create.return_value = row

        result = await request_service.create_request(
            vertical="agro",
            client_telegram_id=client_user_id,
            product="wheat",
            description="500t",
        )
        assert result["request_number"] == "AGRO-00099"
        create.assert_awaited_once()
