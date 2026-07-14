# Tenant entry registry engine — deep links, owner notes, navigation guards.

from __future__ import annotations

import uuid
from typing import Any

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import BOT_USERNAME, OWNER_ID
from database.session import get_session
from repositories.tenant_entry_registry_repository import (
    OwnerVerticalNoteRepository,
    TenantEntryLinkRepository,
)
from repositories.user_vertical_preferences_repository import UserVerticalPreferencesRepository
from services.automotive_localization import normalize_language, t
from services.tenant_routing import (
    ENTRY_LINK_REGISTRY,
    TENANT_ALLOWED_MODULES,
    VERTICAL_TO_MODULE,
    TenantEntryConfig,
    entry_link_seed_rows,
    format_deeplink_url,
    is_owner,
    module_for_button_text,
    parse_entry_link,
)


class TenantRoutingEngineV1:
    @staticmethod
    async def ensure_registry_seeded() -> None:
        async with get_session() as session:
            repo = TenantEntryLinkRepository(session)
            for row in entry_link_seed_rows():
                code = row.pop("code")
                await repo.upsert_seed(code=code, **row)

    @staticmethod
    async def list_active_entry_links() -> list[dict[str, Any]]:
        async with get_session() as session:
            rows = await TenantEntryLinkRepository(session).list_active()
        return [
            {
                "code": row.code,
                "tenant_code": row.tenant_code,
                "vertical": row.vertical,
                "title_ru": row.title_ru,
                "title_uk": row.title_uk,
                "preset_role": row.preset_role,
                "entry_target": row.entry_target,
            }
            for row in rows
        ]

    @staticmethod
    def resolve_entry_config(code: str) -> TenantEntryConfig | None:
        return ENTRY_LINK_REGISTRY.get(code) or None

    @staticmethod
    async def get_tenant_context(telegram_user_id: int) -> dict[str, Any]:
        async with get_session() as session:
            row = await UserVerticalPreferencesRepository(session).get_by_telegram_id(
                telegram_user_id
            )
        if row is None:
            return {
                "tenant_code": None,
                "source_link": None,
                "vertical": None,
                "role": None,
                "language": "ru",
                "entry_target": None,
                "tenant_scoped": False,
            }
        entry_target = None
        if row.source_link:
            cfg = ENTRY_LINK_REGISTRY.get(row.source_link)
            if cfg:
                entry_target = cfg.entry_target
        tenant_scoped = bool(row.tenant_code) and not is_owner(telegram_user_id)
        return {
            "tenant_code": row.tenant_code,
            "source_link": row.source_link,
            "vertical": row.vertical,
            "role": row.role,
            "language": normalize_language(row.language),
            "entry_target": entry_target,
            "tenant_scoped": tenant_scoped,
            "onboarding_completed": row.onboarding_completed,
        }

    @staticmethod
    async def can_access_module(telegram_user_id: int, module_key: str) -> bool:
        if is_owner(telegram_user_id):
            return True
        ctx = await TenantRoutingEngineV1.get_tenant_context(telegram_user_id)
        if not ctx.get("tenant_scoped"):
            return True
        tenant_code = ctx.get("tenant_code")
        if not tenant_code:
            return True
        allowed = TENANT_ALLOWED_MODULES.get(tenant_code, frozenset())
        return module_key in allowed

    @staticmethod
    async def guard_module_access(telegram_user_id: int, module_key: str) -> bool:
        return await TenantRoutingEngineV1.can_access_module(telegram_user_id, module_key)

    @staticmethod
    async def guard_button_text(telegram_user_id: int, text: str | None) -> bool:
        module_key = module_for_button_text(text)
        if module_key is None:
            return True
        return await TenantRoutingEngineV1.can_access_module(telegram_user_id, module_key)

    @staticmethod
    def build_deeplink(bot_username: str | None, code: str) -> str:
        username = (bot_username or BOT_USERNAME or "your_bot").lstrip("@")
        return format_deeplink_url(username, code)

    @staticmethod
    def format_entry_links_text(
        links: list[dict[str, Any]],
        *,
        bot_username: str | None = None,
        lang: str = "ru",
    ) -> str:
        if not links:
            return "🔗 Entry Links\n\nНет активных ссылок."
        lines = ["🔗 Entry Links", ""]
        for link in links:
            title = link["title_ru"] if lang != "uk" else link["title_uk"]
            url = TenantRoutingEngineV1.build_deeplink(bot_username, link["code"])
            lines.append(f"{title}")
            lines.append(f"`{url}`")
            lines.append("")
        return "\n".join(lines).strip()

    @staticmethod
    def entry_links_inline(
        links: list[dict[str, Any]],
        *,
        bot_username: str | None = None,
    ) -> InlineKeyboardMarkup:
        rows: list[list[InlineKeyboardButton]] = []
        for link in links:
            url = TenantRoutingEngineV1.build_deeplink(bot_username, link["code"])
            rows.append([
                InlineKeyboardButton(
                    text=f"📋 {link['title_ru']}",
                    callback_data=f"owner:link:copy:{link['code']}",
                )
            ])
            rows.append([
                InlineKeyboardButton(text="🔗 Open", url=url),
            ])
        rows.append([InlineKeyboardButton(text="⬅ Назад", callback_data="owner:panel:back")])
        return InlineKeyboardMarkup(inline_keyboard=rows)

    @staticmethod
    async def format_notes_grouped(lang: str = "ru") -> str:
        async with get_session() as session:
            grouped = await OwnerVerticalNoteRepository(session).list_all_grouped()
        if not grouped:
            return "📝 Notes\n\nЗаметок пока нет."
        lines = ["📝 Notes", ""]
        for vertical in sorted(grouped.keys()):
            lines.append(f"▸ {vertical.upper()}")
            for note in grouped[vertical]:
                preview = (note.content or "—").split("\n", 1)[0][:80]
                lines.append(f"  • {note.title}: {preview}")
            lines.append("")
        return "\n".join(lines).strip()

    @staticmethod
    def notes_vertical_inline(verticals: list[str]) -> InlineKeyboardMarkup:
        rows = [
            [InlineKeyboardButton(text=v.upper(), callback_data=f"owner:notes:vertical:{v}")]
            for v in verticals
        ]
        rows.append([InlineKeyboardButton(text="⬅ Назад", callback_data="owner:panel:back")])
        return InlineKeyboardMarkup(inline_keyboard=rows)

    @staticmethod
    def notes_list_inline(notes: list[Any], *, vertical: str) -> InlineKeyboardMarkup:
        rows = []
        for note in notes:
            rows.append([
                InlineKeyboardButton(
                    text=f"✏️ {note.title}",
                    callback_data=f"owner:notes:edit:{note.id}",
                )
            ])
        rows.append([
            InlineKeyboardButton(text="➕ Новая", callback_data=f"owner:notes:new:{vertical}")
        ])
        rows.append([InlineKeyboardButton(text="⬅ Назад", callback_data="owner:notes:back")])
        return InlineKeyboardMarkup(inline_keyboard=rows)

    @staticmethod
    async def get_notes_for_vertical(vertical: str) -> list[OwnerVerticalNote]:
        async with get_session() as session:
            return await OwnerVerticalNoteRepository(session).list_by_vertical(vertical)

    @staticmethod
    async def update_note_content(note_id: uuid.UUID, content: str) -> bool:
        async with get_session() as session:
            row = await OwnerVerticalNoteRepository(session).update_content(note_id, content)
            return row is not None

    @staticmethod
    async def create_note(
        *,
        tenant_code: str,
        vertical: str,
        title: str,
        content: str = "",
    ) -> uuid.UUID:
        async with get_session() as session:
            row = await OwnerVerticalNoteRepository(session).create(
                tenant_code=tenant_code,
                vertical=vertical,
                title=title,
                content=content,
            )
            return row.id

    @staticmethod
    async def get_note(note_id: uuid.UUID):
        async with get_session() as session:
            return await OwnerVerticalNoteRepository(session).get_by_id(note_id)

    @staticmethod
    def verticals_from_registry() -> list[str]:
        return sorted({cfg.vertical for cfg in ENTRY_LINK_REGISTRY.values()})

    @staticmethod
    async def tenant_denied_message(telegram_user_id: int, lang: str | None = None) -> str:
        ctx = await TenantRoutingEngineV1.get_tenant_context(telegram_user_id)
        language = normalize_language(lang or ctx.get("language"))
        tenant = ctx.get("tenant_code") or "—"
        if language == "uk":
            return (
                f"🔒 Доступ обмежено\n\n"
                f"Ваш tenant: {tenant}\n"
                f"Цей розділ недоступний для вашого входу."
            )
        return (
            f"🔒 Доступ ограничен\n\n"
            f"Ваш tenant: {tenant}\n"
            f"Этот раздел недоступен для вашей точки входа."
        )

    @staticmethod
    def module_for_vertical(vertical: str | None) -> str | None:
        if not vertical:
            return None
        return VERTICAL_TO_MODULE.get(vertical, vertical)
