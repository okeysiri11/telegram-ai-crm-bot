"""Epic 46.0 — Telegram mobile CRM polish rules."""
from __future__ import annotations
from typing import Any

MAX_MENU_DEPTH = 2
LAB_LABEL = "🧪 Лаборатория"
DEV_LABEL = "🚧 Разработка"

# Product main menu ids (max depth 2 from these)
PRODUCT_MENU_IDS = (
    "concierge", "ai_command", "work_mode", "memory", "automation",
    "dashboard", "tasks", "notifications", "business", "ai_studio", "settings", "all_sections",
)

# Hidden by default in production
LAB_HIDDEN_BY_DEFAULT = True

def main_menu_depth_ok(button_count: int) -> bool:
    return button_count <= 14  # one screen-ish

def polish_report(catalog_buttons: list[str], *, include_lab: bool) -> dict[str, Any]:
    return {
        "max_depth": MAX_MENU_DEPTH,
        "lab_label": LAB_LABEL,
        "dev_label": DEV_LABEL,
        "lab_hidden_by_default": LAB_HIDDEN_BY_DEFAULT,
        "include_lab": include_lab,
        "product_buttons": list(catalog_buttons),
        "russian_first": True,
        "engineering_hidden": not include_lab,
    }
