"""AUTO 1.0 catalogs — controlled statuses, expenses, documents, photos."""

from __future__ import annotations

from typing import Any

VEHICLE_STATUSES: list[tuple[str, str]] = [
    ("INTEREST", "Интерес"),
    ("AUCTION", "Аукцион"),
    ("WON", "Выигран"),
    ("PURCHASED", "Куплен"),
    ("AWAITING_PICKUP", "Ожидает забора"),
    ("INLAND_TRANSPORT", "Наземная перевозка"),
    ("AT_ORIGIN_PORT", "Порт отправления"),
    ("IN_CONTAINER", "В контейнере"),
    ("SEA_TRANSIT", "Морская перевозка"),
    ("DESTINATION_PORT", "Порт назначения"),
    ("CUSTOMS", "Растаможка"),
    ("CUSTOMS_CLEARED", "Растаможен"),
    ("IN_UKRAINE", "В Украине"),
    ("PREPARATION", "Подготовка"),
    ("READY_FOR_SALE", "Готов к продаже"),
    ("RESERVED", "Зарезервирован"),
    ("SOLD", "Продан"),
    ("CANCELLED", "Отменён"),
]

STATUS_LABELS: dict[str, str] = dict(VEHICLE_STATUSES)
STATUS_IDS: frozenset[str] = frozenset(STATUS_LABELS)

# Dashboard KPI buckets (operational, not free-text).
KPI_STATUS_GROUPS: dict[str, frozenset[str]] = {
    "purchased": frozenset(
        {
            "PURCHASED",
            "AWAITING_PICKUP",
            "INLAND_TRANSPORT",
            "AT_ORIGIN_PORT",
            "IN_CONTAINER",
            "SEA_TRANSIT",
            "DESTINATION_PORT",
            "CUSTOMS",
            "CUSTOMS_CLEARED",
            "IN_UKRAINE",
            "PREPARATION",
            "READY_FOR_SALE",
            "RESERVED",
            "SOLD",
        }
    ),
    "in_transit": frozenset({"INLAND_TRANSPORT", "AT_ORIGIN_PORT", "IN_CONTAINER", "SEA_TRANSIT"}),
    "at_port": frozenset({"DESTINATION_PORT", "AT_ORIGIN_PORT"}),
    "at_customs": frozenset({"CUSTOMS"}),
    "in_ukraine": frozenset({"CUSTOMS_CLEARED", "IN_UKRAINE"}),
    "in_preparation": frozenset({"PREPARATION"}),
    "for_sale": frozenset({"READY_FOR_SALE", "RESERVED"}),
    "sold": frozenset({"SOLD"}),
}

# Overview timeline (business language, mapped from statuses).
LIFECYCLE_STEPS: list[dict[str, Any]] = [
    {"id": "auction", "label_ru": "Аукцион", "statuses": ["INTEREST", "AUCTION"]},
    {"id": "purchased", "label_ru": "Куплен", "statuses": ["WON", "PURCHASED"]},
    {"id": "pickup", "label_ru": "Забран", "statuses": ["AWAITING_PICKUP", "INLAND_TRANSPORT"]},
    {"id": "origin_port", "label_ru": "Порт", "statuses": ["AT_ORIGIN_PORT"]},
    {"id": "container", "label_ru": "Контейнер", "statuses": ["IN_CONTAINER"]},
    {"id": "sea", "label_ru": "Море", "statuses": ["SEA_TRANSIT"]},
    {"id": "ukraine", "label_ru": "Украина", "statuses": ["DESTINATION_PORT", "IN_UKRAINE"]},
    {"id": "customs", "label_ru": "Таможня", "statuses": ["CUSTOMS", "CUSTOMS_CLEARED"]},
    {"id": "prep", "label_ru": "Подготовка", "statuses": ["PREPARATION"]},
    {"id": "sale", "label_ru": "Продажа", "statuses": ["READY_FOR_SALE", "RESERVED", "SOLD"]},
]

EXPENSE_CATEGORIES: list[tuple[str, str]] = [
    ("PURCHASE", "Цена автомобиля"),
    ("AUCTION_FEE", "Комиссия аукциона"),
    ("INLAND_TRANSPORT", "Доставка по стране покупки"),
    ("SEA_FREIGHT", "Морской фрахт"),
    ("PORT_FEE", "Портовые расходы"),
    ("BROKER", "Брокер"),
    ("CUSTOMS", "Таможенные платежи"),
    ("DUTY", "Мито"),
    ("EXCISE", "Акциз"),
    ("IMPORT_VAT", "НДС на импорт"),
    ("CUSTOMS_PENALTY", "Штраф таможни"),
    ("CERTIFICATION", "Сертификация"),
    ("CERT_LAB", "Орган сертификации"),
    ("REGISTRATION", "Регистрация"),
    ("MREO", "МРЕО"),
    ("TRANSPORT_UA", "Доставка по Украине"),
    ("UA_TRANSPORT", "Автовоз по Украине"),
    ("EU_TRANSPORT", "Автовоз по Европе"),
    ("CONTAINER", "Контейнер"),
    ("FORWARDER", "Экспедитор"),
    ("DEMURRAGE", "Демередж"),
    ("DETENTION", "Детейшн"),
    ("TOW_TRUCK", "Эвакуатор"),
    ("REPAIR", "Ремонт"),
    ("PARTS", "Запчасти"),
    ("STORAGE", "Хранение"),
    ("BANK_FEE", "Банковская комиссия"),
    ("OTHER", "Прочие расходы"),
]

EXPENSE_LABELS: dict[str, str] = dict(EXPENSE_CATEGORIES)
EXPENSE_IDS: frozenset[str] = frozenset(EXPENSE_LABELS)

_LOGISTICS_EXPENSE = frozenset(
    {
        "INLAND_TRANSPORT",
        "SEA_FREIGHT",
        "PORT_FEE",
        "TRANSPORT_UA",
        "UA_TRANSPORT",
        "EU_TRANSPORT",
        "CONTAINER",
        "FORWARDER",
        "DEMURRAGE",
        "DETENTION",
        "TOW_TRUCK",
        "STORAGE",
    }
)

_CUSTOMS_FINANCE = frozenset(
    {
        "CUSTOMS",
        "BROKER",
        "DUTY",
        "EXCISE",
        "IMPORT_VAT",
        "CUSTOMS_PENALTY",
        "CERTIFICATION",
        "CERT_LAB",
        "REGISTRATION",
        "MREO",
    }
)

FINANCE_KPI_GROUPS: dict[str, frozenset[str]] = {
    "purchase_cost": frozenset({"PURCHASE"}),
    "logistics": _LOGISTICS_EXPENSE,
    "customs": _CUSTOMS_FINANCE,
    "other": frozenset(EXPENSE_IDS - {"PURCHASE"} - _LOGISTICS_EXPENSE - _CUSTOMS_FINANCE),
}

DOCUMENT_TYPES: list[tuple[str, str]] = [
    ("auction_invoice", "Инвойс аукциона"),
    ("purchase_agreement", "Договор покупки"),
    ("title", "Title / техпаспорт"),
    ("bill_of_sale", "Bill of Sale"),
    ("shipping", "Отгрузочный документ"),
    ("bill_of_lading", "Коносамент (B/L)"),
    ("booking_confirmation", "Подтверждение букинга"),
    ("container_release", "Релиз контейнера"),
    ("gate_pass", "Gate Pass"),
    ("invoice", "Счёт"),
    ("carrier_invoice", "Счёт перевозчика"),
    ("port_invoice", "Портовый счёт"),
    ("packing_list", "Упаковочный лист"),
    ("title_copy", "Копия Title"),
    ("export_document", "Экспортный документ"),
    ("customs_export", "Экспортная таможенная декларация"),
    ("delivery_order", "Delivery Order"),
    ("cmr", "CMR"),
    ("act", "Акт"),
    ("container", "Документ контейнера"),
    ("customs_declaration", "Таможенная декларация"),
    ("broker", "Документы брокера"),
    ("certificate", "Сертификат"),
    ("registration", "Регистрационные документы"),
    ("repair_invoice", "Счёт ремонта"),
    ("sale_agreement", "Договор продажи"),
    ("payment_confirmation", "Подтверждение оплаты"),
    ("passport", "Паспорт"),
    ("id_card", "ID / удостоверение"),
    ("contract", "Договор"),
    ("transfer_act", "Акт приёма-передачи"),
    ("commercial_offer", "Коммерческое предложение"),
    ("bank_receipt", "Банковская квитанция"),
    ("cash_receipt", "Кассовый чек"),
    ("statement", "Выписка"),
    ("insurance", "Страховка"),
    ("inspection", "Осмотр"),
    ("duty_doc", "Документ пошлины"),
    ("vat_doc", "Документ НДС"),
    ("excise_doc", "Документ акциза"),
    ("tax_id_copy", "Копия ИНН"),
    ("other", "Другое"),
]

DOCUMENT_LABELS: dict[str, str] = dict(DOCUMENT_TYPES)
DOCUMENT_IDS: frozenset[str] = frozenset(DOCUMENT_LABELS)

DOCUMENT_OWNERS: frozenset[str] = frozenset(
    {
        "vehicle",
        "client",
        "shipment",
        "container",
        "carrier",
        "driver",
        "truck",
        "vessel",
        "customs",
        "broker",
        "deal",
        "sale",
        "receipt",
        "sale",
        "payment",
        "expense",
    }
)

PHOTO_CATEGORIES: list[tuple[str, str]] = [
    ("AUCTION", "Аукцион"),
    ("DAMAGE", "Повреждения"),
    ("PICKUP", "Забор"),
    ("PORT", "Порт"),
    ("LOADED", "Загрузка"),
    ("WAREHOUSE", "Склад"),
    ("CONTAINER_LOADING", "Погрузка в контейнер"),
    ("SEAL", "Пломба"),
    ("UNLOADING", "Разгрузка"),
    ("DESTINATION_PORT", "Порт назначения"),
    ("DELIVERY", "Доставка"),
    ("ARRIVAL", "Прибытие"),
    ("CUSTOMS", "Таможня"),
    ("REPAIR", "Ремонт"),
    ("READY_FOR_SALE", "Готов к продаже"),
    ("OTHER", "Другое"),
]

PHOTO_LABELS: dict[str, str] = dict(PHOTO_CATEGORIES)
PHOTO_IDS: frozenset[str] = frozenset(PHOTO_LABELS)

CLIENT_STATUSES: list[tuple[str, str]] = [
    ("lead", "Лид"),
    ("active", "Активный"),
    ("reserved", "Резерв"),
    ("buyer", "Покупатель"),
    ("closed", "Закрыт"),
]

PAYMENT_STATUSES: list[tuple[str, str]] = [
    ("planned", "Запланирован"),
    ("pending", "Ожидает"),
    ("paid", "Оплачен"),
    ("cancelled", "Отменён"),
]

CURRENCIES: list[str] = ["USD", "EUR", "UAH", "GEL"]

TASK_STATUSES: list[tuple[str, str]] = [
    ("open", "Открыта"),
    ("in_progress", "В работе"),
    ("done", "Выполнена"),
    ("cancelled", "Отменена"),
]


def catalogs() -> dict[str, Any]:
    def pairs(items: list[tuple[str, str]]) -> list[dict[str, str]]:
        return [{"id": i, "label_ru": l} for i, l in items]

    from services.auto_ops.crm_catalog import crm_catalogs
    from services.auto_ops.customs_catalog import customs_catalogs
    from services.auto_ops.logistics_catalog import logistics_catalogs

    return {
        "vehicle_statuses": pairs(VEHICLE_STATUSES),
        "expense_categories": pairs(EXPENSE_CATEGORIES),
        "document_types": pairs(DOCUMENT_TYPES),
        "document_owners": sorted(DOCUMENT_OWNERS),
        "photo_categories": pairs(PHOTO_CATEGORIES),
        "client_statuses": pairs(CLIENT_STATUSES),
        "payment_statuses": pairs(PAYMENT_STATUSES),
        "currencies": CURRENCIES,
        "task_statuses": pairs(TASK_STATUSES),
        "lifecycle_steps": LIFECYCLE_STEPS,
        "base_currency": "USD",
        **logistics_catalogs(),
        **customs_catalogs(),
        **crm_catalogs(),
    }


def lifecycle_for_status(status: str) -> list[dict[str, Any]]:
    current_idx = -1
    st = (status or "").upper()
    for i, step in enumerate(LIFECYCLE_STEPS):
        if st in step["statuses"]:
            current_idx = i
            break
    out: list[dict[str, Any]] = []
    for i, step in enumerate(LIFECYCLE_STEPS):
        if st == "CANCELLED":
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
