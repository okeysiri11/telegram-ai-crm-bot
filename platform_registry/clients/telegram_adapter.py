"""Telegram client adapter — builds keyboards from Menu Catalog (no platform logic in keyboards)."""

from __future__ import annotations

from typing import Any

from platform_registry.navigation import filter_menu
from platform_registry.service import platform_registry
from platform_registry.visibility import ClientId


def telegram_menu_rows(
    *,
    roles: list[str] | None = None,
    permissions: list[str] | None = None,
    include_owner: bool = True,
    max_per_row: int = 2,
) -> list[list[str]]:
    """Return ReplyKeyboard row labels from the unified catalog."""
    items = filter_menu(
        client=ClientId.TELEGRAM.value,
        roles=roles or (["owner"] if include_owner else ["guest"]),
        permissions=permissions,
        include_owner=include_owner,
    )
    labels: list[str] = []
    for item in items:
        if not item.telegram_command:
            continue
        # Prefer human telegram button text when it looks like a label
        label = item.telegram_command
        if label.startswith("/") or "_" in label and " " not in label and not any(
            ord(c) > 127 for c in label
        ):
            # machine id — use title
            label = item.title
        if label not in labels:
            labels.append(label)

    rows: list[list[str]] = []
    row: list[str] = []
    for label in labels:
        row.append(label)
        if len(row) >= max_per_row:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return rows


def build_owner_keyboard_from_registry(*, show_automotive: bool = True) -> Any:
    """
    Preferred owner keyboard — Sprint 43.0 Super App shell (simple RU menu).
    Full registry catalog remains available via «📂 Все разделы» / Developer Tools.
    """
    try:
        from services.telegram_ai_super_app.keyboards import main_menu_keyboard

        return main_menu_keyboard(include_developer=False)
    except Exception:
        pass
    try:
        from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
    except Exception:
        return telegram_menu_rows(roles=["owner"], include_owner=True)

    rows_labels = telegram_menu_rows(roles=["owner"], include_owner=True)
    if not show_automotive:
        rows_labels = [
            [c for c in row if "Авто" not in c and "auto" not in c.lower()]
            for row in rows_labels
        ]
        rows_labels = [r for r in rows_labels if r]

    keyboard = [[KeyboardButton(text=cell) for cell in row] for row in rows_labels]
    if not keyboard:
        from keyboards import owner_main_menu

        return owner_main_menu(show_automotive=show_automotive)
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def navigation_payload_for_telegram(roles: list[str] | None = None) -> dict[str, Any]:
    return platform_registry.navigation_for(
        client=ClientId.TELEGRAM.value,
        roles=roles or ["owner"],
        include_owner=True,
    )
