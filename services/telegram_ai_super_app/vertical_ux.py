"""Telegram UX bridge for Vertical AI Framework (Sprint 43.4)."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from platform_vertical_ai.framework import VerticalAiFramework, vertical_ai_framework
from platform_vertical_ai.models import VerticalMenuItem
from services.telegram_ai_super_app.catalog import BTN


def vertical_menu_keyboard(vertical_id: str, *, fw: VerticalAiFramework | None = None) -> ReplyKeyboardMarkup:
    framework = fw or vertical_ai_framework
    items = framework.menu_items(vertical_id)
    rows: list[list[KeyboardButton]] = []
    row: list[KeyboardButton] = []
    for item in items:
        row.append(KeyboardButton(text=item.label))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([KeyboardButton(text=BTN.ASK_AI), KeyboardButton(text=BTN.BACK_STUDIO)])
    rows.append([KeyboardButton(text=BTN.BACK_MAIN)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def calendar_periods_inline(vertical_id: str, *, fw: VerticalAiFramework | None = None) -> InlineKeyboardMarkup:
    framework = fw or vertical_ai_framework
    cfg = framework.get(vertical_id)
    rows = [
        [InlineKeyboardButton(text=f"{d} дней", callback_data=f"tsv:cal:{vertical_id}:{d}")]
        for d in cfg.calendar_periods
    ]
    rows.append([InlineKeyboardButton(text="Закрыть", callback_data="tsa:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def publish_after_vertical_inline(job_id: str) -> InlineKeyboardMarkup:
    actions = (
        ("publish", "📤 Опубликовать"),
        ("schedule", "📅 Запланировать"),
        ("download", "📥 Скачать"),
        ("staff", "👤 Сотруднику"),
        ("client", "💬 Клиенту"),
        ("fav", "❤️ В избранное"),
        ("chain", "▶ Вся цепочка"),
        ("retry", "🔄 Повторить"),
    )
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for action, label in actions:
        cb = f"tsv:act:{action}:{job_id}"
        if action == "fav":
            cb = f"tsa:fav:{job_id}"
        elif action == "retry":
            cb = f"tsa:retry:{job_id}"
        row.append(InlineKeyboardButton(text=label, callback_data=cb))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def is_vertical_menu_label(vertical_id: str, text: str, *, fw: VerticalAiFramework | None = None) -> VerticalMenuItem | None:
    framework = fw or vertical_ai_framework
    return framework.resolve_menu(vertical_id, text or "")
