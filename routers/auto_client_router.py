# Auto Client entry router — /start_auto_client command and menu flow.

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from keyboards import auto_client_menu, entry_flow_language_inline
from routers.auto_hub_router import open_auto_client_services, return_auto_client_menu
from services.automotive_localization import btn, is_back_button, normalize_language, t
from services.entry_point_routing import EntryPoint, FlowState, is_auto_client_menu_text
from services.pg_auto_client_request_engine import AutoClientRequestEngineV1
from services.pg_entry_point_engine import EntryPointEngineV1
from services.pg_vertical_onboarding_engine import VerticalOnboardingEngineV1
from states.entry_flow_states import AutoClientFlow, AUTO_CLIENT_PENDING_RESTORE

logger = logging.getLogger(__name__)

router = Router()

LANGUAGE_PICKER_TEXT = "🇺🇦 Выберите язык"

REQUEST_BUY = "buy_car"
REQUEST_SELL = "sell_car"
REQUEST_LISTING = "listing"
REQUEST_MANAGER = "manager_callback"


def _auto_client_services_labels(lang: str | None = None) -> frozenset[str]:
    from services.automotive_localization import normalize_language

    language = normalize_language(lang)
    keys = ("hub_insurance", "hub_credit", "hub_leasing", "hub_logistics", "hub_legal", "back")
    return frozenset(btn(key, language) for key in keys)


async def _restore_auto_client_fsm(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return
    pending = await VerticalOnboardingEngineV1.get_auto_client_pending(message.from_user.id)
    if not pending:
        return
    mapping = AUTO_CLIENT_PENDING_RESTORE.get(pending)
    if mapping is None:
        return
    fsm_state, request_type = mapping
    await state.set_state(fsm_state)
    await state.update_data(request_type=request_type)
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
    await _restore_auto_client_fsm(message, state)


async def _finish_request(
    message: Message,
    state: FSMContext,
    *,
    request_type: str,
    description: str | None = None,
    photo_file_id: str | None = None,
    client_phone: str | None = None,
) -> None:
    user = message.from_user
    lang = await VerticalOnboardingEngineV1.get_language(user.id)
    prefs = await VerticalOnboardingEngineV1.get_preferences(user.id)
    source_link = prefs.get("source_link") or "auto_client"

    logger.info(
        "AUTO_CLIENT finish_request type=%s user=%s phone=%s description_len=%s",
        request_type,
        user.id,
        bool(client_phone),
        len(description or ""),
    )

    try:
        result = await AutoClientRequestEngineV1.submit(
            flow_request_type=request_type,
            client_telegram_id=user.id,
            client_username=user.username,
            client_full_name=user.full_name,
            client_phone=client_phone,
            source_link=source_link,
            description=description,
            photo_file_id=photo_file_id,
        )

        # Best-effort CRM lead sync.
        try:
            from services.pg_lead_engine import LeadEngineV1

            await LeadEngineV1.submit_auto_client_request(
                telegram_user_id=user.id,
                request_type=request_type,
                description=description,
                photo_file_id=photo_file_id,
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
        await state.update_data(request_type=None, photo_file_id=None, client_phone=None)
        await EntryPointEngineV1.set_current_flow(user.id, FlowState.AUTO_CLIENT_MENU)
        await state.set_state(AutoClientFlow.menu)


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
        await VerticalOnboardingEngineV1.save_auto_client_pending(
            telegram_user_id=user_id,
            pending="ac:desc:buy_car",
        )
        await state.set_state(AutoClientFlow.awaiting_description)
        await state.update_data(request_type=REQUEST_BUY)
        await message.answer(
            "Опишите марку, бюджет и город.",
            reply_markup=auto_client_menu(lang),
        )
        return

    if text == sell_label:
        logger.info("AUTO SELL BUTTON CLICKED user=%s", user_id)
        await VerticalOnboardingEngineV1.save_auto_client_pending(
            telegram_user_id=user_id,
            pending="ac:desc:sell_car",
        )
        await state.set_state(AutoClientFlow.awaiting_description)
        await state.update_data(request_type=REQUEST_SELL)
        await message.answer(
            "Укажите марку, год и пробег.",
            reply_markup=auto_client_menu(lang),
        )
        return

    if text == listing_label:
        logger.info("AUTO LISTING BUTTON CLICKED user=%s", user_id)
        await VerticalOnboardingEngineV1.save_auto_client_pending(
            telegram_user_id=user_id,
            pending="ac:photo:listing",
        )
        await state.set_state(AutoClientFlow.awaiting_photo)
        await state.update_data(request_type=REQUEST_LISTING, photo_file_id=None)
        await message.answer(
            "Пришлите фото и описание автомобиля.",
            reply_markup=auto_client_menu(lang),
        )
        return

    if text == services_label:
        await open_auto_client_services(message, state)
        return

    if text == manager_label:
        await VerticalOnboardingEngineV1.save_auto_client_pending(
            telegram_user_id=user_id,
            pending="ac:phone:manager",
        )
        await state.set_state(AutoClientFlow.awaiting_phone)
        await state.update_data(request_type=REQUEST_MANAGER)
        await message.answer(
            "📞 Отправьте номер телефона или нажмите «Поделиться контактом».",
            reply_markup=auto_client_menu(lang),
        )
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
    """«⬅ Назад» in Auto Client — return to menu, never echo the button label."""
    if not await _ensure_auto_client(message):
        return
    current = await state.get_state()
    logger.info(
        "AUTO_CLIENT back user=%s state=%s",
        message.from_user.id,
        current,
    )
    if current == AutoClientFlow.services_hub.state:
        await return_auto_client_menu(message, state)
        return
    await VerticalOnboardingEngineV1.clear_auto_client_pending(message.from_user.id)
    await state.set_state(AutoClientFlow.menu)
    await state.update_data(request_type=None, photo_file_id=None, client_phone=None)
    lang = await VerticalOnboardingEngineV1.get_language(message.from_user.id)
    await EntryPointEngineV1.set_current_flow(message.from_user.id, FlowState.AUTO_CLIENT_MENU)
    await message.answer(t("auto_client_menu_hint", lang), reply_markup=auto_client_menu(lang))


@router.message(StateFilter(AutoClientFlow.awaiting_photo), F.photo)
async def auto_client_listing_photo(message: Message, state: FSMContext) -> None:
    if not await _ensure_auto_client(message):
        return

    photo = message.photo[-1]
    lang = await VerticalOnboardingEngineV1.get_language(message.from_user.id)
    await state.update_data(photo_file_id=photo.file_id, request_type=REQUEST_LISTING)
    await VerticalOnboardingEngineV1.save_auto_client_pending(
        telegram_user_id=message.from_user.id,
        pending="ac:ldsc:listing",
    )
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


async def _resolve_pending_request(state: FSMContext) -> tuple[str | None, str | None]:
    data = await state.get_data()
    current = await state.get_state()
    request_type = data.get("request_type")
    photo_file_id = data.get("photo_file_id")

    if current == AutoClientFlow.awaiting_description.state:
        return request_type or REQUEST_BUY, None
    if current == AutoClientFlow.awaiting_listing_description.state:
        return REQUEST_LISTING, photo_file_id
    if current == AutoClientFlow.awaiting_phone.state:
        return REQUEST_MANAGER, None
    if current == AutoClientFlow.awaiting_photo.state:
        return REQUEST_LISTING, None
    if request_type in {REQUEST_BUY, REQUEST_SELL}:
        return request_type, None
    if request_type == REQUEST_LISTING and photo_file_id:
        return REQUEST_LISTING, photo_file_id
    if request_type == REQUEST_LISTING:
        return REQUEST_LISTING, None
    return None, None


async def _auto_client_text_filter(message: Message) -> bool:
    if not message.from_user or not message.text:
        return False
    text = message.text.strip()
    if not text or text.startswith("/"):
        return False
    if is_auto_client_menu_text(text):
        return False
    for check_lang in ("ru", "uk"):
        if text in _auto_client_services_labels(check_lang):
            return False
    pending = await VerticalOnboardingEngineV1.get_auto_client_pending(message.from_user.id)
    if pending == "ac:phone:manager":
        return False
    ctx = await EntryPointEngineV1.get_flow_context(message.from_user.id)
    return (
        ctx.get("entry_point") == EntryPoint.AUTO_CLIENT.value
        or ctx.get("source_link") == "auto_client"
    )


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
    await _finish_request(
        message,
        state,
        request_type=REQUEST_MANAGER,
        description="Клиент запросил связь с менеджером.",
        client_phone=phone,
    )


@router.message(StateFilter(AutoClientFlow.awaiting_phone))
async def auto_client_manager_phone_text(message: Message, state: FSMContext) -> None:
    if not await _ensure_auto_client(message) or not message.text:
        return
    text = message.text.strip()
    if is_back_button(text):
        await return_auto_client_menu(message, state)
        return
    if is_auto_client_menu_text(text):
        await VerticalOnboardingEngineV1.clear_auto_client_pending(message.from_user.id)
        await state.set_state(AutoClientFlow.menu)
        await auto_client_menu_action(message, state)
        return
    lang = await VerticalOnboardingEngineV1.get_language(message.from_user.id)
    digits = "".join(ch for ch in text if ch.isdigit() or ch == "+")
    if len(digits.replace("+", "")) < 7:
        await message.answer(
            "Введите корректный номер телефона или отправьте контакт.",
            reply_markup=auto_client_menu(lang),
        )
        return
    await _finish_request(
        message,
        state,
        request_type=REQUEST_MANAGER,
        description="Клиент запросил связь с менеджером.",
        client_phone=digits,
    )


@router.message(_auto_client_text_filter)
async def auto_client_text_input(message: Message, state: FSMContext) -> None:
    if not message.from_user or not message.text:
        return
    text = message.text.strip()
    if is_back_button(text):
        await return_auto_client_menu(message, state)
        return
    if not await _ensure_auto_client(message):
        return

    request_type, photo_file_id = await _resolve_pending_request(state)
    logger.info(
        "AUTO_CLIENT text_input user=%s state=%s request_type=%s text=%r",
        message.from_user.id,
        await state.get_state(),
        request_type,
        text[:80],
    )

    if request_type is None:
        lang = await VerticalOnboardingEngineV1.get_language(message.from_user.id)
        await message.answer(
            "Выберите действие в меню, затем отправьте описание.",
            reply_markup=auto_client_menu(lang),
        )
        return

    if request_type == REQUEST_LISTING and not photo_file_id:
        current = await state.get_state()
        if current != AutoClientFlow.awaiting_listing_description.state:
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
        request_type=request_type,
        description=text,
        photo_file_id=photo_file_id if request_type == REQUEST_LISTING else None,
    )
