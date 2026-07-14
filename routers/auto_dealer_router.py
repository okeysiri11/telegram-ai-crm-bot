# Auto Dealer entry router — /start_auto_dealer command and onboarding flow.

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from keyboards import entry_flow_language_inline
from services.automotive_localization import normalize_language, t
from services.entry_point_routing import EntryPoint, FlowState
from services.pg_entry_point_engine import EntryPointEngineV1
from services.pg_vertical_onboarding_engine import VerticalOnboardingEngineV1
from states.entry_flow_states import AutoDealerFlow

logger = logging.getLogger(__name__)

router = Router()

LANGUAGE_PICKER_TEXT = "🇺🇦 Выберите язык"


@router.message(Command("start_auto_dealer"))
async def cmd_start_auto_dealer(message: Message, state: FSMContext) -> None:
    user = message.from_user
    await state.clear()

    await EntryPointEngineV1._clear_blocked_sessions(user.id)
    result = await VerticalOnboardingEngineV1.save_entry_link(
        telegram_user_id=user.id,
        source_link="auto_dealer",
        full_name=user.full_name or "",
        username=user.username or "",
    )
    await EntryPointEngineV1._ingest_lead(user, "auto_dealer", result)

    await state.set_state(AutoDealerFlow.language_select)
    await message.answer(
        LANGUAGE_PICKER_TEXT,
        reply_markup=entry_flow_language_inline(prefix="auto_dealer"),
    )
    logger.info("AUTO_DEALER flow started for user %s", user.id)


@router.callback_query(F.data.startswith("auto_dealer:lang:"))
async def auto_dealer_language_selected(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return

    user_id = callback.from_user.id
    ctx = await EntryPointEngineV1.get_flow_context(user_id)
    if ctx.get("entry_point") != EntryPoint.AUTO_DEALER.value:
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
        role="dealer",
    )

    await EntryPointEngineV1.route_after_language(callback.message, user_id, language)
    await state.set_state(AutoDealerFlow.dealer_onboarding)
