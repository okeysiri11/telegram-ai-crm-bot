"""AUTO 1.3 CRM catalogs — deals, reservations, receipts, reports, profit.

Counts and money come from stored records only. No employee scoring.
"""

from __future__ import annotations

from typing import Any

DEAL_STAGES: list[tuple[str, str]] = [
    ("LEAD", "Лид"),
    ("CONTACT", "Контакт"),
    ("VEHICLE_SELECTED", "Выбор автомобиля"),
    ("RESERVED", "Резерв"),
    ("DEPOSIT", "Депозит"),
    ("CONTRACT", "Договор"),
    ("PARTIAL_PAYMENT", "Частичная оплата"),
    ("FINAL_PAYMENT", "Полная оплата"),
    ("HANDOVER", "Выдача"),
    ("COMPLETED", "Сделка закрыта"),
    ("CANCELLED", "Отмена"),
    ("LOST", "Потерян"),
]

DEAL_STAGE_LABELS = dict(DEAL_STAGES)
DEAL_STAGE_IDS = frozenset(DEAL_STAGE_LABELS)

NEXT_STAGE: dict[str, str] = {
    "LEAD": "CONTACT",
    "CONTACT": "VEHICLE_SELECTED",
    "VEHICLE_SELECTED": "RESERVED",
    "RESERVED": "DEPOSIT",
    "DEPOSIT": "CONTRACT",
    "CONTRACT": "PARTIAL_PAYMENT",
    "PARTIAL_PAYMENT": "FINAL_PAYMENT",
    "FINAL_PAYMENT": "HANDOVER",
    "HANDOVER": "COMPLETED",
    "COMPLETED": "COMPLETED",
    "CANCELLED": "LEAD",
    "LOST": "LEAD",
}

CRM_PIPELINE: list[dict[str, Any]] = [
    {"id": "lead", "label_ru": "Лид", "stages": ["LEAD"]},
    {"id": "contact", "label_ru": "Контакт", "stages": ["CONTACT"]},
    {"id": "select", "label_ru": "Автомобиль", "stages": ["VEHICLE_SELECTED"]},
    {"id": "reserve", "label_ru": "Резерв", "stages": ["RESERVED"]},
    {"id": "pay", "label_ru": "Оплата", "stages": ["DEPOSIT", "CONTRACT", "PARTIAL_PAYMENT", "FINAL_PAYMENT"]},
    {"id": "handover", "label_ru": "Выдача", "stages": ["HANDOVER"]},
    {"id": "done", "label_ru": "Закрыто", "stages": ["COMPLETED"]},
]

CRM_TABS: list[dict[str, Any]] = [
    {"id": "all", "label_ru": "Все сделки", "stages": None},
    {"id": "leads", "label_ru": "Лиды", "stages": ["LEAD", "CONTACT"]},
    {"id": "active", "label_ru": "В работе", "stages": ["VEHICLE_SELECTED", "RESERVED", "DEPOSIT", "CONTRACT", "PARTIAL_PAYMENT", "FINAL_PAYMENT", "HANDOVER"]},
    {"id": "reserved", "label_ru": "Резерв", "stages": ["RESERVED"]},
    {"id": "paying", "label_ru": "Оплата", "stages": ["DEPOSIT", "PARTIAL_PAYMENT", "FINAL_PAYMENT"]},
    {"id": "done", "label_ru": "Закрытые", "stages": ["COMPLETED"]},
    {"id": "problems", "label_ru": "Проблемные", "stages": ["CANCELLED", "LOST"]},
]

RESERVATION_STATUSES: list[tuple[str, str]] = [
    ("ACTIVE", "Активен"),
    ("EXPIRED", "Истёк"),
    ("CANCELLED", "Отменён"),
    ("CONVERTED", "В сделку"),
]

RESERVATION_STATUS_IDS = frozenset(dict(RESERVATION_STATUSES))
RESERVATION_LABELS = dict(RESERVATION_STATUSES)

SALE_STATUSES: list[tuple[str, str]] = [
    ("OPEN", "Открыта"),
    ("COMPLETED", "Завершена"),
    ("CANCELLED", "Отменена"),
]

SALE_STATUS_IDS = frozenset(dict(SALE_STATUSES))
SALE_LABELS = dict(SALE_STATUSES)

RECEIPT_KINDS: list[tuple[str, str]] = [
    ("DEPOSIT", "Депозит"),
    ("PARTIAL", "Частичная оплата"),
    ("FINAL", "Финальная оплата"),
    ("REFUND", "Возврат"),
    ("OTHER", "Другое"),
]

RECEIPT_KIND_IDS = frozenset(dict(RECEIPT_KINDS))
RECEIPT_KIND_LABELS = dict(RECEIPT_KINDS)

RECEIPT_STATUSES: list[tuple[str, str]] = [
    ("planned", "Запланирован"),
    ("pending", "Ожидает"),
    ("confirmed", "Подтверждён"),
    ("void", "Аннулирован"),
    ("cancelled", "Отменён"),
    ("refunded", "Возврат"),
]

RECEIPT_STATUS_IDS = frozenset(dict(RECEIPT_STATUSES))

CONFIRMED_RECEIPT = frozenset({"confirmed"})
CLOSED_FINANCIAL = frozenset({"confirmed", "void", "refunded"})

IDENTITY_DOC_TYPES = frozenset({"passport", "id_card", "identity", "contract"})

REPORT_TYPES: list[dict[str, str]] = [
    {"id": "sales", "label_ru": "Продажи"},
    {"id": "vehicle_profit", "label_ru": "Прибыль по автомобилям"},
    {"id": "expenses", "label_ru": "Расходы"},
    {"id": "receipts", "label_ru": "Поступления"},
    {"id": "client_debt", "label_ru": "Задолженность клиентов"},
    {"id": "managers", "label_ru": "Работа менеджеров"},
    {"id": "funnel", "label_ru": "Воронка продаж"},
    {"id": "in_stock", "label_ru": "Автомобили в наличии"},
    {"id": "in_transit", "label_ru": "Автомобили в пути"},
]

IN_STOCK_STATUSES = frozenset({"READY_FOR_SALE", "RESERVED", "IN_UKRAINE", "PREPARATION", "CUSTOMS_CLEARED"})
IN_TRANSIT_STATUSES = frozenset({"INLAND_TRANSPORT", "AT_ORIGIN_PORT", "IN_CONTAINER", "SEA_TRANSIT"})

TELEGRAM_CRM_INTENTS: list[dict[str, str]] = [
    {"command": "/client <name>", "intent": "client_search", "note_ru": "Клиент"},
    {"command": "/deal <VIN>", "intent": "deal_by_vin", "note_ru": "Сделка"},
    {"command": "/sale <VIN>", "intent": "sale_by_vin", "note_ru": "Продажа и баланс"},
]

PII_FIELDS = ("passport_ref", "tax_id", "address", "id_number", "identity_notes")


def _pairs(items: list[tuple[str, str]]) -> list[dict[str, str]]:
    return [{"id": i, "label_ru": l} for i, l in items]


def crm_catalogs() -> dict[str, Any]:
    return {
        "deal_stages": _pairs(DEAL_STAGES),
        "crm_tabs": CRM_TABS,
        "crm_pipeline": CRM_PIPELINE,
        "reservation_statuses": _pairs(RESERVATION_STATUSES),
        "sale_statuses": _pairs(SALE_STATUSES),
        "receipt_kinds": _pairs(RECEIPT_KINDS),
        "receipt_statuses": _pairs(RECEIPT_STATUSES),
        "report_types": REPORT_TYPES,
        "crm_policy": {
            "hard_delete_payments": False,
            "hard_delete_sales": False,
            "employee_scoring": False,
            "live_scoring": False,
            "pii_backend": True,
        },
    }


def pipeline_for_stage(stage: str) -> list[dict[str, Any]]:
    st = (stage or "").upper()
    current_idx = -1
    for i, step in enumerate(CRM_PIPELINE):
        if st in step["stages"]:
            current_idx = i
            break
    out: list[dict[str, Any]] = []
    for i, step in enumerate(CRM_PIPELINE):
        if st in {"CANCELLED", "LOST"}:
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


def profit_snapshot(*, cost: float, revenue: float) -> dict[str, Any]:
    """Profit / ROI / margin from stored cost and revenue. Never invents a sale."""
    cost = round(float(cost or 0), 2)
    revenue = round(float(revenue or 0), 2)
    profit = round(revenue - cost, 2)
    roi = round((profit / cost) * 100, 2) if cost else None
    margin = round((profit / revenue) * 100, 2) if revenue else None
    return {
        "cost": cost,
        "revenue": revenue,
        "profit": profit,
        "roi_pct": roi,
        "margin_pct": margin,
        "from_records": True,
        "incomplete": cost == 0 and revenue == 0,
    }
