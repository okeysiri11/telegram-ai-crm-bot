"""Integration tests — manager assignment via dynamic pool."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from config import OWNER_ID
from services.manager_service import manager_service
from services.manager_pool_service import manager_pool_service
from services.system_roles import Vertical


@pytest.mark.asyncio
async def test_auto_manager_from_pool():
    pool_mgr = {
        "user_id": str(uuid.uuid4()),
        "telegram_id": 393792086,
        "display_name": "Boroda_0003",
        "pool_id": str(uuid.uuid4()),
        "vertical": Vertical.AUTO.value,
    }
    with patch.object(
        manager_pool_service,
        "assign_manager",
        new=AsyncMock(return_value=pool_mgr),
    ) as assign:
        mgr = await manager_service.resolve_manager_for_vertical(Vertical.AUTO.value)
        assert mgr is not None
        assert mgr["telegram_id"] == pool_mgr["telegram_id"]
        assign.assert_awaited_once_with(Vertical.AUTO.value)


@pytest.mark.asyncio
async def test_agro_manager_from_pool():
    pool_mgr = {
        "user_id": str(uuid.uuid4()),
        "telegram_id": 222222,
        "display_name": "Christopher Moltisanti",
        "pool_id": str(uuid.uuid4()),
        "vertical": Vertical.AGRO.value,
    }
    with patch.object(
        manager_pool_service,
        "assign_manager",
        new=AsyncMock(return_value=pool_mgr),
    ) as assign:
        mgr = await manager_service.resolve_manager_for_vertical(Vertical.AGRO.value)
        assert mgr is not None
        assert mgr["telegram_id"] == pool_mgr["telegram_id"]
        assign.assert_awaited_once_with(Vertical.AGRO.value)


@pytest.mark.asyncio
async def test_super_admin_not_returned_from_pool():
    with patch.object(
        manager_pool_service,
        "assign_manager",
        new=AsyncMock(return_value=None),
    ):
        mgr = await manager_service.resolve_manager_for_vertical(Vertical.AUTO.value)
        assert mgr is None


@pytest.mark.asyncio
async def test_resolve_alternate_excludes_current():
    current_id = uuid.uuid4()
    alternate = {
        "user_id": str(uuid.uuid4()),
        "telegram_id": 333,
        "display_name": "Alternate",
        "pool_id": str(uuid.uuid4()),
    }
    with patch(
        "repositories.user_repository.UserRepository.get_by_id",
        new=AsyncMock(return_value=AsyncMock(telegram_id=111)),
    ), patch.object(
        manager_pool_service,
        "assign_manager",
        new=AsyncMock(return_value=alternate),
    ) as assign:
        mgr = await manager_service.resolve_alternate_manager_for_vertical(
            Vertical.AUTO.value,
            exclude_manager_id=current_id,
        )
        assert mgr == alternate
        assign.assert_awaited_once()
        assert assign.await_args.kwargs["exclude_telegram_ids"] == {111}


@pytest.mark.asyncio
async def test_owner_is_super_admin():
    if OWNER_ID is None:
        pytest.skip("OWNER_ID not configured")
    assert await manager_service.is_super_admin(OWNER_ID) is True
