"""
Sprint 46.5 — deterministic vertical navigation (before AI / Hercules).

Reconnects existing Auto / Agro / Beauty / Crypto menus via view-as personas.
"""

from __future__ import annotations

import logging
from typing import Any

from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup

from services.vertical_role_registry import (
    BTN_BACK,
    BTN_CONCIERGE_OPTIONAL,
    BTN_MAIN_MENU,
    BTN_SWITCH_ROLE,
    PERSONA_LABEL_RU,
    VERTICAL_TITLE_RU,
    VerticalSession,
    vertical_role_registry,
)

logger = logging.getLogger(__name__)

# Messages that MUST NEVER appear when opening a vertical workspace
FORBIDDEN_VERTICAL_NAV_PHRASES = (
    "напишите консьержу",
    "откройте студию",
    "опишите задачу",
    "через ai консьержа",
    "describe your task",
    "open ai studio",
    "write to concierge",
    "откройте студию ai",
)


def role_selector_keyboard(vertical_id: str) -> ReplyKeyboardMarkup:
    personas = vertical_role_registry.personas_for(vertical_id)
    rows: list[list[KeyboardButton]] = []
    row: list[KeyboardButton] = []
    for code in personas:
        row.append(KeyboardButton(text=PERSONA_LABEL_RU[code]))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([KeyboardButton(text=BTN_BACK)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def switch_role_keyboard(vertical_id: str, active_persona: str | None) -> ReplyKeyboardMarkup:
    personas = vertical_role_registry.personas_for(vertical_id)
    rows: list[list[KeyboardButton]] = []
    for code in personas:
        rows.append([KeyboardButton(text=PERSONA_LABEL_RU[code])])
    rows.append([KeyboardButton(text=BTN_BACK)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def _agro_client_menu() -> ReplyKeyboardMarkup:
    """Client subset of existing Agro buttons — no mock module."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🌾 Товары"), KeyboardButton(text="📈 Цены")],
            [KeyboardButton(text="📑 Контракты"), KeyboardButton(text="👥 Контрагенты")],
            [KeyboardButton(text=BTN_SWITCH_ROLE), KeyboardButton(text=BTN_MAIN_MENU)],
            [KeyboardButton(text=BTN_CONCIERGE_OPTIONAL)],
            [KeyboardButton(text=BTN_BACK)],
        ],
        resize_keyboard=True,
    )


def with_vertical_nav_row(base: ReplyKeyboardMarkup) -> ReplyKeyboardMarkup:
    """Append switch-role / main / optional Concierge — Concierge never replaces the menu."""
    rows = [list(r) for r in base.keyboard]
    rows.append(
        [
            KeyboardButton(text=BTN_SWITCH_ROLE),
            KeyboardButton(text=BTN_MAIN_MENU),
        ]
    )
    rows.append([KeyboardButton(text=BTN_CONCIERGE_OPTIONAL)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


# Back-compat alias
_with_nav_row = with_vertical_nav_row


async def _resolve_auth_role(user_id: int) -> str:
    try:
        from config import OWNER_ID

        if OWNER_ID and int(user_id) == int(OWNER_ID):
            return "platform_owner"
    except Exception:
        pass
    try:
        from services.pg_platform_permissions_engine import PlatformPermissionsEngineV1

        if await PlatformPermissionsEngineV1.user_has_permission(user_id, "platform_admin"):
            return "platform_owner"
    except Exception:
        pass
    return "user"


def clear_stale_vertical_context(user_id: int, *, new_vertical: str | None) -> None:
    """Clear temporary vertical/FSM/AI sticky context without touching identity."""
    try:
        from auto_vertical_handlers import (
            auto_billing_flow,
            auto_vertical_active,
            auto_vertical_flow,
            auto_vertical_section,
        )

        if new_vertical != "auto":
            auto_vertical_active.pop(user_id, None)
        auto_vertical_flow.pop(user_id, None)
        auto_vertical_section.pop(user_id, None)
        auto_billing_flow.pop(user_id, None)
    except Exception:
        logger.debug("auto vertical clear skipped", exc_info=True)

    try:
        import handlers as h

        if hasattr(h, "active_module"):
            cur = h.active_module.get(user_id)
            beauty_mod = "cafe_beauty" if new_vertical == "beauty" else new_vertical
            if cur and cur != beauty_mod and cur != new_vertical:
                h.active_module.pop(user_id, None)
            if new_vertical is None:
                h.active_module.pop(user_id, None)
        if hasattr(h, "active_agro_sub") and new_vertical != "agro":
            h.active_agro_sub.pop(user_id, None)
        if hasattr(h, "crypto_otc_flow") and new_vertical != "crypto":
            h.crypto_otc_flow.pop(user_id, None)
    except Exception:
        logger.debug("handlers module clear skipped", exc_info=True)

    try:
        from platform_ai_command.memory.context import context_memory

        context_memory.update(
            str(user_id),
            vertical=new_vertical,
            role=None,
            project=None,
        )
    except Exception:
        logger.debug("context_memory clear skipped", exc_info=True)


async def open_vertical_entry(message: Message, vertical_id: str, *, state: Any = None) -> VerticalSession:
    """Show role selector — NEVER call Hercules."""
    user_id = message.from_user.id if message.from_user else 0
    if state is not None:
        try:
            await state.clear()
        except Exception:
            pass

    clear_stale_vertical_context(user_id, new_vertical=vertical_id)
    auth = await _resolve_auth_role(user_id)
    vertical_role_registry.ensure_authenticated_role(user_id, auth)
    sess = vertical_role_registry.begin_vertical(user_id, vertical_id)

    title = VERTICAL_TITLE_RU.get(vertical_id, vertical_id.upper())
    await message.answer(
        f"{title}\n\nРабочее пространство.\nКак хотите открыть раздел?",
        reply_markup=role_selector_keyboard(vertical_id),
    )
    logger.info(
        "VERTICAL_NAV entry user=%s vertical=%s auth=%s hercules=0",
        user_id,
        vertical_id,
        sess.authenticated_role,
    )
    return sess


async def enter_persona_home(message: Message, persona: str) -> VerticalSession:
    """Open real existing menu for vertical + persona."""
    user_id = message.from_user.id if message.from_user else 0
    sess = vertical_role_registry.get(user_id)
    if not sess.active_vertical:
        await message.answer("Сначала выберите раздел (Auto, Agro, Beauty…).")
        return sess

    sess = vertical_role_registry.set_persona(user_id, persona)
    auth = sess.authenticated_role
    vertical = sess.active_vertical
    crumb = sess.breadcrumb()

    try:
        from platform_ai_command.memory.context import context_memory

        context_memory.update(
            str(user_id),
            vertical=vertical,
            role=persona,
            authenticated_role=auth,
        )
    except Exception:
        pass

    await message.answer(
        f"{crumb}\n\nПросмотр от имени: {PERSONA_LABEL_RU.get(persona, persona)}\n"
        f"Авторизация: {auth} (не меняется)."
    )

    if vertical == "auto":
        await _enter_auto(message, user_id, persona)
    elif vertical == "agro":
        await _enter_agro(message, user_id, persona)
    elif vertical == "beauty":
        await _enter_beauty(message, user_id, persona)
    elif vertical == "crypto":
        await _enter_crypto(message, user_id, persona)
    elif vertical == "legal":
        from keyboards import law_module_menu

        await message.answer(
            "⚖ Юриспруденция — рабочее меню",
            reply_markup=_with_nav_row(law_module_menu()),
        )
    elif vertical == "drone":
        from keyboards import drone_module_menu

        await message.answer(
            "🚁 Дроны — рабочее меню",
            reply_markup=_with_nav_row(drone_module_menu()),
        )
    elif vertical == "travel":
        await _enter_travel(message, user_id, persona)
    else:
        await message.answer(
            f"Раздел {vertical} · {persona}\n\nФункциональное меню раздела.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text=BTN_SWITCH_ROLE)],
                    [KeyboardButton(text=BTN_MAIN_MENU)],
                    [KeyboardButton(text=BTN_CONCIERGE_OPTIONAL)],
                ],
                resize_keyboard=True,
            ),
        )

    logger.info(
        "VERTICAL_NAV home user=%s vertical=%s persona=%s auth=%s",
        user_id,
        vertical,
        persona,
        auth,
    )
    return sess


async def _enter_auto(message: Message, user_id: int, persona: str) -> None:
    from auto_vertical_handlers import auto_vertical_active, handle_auto_menu_request
    from keyboards import auto_client_menu, auto_vertical_menu

    auto_vertical_active[user_id] = True
    if persona == "client":
        await message.answer(
            "🚗 Auto · Client\n\nКлиентский интерфейс.",
            reply_markup=_with_nav_row(auto_client_menu()),
        )
        return
    if persona == "dealer":
        await message.answer(
            "🚗 Auto · Dealer\n\nИнтерфейс дилера — существующие функции Auto.",
            reply_markup=_with_nav_row(auto_vertical_menu()),
        )
        return
    # owner — full hub via existing opener
    await handle_auto_menu_request(message)
    await message.answer(
        f"{BTN_SWITCH_ROLE} — сменить роль просмотра · {BTN_MAIN_MENU} — выход",
    )


async def _enter_agro(message: Message, user_id: int, persona: str) -> None:
    import handlers as h
    from keyboards import agro_menu

    h.active_module[user_id] = "agro"
    if hasattr(h, "active_agro_sub"):
        h.active_agro_sub.pop(user_id, None)

    if persona == "client":
        await message.answer(
            "🌾 Agro · Client\n\nПоиск товара, заявки, контрагенты.",
            reply_markup=_agro_client_menu(),
        )
        return
    # owner + trader → real agro_menu
    label = "Owner" if persona == "owner" else "Trader"
    await message.answer(
        f"🌾 Agro · {label}\n\nРаздел Agro Trading",
        reply_markup=_with_nav_row(agro_menu()),
    )


async def _enter_beauty(message: Message, user_id: int, persona: str) -> None:
    import handlers as h
    from keyboards import cafe_beauty_module_menu

    h.active_module[user_id] = "cafe_beauty"
    labels = {
        "owner": "Owner",
        "manager": "Manager",
        "specialist": "Specialist",
        "client": "Client",
    }
    await message.answer(
        f"💄 Beauty · {labels.get(persona, persona)}\n\nCafe & Beauty — рабочее меню",
        reply_markup=_with_nav_row(cafe_beauty_module_menu()),
    )


async def _enter_crypto(message: Message, user_id: int, persona: str) -> None:
    from handlers import open_crypto_otc

    await open_crypto_otc(message)
    # Tip only — do not replace crypto_otc_menu keyboard
    await message.answer(
        f"Просмотр: {PERSONA_LABEL_RU.get(persona, persona)}\n"
        f"{BTN_SWITCH_ROLE} · {BTN_MAIN_MENU} · {BTN_CONCIERGE_OPTIONAL}",
    )


async def _enter_travel(message: Message, user_id: int, persona: str) -> None:
    import handlers as h
    from keyboards import travel_module_menu

    if hasattr(h, "active_module"):
        h.active_module[user_id] = "travel"
    label = PERSONA_LABEL_RU.get(persona, persona)
    await message.answer(
        f"✈ Travel · {label}\n\n"
        "Туры · бронирования · отели · авиа · документы · платежи.",
        reply_markup=_with_nav_row(travel_module_menu()),
    )


async def show_switch_role(message: Message) -> None:
    sess = vertical_role_registry.get(message.from_user.id if message.from_user else 0)
    if not sess.active_vertical:
        await message.answer("Сначала откройте раздел.")
        return
    vertical_role_registry.begin_vertical(message.from_user.id, sess.active_vertical)
    await message.answer(
        f"{VERTICAL_TITLE_RU.get(sess.active_vertical, sess.active_vertical)}\n\n"
        "Выберите роль просмотра (авторизация Owner не меняется):",
        reply_markup=role_selector_keyboard(sess.active_vertical),
    )


async def go_main_menu(message: Message, *, state: Any = None) -> None:
    user_id = message.from_user.id if message.from_user else 0
    if state is not None:
        try:
            await state.clear()
        except Exception:
            pass
    clear_stale_vertical_context(user_id, new_vertical=None)
    vertical_role_registry.clear_vertical(user_id)
    try:
        from services.telegram_ai_super_app.keyboards import main_menu_keyboard

        await message.answer(
            "🏠 Главное меню\n\nВыберите вертикаль (рабочее пространство) или опционального AI-помощника.",
            reply_markup=main_menu_keyboard(
                include_developer=await _resolve_auth_role(user_id) == "platform_owner"
            ),
        )
    except Exception:
        from keyboards import owner_main_menu

        await message.answer("🏠 Главное меню", reply_markup=owner_main_menu())


async def go_back(message: Message, *, state: Any = None) -> None:
    """Predictable back stack: home → role selector → main menu."""
    user_id = message.from_user.id if message.from_user else 0
    sess = vertical_role_registry.get(user_id)
    if sess.fsm_state == "vertical_home" and sess.active_vertical:
        await open_vertical_entry(message, sess.active_vertical, state=state)
        return
    if sess.fsm_state == "vertical_entry" or sess.active_vertical:
        await go_main_menu(message, state=state)
        return
    await go_main_menu(message, state=state)
