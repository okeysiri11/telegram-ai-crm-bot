"""Integration tests — AUTO buy_car multi-step flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from services.auto_client_flow_engine import (
    FLOW_STEPS,
    REQUEST_BUY,
    first_step,
    next_step,
    validate_text_step,
    vin_present,
)
from states.entry_flow_states import AUTO_CLIENT_PENDING_RESTORE, AutoClientFlow


@pytest.mark.asyncio
async def test_buy_car_step_sequence():
    steps = FLOW_STEPS[REQUEST_BUY]
    assert first_step(REQUEST_BUY) == "brand"
    assert steps[-1] == "vin_optional"
    current = first_step(REQUEST_BUY)
    visited = [current]
    while current:
        current = next_step(REQUEST_BUY, current)
        if current:
            visited.append(current)
    assert visited == list(steps)


@pytest.mark.asyncio
async def test_buy_car_validate_steps():
    ok, err, val = validate_text_step("brand", "BMW", flow_type=REQUEST_BUY)
    assert ok and val == "BMW"

    ok, err, val = validate_text_step("year", "2021", flow_type=REQUEST_BUY)
    assert ok and val == 2021

    ok, err, _ = validate_text_step("year", "abc", flow_type=REQUEST_BUY)
    assert not ok


@pytest.mark.asyncio
async def test_buy_car_photos_done_advances(mock_message, mock_fsm_context, sample_submit_result):
    from routers.auto_client_router import _advance_after_step, _finish_request

    store = mock_fsm_context._store
    store.update(
        {
            "flow_type": REQUEST_BUY,
            "flow_step": "photos",
            "brand": "BMW",
            "model": "X5",
            "year": 2021,
            "engine": "3.0",
            "color": "black",
            "user_description": "Need SUV",
            "photo_file_ids": ["photo1", "photo2"],
            "client_phone": "+380501234567",
        }
    )
    await mock_fsm_context.set_state(AutoClientFlow.awaiting_photos.state)

    with patch(
        "routers.auto_client_router.VerticalOnboardingEngineV1.get_language",
        new=AsyncMock(return_value="ru"),
    ), patch(
        "routers.auto_client_router.VerticalOnboardingEngineV1.get_preferences",
        new=AsyncMock(return_value={"source_link": "auto_client"}),
    ), patch(
        "routers.auto_client_router.VerticalOnboardingEngineV1.clear_auto_client_pending",
        new=AsyncMock(),
    ), patch(
        "routers.auto_client_router.EntryPointEngineV1.set_current_flow",
        new=AsyncMock(),
    ), patch(
        "services.pg_auto_client_request_engine.AutoClientRequestEngineV1.submit",
        new=AsyncMock(return_value=sample_submit_result),
    ), patch(
        "services.pg_lead_engine.LeadEngineV1.submit_auto_client_request",
        new=AsyncMock(),
    ), patch(
        "services.pg_manager_delivery_engine.ManagerDeliveryEngineV1.notify_auto_client_request",
        new=AsyncMock(),
    ), patch(
        "routers.auto_client_router.VerticalOnboardingEngineV1.save_auto_client_pending",
        new=AsyncMock(),
    ), patch(
        "services.pg_ai_manager_engine.AiManagerEngineV1.qualify_message",
        new=AsyncMock(return_value=None),
    ), patch(
        "routers.auto_client_router.auto_client_menu",
        return_value=None,
    ):
        await _advance_after_step(mock_message, mock_fsm_context)
        # After photos → phone step
        data = await mock_fsm_context.get_data()
        assert data.get("flow_step") == "phone"

        store["flow_step"] = "vin_optional"
        await _finish_request(mock_message, mock_fsm_context)
        mock_message.answer.assert_called()
        assert "AUTO-9999" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_buy_car_vin_no_finishes_without_vin(mock_message, mock_fsm_context, sample_submit_result):
    from routers.auto_client_router import auto_client_vin_no

    callback = AsyncMock()
    callback.message = mock_message
    callback.from_user = mock_message.from_user
    callback.answer = AsyncMock()

    mock_fsm_context._store.update(
        {
            "flow_type": REQUEST_BUY,
            "flow_step": "vin_optional",
            "brand": "Audi",
            "model": "A4",
            "user_description": "Buy used",
            "client_phone": "+380501111111",
        }
    )
    await mock_fsm_context.set_state(AutoClientFlow.awaiting_vin_choice.state)

    with patch(
        "routers.auto_client_router._ensure_auto_client_user",
        new=AsyncMock(return_value=True),
    ), patch(
        "routers.auto_client_router._remove_inline_keyboard",
        new=AsyncMock(),
    ), patch(
        "routers.auto_client_router.VerticalOnboardingEngineV1.get_language",
        new=AsyncMock(return_value="ru"),
    ), patch(
        "routers.auto_client_router.VerticalOnboardingEngineV1.get_preferences",
        new=AsyncMock(return_value={"source_link": "auto_client"}),
    ), patch(
        "routers.auto_client_router.VerticalOnboardingEngineV1.clear_auto_client_pending",
        new=AsyncMock(),
    ), patch(
        "routers.auto_client_router.EntryPointEngineV1.set_current_flow",
        new=AsyncMock(),
    ), patch(
        "services.pg_auto_client_request_engine.AutoClientRequestEngineV1.submit",
        new=AsyncMock(return_value=sample_submit_result),
    ), patch(
        "services.pg_lead_engine.LeadEngineV1.submit_auto_client_request",
        new=AsyncMock(),
    ):
        await auto_client_vin_no(callback, mock_fsm_context)
        data = await mock_fsm_context.get_data()
        assert data.get("vin") is None


@pytest.mark.asyncio
async def test_buy_car_photo_skip_callback(mock_message, mock_fsm_context):
    from routers.auto_client_router import auto_client_photos_action

    callback = AsyncMock()
    callback.data = "ac:photos:skip"
    callback.message = mock_message
    callback.from_user = mock_message.from_user
    callback.answer = AsyncMock()

    mock_fsm_context._store.update({"flow_type": REQUEST_BUY, "flow_step": "photos"})
    await mock_fsm_context.set_state(AutoClientFlow.awaiting_photos.state)

    with patch(
        "routers.auto_client_router._ensure_auto_client_user",
        new=AsyncMock(return_value=True),
    ), patch(
        "routers.auto_client_router._advance_after_step",
        new=AsyncMock(),
    ) as advance:
        await auto_client_photos_action(callback, mock_fsm_context)
        advance.assert_awaited_once()


def test_pending_restore_covers_buy_car_steps():
    for step in FLOW_STEPS[REQUEST_BUY]:
        from services.auto_client_flow_engine import pending_key

        key = pending_key(REQUEST_BUY, step)
        assert key in AUTO_CLIENT_PENDING_RESTORE


def test_vin_present():
    assert vin_present({"vin": "WVWZZZ1JZ3W386752"})
    assert not vin_present({"vin": None})
    assert not vin_present({})
