"""HOTFIX 46.2.2 — Auto Add Vehicle Telegram router (FSM-first, before Super App / AI).

Production path for «🚗 Добавить авто».
Deterministic form — never LLM.
"""

from __future__ import annotations

import logging
import uuid
from decimal import Decimal, InvalidOperation
from typing import Any

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from keyboards import (
    auto_add_car_after_create_inline,
    auto_add_car_vin_inline,
    auto_add_car_vin_skip_inline,
    auto_vertical_menu,
)
from services.auto_add_vehicle_flow import (
    FLOW_NAME,
    clear_add_vehicle,
    clear_process_flow,
    format_vehicle_created_ru,
    mirror_process_flow,
    persist_add_vehicle,
)
from services.auto_add_vehicle_vin import resolve_vin_decision
from services.handler_auth import log_audit
from services.pg_car_engine import CarEngineError, CarEngineV1
from services.pg_vertical_onboarding_engine import VerticalOnboardingEngineV1
from services.vin_decoder import validate_vin
from src.verticals.auto.service import AutoVerticalService
from states.entry_flow_states import AutoAddVehicleFlow

logger = logging.getLogger(__name__)

router = Router(name="auto_add_vehicle")

# Test / diagnostic counters (reset in tests)
AI_ROUTER_BLOCK_COUNT = 0
GENERAL_AI_CALLS_DURING_FSM = 0


def _diag(
    *,
    user_id: int | None,
    chat_id: int | None,
    text: str | None,
    callback_data: str | None,
    active_flow: str | None,
    active_state: str | None,
    handler_selected: str,
    router_selected: str = "auto_add_vehicle",
) -> None:
    logger.info(
        "TELEGRAM_UPDATE user_id=%s chat_id=%s text=%r callback_data=%r "
        "active_flow=%s active_state=%s handler_selected=%s router_selected=%s",
        user_id,
        chat_id,
        text,
        callback_data,
        active_flow,
        active_state,
        handler_selected,
        router_selected,
    )


async def _lang(user_id: int) -> str:
    return await VerticalOnboardingEngineV1.get_language(user_id)


async def start_add_vehicle(message: Message, state: FSMContext, user_id: int) -> None:
    """Entry from Auto vertical menu — clears competing Super App / AI FSM."""
    await state.clear()
    draft: dict[str, Any] = {}
    await persist_add_vehicle(state, step="make", draft=draft)
    mirror_process_flow(user_id, "make", draft)
    _diag(
        user_id=user_id,
        chat_id=message.chat.id if message.chat else None,
        text=message.text,
        callback_data=None,
        active_flow=FLOW_NAME,
        active_state="MAKE",
        handler_selected="start_add_vehicle",
    )
    await message.answer(
        "🚗 Добавить авто\n\nУкажите марку автомобиля:",
        reply_markup=auto_vertical_menu(await _lang(user_id)),
    )


async def _draft(state: FSMContext) -> dict[str, Any]:
    data = await state.get_data()
    return dict(data.get("draft") or {})


async def _set_step(state: FSMContext, user_id: int, step: str, draft: dict[str, Any]) -> None:
    await persist_add_vehicle(state, step=step, draft=draft)
    mirror_process_flow(user_id, step, draft)


async def _finalize(message: Message, state: FSMContext, user_id: int, draft: dict[str, Any]) -> bool:
    from services.auto_client_output import user_facing_tenant_error_ru
    from services.auto_telegram_tenant import ensure_telegram_tenant_session

    fields = dict(draft.get("fields") or {})
    fields.pop("extra_costs_total", None)
    vin = draft.get("vin")
    make = draft.get("make") or "Авто"
    model = draft.get("model") or "—"
    year = draft.get("year") or 0

    try:
        tenant = await ensure_telegram_tenant_session(user_id)
        if not tenant.get("ok"):
            await _set_step(state, user_id, "finalize_retry", draft)
            await message.answer(
                tenant.get("message_ru") or user_facing_tenant_error_ru(),
                reply_markup=auto_vertical_menu(await _lang(user_id)),
            )
            return False
    except Exception:
        logger.warning("AUTO_ADD tenant ensure failed user=%s", user_id, exc_info=True)

    try:
        car = await CarEngineV1.create_car(
            user_id,
            vin=vin,
            make=make,
            model=model,
            year=int(year) if year else 0,
            **fields,
        )
    except (CarEngineError, PermissionError) as exc:
        await _set_step(state, user_id, "finalize_retry", draft)
        msg = user_facing_tenant_error_ru() if isinstance(exc, PermissionError) else f"❌ Не удалось сохранить: {exc}"
        await message.answer(msg, reply_markup=auto_vertical_menu(await _lang(user_id)))
        return False
    except Exception:
        logger.exception("AUTO_ADD create failed user=%s", user_id)
        await _set_step(state, user_id, "finalize_retry", draft)
        await message.answer(
            "❌ Не удалось сохранить автомобиль. Данные сохранены — напишите «сохранить».",
            reply_markup=auto_vertical_menu(await _lang(user_id)),
        )
        return False

    if vin:
        try:
            await AutoVerticalService.record_vin_intake(
                vin=vin,
                car_id=uuid.UUID(car["id"]),
                created_by=user_id,
            )
        except Exception:
            logger.debug("VIN intake skipped", exc_info=True)

    await clear_add_vehicle(state)
    clear_process_flow(user_id)
    await message.answer(
        format_vehicle_created_ru(draft, vin=vin),
        reply_markup=auto_add_car_after_create_inline(car.get("id")),
    )
    await message.answer(
        "Автомобиль в списке. Фото можно добавить позже — это необязательно.",
        reply_markup=auto_vertical_menu(await _lang(user_id)),
    )
    log_audit(user_id, "create", "auto_vertical", vin or car["id"])
    logger.info("AUTO_ADD COMPLETED user=%s vehicle_id=%s vin=%s", user_id, car.get("id"), bool(vin))
    return True


async def handle_vin_yes(message: Message, state: FSMContext, user_id: int) -> None:
    draft = await _draft(state)
    await _set_step(state, user_id, "vin_input", draft)
    _diag(
        user_id=user_id,
        chat_id=message.chat.id if message.chat else None,
        text=None,
        callback_data=None,
        active_flow=FLOW_NAME,
        active_state="WAITING_VIN",
        handler_selected="handle_vin_yes",
    )
    await message.answer(
        "Отправьте VIN автомобиля.",
        reply_markup=auto_add_car_vin_skip_inline(),
    )


async def handle_vin_no(message: Message, state: FSMContext, user_id: int) -> None:
    draft = await _draft(state)
    draft["vin"] = None
    await state.update_data(active_flow=FLOW_NAME, active_state="VIN_NO", draft=draft)
    mirror_process_flow(user_id, "vin_optional", draft)
    _diag(
        user_id=user_id,
        chat_id=message.chat.id if message.chat else None,
        text=None,
        callback_data=None,
        active_flow=FLOW_NAME,
        active_state="VIN_NO",
        handler_selected="handle_vin_no",
    )
    await _finalize(message, state, user_id, draft)


# --- Form steps ---


@router.message(StateFilter(AutoAddVehicleFlow.make), F.text)
async def step_make(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    text = (message.text or "").strip()
    _diag(
        user_id=user_id,
        chat_id=message.chat.id,
        text=text,
        callback_data=None,
        active_flow=FLOW_NAME,
        active_state="MAKE",
        handler_selected="step_make",
    )
    if not text:
        await message.answer("Укажите марку автомобиля:")
        return
    draft = await _draft(state)
    draft["make"] = text
    await _set_step(state, user_id, "model", draft)
    await message.answer("Укажите модель:")


@router.message(StateFilter(AutoAddVehicleFlow.model), F.text)
async def step_model(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    text = (message.text or "").strip()
    if not text:
        await message.answer("Укажите модель:")
        return
    draft = await _draft(state)
    draft["model"] = text
    await _set_step(state, user_id, "year", draft)
    await message.answer("Укажите год выпуска:")


@router.message(StateFilter(AutoAddVehicleFlow.year), F.text)
async def step_year(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    text = (message.text or "").strip()
    if not text.isdigit() or len(text) != 4:
        await message.answer("Укажите год четырёхзначным числом (например 2022):")
        return
    draft = await _draft(state)
    draft["year"] = int(text)
    await _set_step(state, user_id, "color", draft)
    await message.answer("Укажите цвет (или «-» чтобы пропустить):")


@router.message(StateFilter(AutoAddVehicleFlow.color), F.text)
async def step_color(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    text = (message.text or "").strip()
    draft = await _draft(state)
    if text != "-":
        draft["color"] = text
    await _set_step(state, user_id, "mileage", draft)
    await message.answer("Укажите пробег в км (или «-» чтобы пропустить):")


@router.message(StateFilter(AutoAddVehicleFlow.mileage), F.text)
async def step_mileage(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    text = (message.text or "").strip()
    draft = await _draft(state)
    if text != "-":
        digits = "".join(ch for ch in text if ch.isdigit())
        if not digits:
            await message.answer("Укажите пробег числом или «-»:")
            return
        draft["mileage"] = int(digits)
    await _set_step(state, user_id, "purchase_price", draft)
    await message.answer("Введите цену закупки (число) или «-» чтобы пропустить:")


@router.message(StateFilter(AutoAddVehicleFlow.purchase_price), F.text)
async def step_purchase_price(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    text = (message.text or "").strip()
    draft = await _draft(state)
    fields: dict[str, Any] = {}
    if text != "-":
        try:
            fields["purchase_price"] = Decimal(text.replace(",", "."))
        except InvalidOperation:
            await message.answer("Введите число или «-»:")
            return
    if draft.get("color"):
        fields["color"] = draft["color"]
    if draft.get("mileage") is not None:
        fields["mileage"] = draft["mileage"]
    draft["fields"] = fields
    await _set_step(state, user_id, "optional_costs", draft)
    await message.answer(
        "Доп. расходы одной строкой через пробел "
        "(delivery customs repair advertising) или «-»:\n"
        "Пример: 800 1200 500 200\n"
        "Можно одно число, например: 100"
    )


@router.message(StateFilter(AutoAddVehicleFlow.optional_costs), F.text)
async def step_optional_costs(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    text = (message.text or "").strip()
    from services.auto_add_vehicle_vin import parse_extra_costs_line

    draft = await _draft(state)
    fields = dict(draft.get("fields") or {})
    try:
        fields.update(parse_extra_costs_line(text))
    except ValueError:
        await message.answer("Введите до 4 чисел или «-»:")
        return
    draft["fields"] = fields
    await _set_step(state, user_id, "vin_optional", draft)
    _diag(
        user_id=user_id,
        chat_id=message.chat.id,
        text=text,
        callback_data=None,
        active_flow=FLOW_NAME,
        active_state="VIN_DECISION",
        handler_selected="step_optional_costs→vin_decision",
    )
    await message.answer(
        "Хотите добавить VIN автомобиля?",
        reply_markup=auto_add_car_vin_inline(),
    )


@router.message(StateFilter(AutoAddVehicleFlow.vin_decision), F.text)
async def vin_decision_text(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    text = (message.text or "").strip()
    decision = resolve_vin_decision(text)
    _diag(
        user_id=user_id,
        chat_id=message.chat.id,
        text=text,
        callback_data=None,
        active_flow=FLOW_NAME,
        active_state="VIN_DECISION",
        handler_selected=f"vin_decision_text:{decision}",
    )
    if decision == "yes":
        await handle_vin_yes(message, state, user_id)
        return
    if decision == "no":
        await handle_vin_no(message, state, user_id)
        return
    await message.answer(
        "Хотите добавить VIN автомобиля?",
        reply_markup=auto_add_car_vin_inline(),
    )


@router.message(StateFilter(AutoAddVehicleFlow.waiting_vin), F.text)
async def waiting_vin_text(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    text = (message.text or "").strip()
    decision = resolve_vin_decision(text)
    _diag(
        user_id=user_id,
        chat_id=message.chat.id,
        text=text,
        callback_data=None,
        active_flow=FLOW_NAME,
        active_state="WAITING_VIN",
        handler_selected=f"waiting_vin_text:{decision or 'vin'}",
    )
    if decision == "no":
        await handle_vin_no(message, state, user_id)
        return
    result = validate_vin(text)
    if not result["is_valid"]:
        await message.answer(
            "VIN выглядит некорректно. Проверьте его или нажмите «Пропустить».",
            reply_markup=auto_add_car_vin_skip_inline(),
        )
        return
    draft = await _draft(state)
    draft["vin"] = result["vin"]
    await _finalize(message, state, user_id, draft)


@router.message(StateFilter(AutoAddVehicleFlow.finalize_retry), F.text)
async def finalize_retry_text(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    text = (message.text or "").strip().lower()
    draft = await _draft(state)
    if text in {"сохранить", "повторить", "да", "ок", "нет", "2", "пропустить"}:
        if text in {"нет", "2", "пропустить"}:
            draft["vin"] = None
        await _finalize(message, state, user_id, draft)
        return
    await message.answer(
        "Черновик сохранён. Напишите «сохранить», чтобы создать автомобиль.",
        reply_markup=auto_vertical_menu(await _lang(user_id)),
    )


@router.callback_query(F.data.in_({"auto:add:vin:yes", "auto:add:vin:no", "addcar:vin:yes", "addcar:vin:no"}))
async def vin_decision_callback(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    user_id = callback.from_user.id
    data = callback.data or ""
    decision = resolve_vin_decision(callback_data=data)
    current = await state.get_state()
    # Recover draft from process mirror if FSM somehow empty (should not happen)
    if not current or not current.startswith("AutoAddVehicleFlow:"):
        try:
            import auto_vertical_handlers as avh

            flow = avh.auto_vertical_flow.get(user_id)
            if flow and flow.get("step") in {"vin_optional", "vin_input", "finalize_retry"}:
                step = "vin_optional" if flow["step"] == "vin_optional" else flow["step"]
                await persist_add_vehicle(state, step=step, draft=flow.get("data") or {})
            else:
                await callback.answer("Сессия формы истекла. Начните «Добавить авто» снова.", show_alert=True)
                return
        except Exception:
            await callback.answer("Сессия формы истекла. Начните «Добавить авто» снова.", show_alert=True)
            return

    _diag(
        user_id=user_id,
        chat_id=callback.message.chat.id if callback.message.chat else None,
        text=None,
        callback_data=data,
        active_flow=FLOW_NAME,
        active_state="VIN_DECISION",
        handler_selected=f"vin_decision_callback:{decision}",
    )
    await callback.answer()
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    if decision == "yes":
        await handle_vin_yes(callback.message, state, user_id)
    elif decision == "no":
        await handle_vin_no(callback.message, state, user_id)
    else:
        await callback.message.answer(
            "Хотите добавить VIN автомобиля?",
            reply_markup=auto_add_car_vin_inline(),
        )


@router.callback_query(F.data == "addcar:menu")
async def addcar_menu_callback(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or callback.message is None:
        await callback.answer()
        return
    user_id = callback.from_user.id
    await clear_add_vehicle(state)
    clear_process_flow(user_id)
    from auto_vertical_handlers import _return_to_cars_menu

    await _return_to_cars_menu(callback.message, user_id)
    await callback.answer()


@router.callback_query(F.data.startswith("addcar:photos:"))
async def addcar_photos_callback(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    await callback.message.answer(
        "Пришлите фото через карточку авто позже. Сейчас автомобиль уже сохранён.",
        reply_markup=auto_vertical_menu(await _lang(callback.from_user.id)),
    )
    await callback.answer()
