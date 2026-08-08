"""Epic 46.0 — empty state catalog (RU)."""
from __future__ import annotations

EMPTY_STATES_RU: dict[str, dict[str, str]] = {
    "projects": {"title": "Нет проектов", "cta": "Создать первый проект", "action": "create_project"},
    "clients": {"title": "Нет клиентов", "cta": "Добавить клиента", "action": "create_client"},
    "workflows": {"title": "Нет Workflow", "cta": "Создать Workflow", "action": "create_workflow"},
    "documents": {"title": "Нет документов", "cta": "Создать документ", "action": "create_document"},
    "memory": {"title": "Память пуста", "cta": "Продолжить работу", "action": "open_memory"},
    "notifications": {"title": "Нет уведомлений", "cta": "Открыть дашборд", "action": "open_dashboard"},
    "generations": {"title": "Нет генераций", "cta": "Открыть Студию AI", "action": "open_studio"},
    "tasks": {"title": "Нет задач", "cta": "Создать задачу", "action": "create_task"},
}

def empty_state(kind: str) -> dict[str, str]:
    return dict(EMPTY_STATES_RU.get(kind, {"title": "Пусто", "cta": "Создать", "action": "create"}))
