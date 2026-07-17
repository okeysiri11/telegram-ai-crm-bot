"""Integration tests — AUTO sell_car flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from services.auto_client_flow_engine import FLOW_STEPS, REQUEST_SELL, first_step, next_step
from states.entry_flow_states import AutoClientFlow


@pytest.mark.asyncio
async def test_sell_car_same_steps_as_buy():
    assert FLOW_STEPS[REQUEST_SELL] == FLOW_STEPS["buy_car"]
    assert first_step(REQUEST_SELL) == "brand"


@pytest.mark.asyncio
async def test_sell_car_finish_request(mock_message, mock_fsm_context, sample_submit_result):
    from routers.auto_client_router import _finish_request

    mock_fsm_context._store.update(
        {
            "flow_type": REQUEST_SELL,
            "flow_step": "vin_optional",
            "brand": "Toyota",
            "model": "Camry",
            "year": 2019,
            "user_description": "Selling my car",
            "photo_file_ids": ["p1"],
            "client_phone": "+380509999999",
            "price": 15000,
        }
    )

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
    ) as submit, patch(
        "services.pg_lead_engine.LeadEngineV1.submit_auto_client_request",
        new=AsyncMock(),
    ):
        await _finish_request(mock_message, mock_fsm_context)
        submit.assert_awaited_once()
        call_kwargs = submit.await_args.kwargs
        assert call_kwargs["flow_request_type"] == REQUEST_SELL
        assert call_kwargs["photo_file_ids"] == ["p1"]
        mock_message.answer.assert_called()


@pytest.mark.asyncio
async def test_sell_car_vin_yes_prompts_for_vin(mock_message, mock_fsm_context):
    from routers.auto_client_router import auto_client_vin_yes

    callback = AsyncMock()
    callback.message = mock_message
    callback.from_user = mock_message.from_user
    callback.answer = AsyncMock()

    mock_fsm_context._store.update({"flow_type": REQUEST_SELL, "flow_step": "vin_optional"})
    await mock_fsm_context.set_state(AutoClientFlow.awaiting_vin_choice.state)

    with patch(
        "routers.auto_client_router._ensure_auto_client_user",
        new=AsyncMock(return_value=True),
    ), patch(
        "routers.auto_client_router._remove_inline_keyboard",
        new=AsyncMock(),
    ):
        await auto_client_vin_yes(callback, mock_fsm_context)
        state = await mock_fsm_context.get_state()
        assert state == AutoClientFlow.awaiting_vin.state
        mock_message.answer.assert_called()
        assert "VIN" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_sell_car_step_progression():
    steps = list(FLOW_STEPS[REQUEST_SELL])
    step = first_step(REQUEST_SELL)
    seen = []
    while step:
        seen.append(step)
        step = next_step(REQUEST_SELL, step)
    assert seen == steps
    assert seen[-1] == "vin_optional"
