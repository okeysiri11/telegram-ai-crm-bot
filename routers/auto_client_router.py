# Auto Client entry router — /start_auto_client command and menu flow.

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from keyboards import (
    auto_client_menu,
    auto_client_phone_keyboard,
    auto_client_photos_inline,
    auto_client_vin_inline,
    entry_flow_language_inline,
)
from routers.auto_hub_router import open_auto_client_services, return_auto_client_menu
from services.auto_client_flow_engine import (
    CAR_FLOW_TYPES,
    REQUEST_BUY,
    REQUEST_LISTING,
    REQUEST_MANAGER,
    REQUEST_SELL,
    REQUEST_SERVICES,
    build_description,
    first_step,
    next_step,
    pending_key,
    step_prompt,
    validate_text_step,
    vin_present,
)
from services.automotive_localization import btn, is_back_button, normalize_language, t
from services.entry_point_routing import (
    EntryPoint,
    FlowState,
    is_auto_client_interrupt_text,
    is_auto_client_menu_text,
)
from services.pg_auto_client_request_engine import AutoClientRequestEngineV1
from services.pg_entry_point_engine import EntryPointEngineV1
from services.pg_vertical_onboarding_engine import VerticalOnboardingEngineV1
from states.entry_flow_states import AUTO_CLIENT_PENDING_RESTORE, AutoClientFlow

logger = logging.getLogger(__name__)

router = Router()

LANGUAGE_PICKER_TEXT = "🇺🇦 Выберите язык"


async def _restore_auto_client_fsm(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return
    pending = await VerticalOnboardingEngineV1.get_auto_client_pending(message.from_user.id)
    if not pending:
        return
    mapping = AUTO_CLIENT_PENDING_RESTORE.get(pending)
    if mapping is None:
        return
    fsm_state, flow_type = mapping
    flow_step = pending.rsplit(":", 1)[-1]
    await state.set_state(fsm_state)
    await state.update_data(flow_type=flow_type, flow_step=flow_step)
    logger.info(
        "AUTO_CLIENT FSM restored pending=%s state=%s user=%s",
        pending,
        fsm_state.state,
        message.from_user.id,
    )


async def _ensure_auto_client(message: Message) -> bool:
    if message.from_user is None:
        logger.info("AUTO_CLIENT skip: message has no from_user")
        return False
    ctx = await EntryPointEngineV1.get_flow_context(message.from_user.id)
    entry_point = ctx.get("entry_point")
    source_link = ctx.get("source_link")
    if entry_point == EntryPoint.AUTO_CLIENT.value or source_link == "auto_client":
        return True
    logger.info(
        "AUTO_CLIENT skip: user=%s entry_point=%s source_link=%s",
        message.from_user.id,
        entry_point,
        source_link,
    )
    return False


async def _sync_auto_client_menu_state(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return
    ctx = await EntryPointEngineV1.get_flow_context(message.from_user.id)
    if ctx.get("entry_point") != EntryPoint.AUTO_CLIENT.value and ctx.get("source_link") != "auto_client":
        return
    current = await state.get_state()
    if current is None and ctx.get("current_flow") == FlowState.AUTO_CLIENT_MENU.value:
        await state.set_state(AutoClientFlow.menu)
        logger.info("AUTO_CLIENT FSM synced to menu for user=%s", message.from_user.id)
    await _restore_auto_client_fsm(message, state)


async def _save_flow_pending(user_id: int, flow_type: str, flow_step: str) -> None:
    await VerticalOnboardingEngineV1.save_auto_client_pending(
        telegram_user_id=user_id,
        pending=pending_key(flow_type, flow_step),
    )


async def _set_flow_step(
    message: Message,
    state: FSMContext,
    *,
    flow_type: str,
    flow_step: str,
) -> None:
    user_id = message.from_user.id
    lang = await VerticalOnboardingEngineV1.get_language(user_id)
    await _save_flow_pending(user_id, flow_type, flow_step)

    if flow_step == "photos":
        await state.set_state(AutoClientFlow.awaiting_photos)
        await message.answer(
            step_prompt(flow_type, flow_step),
            reply_markup=auto_client_menu(lang),
        )
        await message.answer("Или пропустите фото:", reply_markup=auto_client_photos_inline())
        return

    if flow_step == "vin_optional":
        await state.set_state(AutoClientFlow.awaiting_vin)
        await message.answer(
            step_prompt(flow_type, flow_step),
            reply_markup=auto_client_vin_inline(),
        )
        return

    if flow_step == "phone":
        await state.set_state(AutoClientFlow.awaiting_phone)
        await message.answer(
            step_prompt(flow_type, flow_step),
            reply_markup=auto_client_phone_keyboard(lang),
        )
        return

    await state.set_state(AutoClientFlow.collecting)
    await message.answer(step_prompt(flow_type, flow_step), reply_markup=auto_client_menu(lang))


async def _start_flow(message: Message, state: FSMContext, flow_type: str, **extra: object) -> None:
    step = first_step(flow_type)
    if step is None:
        return
    await state.update_data(
        flow_type=flow_type,
        flow_step=step,
        photo_file_ids=[],
        **extra,
    )
    await _set_flow_step(message, state, flow_type=flow_type, flow_step=step)


async def _finish_request(message: Message, state: FSMContext) -> None:
    user = message.from_user
    data = await state.get_data()
    flow_type = data.get("flow_type") or REQUEST_BUY
    lang = await VerticalOnboardingEngineV1.get_language(user.id)
    prefs = await VerticalOnboardingEngineV1.get_preferences(user.id)
    source_link = prefs.get("source_link") or "auto_client"

    user_description = data.get("user_description") or data.get("description")
    photo_file_ids: list[str] = list(data.get("photo_file_ids") or [])
    client_phone = data.get("client_phone")

    ai_qualification = None
    if user_description:
        try:
            from services.pg_ai_manager_engine import AiManagerEngineV1

            ai_qualification = await AiManagerEngineV1.qualify_message(
                user_description,
                context={"flow_type": flow_type, "brand": data.get("brand"), "model": data.get("model")},
            )
        except Exception:
            logger.debug("AI qualification skipped", exc_info=True)

    description = build_description(flow_type, {**data, "user_description": user_description})

    has_vin = vin_present(data)
    logger.info(
        "AUTO_CLIENT finish_request type=%s user=%s phone=%s photos=%s VIN_PRESENT=%s",
        flow_type,
        user.id,
        bool(client_phone),
        len(photo_file_ids),
        has_vin,
    )

    try:
        result = await AutoClientRequestEngineV1.submit(
            flow_request_type=flow_type,
            client_telegram_id=user.id,
            client_username=user.username,
            client_full_name=user.full_name,
            client_first_name=user.first_name,
            client_last_name=user.last_name,
            client_language_code=user.language_code,
            client_phone=client_phone,
            source_link=source_link,
            description=description,
            user_description=user_description,
            photo_file_ids=photo_file_ids or None,
            vin=data.get("vin"),
            brand=data.get("brand"),
            model=data.get("model"),
            year=data.get("year"),
            mileage=data.get("mileage"),
            budget=data.get("budget"),
            price=data.get("price"),
            service_type=data.get("service_type"),
            fuel=data.get("fuel"),
            city=data.get("city"),
            engine=data.get("engine"),
            ai_qualification=ai_qualification,
        )

        try:
            from services.pg_lead_engine import LeadEngineV1

            await LeadEngineV1.submit_auto_client_request(
                telegram_user_id=user.id,
                request_type=flow_type,
                description=description,
                photo_file_id=photo_file_ids[0] if photo_file_ids else None,
                phone=client_phone,
                source_link=source_link,
                telegram_username=user.username,
                full_name=user.full_name,
                language=lang,
                notify=False,
            )
        except Exception:
            logger.warning("Lead engine sync failed for auto client request", exc_info=True)

        await message.answer(
            f"✅ Заявка создана\n"
            f"Номер: {result['request_number']}\n"
            f"Менеджер: {result['manager_name']}",
            reply_markup=auto_client_menu(lang),
        )
    except RuntimeError as exc:
        if "AUTO_MANAGER NOT FOUND" in str(exc):
            logger.error("AUTO_MANAGER NOT FOUND")
        await message.answer(
            "❌ Менеджер временно недоступен. Попробуйте позже.",
            reply_markup=auto_client_menu(lang),
        )
    except Exception:
        logger.exception("AUTO_CLIENT request submission failed user=%s", user.id)
        await message.answer(
            "❌ Не удалось создать заявку. Попробуйте ещё раз.",
            reply_markup=auto_client_menu(lang),
        )
    finally:
        await VerticalOnboardingEngineV1.clear_auto_client_pending(user.id)
        await EntryPointEngineV1.set_current_flow(user.id, FlowState.AUTO_CLIENT_MENU)
        await state.clear()


async def _advance_after_step(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    flow_type = data.get("flow_type")
    flow_step = data.get("flow_step")
    if not flow_type or not flow_step:
        await return_auto_client_menu(message, state)
        return

    nxt = next_step(flow_type, flow_step)
    if nxt is None:
        await _finish_request(message, state)
        return

    await state.update_data(flow_step=nxt)
    await _set_flow_step(message, state, flow_type=flow_type, flow_step=nxt)


async def _handle_interrupt(message: Message, state: FSMContext) -> bool:
    text = (message.text or "").strip()
    lang = await VerticalOnboardingEngineV1.get_language(message.from_user.id)
    if not is_auto_client_interrupt_text(text, lang):
        return False

    await VerticalOnboardingEngineV1.clear_auto_client_pending(message.from_user.id)
    await state.clear()

    if is_auto_client_menu_text(text, lang):
        await auto_client_menu_action(message, state)
        return True

    if is_back_button(text, lang):
        await return_auto_client_menu(message, state)
        return True

    return True


@router.message(Command("start_auto_client", ignore_mention=True))
async def cmd_start_auto_client(message: Message, state: FSMContext) -> None:
    user = message.from_user
    await state.clear()

    await EntryPointEngineV1._clear_blocked_sessions(user.id)
    result = await VerticalOnboardingEngineV1.save_entry_link(
        telegram_user_id=user.id,
        source_link="auto_client",
        full_name=user.full_name or "",
        username=user.username or "",
    )
    await EntryPointEngineV1._ingest_lead(user, "auto_client", result)

    await state.set_state(AutoClientFlow.language_select)
    await message.answer(
        LANGUAGE_PICKER_TEXT,
        reply_markup=entry_flow_language_inline(prefix="auto_client"),
    )
    logger.info("AUTO_CLIENT flow started for user %s", user.id)


@router.callback_query(F.data.startswith("auto_client:lang:"))
async def auto_client_language_selected(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return

    user_id = callback.from_user.id
    ctx = await EntryPointEngineV1.get_flow_context(user_id)
    entry_point = EntryPointEngineV1._resolve_entry_point(ctx)
    if entry_point != EntryPoint.AUTO_CLIENT and ctx.get("source_link") != "auto_client":
        await callback.answer()
        return

    lang = callback.data.rsplit(":", 1)[-1]
    await VerticalOnboardingEngineV1.save_language(
        telegram_user_id=user_id,
        language=lang,
    )
    language = normalize_language(lang)
    await callback.answer()
    await callback.message.answer(t("language_saved", language))

    prefs = await VerticalOnboardingEngineV1.get_preferences(user_id)
    from services.pg_lead_engine import LeadEngineV1

    await LeadEngineV1.enrich_latest_for_user(
        telegram_user_id=user_id,
        source_link=prefs.get("source_link") or "auto_client",
        language=language,
        role="buyer",
    )

    routed = await EntryPointEngineV1.route_after_language(callback.message, user_id, language)
    if not routed:
        await EntryPointEngineV1.set_current_flow(user_id, FlowState.AUTO_CLIENT_MENU)
        await callback.message.answer(
            "Выберите действие:",
            reply_markup=auto_client_menu(language),
        )

    await state.set_state(AutoClientFlow.menu)
    logger.info("AUTO_CLIENT language selected user=%s state=menu", user_id)


def _auto_client_menu_filter(message: Message) -> bool:
    if not message.from_user or not message.text:
        return False
    return is_auto_client_menu_text(message.text)


@router.message(_auto_client_menu_filter)
async def auto_client_menu_action(message: Message, state: FSMContext) -> None:
    logger.info(
        "AUTO_CLIENT menu handler entered text=%r user=%s fsm_state=%s",
        message.text,
        message.from_user.id if message.from_user else None,
        await state.get_state(),
    )

    if not await _ensure_auto_client(message):
        await message.answer("Сессия Auto Client не активна. Отправьте /start_auto_client")
        return

    user_id = message.from_user.id
    current = await state.get_state()
    if current and current != AutoClientFlow.menu.state:
        await VerticalOnboardingEngineV1.clear_auto_client_pending(user_id)
        await state.clear()

    await _sync_auto_client_menu_state(message, state)

    lang = await VerticalOnboardingEngineV1.get_language(user_id)
    text = (message.text or "").strip()
    await EntryPointEngineV1.set_current_flow(user_id, FlowState.AUTO_CLIENT_MENU)
    await state.set_state(AutoClientFlow.menu)

    buy_label = btn("client_buy_car", lang)
    sell_label = btn("client_sell_car", lang)
    listing_label = btn("client_listing", lang)
    services_label = btn("client_services", lang)
    manager_label = btn("client_manager", lang)

    if text == buy_label:
        logger.info("AUTO SEARCH BUTTON CLICKED user=%s", user_id)
        await _start_flow(message, state, REQUEST_BUY)
        return

    if text == sell_label:
        logger.info("AUTO SELL BUTTON CLICKED user=%s", user_id)
        await _start_flow(message, state, REQUEST_SELL)
        return

    if text == listing_label:
        logger.info("AUTO LISTING BUTTON CLICKED user=%s", user_id)
        await _start_flow(message, state, REQUEST_LISTING)
        return

    if text == services_label:
        await open_auto_client_services(message, state)
        return

    if text == manager_label:
        logger.info("AUTO MANAGER BUTTON CLICKED user=%s", user_id)
        await _start_flow(message, state, REQUEST_MANAGER)
        return

    await message.answer("Выберите действие:", reply_markup=auto_client_menu(lang))


async def _auto_client_back_filter(message: Message) -> bool:
    if not message.from_user or not message.text:
        return False
    if not is_back_button(message.text):
        return False
    ctx = await EntryPointEngineV1.get_flow_context(message.from_user.id)
    return (
        ctx.get("entry_point") == EntryPoint.AUTO_CLIENT.value
        or ctx.get("source_link") == "auto_client"
    )


@router.message(_auto_client_back_filter)
async def auto_client_back_navigation(message: Message, state: FSMContext) -> None:
    if not await _ensure_auto_client(message):
        return
    current = await state.get_state()
    logger.info("AUTO_CLIENT back user=%s state=%s", message.from_user.id, current)
    await VerticalOnboardingEngineV1.clear_auto_client_pending(message.from_user.id)
    await state.clear()
    if current == AutoClientFlow.services_hub.state:
        await return_auto_client_menu(message, state)
        return
    await return_auto_client_menu(message, state)


@router.message(StateFilter(AutoClientFlow.collecting), F.text)
async def auto_client_collecting_text(message: Message, state: FSMContext) -> None:
    if not await _ensure_auto_client(message):
        return
    if await _handle_interrupt(message, state):
        return

    data = await state.get_data()
    flow_type = data.get("flow_type")
    flow_step = data.get("flow_step")
    if not flow_type or not flow_step:
        await return_auto_client_menu(message, state)
        return

    text = (message.text or "").strip()
    ok, error, value = validate_text_step(flow_step, text, flow_type=flow_type)
    if not ok:
        lang = await VerticalOnboardingEngineV1.get_language(message.from_user.id)
        await message.answer(error or "Некорректное значение.", reply_markup=auto_client_menu(lang))
        return

    if flow_step == "description":
        await state.update_data(user_description=value)
    else:
        await state.update_data(**{flow_step: value})

    await _advance_after_step(message, state)


@router.message(StateFilter(AutoClientFlow.awaiting_photos), F.photo)
async def auto_client_collect_photos(message: Message, state: FSMContext) -> None:
    if not await _ensure_auto_client(message):
        return

    from services.photo_album_collector import photo_album_collector

    album = await photo_album_collector.add_photo(message)
    if album is None:
        return

    data = await state.get_data()
    photos: list[str] = list(data.get("photo_file_ids") or [])
    photos.extend(album)
    await state.update_data(photo_file_ids=photos)
    lang = await VerticalOnboardingEngineV1.get_language(message.from_user.id)
    await message.answer(
        f"Фото {len(photos)} получено. Отправьте ещё или нажмите «Готово».",
        reply_markup=auto_client_photos_inline(),
    )


@router.message(StateFilter(AutoClientFlow.awaiting_photos))
async def auto_client_photos_non_photo(message: Message, state: FSMContext) -> None:
    if not await _ensure_auto_client(message):
        return
    if await _handle_interrupt(message, state):
        return
    lang = await VerticalOnboardingEngineV1.get_language(message.from_user.id)
    await message.answer(
        "Пришлите фото или используйте кнопки «Готово» / «Пропустить».",
        reply_markup=auto_client_photos_inline(),
    )


@router.callback_query(F.data.in_({"ac:photos:done", "ac:photos:skip"}))
async def auto_client_photos_action(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    if not await _ensure_auto_client(callback.message):
        await callback.answer()
        return

    current = await state.get_state()
    if current != AutoClientFlow.awaiting_photos.state:
        await callback.answer()
        return

    await callback.answer()
    await _advance_after_step(callback.message, state)


@router.callback_query(F.data.in_({"ac:vin:add", "ac:vin:skip"}))
async def auto_client_vin_action(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    if not await _ensure_auto_client(callback.message):
        await callback.answer()
        return

    current = await state.get_state()
    if current != AutoClientFlow.awaiting_vin.state:
        await callback.answer()
        return

    await callback.answer()
    if callback.data == "ac:vin:skip":
        await state.update_data(vin=None, awaiting_vin_input=False)
        await _finish_request(callback.message, state)
        return

    await state.set_state(AutoClientFlow.awaiting_vin)
    await state.update_data(flow_step="vin", awaiting_vin_input=True)
    await callback.message.answer(
        "Введите VIN автомобиля:",
        reply_markup=auto_client_vin_inline(),
    )


@router.message(StateFilter(AutoClientFlow.awaiting_vin), F.text)
async def auto_client_vin_text(message: Message, state: FSMContext) -> None:
    if not await _ensure_auto_client(message):
        return
    if await _handle_interrupt(message, state):
        return

    data = await state.get_data()
    if not data.get("awaiting_vin_input"):
        await message.answer(
            "Хотите добавить VIN автомобиля?",
            reply_markup=auto_client_vin_inline(),
        )
        return

    text = (message.text or "").strip()
    from services.auto_client_flow_engine import SKIP_TOKENS

    if text.lower() in SKIP_TOKENS:
        await state.update_data(vin=None, awaiting_vin_input=False)
        await _finish_request(message, state)
        return

    ok, error, value = validate_text_step("vin", text, flow_type=data.get("flow_type") or REQUEST_BUY)
    if not ok:
        await message.answer(
            f"❌ {error}\n\nВведите VIN ещё раз или нажмите «Нет».",
            reply_markup=auto_client_vin_inline(),
        )
        return

    await state.update_data(vin=value, awaiting_vin_input=False)
    await _finish_request(message, state)


@router.message(StateFilter(AutoClientFlow.awaiting_phone), F.contact)
async def auto_client_manager_contact(message: Message, state: FSMContext) -> None:
    if not await _ensure_auto_client(message) or message.contact is None:
        return
    phone = message.contact.phone_number
    if not phone:
        lang = await VerticalOnboardingEngineV1.get_language(message.from_user.id)
        await message.answer(
            "Не удалось прочитать номер. Введите телефон текстом.",
            reply_markup=auto_client_menu(lang),
        )
        return
    await state.update_data(client_phone=phone)
    lang = await VerticalOnboardingEngineV1.get_language(message.from_user.id)
    await message.answer("✅ Номер получен.", reply_markup=auto_client_menu(lang))

    data = await state.get_data()
    flow_type = data.get("flow_type")
    if flow_type in CAR_FLOW_TYPES:
        await state.update_data(flow_step="phone")
        await _advance_after_step(message, state)
        return
    await _finish_request(message, state)


@router.message(StateFilter(AutoClientFlow.awaiting_phone), F.text)
async def auto_client_phone_text(message: Message, state: FSMContext) -> None:
    if not await _ensure_auto_client(message) or not message.text:
        return
    if await _handle_interrupt(message, state):
        return

    data = await state.get_data()
    flow_type = data.get("flow_type") or REQUEST_MANAGER
    text = message.text.strip()
    ok, error, value = validate_text_step("phone", text, flow_type=flow_type)
    if not ok:
        lang = await VerticalOnboardingEngineV1.get_language(message.from_user.id)
        await message.answer(error or "Некорректный номер.", reply_markup=auto_client_menu(lang))
        return

    await state.update_data(client_phone=value, flow_step="phone")
    if flow_type in CAR_FLOW_TYPES:
        await _advance_after_step(message, state)
        return
    await _finish_request(message, state)


async def start_auto_client_service_flow(
    message: Message,
    state: FSMContext,
    *,
    service_type: str,
) -> None:
    """Called from auto_hub_router after user picks a service category."""
    await state.clear()
    await _start_flow(message, state, REQUEST_SERVICES, service_type=service_type)
