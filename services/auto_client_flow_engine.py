# Auto Client multi-step flow — step order, validation, payload assembly.

from __future__ import annotations

from typing import Any

from services.vin_decoder import validate_vin

REQUEST_BUY = "buy_car"
REQUEST_SELL = "sell_car"
REQUEST_LISTING = "listing"
REQUEST_SERVICES = "services"
REQUEST_MANAGER = "manager_callback"

SKIP_TOKENS = frozenset({"-", "пропустить", "skip", "нет"})

# Unified car questionnaire: VIN is always last and optional.
_CAR_FLOW_STEPS = (
    "brand",
    "model",
    "year",
    "engine",
    "color",
    "description",
    "photos",
    "phone",
    "vin_optional",
)

FLOW_STEPS: dict[str, tuple[str, ...]] = {
    REQUEST_BUY: _CAR_FLOW_STEPS,
    REQUEST_SELL: _CAR_FLOW_STEPS,
    REQUEST_LISTING: _CAR_FLOW_STEPS,
    REQUEST_SERVICES: ("description", "photos", "phone"),
    REQUEST_MANAGER: ("description", "phone"),
}

STEP_PROMPTS: dict[str, str] = {
    "brand": "Укажите марку автомобиля:",
    "model": "Укажите модель:",
    "year": "Укажите год (или «-» чтобы пропустить):",
    "engine": "Укажите объём двигателя (или «-» чтобы пропустить):",
    "color": "Укажите цвет (или «-» чтобы пропустить):",
    "description": "Опишите ваш запрос:",
    "phone": "📞 Отправьте номер телефона или нажмите «Поделиться контактом».",
    "vin_optional": "Хотите добавить VIN автомобиля?",
    "photos": "Пришлите фото (можно несколько). Когда закончите — нажмите «Готово» или «Пропустить».",
}

REQUEST_TYPE_LABELS: dict[str, str] = {
    REQUEST_BUY: "Поиск автомобиля",
    REQUEST_SELL: "Продажа автомобиля",
    REQUEST_LISTING: "Размещение объявления",
    REQUEST_SERVICES: "Автоуслуги",
    REQUEST_MANAGER: "Связь с менеджером",
}

CAR_FLOW_TYPES = frozenset({REQUEST_BUY, REQUEST_SELL, REQUEST_LISTING})


def first_step(flow_type: str) -> str | None:
    steps = FLOW_STEPS.get(flow_type)
    return steps[0] if steps else None


def next_step(flow_type: str, current_step: str) -> str | None:
    steps = FLOW_STEPS.get(flow_type, ())
    try:
        idx = steps.index(current_step)
    except ValueError:
        return None
    if idx + 1 >= len(steps):
        return None
    return steps[idx + 1]


def step_prompt(flow_type: str, step: str) -> str:
    if step == "description" and flow_type == REQUEST_MANAGER:
        return "Опишите ваш вопрос или запрос:"
    if step == "description" and flow_type == REQUEST_SERVICES:
        return "Опишите, какая услуга вам нужна:"
    if step == "year" and flow_type in CAR_FLOW_TYPES:
        return "Укажите год выпуска:"
    return STEP_PROMPTS.get(step, "Введите значение:")


def _is_skip(text: str) -> bool:
    return text.strip().lower() in SKIP_TOKENS


def validate_text_step(step: str, text: str, *, flow_type: str) -> tuple[bool, str | None, Any]:
    """Return (ok, error_message, parsed_value)."""
    cleaned = text.strip()
    if not cleaned:
        return False, "Поле не может быть пустым.", None

    if step == "year":
        if _is_skip(cleaned):
            if flow_type == REQUEST_BUY:
                return True, None, None
            return False, "Укажите год выпуска.", None
        if not cleaned.isdigit() or len(cleaned) != 4:
            return False, "Укажите год четырёхзначным числом (например 2021).", None
        return True, None, int(cleaned)

    if step in {"engine", "color"}:
        if _is_skip(cleaned):
            return True, None, None
        return True, None, cleaned

    if step == "phone":
        digits = "".join(ch for ch in cleaned if ch.isdigit() or ch == "+")
        if len(digits.replace("+", "")) < 7:
            return False, "Введите корректный номер телефона.", None
        return True, None, digits

    if step == "vin":
        # Validated only when the user voluntarily enters a VIN.
        result = validate_vin(cleaned)
        if not result["is_valid"]:
            return False, "\n".join(result["errors"]), None
        return True, None, result["vin"]

    return True, None, cleaned


def build_description(flow_type: str, data: dict[str, Any]) -> str:
    """Human-readable summary stored in description column."""
    parts: list[str] = []
    if flow_type == REQUEST_SERVICES and data.get("service_type"):
        parts.append(f"Услуга: {data['service_type']}")
    for key, label in (
        ("brand", "Марка"),
        ("model", "Модель"),
        ("year", "Год"),
        ("engine", "Объём двигателя"),
        ("color", "Цвет"),
        ("mileage", "Пробег"),
        ("budget", "Бюджет"),
        ("price", "Цена"),
        ("vin", "VIN"),
    ):
        value = data.get(key)
        if value is not None and value != "":
            parts.append(f"{label}: {value}")
    user_desc = (data.get("user_description") or data.get("description") or "").strip()
    if user_desc:
        parts.append(f"Описание: {user_desc}")
    return "\n".join(parts) if parts else user_desc or "—"


def build_manager_notification_lines(
    *,
    flow_type: str,
    request_number: str,
    data: dict[str, Any],
    client_username: str | None,
    client_full_name: str | None,
    client_phone: str | None,
) -> list[str]:
    type_label = REQUEST_TYPE_LABELS.get(flow_type, flow_type)
    photos = data.get("photo_file_ids") or []

    lines = ["🚗 Новый лид", "", "Type:", type_label]

    field_map = (
        ("brand", "Brand"),
        ("model", "Model"),
        ("year", "Year"),
        ("engine", "Engine"),
        ("color", "Color"),
        ("mileage", "Mileage"),
        ("budget", "Budget"),
        ("price", "Price"),
        ("service_type", "Service"),
        ("vin", "VIN"),
    )
    for key, label in field_map:
        value = data.get(key)
        if value is not None and value != "":
            suffix = " USD" if key in {"budget", "price"} and isinstance(value, (int, float)) else ""
            lines.extend(["", f"{label}:", f"{value}{suffix}"])

    user_desc = (data.get("user_description") or "").strip()
    if user_desc:
        lines.extend(["", "Description:", user_desc[:3500]])

    if photos:
        lines.extend(["", "Photos:", f"{len(photos)} attached"])
    else:
        lines.extend(["", "Photos:", "none"])

    client_line = f"@{client_username}" if client_username else (client_full_name or "—")
    lines.extend(["", "Client:", client_line])
    if client_phone:
        lines.append(client_phone)

    lines.extend(["", f"Request: {request_number}"])
    vin_present = bool(data.get("vin"))
    lines.extend(["", f"VIN_PRESENT={vin_present}"])
    return lines


def pending_key(flow_type: str, step: str) -> str:
    return f"ac:{flow_type}:{step}"


def vin_present(data: dict[str, Any] | None) -> bool:
    vin = (data or {}).get("vin")
    return bool(vin and str(vin).strip())
