# Vertical-first onboarding — deep links, language, role persistence.

from __future__ import annotations

from typing import Any

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

from database import ensure_user
from database.session import get_session
from repositories.user_vertical_preferences_repository import UserVerticalPreferencesRepository
from services.automotive_localization import (
    AUTO_ROLE_CODES,
    DEFAULT_LANGUAGE,
    VERTICAL_DEEP_LINKS,
    btn,
    normalize_language,
    role_label,
    t,
)
from services.tenant_routing import (
    ENTRY_LINK_REGISTRY,
    legacy_vertical_from_args,
    parse_entry_link as resolve_entry_link,
)


class VerticalOnboardingEngineV1:
    @staticmethod
    async def get_preferences(telegram_user_id: int) -> dict[str, Any]:
        async with get_session() as session:
            row = await UserVerticalPreferencesRepository(session).get_by_telegram_id(
                telegram_user_id
            )
        if row is None:
            return {
                "telegram_user_id": telegram_user_id,
                "vertical": None,
                "tenant_code": None,
                "source_link": None,
                "language": DEFAULT_LANGUAGE,
                "role": None,
                "onboarding_step": None,
                "onboarding_completed": False,
            }
        return {
            "telegram_user_id": row.telegram_user_id,
            "vertical": row.vertical,
            "tenant_code": row.tenant_code,
            "source_link": row.source_link,
            "language": normalize_language(row.language),
            "role": row.role,
            "onboarding_step": row.onboarding_step,
            "onboarding_completed": row.onboarding_completed,
        }

    @staticmethod
    async def get_language(telegram_user_id: int) -> str:
        prefs = await VerticalOnboardingEngineV1.get_preferences(telegram_user_id)
        return normalize_language(prefs.get("language"))

    @staticmethod
    async def save_entry_link(
        *,
        telegram_user_id: int,
        source_link: str,
        full_name: str = "",
        username: str = "",
    ) -> dict[str, Any]:
        ensure_user(telegram_user_id, full_name=full_name, username=username)
        cfg = ENTRY_LINK_REGISTRY.get(source_link)
        if cfg is None:
            raise ValueError(f"Unsupported entry link: {source_link}")
        async with get_session() as session:
            row = await UserVerticalPreferencesRepository(session).upsert(
                telegram_user_id=telegram_user_id,
                vertical=cfg.vertical,
                tenant_code=cfg.tenant_code,
                source_link=cfg.code,
                onboarding_step="language",
                onboarding_completed=False,
            )
        return {
            "vertical": row.vertical,
            "tenant_code": row.tenant_code,
            "source_link": row.source_link,
            "language": normalize_language(row.language),
            "onboarding_step": row.onboarding_step,
            "preset_role": cfg.preset_role,
            "entry_target": cfg.entry_target,
        }

    @staticmethod
    async def save_vertical_entry(
        *,
        telegram_user_id: int,
        vertical: str,
        full_name: str = "",
        username: str = "",
    ) -> dict[str, Any]:
        ensure_user(telegram_user_id, full_name=full_name, username=username)
        vertical_key = vertical.strip().lower()
        if vertical_key not in VERTICAL_DEEP_LINKS:
            raise ValueError(f"Unsupported vertical: {vertical}")
        async with get_session() as session:
            row = await UserVerticalPreferencesRepository(session).upsert(
                telegram_user_id=telegram_user_id,
                vertical=vertical_key,
                onboarding_step="language",
                onboarding_completed=False,
            )
        return {
            "vertical": row.vertical,
            "language": normalize_language(row.language),
            "onboarding_step": row.onboarding_step,
        }

    @staticmethod
    def _needs_role_picker(prefs) -> bool:
        if prefs is None or prefs.vertical != "auto":
            return False
        if prefs.source_link:
            cfg = ENTRY_LINK_REGISTRY.get(prefs.source_link)
            if cfg and cfg.preset_role:
                return False
        return True

    @staticmethod
    async def save_language(*, telegram_user_id: int, language: str) -> dict[str, Any]:
        lang = normalize_language(language)
        async with get_session() as session:
            repo = UserVerticalPreferencesRepository(session)
            prefs = await repo.get_by_telegram_id(telegram_user_id)
            preset_role = None
            if prefs and prefs.source_link:
                cfg = ENTRY_LINK_REGISTRY.get(prefs.source_link)
                if cfg:
                    preset_role = cfg.preset_role

            if preset_role:
                next_step = "completed"
                completed = True
                row = await repo.upsert(
                    telegram_user_id=telegram_user_id,
                    language=lang,
                    role=preset_role,
                    onboarding_step=next_step,
                    onboarding_completed=completed,
                )
            else:
                next_step = "role" if VerticalOnboardingEngineV1._needs_role_picker(prefs) else "completed"
                completed = next_step == "completed"
                row = await repo.upsert(
                    telegram_user_id=telegram_user_id,
                    language=lang,
                    onboarding_step=next_step,
                    onboarding_completed=completed,
                )
        return {
            "language": normalize_language(row.language),
            "onboarding_step": row.onboarding_step,
            "onboarding_completed": row.onboarding_completed,
            "vertical": row.vertical,
            "tenant_code": row.tenant_code,
            "source_link": row.source_link,
            "role": row.role,
            "preset_role": preset_role,
        }

    @staticmethod
    async def save_role(*, telegram_user_id: int, role: str) -> dict[str, Any]:
        if role not in AUTO_ROLE_CODES:
            raise ValueError(f"Unsupported role: {role}")
        async with get_session() as session:
            row = await UserVerticalPreferencesRepository(session).upsert(
                telegram_user_id=telegram_user_id,
                role=role,
                onboarding_step="completed",
                onboarding_completed=True,
            )
        return {
            "role": row.role,
            "language": normalize_language(row.language),
            "vertical": row.vertical,
            "tenant_code": row.tenant_code,
            "source_link": row.source_link,
            "onboarding_completed": row.onboarding_completed,
        }

    @staticmethod
    async def update_language(*, telegram_user_id: int, language: str) -> str:
        lang = normalize_language(language)
        async with get_session() as session:
            await UserVerticalPreferencesRepository(session).upsert(
                telegram_user_id=telegram_user_id,
                language=lang,
            )
        return lang

    @staticmethod
    def language_picker_inline() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=t("lang_russian", "ru"),
                        callback_data="onboard:lang:ru",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=t("lang_ukrainian", "uk"),
                        callback_data="onboard:lang:uk",
                    )
                ],
            ]
        )

    @staticmethod
    def auto_role_picker_keyboard(lang: str | None = None) -> ReplyKeyboardMarkup:
        language = normalize_language(lang)
        rows = [
            [KeyboardButton(text=role_label("buyer", language)), KeyboardButton(text=role_label("seller", language))],
            [KeyboardButton(text=role_label("dealer", language)), KeyboardButton(text=role_label("marketplace", language))],
            [KeyboardButton(text=role_label("partner", language)), KeyboardButton(text=role_label("insurance", language))],
            [KeyboardButton(text=role_label("bank", language)), KeyboardButton(text=role_label("logistics", language))],
            [KeyboardButton(text=role_label("legal_partner", language))],
            [KeyboardButton(text=role_label("service_station", language)), KeyboardButton(text=role_label("parts_store", language))],
        ]
        return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

    @staticmethod
    def settings_menu_keyboard(lang: str | None = None) -> ReplyKeyboardMarkup:
        language = normalize_language(lang)
        cart_label = "🛒 Кошик" if language == "uk" else "🛒 Корзина"
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=cart_label)],
                [KeyboardButton(text=t("settings_language", language))],
                [KeyboardButton(text=btn("back", language))],
            ],
            resize_keyboard=True,
        )

    @staticmethod
    def parse_deep_link(args: str | None) -> str | None:
        """Legacy parser — returns vertical key only."""
        entry = resolve_entry_link(args)
        if entry:
            return entry.vertical
        return legacy_vertical_from_args(args)

    @staticmethod
    def parse_entry_link_code(args: str | None) -> str | None:
        """Returns entry link code (auto_client, agro, ...)."""
        from services.start_payload_parser import parse_start_payload

        payload = parse_start_payload(args)
        if payload.link_code and payload.link_code in ENTRY_LINK_REGISTRY:
            return payload.link_code
        return legacy_vertical_from_args(args)
