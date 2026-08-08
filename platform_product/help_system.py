"""Epic 46.0 — per-screen help contract."""
from __future__ import annotations
from typing import Any

def help_for(screen_id: str, *, title: str, description: str, how: str, related: list[str] | None = None) -> dict[str, Any]:
    return {
        "screen_id": screen_id,
        "title_ru": title,
        "description_ru": description,
        "how_ru": how,
        "video_ru": "Скоро",
        "example_ru": "Пример доступен в справке раздела.",
        "related": list(related or []),
    }

CORE_HELP = [
    help_for("owner", title="Панель владельца", description="Сводка по бизнесу и AI.", how="Откройте виджеты и быстрые действия.", related=["/workflows", "/ai-command"]),
    help_for("settings", title="Настройки", description="Единый раздел настроек.", how="Выберите вкладку слева/сверху.", related=["/settings?tab=ai"]),
    help_for("workflows", title="Автоматизация", description="Запуск и монитор Workflow.", how="Создайте цель или выберите шаблон.", related=["/ai-command"]),
    help_for("memory", title="Память", description="Непрерывный контекст работы.", how="Продолжите незавершённое.", related=["/ai-workspace"]),
    help_for("telegram", title="Telegram", description="Мобильная Enterprise CRM.", how="Используйте главное меню — максимум 2 уровня.", related=[]),
]
