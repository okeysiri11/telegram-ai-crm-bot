"""Epic 46.0 — Russian First glossary & UI string policy."""
from __future__ import annotations

# User-facing terms (EN internal → RU UI)
GLOSSARY_RU: dict[str, str] = {
    "Dashboard": "Дашборд",
    "Settings": "Настройки",
    "Workflow": "Автоматизация",
    "Workflows": "Автоматизация",
    "Memory": "Память",
    "Planner": "Планировщик",
    "Automation": "Автоматизация",
    "History": "История",
    "Builder": "Конструктор",
    "Studio": "Студия",
    "Library": "Библиотека",
    "Scheduler": "Планировщик задач",
    "Runner": "Исполнитель",
    "Notifications": "Уведомления",
    "Security": "Безопасность",
    "Integrations": "Интеграции",
    "Profile": "Профиль",
    "Organization": "Организация",
    "Voice": "Голос",
    "Models": "Модели",
    "License": "Лицензия",
    "Search": "Поиск",
    "Command": "Команда",
    "Approve": "Подтвердить",
    "Cancel": "Отмена",
    "Retry": "Повторить",
    "Save": "Сохранить",
    "Delete": "Удалить",
    "Create": "Создать",
    "Edit": "Редактировать",
    "Loading": "Загрузка…",
    "Error": "Ошибка",
    "Success": "Успешно",
    "Warning": "Внимание",
    "Info": "Информация",
}

# Forbidden raw English UI tokens in product surfaces (case-sensitive checks for whole words)
FORBIDDEN_UI_EN = (
    "Click here",
    "Submit",
    "Cancel",
    "Loading...",
    "Something went wrong",
    "Not found",
    "Access denied",
    "Settings",
    "Dashboard",
)

SETTINGS_SECTIONS_RU = (
    "Профиль",
    "Организация",
    "AI",
    "Голос",
    "Telegram",
    "Интеграции",
    "Безопасность",
    "Уведомления",
    "Модели",
    "Память",
    "Автоматизация",
    "Лицензия",
)

def translate_term(en: str) -> str:
    return GLOSSARY_RU.get(en, en)

def is_forbidden_ui(text: str) -> bool:
    return any(tok in (text or "") for tok in FORBIDDEN_UI_EN)
