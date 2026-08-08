"""Epic 46.0 — unified error experience (RU)."""
from __future__ import annotations
from typing import Any

def format_error(*, code: str, reason: str, what_to_do: str) -> dict[str, Any]:
    return {
        "title_ru": "Что-то пошло не так",
        "code": code,
        "reason_ru": reason,
        "what_to_do_ru": what_to_do,
        "actions": [
            {"id": "retry", "label_ru": "Повторить"},
            {"id": "report", "label_ru": "Сообщить"},
        ],
    }

STANDARD_ERRORS = {
    "network": format_error(code="NETWORK", reason="Нет связи с сервером.", what_to_do="Проверьте интернет и повторите."),
    "forbidden": format_error(code="FORBIDDEN", reason="Недостаточно прав.", what_to_do="Обратитесь к администратору."),
    "not_found": format_error(code="NOT_FOUND", reason="Раздел или объект не найден.", what_to_do="Вернитесь на дашборд или воспользуйтесь поиском."),
    "validation": format_error(code="VALIDATION", reason="Данные заполнены неверно.", what_to_do="Исправьте поля и отправьте снова."),
}
