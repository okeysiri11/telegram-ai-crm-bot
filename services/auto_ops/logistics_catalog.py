"""AUTO 1.1 logistics catalogs — controlled types, statuses, ports, delay."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

SHIPMENT_TYPES: list[tuple[str, str]] = [
    ("AUCTION_PICKUP", "Забор с аукциона"),
    ("INLAND_TRUCK", "Наземная перевозка"),
    ("RAIL", "Ж/Д перевозка"),
    ("PORT_TRANSFER", "Доставка в порт"),
    ("CONTAINER", "Контейнер"),
    ("SEA_FREIGHT", "Морской фрахт"),
    ("RO_RO", "Ro-Ro"),
    ("EU_TRUCK", "Автовоз по Европе"),
    ("UA_TRUCK", "Автовоз по Украине"),
    ("TOW_TRUCK", "Эвакуатор"),
    ("OTHER", "Другое"),
]

SHIPMENT_TYPE_LABELS = dict(SHIPMENT_TYPES)
SHIPMENT_TYPE_IDS = frozenset(SHIPMENT_TYPE_LABELS)

SHIPMENT_STATUSES: list[tuple[str, str]] = [
    ("PLANNED", "Запланирован"),
    ("BOOKED", "Забронирован"),
    ("AWAITING_PICKUP", "Ожидает забора"),
    ("PICKED_UP", "Забран"),
    ("IN_TRANSIT", "В пути"),
    ("ARRIVED_AT_PORT", "Прибыл в порт"),
    ("PORT_PROCESSING", "Обработка в порту"),
    ("LOADED_IN_CONTAINER", "Загружен в контейнер"),
    ("LOADED_ON_VESSEL", "Погружен на судно"),
    ("SEA_TRANSIT", "В море"),
    ("ARRIVED_DESTINATION_PORT", "Порт назначения"),
    ("PORT_RELEASE", "Выпуск из порта"),
    ("CUSTOMS_HANDOFF", "Передан на таможню"),
    ("UA_INLAND_TRANSIT", "Доставка по Украине"),
    ("DELIVERED", "Доставлен"),
    ("DELAYED", "Задержка"),
    ("ON_HOLD", "На паузе"),
    ("CANCELLED", "Отменён"),
]

SHIPMENT_STATUS_LABELS = dict(SHIPMENT_STATUSES)
SHIPMENT_STATUS_IDS = frozenset(SHIPMENT_STATUS_LABELS)

LOGISTICS_TABS: list[dict[str, Any]] = [
    {"id": "all", "label_ru": "Все перевозки", "statuses": None, "exclude": ["CANCELLED"]},
    {"id": "awaiting_pickup", "label_ru": "Ожидают забора", "statuses": ["PLANNED", "BOOKED", "AWAITING_PICKUP"]},
    {"id": "inland", "label_ru": "В пути по стране покупки", "statuses": ["PICKED_UP", "IN_TRANSIT"]},
    {"id": "origin_port", "label_ru": "В порту", "statuses": ["ARRIVED_AT_PORT", "PORT_PROCESSING"]},
    {"id": "container", "label_ru": "В контейнере", "statuses": ["LOADED_IN_CONTAINER"]},
    {"id": "sea", "label_ru": "В море", "statuses": ["LOADED_ON_VESSEL", "SEA_TRANSIT"]},
    {"id": "destination_port", "label_ru": "В порту назначения", "statuses": ["ARRIVED_DESTINATION_PORT", "PORT_RELEASE"]},
    {"id": "ua_delivery", "label_ru": "Доставка по Украине", "statuses": ["CUSTOMS_HANDOFF", "UA_INLAND_TRANSIT"]},
    {"id": "done", "label_ru": "Завершённые", "statuses": ["DELIVERED"]},
    {"id": "problems", "label_ru": "Проблемные", "statuses": ["DELAYED", "ON_HOLD"], "problems": True},
]

PIPELINE_STAGES: list[dict[str, Any]] = [
    {"id": "auction", "label_ru": "Аукцион", "statuses": ["PLANNED", "BOOKED"]},
    {"id": "pickup", "label_ru": "Забор", "statuses": ["AWAITING_PICKUP", "PICKED_UP"]},
    {"id": "warehouse", "label_ru": "Склад перевозчика", "statuses": ["IN_TRANSIT"]},
    {"id": "us_port", "label_ru": "Порт отправления", "statuses": ["ARRIVED_AT_PORT", "PORT_PROCESSING"]},
    {"id": "container", "label_ru": "Контейнер", "statuses": ["LOADED_IN_CONTAINER"]},
    {"id": "vessel", "label_ru": "Судно", "statuses": ["LOADED_ON_VESSEL", "SEA_TRANSIT"]},
    {"id": "dest_port", "label_ru": "Порт назначения", "statuses": ["ARRIVED_DESTINATION_PORT", "PORT_RELEASE"]},
    {"id": "customs", "label_ru": "Таможня", "statuses": ["CUSTOMS_HANDOFF"]},
    {"id": "ua_truck", "label_ru": "Автовоз", "statuses": ["UA_INLAND_TRANSIT"]},
    {"id": "delivery", "label_ru": "Склад / клиент", "statuses": ["DELIVERED"]},
]

CARRIER_TYPES: list[tuple[str, str]] = [
    ("auction_pickup", "Забор с аукциона"),
    ("truck", "Автовоз / фура"),
    ("container_forwarder", "Экспедитор контейнера"),
    ("shipping_line", "Судоходная линия"),
    ("port_agent", "Портовый агент"),
    ("customs_broker", "Таможенный брокер"),
    ("ua_carrier", "Перевозчик UA"),
    ("tow_truck", "Эвакуатор"),
    ("other", "Другое"),
]

TRUCK_TYPES: list[tuple[str, str]] = [
    ("truck", "Грузовик"),
    ("car_transporter", "Автовоз"),
    ("tow_truck", "Эвакуатор"),
    ("tractor", "Тягач"),
    ("trailer", "Прицеп"),
    ("other", "Другое"),
]

CONTAINER_TYPES: list[tuple[str, str]] = [
    ("20FT", "20FT"),
    ("40FT", "40FT"),
    ("40HC", "40HC"),
    ("45FT", "45FT"),
    ("OTHER", "Другое"),
]

CONTAINER_STATUSES: list[tuple[str, str]] = [
    ("PLANNED", "Запланирован"),
    ("BOOKED", "Забронирован"),
    ("LOADING", "Погрузка"),
    ("SEALED", "Опломбирован"),
    ("IN_TRANSIT", "В пути"),
    ("ARRIVED", "Прибыл"),
    ("UNLOADED", "Разгружен"),
    ("CLOSED", "Закрыт"),
]

VESSEL_STATUSES: list[tuple[str, str]] = [
    ("PLANNED", "Запланирован"),
    ("LOADING", "Погрузка"),
    ("DEPARTED", "Вышел"),
    ("AT_SEA", "В море"),
    ("ARRIVED", "Прибыл"),
    ("CLOSED", "Закрыт"),
]

EVENT_TYPES: list[tuple[str, str]] = [
    ("vehicle_won", "Автомобиль выигран на аукционе"),
    ("pickup_scheduled", "Забор запланирован"),
    ("vehicle_collected", "Автомобиль забран"),
    ("arrived_warehouse", "Прибыл на склад"),
    ("arrived_port", "Прибыл в порт"),
    ("container_assigned", "Назначен контейнер"),
    ("container_sealed", "Контейнер опломбирован"),
    ("loaded_on_vessel", "Погружен на судно"),
    ("vessel_departed", "Судно вышло"),
    ("eta_changed", "ETA изменена"),
    ("arrived_destination", "Прибыл в порт назначения"),
    ("port_released", "Выпущен из порта"),
    ("customs_handoff", "Передан на таможню"),
    ("delivered", "Доставлен"),
    ("comment", "Комментарий"),
    ("status_changed", "Этап изменён"),
    ("carrier_assigned", "Назначен перевозчик"),
    ("vessel_assigned", "Назначено судно"),
    ("expense_added", "Добавлен расход"),
    ("document_added", "Добавлен документ"),
    ("photo_added", "Добавлено фото"),
    ("task_created", "Создана задача"),
    ("location_updated", "Местоположение обновлено вручную"),
]

EVENT_SOURCES: list[tuple[str, str]] = [
    ("MANUAL", "Вручную"),
    ("TELEGRAM", "Telegram"),
    ("API", "API"),
    ("IMPORT", "Импорт"),
    ("SYSTEM", "Система"),
]

EVENT_SOURCE_IDS = frozenset(dict(EVENT_SOURCES))
EVENT_SOURCE_LABELS = dict(EVENT_SOURCES)

CONFIRMATION_STATUSES: list[tuple[str, str]] = [
    ("CONFIRMED", "Подтверждено"),
    ("UNCONFIRMED", "Не подтверждено"),
]

CONFIRMATION_IDS = frozenset(dict(CONFIRMATION_STATUSES))

PROVIDER_TYPES: list[tuple[str, str]] = [
    ("ais", "AIS / судно"),
    ("container", "Контейнер"),
    ("vessel", "Судоходная линия"),
    ("port", "Порт"),
    ("other", "Другое"),
]

PROVIDER_TYPE_IDS = frozenset(dict(PROVIDER_TYPES))

# Optional suggested tasks on stage change. Never irreversible (no auto-clear / deliver).
SUGGESTED_TASKS_BY_STATUS: dict[str, str] = {
    "BOOKED": "Получить Bill of Lading",
    "ARRIVED_DESTINATION_PORT": "Подготовить таможню",
    "CUSTOMS_HANDOFF": "Назначить автовоз",
}

ASSIGNMENT_SLOTS: list[tuple[str, str]] = [
    ("responsible_manager_id", "Менеджер"),
    ("assigned_forwarder_id", "Экспедитор"),
    ("accountant_reviewer_id", "Бухгалтер-ревьюер"),
    ("customs_responsible_id", "Ответственный за таможню"),
]

DEFAULT_LOGISTICS_POLICY: dict[str, bool] = {
    "require_manager_on_active_shipment": False,
    "auto_create_suggested_tasks": True,
    "manager_see_assigned_transport_cost": True,
    "accountant_may_change_status": False,
}

_SOURCE_ALIASES = {
    "manual": "MANUAL",
    "user": "MANUAL",
    "web": "MANUAL",
    "desk": "MANUAL",
    "telegram": "TELEGRAM",
    "bot": "TELEGRAM",
    "api": "API",
    "provider": "API",
    "ais": "API",
    "import": "IMPORT",
    "csv": "IMPORT",
    "xls": "IMPORT",
    "system": "SYSTEM",
}


def normalize_event_source(value: Any) -> str:
    raw = str(value or "manual").strip()
    if raw.upper() in EVENT_SOURCE_IDS:
        return raw.upper()
    return _SOURCE_ALIASES.get(raw.lower(), "MANUAL")


def confirmation_for_source(source: str, explicit: Any = None) -> str:
    if explicit not in (None, ""):
        raw = str(explicit).strip().upper()
        if raw in CONFIRMATION_IDS:
            return raw
    src = normalize_event_source(source)
    if src == "IMPORT":
        return "UNCONFIRMED"
    return "CONFIRMED"


def suggested_task_title(status: str) -> str | None:
    return SUGGESTED_TASKS_BY_STATUS.get(str(status or "").strip().upper())

LOGISTICS_EXPENSE_IDS = frozenset(
    {
        "INLAND_TRANSPORT",
        "PORT_FEE",
        "CONTAINER",
        "SEA_FREIGHT",
        "FORWARDER",
        "BROKER",
        "STORAGE",
        "DEMURRAGE",
        "DETENTION",
        "EU_TRANSPORT",
        "UA_TRANSPORT",
        "TRANSPORT_UA",
        "TOW_TRUCK",
        "OTHER",
    }
)

DEFAULT_DELAY_THRESHOLDS = {"yellow_days": 3, "orange_days": 7}

# Verified UNECE UN/LOCODE — no invented codes, no GPS.
REFERENCE_PORTS: list[dict[str, str]] = [
    {"unlocode": "USNYC", "name": "New York", "country": "US", "city": "New York"},
    {"unlocode": "USLAX", "name": "Los Angeles", "country": "US", "city": "Los Angeles"},
    {"unlocode": "USMIA", "name": "Miami", "country": "US", "city": "Miami"},
    {"unlocode": "USSAV", "name": "Savannah", "country": "US", "city": "Savannah"},
    {"unlocode": "USJAX", "name": "Jacksonville", "country": "US", "city": "Jacksonville"},
    {"unlocode": "USHOU", "name": "Houston", "country": "US", "city": "Houston"},
    {"unlocode": "USBAL", "name": "Baltimore", "country": "US", "city": "Baltimore"},
    {"unlocode": "USORF", "name": "Norfolk", "country": "US", "city": "Norfolk"},
    {"unlocode": "GEPTI", "name": "Poti", "country": "GE", "city": "Poti"},
    {"unlocode": "GEBAT", "name": "Batumi", "country": "GE", "city": "Batumi"},
    {"unlocode": "UAODS", "name": "Odesa", "country": "UA", "city": "Odesa"},
    {"unlocode": "NLRTM", "name": "Rotterdam", "country": "NL", "city": "Rotterdam"},
    {"unlocode": "DEHAM", "name": "Hamburg", "country": "DE", "city": "Hamburg"},
    {"unlocode": "BEANR", "name": "Antwerp", "country": "BE", "city": "Antwerp"},
    {"unlocode": "PLGDN", "name": "Gdansk", "country": "PL", "city": "Gdansk"},
    {"unlocode": "LTKLJ", "name": "Klaipeda", "country": "LT", "city": "Klaipeda"},
]

TELEGRAM_INTENTS: list[dict[str, str]] = [
    {"command": "/auto", "intent": "open_desk", "note_ru": "Открыть рабочее пространство Авто"},
    {"command": "/vin <VIN>", "intent": "vehicle_by_vin", "note_ru": "Карточка автомобиля"},
    {"command": "/logistics <VIN>", "intent": "shipment_by_vin", "note_ru": "Текущая перевозка"},
    {"command": "/container <NUMBER>", "intent": "container_by_number", "note_ru": "Контейнер и состав"},
    {"command": "/eta <VIN>", "intent": "eta_by_vin", "note_ru": "ETA и задержка"},
    {"command": "/expense <VIN>", "intent": "add_expense", "note_ru": "Добавить расход"},
    {"command": "/task <VIN>", "intent": "add_task", "note_ru": "Создать задачу"},
]


def _pairs(items: list[tuple[str, str]]) -> list[dict[str, str]]:
    return [{"id": i, "label_ru": l} for i, l in items]


def logistics_catalogs() -> dict[str, Any]:
    return {
        "shipment_types": _pairs(SHIPMENT_TYPES),
        "shipment_statuses": _pairs(SHIPMENT_STATUSES),
        "logistics_tabs": LOGISTICS_TABS,
        "pipeline_stages": PIPELINE_STAGES,
        "carrier_types": _pairs(CARRIER_TYPES),
        "truck_types": _pairs(TRUCK_TYPES),
        "container_types": _pairs(CONTAINER_TYPES),
        "container_statuses": _pairs(CONTAINER_STATUSES),
        "vessel_statuses": _pairs(VESSEL_STATUSES),
        "event_types": _pairs(EVENT_TYPES),
        "event_sources": _pairs(EVENT_SOURCES),
        "confirmation_statuses": _pairs(CONFIRMATION_STATUSES),
        "provider_types": _pairs(PROVIDER_TYPES),
        "assignment_slots": [{"id": i, "label_ru": l} for i, l in ASSIGNMENT_SLOTS],
        "suggested_tasks": [{"status": k, "title": v} for k, v in SUGGESTED_TASKS_BY_STATUS.items()],
        "logistics_policy_defaults": dict(DEFAULT_LOGISTICS_POLICY),
        "reference_ports": REFERENCE_PORTS,
        "delay_thresholds": DEFAULT_DELAY_THRESHOLDS,
        "telegram_intents": TELEGRAM_INTENTS,
        "tracking_policy": {
            "live_ais": False,
            "live_container": False,
            "manual_label_ru": "Введено вручную",
            "provider_label_ru": "Получено от источника",
            "map_label_ru": "Схема маршрута, не live-tracking",
            "unavailable_ru": "Автоматическое отслеживание недоступно",
        },
    }


def _parse_day(value: Any) -> date | None:
    if value in (None, ""):
        return None
    raw = str(value).strip()
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(raw[:10])
        except ValueError:
            return None


def delay_report(
    *,
    planned_eta: Any = None,
    current_eta: Any = None,
    delivery_date_planned: Any = None,
    status: str | None = None,
    today: date | None = None,
    yellow_days: int = 3,
    orange_days: int = 7,
) -> dict[str, Any]:
    """Delay from stored dates only. Never invents an ETA."""
    today = today or datetime.now(timezone.utc).date()
    st = (status or "").upper()
    complete = st in {"DELIVERED", "CANCELLED"}
    planned = _parse_day(planned_eta) or _parse_day(delivery_date_planned)
    current = _parse_day(current_eta) or planned
    delay_days = 0
    overdue = False
    if planned and current:
        delay_days = (current - planned).days
    if not complete and planned and today > planned and (current is None or current <= planned):
        overdue = True
        delay_days = max(delay_days, (today - planned).days)
    if delay_days < 0:
        delay_days = 0
    if complete:
        level = "green"
    elif overdue or delay_days > orange_days or st in {"DELAYED", "ON_HOLD"}:
        level = "red"
    elif delay_days > yellow_days:
        level = "orange"
    elif delay_days > 0:
        level = "yellow"
    else:
        level = "green"
    return {
        "planned_eta": planned.isoformat() if planned else None,
        "current_eta": current.isoformat() if current else None,
        "delay_days": delay_days,
        "overdue": overdue and not complete,
        "level": level,
        "source": "stored_dates",
        "eta_source_label_ru": "Введено вручную",
    }


def pipeline_for_status(status: str) -> list[dict[str, Any]]:
    st = (status or "").upper()
    current_idx = -1
    for i, step in enumerate(PIPELINE_STAGES):
        if st in step["statuses"]:
            current_idx = i
            break
    out: list[dict[str, Any]] = []
    for i, step in enumerate(PIPELINE_STAGES):
        if st in {"CANCELLED", "ON_HOLD", "DELAYED"} and current_idx < 0:
            state = "muted"
        elif current_idx < 0:
            state = "muted"
        elif i < current_idx:
            state = "done"
        elif i == current_idx:
            state = "current"
        else:
            state = "future"
        out.append({**step, "state": state})
    return out
