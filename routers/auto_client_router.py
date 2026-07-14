# Auto Client entry router — /start_auto_client command and menu flow.

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from keyboards import auto_client_menu, entry_flow_language_inline
from services.automotive_localization import btn, normalize_language, t
from services.entry_point_routing import EntryPoint, FlowState, is_auto_client_menu_text
from services.pg_entry_point_engine import EntryPointEngineV1
from services.pg_vertical_onboarding_engine import VerticalOnboardingEngineV1
from states.entry_flow_states import AutoClientFlow

logger = logging.getLogger(__name__)

router = Router()

LANGUAGE_PICKER_TEXT = "🇺🇦 Выберите язык"


@router.message(Command("start_auto_client", ignore_mention=True))
async def cmd_start_auto_client(message: Message, state: FSMContext) -> None:
    print("========== AUTO CLIENT HANDLER STARTED ==========")
    print(f"TEXT={message.text}")
    print(f"USER={message.from_user.id}")

    await message.answer(
        "DEBUG: AUTO CLIENT HANDLER WORKS"
    )

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
    if ctx.get("entry_point") != EntryPoint.AUTO_CLIENT.value:
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

    from services.pg_lead_engine import LeadEngineV1

    prefs = await VerticalOnboardingEngineV1.get_preferences(user_id)
    await LeadEngineV1.enrich_latest_for_user(
        telegram_user_id=user_id,
        source_link=prefs.get("source_link"),
        language=language,
        role="buyer",
    )

    await EntryPointEngineV1.route_after_language(callback.message, user_id, language)
    await state.set_state(AutoClientFlow.menu)


def _auto_client_menu_filter(message: Message) -> bool:
    if not message.from_user or not message.text:
        return False
    return is_auto_client_menu_text(message.text)


@router.message(_auto_client_menu_filter)
async def auto_client_menu_action(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    ctx = await EntryPointEngineV1.get_flow_context(user_id)
    if ctx.get("entry_point") != EntryPoint.AUTO_CLIENT.value:
        return

    lang = await VerticalOnboardingEngineV1.get_language(user_id)
    text = (message.text or "").strip()
    await EntryPointEngineV1.set_current_flow(user_id, FlowState.AUTO_CLIENT_MENU)
    await state.set_state(AutoClientFlow.menu)

    replies = {
        btn("client_buy_car", lang): "🚗 Поиск автомобиля. Опишите марку, бюджет и город.",
        btn("client_sell_car", lang): "💰 Продажа автомобиля. Укажите марку, год и пробег.",
        btn("client_listing", lang): "📢 Размещение объявления. Пришлите фото и описание авто.",
        btn("client_services", lang): "🛠 Автоуслуги: сервис, страхование, кредит, логистика.",
        btn("client_manager", lang): "📞 Менеджер получил запрос и свяжется с вами.",
    }
    reply = replies.get(text, "Выберите действие:")
    await message.answer(reply, reply_markup=auto_client_menu(lang))
