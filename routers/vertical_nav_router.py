"""
Sprint 46.5 — Vertical navigation router.

Priority: AFTER add-car FSM, BEFORE Super App / AI Command / Hercules.
Deterministic vertical + role selection never calls Hercules.
"""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from services.vertical_nav_service import (
    enter_persona_home,
    go_back,
    go_main_menu,
    open_vertical_entry,
    show_switch_role,
)
from services.vertical_role_registry import (
    BTN_BACK,
    BTN_MAIN_MENU,
    BTN_SWITCH_ROLE,
    PERSONA_BUTTONS,
    VERTICAL_ENTRY_LABELS,
    vertical_role_registry,
)

logger = logging.getLogger(__name__)

router = Router(name="vertical_nav")

_ENTRY_LABELS = frozenset(VERTICAL_ENTRY_LABELS.keys())
_PERSONA_LABELS = frozenset(PERSONA_BUTTONS)

_TRAVEL_SECTIONS: dict[str, str] = {
    "🗺 Туры": "Раздел «Туры»: каталог направлений и пакетных предложений.",
    "📅 Бронирования": "Раздел «Бронирования»: активные и ожидающие брони.",
    "👥 Клиенты Travel": "Раздел «Клиенты»: карточки путешественников.",
    "🏨 Отели": "Раздел «Отели»: размещение и подтверждения.",
    "✈ Авиабилеты": "Раздел «Авиабилеты»: рейсы и выписка.",
    "📄 Документы Travel": "Раздел «Документы»: визы и пакеты документов.",
    "💳 Платежи Travel": "Раздел «Платежи»: оплаты по бронированиям.",
    "📊 Аналитика Travel": "Раздел «Аналитика»: загрузка и продажи Travel.",
}


def _is_vertical_entry(message: Message) -> bool:
    text = (message.text or "").strip()
    vertical_id = VERTICAL_ENTRY_LABELS.get(text)
    if not vertical_id or not message.from_user:
        return False
    sess = vertical_role_registry.get(message.from_user.id)
    # Already inside this workspace — do not steal module sub-buttons / re-prompt AI
    if sess.active_vertical == vertical_id and sess.fsm_state == "vertical_home":
        return False
    return True


@router.message(_is_vertical_entry)
async def vertical_entry_button(message: Message, state: FSMContext) -> None:
    vertical_id = vertical_role_registry.resolve_entry_label(message.text)
    if not vertical_id:
        return
    logger.info(
        "TELEGRAM_UPDATE handler_selected=vertical_entry_button vertical=%s text=%r",
        vertical_id,
        message.text,
    )
    await open_vertical_entry(message, vertical_id, state=state)


@router.message(
    lambda m: (
        bool(m.text)
        and m.text.strip() in _PERSONA_LABELS
        and vertical_role_registry.get(m.from_user.id).fsm_state
        in {"vertical_entry", "vertical_home"}
        and vertical_role_registry.get(m.from_user.id).active_vertical is not None
    )
)
async def vertical_persona_selected(message: Message, state: FSMContext) -> None:
    persona = vertical_role_registry.resolve_persona_label(message.text)
    if not persona:
        return
    sess = vertical_role_registry.get(message.from_user.id)
    allowed = vertical_role_registry.personas_for(sess.active_vertical or "")
    if persona not in allowed:
        await message.answer("Эта роль недоступна в текущем разделе.")
        return
    await state.clear()
    await enter_persona_home(message, persona)


@router.message(F.text.in_({BTN_SWITCH_ROLE, "🔄 Роль"}))
async def vertical_switch_role(message: Message, state: FSMContext) -> None:
    await show_switch_role(message)


@router.message(F.text == BTN_MAIN_MENU)
async def vertical_main_menu(message: Message, state: FSMContext) -> None:
    await go_main_menu(message, state=state)


@router.message(
    lambda m: (
        bool(m.text)
        and m.text.strip() in {BTN_BACK, "⬅ Назад", "⬅️ Назад"}
        and vertical_role_registry.get(m.from_user.id).active_vertical is not None
    )
)
async def vertical_back(message: Message, state: FSMContext) -> None:
    await go_back(message, state=state)


@router.message(
    lambda m: (
        bool(m.text)
        and m.text.strip() in _TRAVEL_SECTIONS
        and vertical_role_registry.get(m.from_user.id).active_vertical == "travel"
    )
)
async def travel_section(message: Message, state: FSMContext) -> None:
    """Functional Travel sections — never Concierge/Studio prompts."""
    text = (message.text or "").strip()
    body = _TRAVEL_SECTIONS.get(text, text)
    from keyboards import travel_module_menu
    from services.vertical_nav_service import with_vertical_nav_row

    await message.answer(body, reply_markup=with_vertical_nav_row(travel_module_menu()))
