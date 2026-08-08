"""Telegram keyboards — Sprint 43.3 product UX (Russian tasks only)."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from services.telegram_ai_super_app.catalog import (
    AI_STUDIO_OPTIONS,
    ALL_SECTIONS,
    BTN,
    BUSINESS_SECTIONS,
    CONCIERGE_EXAMPLES,
    DEVELOPER_MENU_BUTTONS,
    MAIN_MENU_BUTTONS,
    POST_GEN_WORKFLOW,
    PUBLISH_CHANNELS_RU,
)
from services.telegram_ai_super_app.templates import TEMPLATE_CATEGORIES


def main_menu_keyboard(*, include_developer: bool = False) -> ReplyKeyboardMarkup:
    """
    Owner main menu — Sprint 46.5.1

    Vertical workspaces first (manual navigation).
    Concierge / AI Studio are optional assistants — never replace verticals.
    """
    rows: list[list[KeyboardButton]] = []

    # --- Vertical workspaces (MAIN → VERTICAL) ---
    vert_row: list[KeyboardButton] = []
    for btn in BUSINESS_SECTIONS:
        if btn.id == "crm":
            continue
        vert_row.append(KeyboardButton(text=btn.label))
        if len(vert_row) == 2:
            rows.append(vert_row)
            vert_row = []
    if vert_row:
        rows.append(vert_row)

    rows.append([KeyboardButton(text="📇 CRM"), KeyboardButton(text=BTN.BUSINESS)])

    # --- Platform chrome (no Concierge/Studio here — below as optional) ---
    chrome_row: list[KeyboardButton] = []
    for btn in MAIN_MENU_BUTTONS:
        if btn.id in {"business", "concierge", "ai_studio", "ai_command"}:
            continue
        chrome_row.append(KeyboardButton(text=btn.label))
        if len(chrome_row) == 2:
            rows.append(chrome_row)
            chrome_row = []
    if chrome_row:
        rows.append(chrome_row)

    # --- Optional AI (assistant / studio — never the only path) ---
    rows.append(
        [
            KeyboardButton(text=BTN.CONCIERGE),
            KeyboardButton(text=BTN.AI_STUDIO),
        ]
    )
    rows.append([KeyboardButton(text=BTN.AI_COMMAND), KeyboardButton(text=BTN.ASK_AI)])
    if include_developer:
        rows.append([KeyboardButton(text=BTN.DEVELOPER)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def developer_menu_keyboard() -> ReplyKeyboardMarkup:
    rows: list[list[KeyboardButton]] = []
    row: list[KeyboardButton] = []
    for btn in DEVELOPER_MENU_BUTTONS:
        row.append(KeyboardButton(text=btn.label))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([KeyboardButton(text=BTN.BACK_MAIN)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def hercules_menu_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="🟢 Hercules"), KeyboardButton(text="📊 Загрузка")],
        [KeyboardButton(text="🖥 GPU"), KeyboardButton(text="⚙ CPU")],
        [KeyboardButton(text="📦 Очереди"), KeyboardButton(text="🤖 Workers")],
        [KeyboardButton(text="📈 Метрики"), KeyboardButton(text="📜 История")],
        [KeyboardButton(text=BTN.BACK_MAIN)],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def ai_command_menu_keyboard() -> ReplyKeyboardMarkup:
    from platform_ai_command.telegram.menu import menu_labels

    labels = menu_labels()
    rows: list[list[KeyboardButton]] = []
    row: list[KeyboardButton] = []
    for label in labels:
        row.append(KeyboardButton(text=label))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([KeyboardButton(text=BTN.ASK_AI), KeyboardButton(text=BTN.BACK_MAIN)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def work_mode_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⚪ Human Mode"), KeyboardButton(text="🟢 AI Mode")],
            [KeyboardButton(text="🎙 Voice Mode")],
            [KeyboardButton(text="📌 Сделать режимом по умолчанию"), KeyboardButton(text="📌 Запомнить режим")],
            [KeyboardButton(text=BTN.BACK_MAIN)],
        ],
        resize_keyboard=True,
    )


def memory_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Последние разговоры"), KeyboardButton(text="Продолжить работу")],
            [KeyboardButton(text="Проекты"), KeyboardButton(text="Избранное")],
            [KeyboardButton(text="Недавние документы"), KeyboardButton(text="Последние генерации")],
            [KeyboardButton(text="AI Summary"), KeyboardButton(text="Поиск")],
            [KeyboardButton(text=BTN.BACK_MAIN)],
        ],
        resize_keyboard=True,
    )


def automation_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Создать Workflow"), KeyboardButton(text="Мои Workflow")],
            [KeyboardButton(text="Библиотека"), KeyboardButton(text="Активные процессы")],
            [KeyboardButton(text="Запланированные"), KeyboardButton(text="История")],
            [KeyboardButton(text="Фоновые задачи"), KeyboardButton(text="Монитор")],
            [KeyboardButton(text="Настройки"), KeyboardButton(text=BTN.BACK_MAIN)],
        ],
        resize_keyboard=True,
    )


def business_menu_keyboard() -> ReplyKeyboardMarkup:
    rows: list[list[KeyboardButton]] = []
    row: list[KeyboardButton] = []
    for btn in BUSINESS_SECTIONS:
        row.append(KeyboardButton(text=btn.label))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([KeyboardButton(text=BTN.ASK_AI), KeyboardButton(text=BTN.BACK_MAIN)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def all_sections_keyboard(*, include_developer: bool = False) -> ReplyKeyboardMarkup:
    rows: list[list[KeyboardButton]] = []
    row: list[KeyboardButton] = []
    for btn in ALL_SECTIONS:
        if btn.id == "developer" and not include_developer:
            continue
        row.append(KeyboardButton(text=btn.label))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([KeyboardButton(text=BTN.ASK_AI), KeyboardButton(text=BTN.BACK_MAIN)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def ai_studio_keyboard() -> ReplyKeyboardMarkup:
    """Sprint 43.3 — task menu."""
    primary_ids = (
        "image",
        "video",
        "voice",
        "voice_clone",
        "reels",
        "ads",
        "document",
        "presentation",
        "text",
        "prompt",
        "history",
        "favorites",
        "beauty",
        "templates",
        "settings",
    )
    by_id = {o.id: o for o in AI_STUDIO_OPTIONS}
    rows: list[list[KeyboardButton]] = []
    row: list[KeyboardButton] = []
    for pid in primary_ids:
        opt = by_id.get(pid)
        if not opt:
            continue
        # Prefer BTN.BEAUTY label for beauty entry
        label = BTN.BEAUTY if pid == "beauty" else opt.label
        row.append(KeyboardButton(text=label))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([KeyboardButton(text=BTN.ASK_AI), KeyboardButton(text=BTN.BACK_MAIN)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def ask_ai_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN.ASK_AI)],
            [KeyboardButton(text=BTN.AI_STUDIO), KeyboardButton(text=BTN.BACK_MAIN)],
        ],
        resize_keyboard=True,
    )


def concierge_examples_inline() -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for ex in CONCIERGE_EXAMPLES:
        rows.append([InlineKeyboardButton(text=ex, callback_data=f"tsa:ex:{ex[:40]}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def choices_inline(prefix: str, choices: list[str]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=c, callback_data=f"{prefix}:{i}")] for i, c in enumerate(choices)]
    rows.append([InlineKeyboardButton(text="Отмена", callback_data="tsa:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_generate_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BTN.GENERATE_NOW, callback_data="tsa:gen:now")],
            [InlineKeyboardButton(text="Изменить ответы", callback_data="tsa:gen:edit")],
            [InlineKeyboardButton(text="Отмена", callback_data="tsa:cancel")],
        ]
    )


def post_generation_inline(job_id: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for action, label in POST_GEN_WORKFLOW:
        cb = f"tsa:wf:{action}:{job_id}"
        if action == "retry":
            cb = f"tsa:retry:{job_id}"
        elif action == "fav":
            cb = f"tsa:fav:{job_id}"
        elif action == "export":
            cb = f"tsa:export:{job_id}"
        row.append(InlineKeyboardButton(text=label, callback_data=cb))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def publish_channels_inline(job_id: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=label, callback_data=f"tsa:pub:{ch}:{job_id}")]
        for ch, label in PUBLISH_CHANNELS_RU
    ]
    rows.append([InlineKeyboardButton(text="Назад", callback_data=f"tsa:wf:back:{job_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def template_categories_inline() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=cat, callback_data=f"tsa:tplcat:{i}")]
        for i, cat in enumerate(TEMPLATE_CATEGORIES)
    ]
    rows.append([InlineKeyboardButton(text="Закрыть", callback_data="tsa:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def templates_inline(category_index: int, titles: list[str]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=t, callback_data=f"tsa:tpl:{category_index}:{i}")]
        for i, t in enumerate(titles[:12])
    ]
    rows.append([InlineKeyboardButton(text="← Категории", callback_data="tsa:tplcat:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
