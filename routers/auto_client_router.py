# Auto Client entry router — /start_auto_client command and menu flow.

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from keyboards import auto_client_menu, entry_flow_language_inline
from services.automotive_localization import btn, normalize_language, t
from services.entry_point_routing import EntryPoint, FlowState, is_auto_client_menu_text
from services.pg_entry_point_engine import EntryPointEngineV1
from services.pg_lead_engine import LeadEngineV1
from services.pg_vertical_onboarding_engine import VerticalOnboardingEngineV1
from states.entry_flow_states import AutoClientFlow

logger = logging.getLogger(__name__)

router = Router()

LANGUAGE_PICKER_TEXT = "🇺🇦 Выберите язык"

REQUEST_BUY = "buy_car"
REQUEST_SELL = "sell_car"
REQUEST_LISTING = "listing"
REQUEST_MANAGER = "manager_callback"


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
    """Restore FSM after bot restart or menu shown outside auto_client_router."""
    if message.from_user is None:
        return
    ctx = await EntryPointEngineV1.get_flow_context(message.from_user.id)
    if ctx.get("entry_point") != EntryPoint.AUTO_CLIENT.value and ctx.get("source_link") != "auto_client":
        return
    current = await state.get_state()
    if current is None and ctx.get("current_flow") == FlowState.AUTO_CLIENT_MENU.value:
        await state.set_state(AutoClientFlow.menu)
        logger.info("AUTO_CLIENT FSM synced to menu for user=%s", message.from_user.id)


async def _finish_request(
    message: Message,
    state: FSMContext,
    *,
    request_type: str,
    description: str | None = None,
    photo_file_id: str | None = None,
) -> None:
    user = message.from_user
    lang = await VerticalOnboardingEngineV1.get_language(user.id)

    await LeadEngineV1.submit_auto_client_request(
        telegram_user_id=user.id,
        request_type=request_type,
        description=description,
        photo_file_id=photo_file_id,
        source_link="auto_client",
        telegram_username=user.username,
        full_name=user.full_name,
        language=lang,
    )

    await state.clear()
    await EntryPointEngineV1.set_current_flow(user.id, FlowState.AUTO_CLIENT_MENU)
    await state.set_state(AutoClientFlow.menu)

    confirmations = {
        REQUEST_BUY: "✅ Заявка на поиск автомобиля создана.\nМенеджер получил уведомление.",
        REQUEST_SELL: "✅ Заявка на продажу автомобиля создана.\nМенеджер получил уведомление.",
        REQUEST_LISTING: "✅ Объявление отправлено.\nМенеджер получил фото и описание.",
        REQUEST_MANAGER: "✅ Менеджер получил запрос и свяжется с вами.",
    }
    await message.answer(
        confirmations.get(request_type, "✅ Заявка создана."),
        reply_markup=auto_client_menu(lang),
    )


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
    matched = is_auto_client_menu_text(message.text)
    if matched:
        logger.info(
            "AUTO_CLIENT menu filter matched text=%r user=%s",
            message.text,
            message.from_user.id,
        )
    return matched


@router.message(_auto_client_menu_filter)
async def auto_client_menu_action(message: Message, state: FSMContext) -> None:
    logger.info(
        "AUTO_CLIENT menu handler entered text=%r user=%s fsm_state=%s",
        message.text,
        message.from_user.id if message.from_user else None,
        await state.get_state(),
    )
    await _sync_auto_client_menu_state(message, state)

    if not await _ensure_auto_client(message):
        await message.answer("Сессия Auto Client не активна. Отправьте /start_auto_client")
        return

    user_id = message.from_user.id
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
        await state.set_state(AutoClientFlow.awaiting_description)
        await state.update_data(request_type=REQUEST_BUY)
        await message.answer(
            "Опишите марку, бюджет и город.",
            reply_markup=auto_client_menu(lang),
        )
        return

    if text == sell_label:
        logger.info("AUTO SELL BUTTON CLICKED user=%s", user_id)
        await state.set_state(AutoClientFlow.awaiting_description)
        await state.update_data(request_type=REQUEST_SELL)
        await message.answer(
            "Укажите марку, год и пробег.",
            reply_markup=auto_client_menu(lang),
        )
        return

    if text == listing_label:
        logger.info("AUTO LISTING BUTTON CLICKED user=%s", user_id)
        await state.set_state(AutoClientFlow.awaiting_photo)
        await state.update_data(request_type=REQUEST_LISTING, photo_file_id=None)
        await message.answer(
            "Пришлите фото и описание автомобиля.",
            reply_markup=auto_client_menu(lang),
        )
        return

    if text == services_label:
        await message.answer(
            "🛠 Автоуслуги: сервис, страхование, кредит, логистика.\n"
            "Выберите «Связаться с менеджером» для персональной консультации.",
            reply_markup=auto_client_menu(lang),
        )
        return

    if text == manager_label:
        await _finish_request(
            message,
            state,
            request_type=REQUEST_MANAGER,
            description="Клиент запросил связь с менеджером.",
        )
        return

    await message.answer("Выберите действие:", reply_markup=auto_client_menu(lang))


@router.message(StateFilter(AutoClientFlow.awaiting_photo), F.photo)
async def auto_client_listing_photo(message: Message, state: FSMContext) -> None:
    if not await _ensure_auto_client(message):
        return

    photo = message.photo[-1]
    lang = await VerticalOnboardingEngineV1.get_language(message.from_user.id)
    await state.update_data(photo_file_id=photo.file_id, request_type=REQUEST_LISTING)
    await state.set_state(AutoClientFlow.awaiting_listing_description)
    await message.answer(
        "Фото получено.\nТеперь опишите автомобиль: марка, год, цена, город.",
        reply_markup=auto_client_menu(lang),
    )


@router.message(StateFilter(AutoClientFlow.awaiting_photo))
async def auto_client_listing_photo_required(message: Message, state: FSMContext) -> None:
    if not await _ensure_auto_client(message):
        return
    if message.text and is_auto_client_menu_text(message.text):
        await state.set_state(AutoClientFlow.menu)
        await auto_client_menu_action(message, state)
        return
    lang = await VerticalOnboardingEngineV1.get_language(message.from_user.id)
    await message.answer(
        "Пожалуйста, пришлите фото автомобиля.",
        reply_markup=auto_client_menu(lang),
    )


@router.message(StateFilter(AutoClientFlow.awaiting_description), F.text)
async def auto_client_description(message: Message, state: FSMContext) -> None:
    if not await _ensure_auto_client(message):
        return

    text = (message.text or "").strip()
    if not text or text.startswith("/"):
        return
    if is_auto_client_menu_text(text):
        await state.set_state(AutoClientFlow.menu)
        await auto_client_menu_action(message, state)
        return

    data = await state.get_data()
    request_type = data.get("request_type") or REQUEST_BUY
    await _finish_request(
        message,
        state,
        request_type=request_type,
        description=text,
    )


@router.message(StateFilter(AutoClientFlow.awaiting_listing_description), F.text)
async def auto_client_listing_description(message: Message, state: FSMContext) -> None:
    if not await _ensure_auto_client(message):
        return

    text = (message.text or "").strip()
    if not text or text.startswith("/"):
        return
    if is_auto_client_menu_text(text):
        await state.set_state(AutoClientFlow.menu)
        await auto_client_menu_action(message, state)
        return

    data = await state.get_data()
    photo_file_id = data.get("photo_file_id")
    if not photo_file_id:
        lang = await VerticalOnboardingEngineV1.get_language(message.from_user.id)
        await state.set_state(AutoClientFlow.awaiting_photo)
        await message.answer(
            "Сначала пришлите фото автомобиля.",
            reply_markup=auto_client_menu(lang),
        )
        return

    await _finish_request(
        message,
        state,
        request_type=REQUEST_LISTING,
        description=text,
        photo_file_id=photo_file_id,
    )
