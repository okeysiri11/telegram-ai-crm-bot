"""Routing table generated from Menu Catalog."""

from __future__ import annotations

from platform_registry.menus import MENU_CATALOG, MenuItem


def all_routes() -> list[dict[str, str | None]]:
    rows: list[dict[str, str | None]] = []
    for item in MENU_CATALOG:
        if not item.route:
            continue
        rows.append(
            {
                "id": item.id,
                "route": item.route,
                "telegram_command": item.telegram_command,
                "title": item.title,
            }
        )
    return rows


def resolve_route(item_id: str) -> str | None:
    for item in MENU_CATALOG:
        if item.id == item_id:
            return item.route
    return None


def resolve_telegram_command(command: str) -> MenuItem | None:
    needle = command.strip()
    for item in MENU_CATALOG:
        if item.telegram_command and item.telegram_command == needle:
            return item
        if item.telegram_command and item.telegram_command.lstrip("/").lower() == needle.lstrip("/").lower():
            return item
    return None
