# Auto Hub services router — partner categories for Auto Client services menu.

from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from automotive_partner_handlers import HUB_BUTTON_TO_CATEGORY, show_partner_category
from keyboards import auto_client_menu, auto_client_services_menu
from services.automotive_localization import (
    category_header,
    hub_screen_to_category,
    is_back_button,
    resolve_auto_screen,
    t,
)
from services.entry_point_routing import FlowState
from services.pg_entry_point_engine import EntryPointEngineV1
from services.pg_vertical_onboarding_engine import VerticalOnboardingEngineV1
from states.entry_flow_states import AutoClientFlow

logger = logging.getLogger(__name__)

router = Router()

_SERVICES_SCREEN_KEYS = frozenset({
    "hub_insurance",
    "hub_credit",
    "hub_leasing",
    "hub_logistics",
    "hub_legal",
    "back",
})


def _auto_client_services_labels(lang: str | None = None) -> frozenset[str]:
    from services.automotive_localization import btn, normalize_language

    language = normalize_language(lang)
    return frozenset(btn(key, language) for key in _SERVICES_SCREEN_KEYS)


async def _ensure_auto_client_services(message: Message) -> bool:
    if message.from_user is None:
        return False
    ctx = await EntryPointEngineV1.get_flow_context(message.from_user.id)
    return ctx.get("source_link") == "auto_client" or ctx.get("entry_point") == "AUTO_CLIENT"


async def return_auto_client_menu(message: Message, state: FSMContext) -> None:
    """Reset Auto Client FSM and show main client menu (single navigation message)."""
    user_id = message.from_user.id
    lang = await VerticalOnboardingEngineV1.get_language(user_id)
    await VerticalOnboardingEngineV1.clear_auto_client_pending(user_id)
    await EntryPointEngineV1.set_current_flow(user_id, FlowState.AUTO_CLIENT_MENU)
    await state.set_state(AutoClientFlow.menu)
    await state.update_data(request_type=None, photo_file_id=None, client_phone=None)
    await message.answer(
        t("auto_client_menu_hint", lang),
        reply_markup=auto_client_menu(lang),
    )


async def open_auto_client_services(message: Message, state: FSMContext) -> None:
    """Entry from auto_client_router «Автоуслуги» button."""
    user_id = message.from_user.id
    lang = await VerticalOnboardingEngineV1.get_language(user_id)
    await VerticalOnboardingEngineV1.save_auto_client_pending(
        telegram_user_id=user_id,
        pending="ac:services:hub",
    )
    await state.set_state(AutoClientFlow.services_hub)
    await state.update_data(request_type=None, photo_file_id=None, client_phone=None)
    await message.answer(
        t("auto_client_services_hint", lang),
        reply_markup=auto_client_services_menu(lang),
    )


async def _services_hub_text_filter(message: Message) -> bool:
    if not message.text:
        return False
    return resolve_auto_screen(message.text) in _SERVICES_SCREEN_KEYS


@router.message(StateFilter(AutoClientFlow.services_hub), _services_hub_text_filter)
async def auto_client_services_action(message: Message, state: FSMContext) -> None:
    if not await _ensure_auto_client_services(message):
        return

    user_id = message.from_user.id
    lang = await VerticalOnboardingEngineV1.get_language(user_id)
    screen_key = resolve_auto_screen(message.text)
    logger.info("AUTO_CLIENT services action user=%s screen=%s", user_id, screen_key)

    if screen_key == "back" or is_back_button(message.text, lang):
        await return_auto_client_menu(message, state)
        return

    category = hub_screen_to_category(screen_key or "")
    if category is None:
        await message.answer(
            t("auto_client_services_hint", lang),
            reply_markup=auto_client_services_menu(lang),
        )
        return

    try:
        partner_category = HUB_BUTTON_TO_CATEGORY.get(category, category)
        await show_partner_category(
            message,
            user_id,
            partner_category,
            reply_markup=auto_client_services_menu(lang),
        )
    except Exception as exc:
        logger.warning("AUTO_CLIENT services category failed user=%s cat=%s", user_id, category, exc_info=True)
        await message.answer(
            f"{category_header(category, lang)}\n\n"
            f"{t('auto_client_service_unavailable', lang)}",
            reply_markup=auto_client_services_menu(lang),
        )
