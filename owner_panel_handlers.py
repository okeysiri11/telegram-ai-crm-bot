# Owner Panel — entry link registry and vertical notes.

from __future__ import annotations

import logging
import uuid

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, Message

from config import OWNER_ID
from database import log_audit
from keyboards import owner_main_menu, owner_panel_menu
from services.pg_tenant_entry_registry_engine import TenantRoutingEngineV1

logger = logging.getLogger(__name__)

owner_panel_router = Router()

owner_panel_active: set[int] = set()
owner_notes_edit_flow: dict[int, dict] = {}


def _is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


async def _bot_username(bot: Bot) -> str:
    me = await bot.get_me()
    return me.username or ""


@owner_panel_router.message(F.text == "👑 Owner Panel")
async def open_owner_panel(message: Message) -> None:
    user_id = message.from_user.id
    if not _is_owner(user_id):
        await message.answer("Нет доступа.", reply_markup=owner_main_menu())
        return
    owner_panel_active.add(user_id)
    log_audit(user_id, "open", "owner_panel")
    await message.answer(
        "👑 Owner Panel\n\nУправление точками входа и заметками.",
        reply_markup=owner_panel_menu(),
    )


@owner_panel_router.message(
    lambda m: m.from_user.id in owner_panel_active
    and m.text in {
        "🔗 Entry Links",
        "📝 Notes",
        "⬅ Назад",
    }
)
async def owner_panel_screen(message: Message, bot: Bot) -> None:
    user_id = message.from_user.id
    if not _is_owner(user_id):
        return

    if message.text == "⬅ Назад":
        owner_panel_active.discard(user_id)
        owner_notes_edit_flow.pop(user_id, None)
        await message.answer("Главное меню", reply_markup=owner_main_menu())
        return

    if message.text == "🔗 Entry Links":
        await TenantRoutingEngineV1.ensure_registry_seeded()
        links = await TenantRoutingEngineV1.list_active_entry_links()
        username = await _bot_username(bot)
        text = TenantRoutingEngineV1.format_entry_links_text(links, bot_username=username)
        await message.answer(
            text,
            parse_mode="Markdown",
            reply_markup=TenantRoutingEngineV1.entry_links_inline(links, bot_username=username),
        )
        return

    if message.text == "📝 Notes":
        text = await TenantRoutingEngineV1.format_notes_grouped()
        verticals = TenantRoutingEngineV1.verticals_from_registry()
        await message.answer(
            text,
            reply_markup=TenantRoutingEngineV1.notes_vertical_inline(verticals),
        )


@owner_panel_router.callback_query(F.data.startswith("owner:link:copy:"))
async def owner_copy_link(callback: CallbackQuery, bot: Bot) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    if not _is_owner(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    code = callback.data.rsplit(":", 1)[-1]
    username = await _bot_username(bot)
    url = TenantRoutingEngineV1.build_deeplink(username, code)
    cfg = TenantRoutingEngineV1.resolve_entry_config(code)
    title = cfg.title_ru if cfg else code
    await callback.answer("Ссылка отправлена")
    await callback.message.answer(
        f"📋 {title}\n\nСкопируйте ссылку:\n`{url}`",
        parse_mode="Markdown",
    )


@owner_panel_router.callback_query(F.data == "owner:panel:back")
async def owner_panel_back(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    user_id = callback.from_user.id
    if not _is_owner(user_id):
        await callback.answer()
        return
    owner_panel_active.add(user_id)
    await callback.answer()
    await callback.message.answer(
        "👑 Owner Panel",
        reply_markup=owner_panel_menu(),
    )


@owner_panel_router.callback_query(F.data.startswith("owner:notes:vertical:"))
async def owner_notes_vertical(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    if not _is_owner(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    vertical = callback.data.rsplit(":", 1)[-1]
    notes = await TenantRoutingEngineV1.get_notes_for_vertical(vertical)
    lines = [f"📝 Notes — {vertical.upper()}", ""]
    if not notes:
        lines.append("Заметок пока нет.")
    else:
        for note in notes:
            preview = (note.content or "—").split("\n", 1)[0][:120]
            lines.append(f"• {note.title}: {preview}")
    await callback.answer()
    await callback.message.answer(
        "\n".join(lines),
        reply_markup=TenantRoutingEngineV1.notes_list_inline(notes, vertical=vertical),
    )


@owner_panel_router.callback_query(F.data.startswith("owner:notes:edit:"))
async def owner_notes_edit(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    user_id = callback.from_user.id
    if not _is_owner(user_id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    note_id = uuid.UUID(callback.data.rsplit(":", 1)[-1])
    note = await TenantRoutingEngineV1.get_note(note_id)
    if note is None:
        await callback.answer("Заметка не найдена", show_alert=True)
        return
    owner_notes_edit_flow[user_id] = {"note_id": str(note_id), "vertical": note.vertical}
    await callback.answer()
    await callback.message.answer(
        f"✏️ {note.title}\n\nТекущий текст:\n{note.content or '—'}\n\n"
        "Отправьте новый текст заметки одним сообщением."
    )


@owner_panel_router.callback_query(F.data.startswith("owner:notes:new:"))
async def owner_notes_new(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    user_id = callback.from_user.id
    if not _is_owner(user_id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    vertical = callback.data.rsplit(":", 1)[-1]
    tenant_code = vertical
    for cfg in __import__("services.tenant_routing", fromlist=["ENTRY_LINK_REGISTRY"]).ENTRY_LINK_REGISTRY.values():
        if cfg.vertical == vertical:
            tenant_code = cfg.tenant_code
            break
    owner_notes_edit_flow[user_id] = {
        "note_id": None,
        "vertical": vertical,
        "tenant_code": tenant_code,
        "step": "title",
    }
    await callback.answer()
    await callback.message.answer(f"➕ Новая заметка ({vertical})\n\nВведите заголовок:")


@owner_panel_router.callback_query(F.data == "owner:notes:back")
async def owner_notes_back(callback: CallbackQuery) -> None:
    if callback.message is None:
        await callback.answer()
        return
    await callback.answer()
    text = await TenantRoutingEngineV1.format_notes_grouped()
    verticals = TenantRoutingEngineV1.verticals_from_registry()
    await callback.message.answer(
        text,
        reply_markup=TenantRoutingEngineV1.notes_vertical_inline(verticals),
    )


@owner_panel_router.message(lambda m: m.from_user.id in owner_notes_edit_flow)
async def owner_notes_edit_message(message: Message) -> None:
    user_id = message.from_user.id
    if not _is_owner(user_id):
        return
    flow = owner_notes_edit_flow.get(user_id, {})
    text = (message.text or "").strip()
    if not text:
        await message.answer("Введите текст.")
        return

    if flow.get("step") == "title":
        flow["title"] = text
        flow["step"] = "content"
        await message.answer("Введите текст заметки:")
        return

    note_id = flow.get("note_id")
    if note_id:
        await TenantRoutingEngineV1.update_note_content(uuid.UUID(note_id), text)
        owner_notes_edit_flow.pop(user_id, None)
        await message.answer("✅ Заметка обновлена.", reply_markup=owner_panel_menu())
        return

    title = flow.get("title", "Заметка")
    await TenantRoutingEngineV1.create_note(
        tenant_code=flow.get("tenant_code", flow.get("vertical", "auto")),
        vertical=flow.get("vertical", "auto"),
        title=title,
        content=text,
    )
    owner_notes_edit_flow.pop(user_id, None)
    await message.answer("✅ Заметка создана.", reply_markup=owner_panel_menu())
