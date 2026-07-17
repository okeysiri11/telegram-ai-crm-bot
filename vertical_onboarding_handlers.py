# Vertical-first onboarding handlers — language and role selection.

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from services.handler_auth import log_audit
from services.automotive_localization import (
    all_role_labels,
    btn,
    hub_screen_to_category,
    normalize_language,
    role_code_from_label,
    t,
)
from services.pg_tenant_entry_registry_engine import TenantRoutingEngineV1
from services.pg_vertical_onboarding_engine import VerticalOnboardingEngineV1
from services.tenant_routing import ENTRY_LINK_REGISTRY, is_owner

logger = logging.getLogger(__name__)

vertical_onboarding_router = Router()

onboarding_role_flow: set[int] = set()
settings_flow: set[int] = set()


async def begin_entry_link_onboarding(
    message: Message,
    source_link: str,
    *,
    start_args: str | None = None,
) -> None:
    user = message.from_user
    result = await VerticalOnboardingEngineV1.save_entry_link(
        telegram_user_id=user.id,
        source_link=source_link,
        full_name=user.full_name or "",
        username=user.username or "",
    )
    from services.pg_lead_engine import LeadEngineV1

    await LeadEngineV1.ingest_from_deep_link(
        telegram_user_id=user.id,
        telegram_username=user.username,
        full_name=user.full_name,
        start_args=start_args or source_link,
        vertical=result.get("vertical"),
        role=result.get("preset_role"),
        source_link=source_link,
    )
    log_audit(user.id, "onboard", "entry_link", source_link)
    await message.answer(
        t("lang_picker_title", "ru"),
        reply_markup=VerticalOnboardingEngineV1.language_picker_inline(),
    )


async def begin_vertical_onboarding(
    message: Message,
    vertical: str,
    *,
    start_args: str | None = None,
) -> None:
    user = message.from_user
    await VerticalOnboardingEngineV1.save_vertical_entry(
        telegram_user_id=user.id,
        vertical=vertical,
        full_name=user.full_name or "",
        username=user.username or "",
    )
    from services.pg_lead_engine import LeadEngineV1

    await LeadEngineV1.ingest_from_deep_link(
        telegram_user_id=user.id,
        telegram_username=user.username,
        full_name=user.full_name,
        start_args=start_args or vertical,
        vertical=vertical,
        source_link=vertical,
    )
    log_audit(user.id, "onboard", "vertical", vertical)
    await message.answer(
        t("lang_picker_title", "ru"),
        reply_markup=VerticalOnboardingEngineV1.language_picker_inline(),
    )


async def enter_tenant_vertical(message: Message, user_id: int, lang: str) -> None:
    ctx = await TenantRoutingEngineV1.get_tenant_context(user_id)
    vertical = ctx.get("vertical") or "auto"
    entry_target = ctx.get("entry_target")
    await enter_vertical_after_onboarding(
        message,
        vertical,
        lang,
        entry_target=entry_target,
        tenant_scoped=ctx.get("tenant_scoped", False),
    )


async def enter_vertical_after_onboarding(
    message: Message,
    vertical: str,
    lang: str,
    *,
    entry_target: str | None = None,
    tenant_scoped: bool = False,
) -> None:
    from keyboards import tenant_scoped_menu
    from services.pg_entry_point_engine import EntryPointEngineV1
    from services.entry_point_routing import EntryPoint

    user_id = message.from_user.id
    ctx = await EntryPointEngineV1.get_flow_context(user_id)
    if ctx.get("entry_point") == EntryPoint.AUTO_CLIENT.value:
        await EntryPointEngineV1._show_auto_client_menu(message, lang)
        return

    scoped_markup = tenant_scoped_menu(
        await TenantRoutingEngineV1.get_tenant_context(user_id),
        lang,
    )

    if vertical == "auto":
        from auto_vertical_handlers import (
            _handle_auto_vertical_screen,
            _open_auto_hub,
            _open_cars_section,
            auto_vertical_active,
            handle_auto_menu_request,
        )

        if entry_target:
            auto_vertical_active[user_id] = True
            if entry_target == "hub_cars":
                await _open_cars_section(message, user_id)
            elif entry_target.startswith("hub_"):
                category = hub_screen_to_category(entry_target)
                if category:
                    from automotive_partner_handlers import show_partner_category

                    await show_partner_category(message, user_id, category)
                else:
                    await _open_auto_hub(message, user_id)
            else:
                await _handle_auto_vertical_screen(message, user_id, btn(entry_target, lang))
            if tenant_scoped and scoped_markup:
                await message.answer(t("tenant_scoped_hint", lang), reply_markup=scoped_markup)
            return

        if tenant_scoped:
            await handle_auto_menu_request(message)
            if scoped_markup:
                await message.answer(t("tenant_scoped_hint", lang), reply_markup=scoped_markup)
            return

        await handle_auto_menu_request(message)
        return

    if vertical == "agro":
        await message.answer(
            "🌾 Agro Trading",
            reply_markup=scoped_markup or __import__("keyboards", fromlist=["agro_menu"]).agro_menu(),
        )
        return
    if vertical == "legal":
        await message.answer(
            "⚖ Юриспруденция",
            reply_markup=scoped_markup or __import__("keyboards", fromlist=["law_module_menu"]).law_module_menu(),
        )
        return
    if vertical == "drones":
        await message.answer(
            "🚁 Drone Engineering",
            reply_markup=scoped_markup or __import__("keyboards", fromlist=["drone_module_menu"]).drone_module_menu(),
        )
        return
    if vertical in {"finance", "crypto"}:
        await message.answer(
            "💰 Crypto OTC",
            reply_markup=scoped_markup or __import__("keyboards", fromlist=["crypto_otc_menu"]).crypto_otc_menu(),
        )
        return
    if vertical in {"cafe", "beauty"}:
        await message.answer(
            "☕ Cafe & Beauty",
            reply_markup=scoped_markup or __import__("keyboards", fromlist=["cafe_beauty_module_menu"]).cafe_beauty_module_menu(),
        )
        return
    await message.answer(t("onboarding_complete", lang), reply_markup=scoped_markup)


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

    from services.pg_lead_engine import LeadEngineV1
    from services.pg_entry_point_engine import EntryPointEngineV1

    prefs = await VerticalOnboardingEngineV1.get_preferences(user_id)
    await LeadEngineV1.enrich_latest_for_user(
        telegram_user_id=user_id,
        source_link=prefs.get("source_link"),
        language=language,
        role=result.get("role"),
    )

    if await EntryPointEngineV1.route_after_language(callback.message, user_id, language):
        return

    if result.get("onboarding_step") == "role" and result.get("vertical") == "auto":
        onboarding_role_flow.add(user_id)
        await callback.message.answer(
            t("role_picker_title", language),
            reply_markup=VerticalOnboardingEngineV1.auto_role_picker_keyboard(language),
        )
        return

    await enter_tenant_vertical(callback.message, user_id, language)


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
    from services.pg_lead_engine import LeadEngineV1

    prefs = await VerticalOnboardingEngineV1.get_preferences(user_id)
    await LeadEngineV1.enrich_latest_for_user(
        telegram_user_id=user_id,
        source_link=prefs.get("source_link"),
        language=lang,
        role=role_code,
    )
    await message.answer(t("onboarding_complete", lang))
    await enter_tenant_vertical(message, user_id, lang)


@vertical_onboarding_router.message(F.text.in_({"⚙ Настройки", "⚙ Налаштування"}))
async def open_settings(message: Message) -> None:
    user_id = message.from_user.id
    if not await TenantRoutingEngineV1.can_access_module(user_id, "settings"):
        lang = await VerticalOnboardingEngineV1.get_language(user_id)
        await message.answer(await TenantRoutingEngineV1.tenant_denied_message(user_id, lang))
        return
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
    await callback.message.answer(t("onboarding_complete", lang))
    await enter_tenant_vertical(callback.message, user_id, lang)


@vertical_onboarding_router.message(F.text == "🏠 Мой раздел")
async def reopen_tenant_home(message: Message) -> None:
    user_id = message.from_user.id
    ctx = await TenantRoutingEngineV1.get_tenant_context(user_id)
    if not ctx.get("tenant_scoped") and not is_owner(user_id):
        return
    lang = await VerticalOnboardingEngineV1.get_language(user_id)
    await enter_tenant_vertical(message, user_id, lang)
