"""Epic 46.0 — Owner unified dashboard widgets (data contract)."""
from __future__ import annotations
from typing import Any

OWNER_WIDGETS = (
    {"id": "workflows", "title_ru": "Работающие Workflow", "route": "/workflows"},
    {"id": "hercules", "title_ru": "Очередь Hercules", "route": "/platform-builder/hercules"},
    {"id": "studio", "title_ru": "Студия AI", "route": "/ai-studio"},
    {"id": "projects", "title_ru": "Последние проекты", "route": "/projects"},
    {"id": "documents", "title_ru": "Последние документы", "route": "/documents"},
    {"id": "generations", "title_ru": "Последние генерации", "route": "/ai-workspace"},
    {"id": "ai_cost", "title_ru": "Расход AI", "route": "/workflows"},
    {"id": "models", "title_ru": "Использование моделей", "route": "/settings?tab=models"},
    {"id": "notifications", "title_ru": "Уведомления", "route": "/notifications"},
    {"id": "recommendations", "title_ru": "Рекомендации AI", "route": "/ai-command"},
    {"id": "quick_actions", "title_ru": "Быстрые действия", "route": "/ai-command"},
)

def owner_dashboard_contract() -> dict[str, Any]:
    return {
        "title_ru": "Панель владельца",
        "widgets": [dict(w) for w in OWNER_WIDGETS],
        "dual_entry": True,
        "russian_first": True,
    }
