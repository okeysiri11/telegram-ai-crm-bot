"""Client adapters for Platform Registry."""

from platform_registry.clients.telegram_adapter import (
    build_owner_keyboard_from_registry,
    navigation_payload_for_telegram,
    telegram_menu_rows,
)
from platform_registry.clients.web_adapter import web_navigation_groups, web_navigation_payload

__all__ = [
    "build_owner_keyboard_from_registry",
    "navigation_payload_for_telegram",
    "telegram_menu_rows",
    "web_navigation_groups",
    "web_navigation_payload",
]
