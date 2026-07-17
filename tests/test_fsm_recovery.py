"""Integration tests — FSM recovery from persisted pending state."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from services.auto_client_flow_engine import REQUEST_BUY, REQUEST_SELL, pending_key
from states.entry_flow_states import AUTO_CLIENT_PENDING_RESTORE, AutoClientFlow


@pytest.mark.asyncio
async def test_restore_buy_car_photos_step(mock_message, mock_fsm_context):
    from routers.auto_client_router import _restore_auto_client_fsm

    pending = pending_key(REQUEST_BUY, "photos")
    with patch(
        "routers.auto_client_router.VerticalOnboardingEngineV1.get_auto_client_pending",
        new=AsyncMock(return_value=pending),
    ):
        await _restore_auto_client_fsm(mock_message, mock_fsm_context)

    state = await mock_fsm_context.get_state()
    assert state == AutoClientFlow.awaiting_photos.state
    data = await mock_fsm_context.get_data()
    assert data.get("flow_type") == REQUEST_BUY
    assert data.get("flow_step") == "photos"


@pytest.mark.asyncio
async def test_restore_sell_car_vin_optional(mock_message, mock_fsm_context):
    from routers.auto_client_router import _restore_auto_client_fsm

    pending = pending_key(REQUEST_SELL, "vin_optional")
    with patch(
        "routers.auto_client_router.VerticalOnboardingEngineV1.get_auto_client_pending",
        new=AsyncMock(return_value=pending),
    ):
        await _restore_auto_client_fsm(mock_message, mock_fsm_context)

    state = await mock_fsm_context.get_state()
    assert state == AutoClientFlow.awaiting_vin_choice.state


def test_all_flow_steps_have_pending_mapping():
    from services.auto_client_flow_engine import FLOW_STEPS

    for flow_type, steps in FLOW_STEPS.items():
        for step in steps:
            key = pending_key(flow_type, step)
            assert key in AUTO_CLIENT_PENDING_RESTORE, f"missing {key}"


@pytest.mark.asyncio
async def test_redis_required_when_postgres_only():
    from config import POSTGRES_ONLY, REDIS_REQUIRED

    if POSTGRES_ONLY:
        assert REDIS_REQUIRED is True


@pytest.mark.asyncio
async def test_fsm_storage_exits_without_redis_when_required(monkeypatch):
    import fsm_storage

    monkeypatch.setattr(fsm_storage, "REDIS_URL", "")
    monkeypatch.setattr(fsm_storage, "REDIS_REQUIRED", True)

    with pytest.raises(SystemExit):
        await fsm_storage.create_fsm_storage()
