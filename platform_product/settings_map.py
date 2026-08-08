"""Epic 46.0 — unified Settings map (single /settings hub)."""
from __future__ import annotations
from platform_product.russian_first import SETTINGS_SECTIONS_RU

# Canonical tab ids under /settings?tab=
SETTINGS_TABS: tuple[dict[str, str], ...] = (
    {"id": "profile", "label_ru": "Профиль", "path": "/settings?tab=profile"},
    {"id": "organization", "label_ru": "Организация", "path": "/settings?tab=organization"},
    {"id": "ai", "label_ru": "AI", "path": "/settings?tab=ai"},
    {"id": "voice", "label_ru": "Голос", "path": "/settings?tab=voice"},
    {"id": "telegram", "label_ru": "Telegram", "path": "/settings?tab=telegram"},
    {"id": "integrations", "label_ru": "Интеграции", "path": "/settings?tab=integrations"},
    {"id": "security", "label_ru": "Безопасность", "path": "/settings?tab=security"},
    {"id": "notifications", "label_ru": "Уведомления", "path": "/settings?tab=notifications"},
    {"id": "models", "label_ru": "Модели", "path": "/settings?tab=models"},
    {"id": "memory", "label_ru": "Память", "path": "/settings?tab=memory"},
    {"id": "automation", "label_ru": "Автоматизация", "path": "/settings?tab=automation"},
    {"id": "license", "label_ru": "Лицензия", "path": "/settings?tab=license"},
    {"id": "interface", "label_ru": "Интерфейс", "path": "/settings?tab=interface"},
    {"id": "general", "label_ru": "Общие", "path": "/settings?tab=general"},
)

# Legacy aliases → canonical
SETTINGS_ALIASES = {
    "/settings/ai-mode": "/settings?tab=ai",
    "/settings/ai": "/settings?tab=ai",
    "/workspace/settings": "/settings?tab=organization",
}

def canonical_settings_tabs() -> list[dict[str, str]]:
    return [dict(t) for t in SETTINGS_TABS]

def assert_sections_cover_glossary() -> bool:
    labels = {t["label_ru"] for t in SETTINGS_TABS}
    return all(s in labels or s == "AI" for s in SETTINGS_SECTIONS_RU)
