# Realty vertical — multi-step flows, validation, request submission.

from __future__ import annotations

from typing import Any

from services.system_roles import Vertical

SCENARIO_RENT = "rent"
SCENARIO_BUY = "buy"
SCENARIO_SELL = "sell"
SCENARIO_NEW_BUILD = "new_build"
SCENARIO_MANAGEMENT = "management"

SCENARIO_LABELS: dict[str, str] = {
    SCENARIO_RENT: "Аренда",
    SCENARIO_BUY: "Покупка",
    SCENARIO_SELL: "Продажа",
    SCENARIO_NEW_BUILD: "Новостройки",
    SCENARIO_MANAGEMENT: "Управление объектами",
}

OBJECT_TYPES: dict[str, dict[str, str]] = {
    SCENARIO_RENT: {
        "apartment": "Квартира",
        "house": "Дом",
        "commercial": "Коммерческая недвижимость",
    },
    SCENARIO_BUY: {
        "apartment": "Квартира",
        "house": "Дом",
        "land": "Земельный участок",
        "commercial": "Коммерческая недвижимость",
    },
    SCENARIO_SELL: {
        "apartment": "Квартира",
        "house": "Дом",
        "land": "Участок",
        "commercial": "Коммерческая недвижимость",
    },
    SCENARIO_NEW_BUILD: {
        "apartment": "Квартира",
        "house": "Дом",
        "commercial": "Коммерческая недвижимость",
    },
    SCENARIO_MANAGEMENT: {
        "apartment": "Квартира",
        "house": "Дом",
        "commercial": "Коммерческая недвижимость",
    },
}

FLOW_STEPS: dict[str, tuple[str, ...]] = {
    SCENARIO_RENT: ("city", "district", "budget", "rooms", "notes", "photos", "contact"),
    SCENARIO_BUY: ("city", "budget", "area", "requirements", "contact"),
    SCENARIO_SELL: ("address", "area", "price", "description", "photos", "contact"),
    SCENARIO_NEW_BUILD: ("city", "budget", "requirements", "contact"),
    SCENARIO_MANAGEMENT: ("address", "description", "contact"),
}

STEP_PROMPTS: dict[str, str] = {
    "city": "Укажите город:",
    "district": "Укажите район:",
    "budget": "Укажите бюджет (число или диапазон):",
    "rooms": "Сколько комнат нужно?",
    "notes": "Дополнительные пожелания (или «-» чтобы пропустить):",
    "photos": "Пришлите фото объекта (можно несколько). Когда закончите — нажмите «Готово» или «Пропустить».",
    "contact": "📞 Укажите контактный телефон или отправьте контакт:",
    "area": "Укажите желаемую площадь (м²):",
    "requirements": "Дополнительные требования (или «-» чтобы пропустить):",
    "address": "Укажите адрес объекта:",
    "price": "Укажите цену:",
    "description": "Опишите объект:",
}

SKIP_TOKENS = frozenset({"-", "пропустить", "skip", "нет"})


def pending_key(scenario: str, step: str) -> str:
    return f"realty:{scenario}:{step}"


def first_step(scenario: str) -> str | None:
    steps = FLOW_STEPS.get(scenario)
    return steps[0] if steps else None


def next_step(scenario: str, current_step: str) -> str | None:
    steps = FLOW_STEPS.get(scenario, ())
    try:
        idx = steps.index(current_step)
    except ValueError:
        return None
    if idx + 1 >= len(steps):
        return None
    return steps[idx + 1]


def step_prompt(scenario: str, step: str) -> str:
    return STEP_PROMPTS.get(step, "Введите значение:")


def request_type_code(scenario: str, object_type: str) -> str:
    return f"REALTY_{scenario.upper()}_{object_type.upper()}"


def _is_skip(text: str) -> bool:
    return text.strip().lower() in SKIP_TOKENS


def validate_text_step(step: str, text: str) -> tuple[bool, str | None, Any]:
    cleaned = text.strip()
    if not cleaned:
        return False, "Поле не может быть пустым.", None

    if step in {"notes", "requirements"} and _is_skip(cleaned):
        return True, None, ""

    if step == "contact":
        digits = "".join(ch for ch in cleaned if ch.isdigit() or ch == "+")
        if len(digits.replace("+", "")) < 7:
            return False, "Введите корректный номер телефона.", None
        return True, None, digits

    if step in {"budget", "price"}:
        normalized = cleaned.replace(" ", "").replace(",", ".")
        digits = "".join(ch for ch in normalized if ch.isdigit() or ch in {".", "-"})
        if not digits:
            return False, "Укажите сумму или диапазон.", None
        return True, None, cleaned

    if step == "area":
        normalized = cleaned.replace(",", ".")
        try:
            value = float("".join(ch for ch in normalized if ch.isdigit() or ch == "."))
        except ValueError:
            return False, "Укажите площадь числом (м²).", None
        if value <= 0:
            return False, "Площадь должна быть больше нуля.", None
        return True, None, value

    if step == "rooms":
        if cleaned.isdigit():
            return True, None, int(cleaned)
        return True, None, cleaned

    return True, None, cleaned


def build_description(scenario: str, data: dict[str, Any]) -> str:
    scenario_label = SCENARIO_LABELS.get(scenario, scenario)
    object_type = data.get("object_type") or ""
    object_label = ""
    if scenario in OBJECT_TYPES and object_type in OBJECT_TYPES[scenario]:
        object_label = OBJECT_TYPES[scenario][object_type]

    lines = [f"Сценарий: {scenario_label}"]
    if object_label:
        lines.append(f"Тип объекта: {object_label}")

    field_labels = {
        "city": "Город",
        "district": "Район",
        "budget": "Бюджет",
        "rooms": "Комнат",
        "notes": "Пожелания",
        "area": "Площадь (м²)",
        "requirements": "Требования",
        "address": "Адрес",
        "price": "Цена",
        "description": "Описание",
        "contact": "Контакт",
    }
    for key, label in field_labels.items():
        value = data.get(key)
        if value is not None and value != "":
            lines.append(f"{label}: {value}")

    photos = data.get("photo_file_ids") or []
    if photos:
        lines.append(f"Фото: {len(photos)} шт.")
    return "\n".join(lines)


def build_ai_qualification(scenario: str, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "vertical": Vertical.REALTY.value,
        "scenario": scenario,
        "object_type": data.get("object_type"),
        "district": data.get("district"),
        "rooms": data.get("rooms"),
        "area": data.get("area"),
        "requirements": data.get("requirements") or data.get("notes"),
        "address": data.get("address"),
    }


def parse_budget_value(raw: str | None) -> float | None:
    if not raw:
        return None
    digits = "".join(ch for ch in str(raw) if ch.isdigit() or ch == ".")
    if not digits:
        return None
    try:
        return float(digits)
    except ValueError:
        return None


async def submit_realty_request(
    *,
    scenario: str,
    data: dict[str, Any],
    client_telegram_id: int,
    client_name: str = "",
    client_username: str | None = None,
) -> dict[str, Any]:
    from services.request_service import request_service

    object_type = str(data.get("object_type") or "unknown")
    description = build_description(scenario, data)
    photo_ids = list(data.get("photo_file_ids") or [])

    return await request_service.create_request(
        vertical=Vertical.REALTY.value,
        client_telegram_id=client_telegram_id,
        client_name=client_name,
        client_username=client_username,
        product=SCENARIO_LABELS.get(scenario, scenario),
        description=description,
        request_type=request_type_code(scenario, object_type),
        city=data.get("city"),
        budget=parse_budget_value(data.get("budget")),
        price=parse_budget_value(data.get("price")),
        client_phone=data.get("contact"),
        photo_file_ids=photo_ids or None,
        ai_qualification=build_ai_qualification(scenario, data),
    )
