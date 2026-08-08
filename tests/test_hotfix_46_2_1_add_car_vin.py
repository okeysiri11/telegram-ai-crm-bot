"""HOTFIX 46.2.1 — Add-vehicle VIN FSM regression tests (updated for 46.2.2 durable FSM)."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage

from services.auto_add_vehicle_vin import (
    parse_extra_costs_line,
    resolve_vin_decision,
)


@pytest.fixture(autouse=True)
def _clean_flows():
    import auto_vertical_handlers as avh

    avh.auto_vertical_flow.clear()
    yield
    avh.auto_vertical_flow.clear()


def _fsm(user_id: int) -> FSMContext:
    storage = MemoryStorage()
    key = StorageKey(bot_id=1, chat_id=user_id, user_id=user_id)
    return FSMContext(storage=storage, key=key)


def test_resolve_vin_decision_no_variants():
    for raw in ("Нет", "нет", "НЕТ", "no", "2", "-", "пропустить", "без VIN", "❌ Нет"):
        assert resolve_vin_decision(raw) == "no", raw


def test_resolve_vin_decision_yes_variants():
    for raw in ("Да", "да", "ДА", "yes", "1", "+", "✅ Да"):
        assert resolve_vin_decision(raw) == "yes", raw


def test_resolve_vin_decision_callbacks():
    assert resolve_vin_decision(callback_data="addcar:vin:no") == "no"
    assert resolve_vin_decision(callback_data="addcar:vin:yes") == "yes"
    assert resolve_vin_decision(callback_data="auto:add:vin:no") == "no"
    assert resolve_vin_decision(callback_data="auto:add:vin:yes") == "yes"


def test_parse_extra_costs_single_number():
    out = parse_extra_costs_line("100")
    assert out["delivery_cost"] == Decimal("100")


def test_parse_extra_costs_four_numbers():
    out = parse_extra_costs_line("800 1200 500 200")
    assert out["delivery_cost"] == Decimal("800")
    assert out["customs_cost"] == Decimal("1200")
    assert out["repair_cost"] == Decimal("500")
    assert out["advertising_cost"] == Decimal("200")


def test_parse_extra_costs_skip():
    assert parse_extra_costs_line("-") == {}
    assert parse_extra_costs_line("") == {}


def _msg(user_id: int, text: str):
    msg = MagicMock()
    msg.text = text
    msg.from_user = MagicMock(id=user_id)
    msg.chat = MagicMock(id=user_id)
    msg.answer = AsyncMock()
    return msg


@pytest.mark.asyncio
async def test_add_car_flow_vin_no_finalizes_and_resets():
    import auto_vertical_handlers as avh

    uid = 462101
    avh.auto_vertical_active[uid] = True
    avh.auto_vertical_flow[uid] = {
        "step": "vin_optional",
        "data": {
            "make": "BMW",
            "model": "X5",
            "year": 2002,
            "color": "Красный",
            "fields": {
                "purchase_price": Decimal("20000"),
                "delivery_cost": Decimal("100"),
                "color": "Красный",
            },
        },
    }
    msg = _msg(uid, "Нет")
    state = _fsm(uid)
    created = {
        "id": "11111111-1111-1111-1111-111111111111",
        "make": "BMW",
        "model": "X5",
        "year": 2002,
        "vin": None,
    }
    create_mock = AsyncMock(return_value=created)

    with patch.object(avh, "_user_lang", AsyncMock(return_value="ru")), patch(
        "routers.auto_add_vehicle_router.CarEngineV1.create_car", create_mock
    ), patch(
        "services.auto_telegram_tenant.ensure_telegram_tenant_session",
        AsyncMock(return_value={"ok": True}),
    ), patch(
        "routers.auto_add_vehicle_router.VerticalOnboardingEngineV1.get_language",
        AsyncMock(return_value="ru"),
    ), patch("routers.auto_add_vehicle_router.log_audit"), patch.object(avh, "log_audit"):
        await avh.auto_vertical_flow_handler(msg, state)

    assert uid not in avh.auto_vertical_flow
    answers = [c.args[0] for c in msg.answer.call_args_list if c.args]
    assert any("VIN: не указан" in a or "без VIN" in a for a in answers)
    assert create_mock.await_count == 1
    kwargs = create_mock.await_args.kwargs
    assert kwargs.get("vin") is None
    assert kwargs.get("make") == "BMW"
    assert kwargs.get("model") == "X5"
    assert kwargs.get("year") == 2002


@pytest.mark.asyncio
async def test_add_car_flow_vin_2_same_as_no():
    import auto_vertical_handlers as avh

    uid = 462102
    avh.auto_vertical_active[uid] = True
    avh.auto_vertical_flow[uid] = {
        "step": "vin_optional",
        "data": {"make": "BMW", "model": "X5", "year": 2002, "fields": {}},
    }
    msg = _msg(uid, "2")
    state = _fsm(uid)
    create_mock = AsyncMock(
        return_value={"id": "22222222-2222-2222-2222-222222222222", "make": "BMW", "model": "X5"}
    )

    with patch.object(avh, "_user_lang", AsyncMock(return_value="ru")), patch(
        "routers.auto_add_vehicle_router.CarEngineV1.create_car", create_mock
    ), patch(
        "services.auto_telegram_tenant.ensure_telegram_tenant_session",
        AsyncMock(return_value={"ok": True}),
    ), patch(
        "routers.auto_add_vehicle_router.VerticalOnboardingEngineV1.get_language",
        AsyncMock(return_value="ru"),
    ), patch("routers.auto_add_vehicle_router.log_audit"), patch.object(avh, "log_audit"):
        await avh.auto_vertical_flow_handler(msg, state)

    assert uid not in avh.auto_vertical_flow
    assert create_mock.await_count == 1
    assert create_mock.await_args.kwargs.get("vin") is None


@pytest.mark.asyncio
async def test_add_car_flow_vin_yes_asks_vin():
    import auto_vertical_handlers as avh

    uid = 462103
    avh.auto_vertical_active[uid] = True
    avh.auto_vertical_flow[uid] = {
        "step": "vin_optional",
        "data": {"make": "BMW", "model": "X5", "year": 2002, "fields": {}},
    }
    msg = _msg(uid, "Да")
    await avh._handle_add_car_vin_decision(
        msg, uid, decision="yes", input_normalized="да"
    )
    assert avh.auto_vertical_flow[uid]["step"] == "vin_input"
    assert "Отправьте VIN" in msg.answer.call_args.args[0]
    assert avh.auto_vertical_flow[uid]["data"]["make"] == "BMW"


@pytest.mark.asyncio
async def test_add_car_flow_vin_1_same_as_yes():
    import auto_vertical_handlers as avh
    from services.auto_add_vehicle_vin import resolve_vin_decision

    assert resolve_vin_decision("1") == "yes"
    uid = 462104
    avh.auto_vertical_active[uid] = True
    avh.auto_vertical_flow[uid] = {
        "step": "vin_optional",
        "data": {"make": "BMW", "model": "X5", "year": 2002, "fields": {}},
    }
    msg = _msg(uid, "1")
    await avh._handle_add_car_vin_decision(
        msg, uid, decision=resolve_vin_decision("1"), input_normalized="1"
    )
    assert avh.auto_vertical_flow[uid]["step"] == "vin_input"


@pytest.mark.asyncio
async def test_add_car_flow_skip_token_creates():
    import auto_vertical_handlers as avh

    uid = 462108
    avh.auto_vertical_active[uid] = True
    avh.auto_vertical_flow[uid] = {
        "step": "vin_optional",
        "data": {"make": "BMW", "model": "X5", "year": 2002, "fields": {}},
    }
    msg = _msg(uid, "Пропустить")
    state = _fsm(uid)
    create_mock = AsyncMock(
        return_value={"id": "55555555-5555-5555-5555-555555555555", "make": "BMW", "model": "X5"}
    )
    with patch.object(avh, "_user_lang", AsyncMock(return_value="ru")), patch(
        "routers.auto_add_vehicle_router.CarEngineV1.create_car", create_mock
    ), patch(
        "services.auto_telegram_tenant.ensure_telegram_tenant_session",
        AsyncMock(return_value={"ok": True}),
    ), patch(
        "routers.auto_add_vehicle_router.VerticalOnboardingEngineV1.get_language",
        AsyncMock(return_value="ru"),
    ), patch("routers.auto_add_vehicle_router.log_audit"), patch.object(avh, "log_audit"):
        await avh.auto_vertical_flow_handler(msg, state)
    assert uid not in avh.auto_vertical_flow
    assert create_mock.await_args.kwargs.get("vin") is None


@pytest.mark.asyncio
async def test_add_car_flow_vin_provided_creates():
    import auto_vertical_handlers as avh

    uid = 462105
    avh.auto_vertical_active[uid] = True
    avh.auto_vertical_flow[uid] = {
        "step": "vin_input",
        "data": {"make": "BMW", "model": "X5", "year": 2002, "fields": {}},
    }
    msg = _msg(uid, "WBAFR7C50CC811234")
    state = _fsm(uid)
    create_mock = AsyncMock(
        return_value={
            "id": "33333333-3333-3333-3333-333333333333",
            "make": "BMW",
            "model": "X5",
            "vin": "WBAFR7C50CC811234",
        }
    )
    with patch(
        "routers.auto_add_vehicle_router.validate_vin",
        return_value={"is_valid": True, "vin": "WBAFR7C50CC811234", "errors": []},
    ), patch.object(avh, "_user_lang", AsyncMock(return_value="ru")), patch(
        "routers.auto_add_vehicle_router.CarEngineV1.create_car", create_mock
    ), patch(
        "services.auto_telegram_tenant.ensure_telegram_tenant_session",
        AsyncMock(return_value={"ok": True}),
    ), patch(
        "routers.auto_add_vehicle_router.AutoVerticalService.record_vin_intake",
        AsyncMock(),
    ), patch(
        "routers.auto_add_vehicle_router.VerticalOnboardingEngineV1.get_language",
        AsyncMock(return_value="ru"),
    ), patch("routers.auto_add_vehicle_router.log_audit"), patch.object(avh, "log_audit"):
        await avh.auto_vertical_flow_handler(msg, state)

    assert uid not in avh.auto_vertical_flow
    assert create_mock.await_args.kwargs["vin"] == "WBAFR7C50CC811234"
    assert any("добавлен" in c.args[0] for c in msg.answer.call_args_list if c.args)


@pytest.mark.asyncio
async def test_after_vin_no_state_cleared_for_new_command():
    import auto_vertical_handlers as avh

    uid = 462106
    avh.auto_vertical_active[uid] = True
    avh.auto_vertical_flow[uid] = {
        "step": "vin_optional",
        "data": {"make": "BMW", "model": "X5", "year": 2002, "fields": {}},
    }
    msg = _msg(uid, "Нет")
    state = _fsm(uid)
    with patch.object(avh, "_user_lang", AsyncMock(return_value="ru")), patch(
        "routers.auto_add_vehicle_router.CarEngineV1.create_car",
        AsyncMock(return_value={"id": "44444444-4444-4444-4444-444444444444", "make": "BMW", "model": "X5"}),
    ), patch(
        "services.auto_telegram_tenant.ensure_telegram_tenant_session",
        AsyncMock(return_value={"ok": True}),
    ), patch(
        "routers.auto_add_vehicle_router.VerticalOnboardingEngineV1.get_language",
        AsyncMock(return_value="ru"),
    ), patch("routers.auto_add_vehicle_router.log_audit"), patch.object(avh, "log_audit"):
        await avh.auto_vertical_flow_handler(msg, state)
    assert not avh.auto_vertical_flow.get(uid)


@pytest.mark.asyncio
async def test_finalize_preserves_draft_on_tenant_error():
    import auto_vertical_handlers as avh

    uid = 462107
    data = {
        "make": "BMW",
        "model": "X5",
        "year": 2002,
        "fields": {"purchase_price": Decimal("20000")},
    }
    avh.auto_vertical_flow[uid] = {"step": "vin_optional", "data": data}
    msg = MagicMock()
    msg.answer = AsyncMock()

    with patch.object(avh, "_user_lang", AsyncMock(return_value="ru")), patch(
        "services.auto_telegram_tenant.ensure_telegram_tenant_session",
        AsyncMock(return_value={"ok": False, "message_ru": "Не удалось определить организацию."}),
    ):
        ok = await avh._finalize_add_car(msg, uid, data)

    assert ok is False
    assert avh.auto_vertical_flow[uid]["step"] == "finalize_retry"
    assert avh.auto_vertical_flow[uid]["data"]["make"] == "BMW"
    assert avh.auto_vertical_flow[uid]["data"]["fields"]["purchase_price"] == Decimal("20000")
