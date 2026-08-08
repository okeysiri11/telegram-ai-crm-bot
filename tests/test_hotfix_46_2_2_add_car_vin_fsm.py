"""HOTFIX 46.2.2 — Add-car VIN FSM: durable state + AI routing invariant + dispatcher E2E."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Chat, Message, User

from services.auto_add_vehicle_flow import (
    ActiveFlowRoutingRequired,
    FLOW_NAME,
    assert_no_active_add_vehicle,
    clear_add_vehicle,
    has_active_add_vehicle_flow,
    persist_add_vehicle,
)
from services.auto_add_vehicle_vin import resolve_vin_decision
from states.entry_flow_states import AutoAddVehicleFlow


@pytest.fixture
def storage():
    return MemoryStorage()


@pytest.fixture
def dp(storage):
    dispatcher = Dispatcher(storage=storage)
    from routers.auto_add_vehicle_router import router as add_router
    from routers.telegram_super_app_router import router as super_router
    from handlers import router as handlers_router

    dispatcher.include_router(add_router)
    dispatcher.include_router(super_router)
    dispatcher.include_router(handlers_router)
    return dispatcher


def _msg(user_id: int, text: str, *, chat_id: int = 1) -> Message:
    message = MagicMock(spec=Message)
    message.text = text
    message.from_user = User(id=user_id, is_bot=False, first_name="T")
    message.chat = Chat(id=chat_id, type="private")
    message.answer = AsyncMock()
    message.bot = MagicMock()
    return message


@pytest.mark.asyncio
async def test_state_persists_across_separate_updates(storage):
    """Update N asks VIN; process ends; Update N+1 still has VIN_DECISION."""
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.base import StorageKey

    key = StorageKey(bot_id=42, chat_id=7, user_id=7)
    state = FSMContext(storage=storage, key=key)

    draft = {
        "make": "BMW",
        "model": "X5",
        "year": 2002,
        "fields": {"purchase_price": Decimal("15000")},
    }
    await persist_add_vehicle(state, step="vin_optional", draft=draft)
    # Simulate request end — new FSMContext same storage key
    state2 = FSMContext(storage=storage, key=key)
    assert await state2.get_state() == AutoAddVehicleFlow.vin_decision.state
    data = await state2.get_data()
    assert data["active_flow"] == FLOW_NAME
    assert data["active_state"] == "VIN_DECISION"
    assert data["draft"]["make"] == "BMW"
    assert await has_active_add_vehicle_flow(state2)


@pytest.mark.asyncio
async def test_ai_router_guard_raises_when_fsm_active(storage):
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.base import StorageKey

    key = StorageKey(bot_id=1, chat_id=1, user_id=99)
    state = FSMContext(storage=storage, key=key)
    await persist_add_vehicle(state, step="vin_optional", draft={"make": "BMW"})
    with pytest.raises(ActiveFlowRoutingRequired):
        await assert_no_active_add_vehicle(state, user_id=99)


@pytest.mark.asyncio
async def test_vin_no_text_finalizes_via_durable_handler(storage):
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.base import StorageKey
    from routers.auto_add_vehicle_router import vin_decision_text

    key = StorageKey(bot_id=1, chat_id=55, user_id=55)
    state = FSMContext(storage=storage, key=key)
    draft = {
        "make": "BMW",
        "model": "X5",
        "year": 2002,
        "fields": {"purchase_price": Decimal("15000")},
    }
    await persist_add_vehicle(state, step="vin_optional", draft=draft)
    msg = _msg(55, "Нет", chat_id=55)

    create_mock = AsyncMock(return_value={"id": "car-1"})
    with (
        patch("routers.auto_add_vehicle_router.CarEngineV1.create_car", create_mock),
        patch(
            "routers.auto_add_vehicle_router.ensure_telegram_tenant_session",
            new_callable=AsyncMock,
            create=True,
        ),
        patch(
            "services.auto_telegram_tenant.ensure_telegram_tenant_session",
            AsyncMock(return_value={"ok": True}),
        ),
        patch(
            "routers.auto_add_vehicle_router.VerticalOnboardingEngineV1.get_language",
            AsyncMock(return_value="ru"),
        ),
        patch("routers.auto_add_vehicle_router.log_audit"),
    ):
        await vin_decision_text(msg, state)

    create_mock.assert_awaited()
    assert create_mock.await_args.kwargs.get("vin") is None or create_mock.await_args[1].get("vin") is None
    # positional: create_car(user_id, vin=..., ...)
    assert create_mock.await_args.kwargs.get("vin") is None
    assert await state.get_state() is None
    answers = " ".join(str(c.args[0]) for c in msg.answer.await_args_list if c.args)
    assert "Автомобиль добавлен" in answers
    assert "VIN: не указан" in answers


@pytest.mark.asyncio
async def test_vin_yes_goes_to_waiting_vin(storage):
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.base import StorageKey
    from routers.auto_add_vehicle_router import vin_decision_text

    key = StorageKey(bot_id=1, chat_id=56, user_id=56)
    state = FSMContext(storage=storage, key=key)
    await persist_add_vehicle(
        state,
        step="vin_optional",
        draft={"make": "BMW", "model": "X5", "year": 2002, "fields": {}},
    )
    msg = _msg(56, "Да", chat_id=56)
    await vin_decision_text(msg, state)
    assert await state.get_state() == AutoAddVehicleFlow.waiting_vin.state
    assert "Отправьте VIN" in msg.answer.await_args.args[0]


@pytest.mark.asyncio
async def test_callback_auto_add_vin_no(storage):
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.base import StorageKey
    from aiogram.types import CallbackQuery
    from routers.auto_add_vehicle_router import vin_decision_callback

    key = StorageKey(bot_id=1, chat_id=57, user_id=57)
    state = FSMContext(storage=storage, key=key)
    await persist_add_vehicle(
        state,
        step="vin_optional",
        draft={
            "make": "BMW",
            "model": "X5",
            "year": 2002,
            "fields": {"purchase_price": Decimal("15000")},
        },
    )
    msg = _msg(57, "", chat_id=57)
    msg.edit_reply_markup = AsyncMock()
    cb = MagicMock(spec=CallbackQuery)
    cb.data = "auto:add:vin:no"
    cb.from_user = User(id=57, is_bot=False, first_name="T")
    cb.message = msg
    cb.answer = AsyncMock()

    create_mock = AsyncMock(return_value={"id": "car-2"})
    with (
        patch("routers.auto_add_vehicle_router.CarEngineV1.create_car", create_mock),
        patch(
            "services.auto_telegram_tenant.ensure_telegram_tenant_session",
            AsyncMock(return_value={"ok": True}),
        ),
        patch(
            "routers.auto_add_vehicle_router.VerticalOnboardingEngineV1.get_language",
            AsyncMock(return_value="ru"),
        ),
        patch("routers.auto_add_vehicle_router.log_audit"),
    ):
        await vin_decision_callback(cb, state)

    create_mock.assert_awaited()
    assert await state.get_state() is None


def test_resolve_new_callback_ids():
    assert resolve_vin_decision(callback_data="auto:add:vin:yes") == "yes"
    assert resolve_vin_decision(callback_data="auto:add:vin:no") == "no"
    assert resolve_vin_decision(callback_data="addcar:vin:no") == "no"


def test_startup_registers_add_vehicle_before_super_app():
    from startup import BOT_ROUTER_PATHS

    assert BOT_ROUTER_PATHS[0] == "routers.auto_add_vehicle_router"
    assert BOT_ROUTER_PATHS[1] == "routers.telegram_super_app_router"


def test_canonical_vin_question_site():
    from pathlib import Path

    src = Path("routers/auto_add_vehicle_router.py").read_text(encoding="utf-8")
    assert "Хотите добавить VIN автомобиля?" in src
    assert "auto:add:vin:yes" in Path("keyboards.py").read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_optional_skip_tokens_create_vehicle(storage):
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.base import StorageKey
    from routers.auto_add_vehicle_router import vin_decision_text

    for token in ("Нет", "2", "пропустить", "no"):
        key = StorageKey(bot_id=1, chat_id=100, user_id=100)
        state = FSMContext(storage=storage, key=key)
        await persist_add_vehicle(
            state,
            step="vin_optional",
            draft={"make": "Audi", "model": "A6", "year": 2018, "fields": {}},
        )
        msg = _msg(100, token, chat_id=100)
        create_mock = AsyncMock(return_value={"id": "c"})
        with (
            patch("routers.auto_add_vehicle_router.CarEngineV1.create_car", create_mock),
            patch(
                "services.auto_telegram_tenant.ensure_telegram_tenant_session",
                AsyncMock(return_value={"ok": True}),
            ),
            patch(
                "routers.auto_add_vehicle_router.VerticalOnboardingEngineV1.get_language",
                AsyncMock(return_value="ru"),
            ),
            patch("routers.auto_add_vehicle_router.log_audit"),
        ):
            await vin_decision_text(msg, state)
        assert create_mock.await_count == 1, token
        await clear_add_vehicle(state)


@pytest.mark.asyncio
async def test_client_sanitize_hides_score_metadata():
    from services.auto_client_output import sanitize_ai_reply_for_client

    raw = "Понял.\nScore: 10\nPriority: LOW\nDept: general\nIntent: OTHER"
    out = sanitize_ai_reply_for_client(raw, role="client")
    assert "Score" not in out
    assert "Priority" not in out
    assert "Dept" not in out
    assert "Intent" not in out
