# Vertical-first onboarding handlers — language and role selection.

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from database import log_audit
from services.automotive_localization import (
    all_role_labels,
    normalize_language,
    role_code_from_label,
    t,
)
from services.pg_vertical_onboarding_engine import VerticalOnboardingEngineV1

logger = logging.getLogger(__name__)

vertical_onboarding_router = Router()

onboarding_role_flow: set[int] = set()
settings_flow: set[int] = set()


async def begin_vertical_onboarding(message: Message, vertical: str) -> None:
    user = message.from_user
    await VerticalOnboardingEngineV1.save_vertical_entry(
        telegram_user_id=user.id,
        vertical=vertical,
        full_name=user.full_name or "",
        username=user.username or "",
    )
    log_audit(user.id, "onboard", "vertical", vertical)
    await message.answer(
        t("lang_picker_title", "ru"),
        reply_markup=VerticalOnboardingEngineV1.language_picker_inline(),
    )


async def enter_vertical_after_onboarding(message: Message, vertical: str, lang: str) -> None:
    if vertical == "auto":
        from auto_vertical_handlers import handle_auto_menu_request

        await handle_auto_menu_request(message)
        return
    if vertical == "agro":
        await message.answer("🌾 Agro Trading", reply_markup=__import__("keyboards", fromlist=["agro_menu"]).agro_menu())
        return
    if vertical == "legal":
        await message.answer("⚖ Юриспруденция", reply_markup=__import__("keyboards", fromlist=["law_module_menu"]).law_module_menu())
        return
    if vertical == "drones":
        await message.answer("🚁 Drone Engineering", reply_markup=__import__("keyboards", fromlist=["drone_module_menu"]).drone_module_menu())
        return
    if vertical in {"finance", "crypto"}:
        await message.answer("💰 Crypto OTC", reply_markup=__import__("keyboards", fromlist=["crypto_otc_menu"]).crypto_otc_menu())
        return
    if vertical in {"cafe", "beauty"}:
        await message.answer("☕ Cafe & Beauty", reply_markup=__import__("keyboards", fromlist=["cafe_beauty_module_menu"]).cafe_beauty_module_menu())
        return
    await message.answer(t("onboarding_complete", lang))


@vertical_onboarding_router.callback_query(F.data.startswith("onboard:lang:"))
async def onboarding_language_callback(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    user_id = callback.from_user.id
    lang = callback.data.rsplit(":", 1)[-1]
    prefs = await VerticalOnboardingEngineV1.get_preferences(user_id)

    if prefs.get("onboarding_completed") or prefs.get("onboarding_step") != "language":
        language = await VerticalOnboardingEngineV1.update_language(
            telegram_user_id=user_id,
            language=lang,
        )
        await callback.answer()
        await callback.message.answer(t("language_saved", language))
        return

    result = await VerticalOnboardingEngineV1.save_language(
        telegram_user_id=user_id,
        language=lang,
    )
    language = normalize_language(result["language"])
    await callback.answer()
    await callback.message.answer(t("language_saved", language))

    if result.get("onboarding_step") == "role" and result.get("vertical") == "auto":
        onboarding_role_flow.add(user_id)
        await callback.message.answer(
            t("role_picker_title", language),
            reply_markup=VerticalOnboardingEngineV1.auto_role_picker_keyboard(language),
        )
        return

    vertical = result.get("vertical") or "auto"
    await enter_vertical_after_onboarding(callback.message, vertical, language)


@vertical_onboarding_router.message(lambda m: m.from_user.id in onboarding_role_flow and m.text in all_role_labels())
async def onboarding_role_selected(message: Message) -> None:
    user_id = message.from_user.id
    lang = await VerticalOnboardingEngineV1.get_language(user_id)
    role_code = role_code_from_label(message.text or "")
    if role_code is None:
        await message.answer(t("role_picker_title", lang))
        return
    await VerticalOnboardingEngineV1.save_role(telegram_user_id=user_id, role=role_code)
    onboarding_role_flow.discard(user_id)
    log_audit(user_id, "onboard", "role", role_code)
    prefs = await VerticalOnboardingEngineV1.get_preferences(user_id)
    await message.answer(t("onboarding_complete", lang))
    await enter_vertical_after_onboarding(message, prefs.get("vertical") or "auto", lang)


@vertical_onboarding_router.message(F.text.in_({"⚙ Настройки", "⚙ Налаштування"}))
async def open_settings(message: Message) -> None:
    user_id = message.from_user.id
    lang = await VerticalOnboardingEngineV1.get_language(user_id)
    settings_flow.add(user_id)
    await message.answer(
        t("settings_title", lang),
        reply_markup=VerticalOnboardingEngineV1.settings_menu_keyboard(lang),
    )


@vertical_onboarding_router.message(F.text == "🌍 Язык / Мова")
async def open_language_settings(message: Message) -> None:
    user_id = message.from_user.id
    lang = await VerticalOnboardingEngineV1.get_language(user_id)
    await message.answer(
        t("lang_picker_title", lang),
        reply_markup=VerticalOnboardingEngineV1.language_picker_inline(),
    )


@vertical_onboarding_router.callback_query(F.data.startswith("onboard:role:"))
async def onboarding_role_callback(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    user_id = callback.from_user.id
    role_code = callback.data.rsplit(":", 1)[-1]
    lang = await VerticalOnboardingEngineV1.get_language(user_id)
    await VerticalOnboardingEngineV1.save_role(telegram_user_id=user_id, role=role_code)
    onboarding_role_flow.discard(user_id)
    await callback.answer()
    prefs = await VerticalOnboardingEngineV1.get_preferences(user_id)
    await callback.message.answer(t("onboarding_complete", lang))
    await enter_vertical_after_onboarding(callback.message, prefs.get("vertical") or "auto", lang)
