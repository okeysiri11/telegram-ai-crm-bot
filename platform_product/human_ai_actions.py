"""Epic 46.0 — dual Human / AI action pairs."""
from __future__ import annotations

DUAL_ACTIONS: tuple[dict[str, str], ...] = (
    {"manual_ru": "Создать проект", "ai_ru": "Создай проект.", "route": "/projects"},
    {"manual_ru": "Создать рекламу", "ai_ru": "Сделай рекламу.", "route": "/ai-studio"},
    {"manual_ru": "Создать документ", "ai_ru": "Подготовь договор.", "route": "/documents"},
    {"manual_ru": "Добавить клиента", "ai_ru": "Найди и создай клиента.", "route": "/crm"},
    {"manual_ru": "Создать Workflow", "ai_ru": "Создай Workflow.", "route": "/workflows"},
    {"manual_ru": "Открыть память", "ai_ru": "Продолжим.", "route": "/ai-workspace"},
    {"manual_ru": "Запустить анализ", "ai_ru": "Запусти анализ.", "route": "/analytics"},
    {"manual_ru": "Создать видео", "ai_ru": "Создай видео.", "route": "/ai-studio"},
)

def dual_actions() -> list[dict[str, str]]:
    return [dict(a) for a in DUAL_ACTIONS]
