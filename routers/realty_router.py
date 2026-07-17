# Realty vertical router — rent / buy / sell / new builds / property management.

from __future__ import annotations

import logging
from typing import Any

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from services.media_service import media_service
from services.realty_flow_engine import (
    FLOW_STEPS,
    OBJECT_TYPES,
    SCENARIO_BUY,
    SCENARIO_LABELS,
    SCENARIO_MANAGEMENT,
    SCENARIO_NEW_BUILD,
    SCENARIO_RENT,
    SCENARIO_SELL,
    build_description,
    first_step,
    next_step,
    pending_key,
    step_prompt,
    submit_realty_request,
    validate_text_step,
)
from states.realty_flow_states import REALTY_PENDING_RESTORE, RealtyFlow

logger = logging.getLogger(__name__)

router = Router(name="realty")

PHOTOS_DONE = "realty:photos:done"
PHOTOS_SKIP = "realty:photos:skip"
BACK_TO_MENU = "realty:menu"
REALTY_PREFIX = "realty:"


def _main_menu_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=label, callback_data=f"{REALTY_PREFIX}scenario:{code}")]
        for code, label in SCENARIO_LABELS.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _object_type_keyboard(scenario: str) -> InlineKeyboardMarkup:
    types = OBJECT_TYPES.get(scenario, {})
    rows = [
        [InlineKeyboardButton(text=label, callback_data=f"{REALTY_PREFIX}object:{scenario}:{code}")]
        for code, label in types.items()
    ]
    rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data=BACK_TO_MENU)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _photos_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Готово", callback_data=PHOTOS_DONE),
                InlineKeyboardButton(text="Пропустить", callback_data=PHOTOS_SKIP),
            ]
        ]
    )


async def _show_menu(message: Message, state: FSMContext) -> None:
    await state.set_state(RealtyFlow.menu)
    await message.answer(
        "🏠 Недвижимость\n\nВыберите сценарий:",
        reply_markup=_main_menu_keyboard(),
    )


async def _restore_realty_fsm(message: Message, state: FSMContext, pending: str) -> bool:
    mapping = REALTY_PENDING_RESTORE.get(pending)
    if mapping is None:
        return False
    fsm_state, scenario = mapping
    step = pending.rsplit(":", 1)[-1]
    await state.set_state(fsm_state)
    await state.update_data(scenario=scenario, flow_step=step)
    await message.answer(step_prompt(scenario or "", step))
    if step == "photos":
        await message.answer("Можно отправить несколько фото.", reply_markup=_photos_keyboard())
    return True


async def _persist_pending(state: FSMContext) -> None:
    data = await state.get_data()
    scenario = data.get("scenario")
    step = data.get("flow_step")
    if scenario and step:
        await state.update_data(realty_pending=pending_key(scenario, step))


async def _start_flow(callback: CallbackQuery, state: FSMContext, scenario: str, object_type: str) -> None:
    step = first_step(scenario)
    if step is None or callback.message is None:
        await callback.answer("Сценарий недоступен", show_alert=True)
        return

    await state.set_state(RealtyFlow.collecting)
    await state.update_data(
        scenario=scenario,
        object_type=object_type,
        flow_step=step,
        photo_file_ids=[],
        realty_pending=pending_key(scenario, step),
    )
    await callback.message.answer(
        f"{SCENARIO_LABELS[scenario]} — {OBJECT_TYPES[scenario][object_type]}\n\n"
        f"{step_prompt(scenario, step)}"
    )
    await callback.answer()


async def _advance_text_step(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    scenario = data.get("scenario")
    step = data.get("flow_step")
    if not scenario or not step:
        await _show_menu(message, state)
        return

    ok, err, value = validate_text_step(step, message.text or "")
    if not ok:
        await message.answer(err or "Некорректное значение.")
        return

    await state.update_data(**{step: value})
    nxt = next_step(scenario, step)
    if nxt is None:
        await _finish_request(message, state)
        return

    await state.update_data(flow_step=nxt, realty_pending=pending_key(scenario, nxt))
    if nxt == "photos":
        await state.set_state(RealtyFlow.awaiting_photos)
        await message.answer(step_prompt(scenario, nxt), reply_markup=_photos_keyboard())
        return
    if nxt == "contact":
        await state.set_state(RealtyFlow.awaiting_contact)
        await message.answer(step_prompt(scenario, nxt))
        return

    await state.set_state(RealtyFlow.collecting)
    await message.answer(step_prompt(scenario, nxt))


async def _finish_request(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    scenario = data.get("scenario")
    if not scenario:
        await _show_menu(message, state)
        return

    user = message.from_user
    try:
        result = await submit_realty_request(
            scenario=scenario,
            data=data,
            client_telegram_id=user.id if user else 0,
            client_name=(user.full_name if user else "") or "",
            client_username=user.username if user else None,
        )
    except Exception:
        logger.exception("Realty request submit failed user=%s", user.id if user else None)
        await message.answer("Не удалось создать заявку. Попробуйте позже.")
        return

    await state.clear()
    request_number = result.get("request_number", "—")
    await message.answer(
        f"✅ Заявка #{request_number} создана.\n"
        f"Менеджер свяжется с вами.\n\n"
        f"{build_description(scenario, data)}"
    )


@router.message(Command("start_realty"))
async def cmd_start_realty(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    pending = data.get("realty_pending")
    if pending and await _restore_realty_fsm(message, state, pending):
        return
    await _show_menu(message, state)


@router.callback_query(F.data == BACK_TO_MENU)
async def realty_back_to_menu(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        await callback.answer()
        return
    await _show_menu(callback.message, state)
    await callback.answer()


@router.callback_query(F.data.startswith(f"{REALTY_PREFIX}scenario:"))
async def realty_pick_scenario(callback: CallbackQuery, state: FSMContext) -> None:
    scenario = (callback.data or "").split(":", 2)[-1]
    if scenario not in SCENARIO_LABELS or callback.message is None:
        await callback.answer("Неизвестный сценарий", show_alert=True)
        return
    await callback.message.answer(
        f"{SCENARIO_LABELS[scenario]} — выберите тип объекта:",
        reply_markup=_object_type_keyboard(scenario),
    )
    await callback.answer()


@router.callback_query(F.data.startswith(f"{REALTY_PREFIX}object:"))
async def realty_pick_object(callback: CallbackQuery, state: FSMContext) -> None:
    parts = (callback.data or "").split(":")
    if len(parts) < 4:
        await callback.answer("Некорректный выбор", show_alert=True)
        return
    scenario, object_type = parts[2], parts[3]
    if scenario not in OBJECT_TYPES or object_type not in OBJECT_TYPES[scenario]:
        await callback.answer("Некорректный тип объекта", show_alert=True)
        return
    await _start_flow(callback, state, scenario, object_type)


@router.message(StateFilter(RealtyFlow.collecting), F.text)
async def realty_collect_text(message: Message, state: FSMContext) -> None:
    await _persist_pending(state)
    await _advance_text_step(message, state)


@router.message(StateFilter(RealtyFlow.awaiting_contact), F.text)
async def realty_collect_contact(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    scenario = data.get("scenario")
    ok, err, value = validate_text_step("contact", message.text or "")
    if not ok:
        await message.answer(err or "Некорректный контакт.")
        return
    await state.update_data(contact=value)
    await _finish_request(message, state)


@router.message(StateFilter(RealtyFlow.awaiting_contact), F.contact)
async def realty_collect_contact_shared(message: Message, state: FSMContext) -> None:
    if message.contact and message.contact.phone_number:
        await state.update_data(contact=message.contact.phone_number)
        await _finish_request(message, state)


@router.message(StateFilter(RealtyFlow.awaiting_photos), F.photo)
async def realty_collect_photo(message: Message, state: FSMContext) -> None:
    if not message.photo:
        return
    file_id = message.photo[-1].file_id
    try:
        await media_service.store_telegram_file(file_id=file_id, destination=f"realty/{file_id}")
    except Exception:
        logger.debug("Realty photo store skipped file_id=%s", file_id, exc_info=True)

    data = await state.get_data()
    photos = list(data.get("photo_file_ids") or [])
    if file_id not in photos:
        photos.append(file_id)
    await state.update_data(photo_file_ids=photos)
    await _persist_pending(state)
    await message.answer(f"Фото добавлено ({len(photos)}). Можно отправить ещё или нажать «Готово».")


@router.callback_query(StateFilter(RealtyFlow.awaiting_photos), F.data.in_({PHOTOS_DONE, PHOTOS_SKIP}))
async def realty_photos_done(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        await callback.answer()
        return
    data = await state.get_data()
    scenario = data.get("scenario")
    if not scenario:
        await _show_menu(callback.message, state)
        await callback.answer()
        return

    nxt = next_step(scenario, "photos")
    if nxt is None:
        await _finish_request(callback.message, state)
        await callback.answer()
        return

    await state.update_data(flow_step=nxt, realty_pending=pending_key(scenario, nxt))
    if nxt == "contact":
        await state.set_state(RealtyFlow.awaiting_contact)
        await callback.message.answer(step_prompt(scenario, nxt))
    else:
        await state.set_state(RealtyFlow.collecting)
        await callback.message.answer(step_prompt(scenario, nxt))
    await callback.answer()


async def restore_realty_fsm_from_pending(message: Message, state: FSMContext, pending: str) -> bool:
    """Public helper for FSM recovery after bot restart."""
    return await _restore_realty_fsm(message, state, pending)
