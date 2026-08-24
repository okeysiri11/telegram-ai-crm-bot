"""AUTO 1.5 analytics catalogs — filters, funnel, completeness, accounts.

Deterministic helpers. No invented market numbers.
"""

from __future__ import annotations

import csv
import io
from datetime import date, datetime, timedelta, timezone
from typing import Any

from services.auto_ops.catalog import DOCUMENT_LABELS, FINANCE_KPI_GROUPS, STATUS_LABELS
from services.auto_ops.crm_catalog import profit_snapshot

ECONOMICS_FILTERS: list[dict[str, str]] = [
    {"id": "all", "label_ru": "Все"},
    {"id": "profitable", "label_ru": "Прибыльные"},
    {"id": "low_margin", "label_ru": "Низкая маржа"},
    {"id": "loss", "label_ru": "Убыток"},
    {"id": "unsold", "label_ru": "Не проданы"},
    {"id": "sold", "label_ru": "Проданы"},
    {"id": "age_30", "label_ru": "30+ дней"},
    {"id": "age_60", "label_ru": "60+ дней"},
    {"id": "age_90", "label_ru": "90+ дней"},
    {"id": "age_120", "label_ru": "120+ дней"},
]

PERIODS: list[dict[str, str]] = [
    {"id": "today", "label_ru": "Сегодня"},
    {"id": "7d", "label_ru": "7 дней"},
    {"id": "30d", "label_ru": "30 дней"},
    {"id": "quarter", "label_ru": "Квартал"},
    {"id": "year", "label_ru": "Год"},
    {"id": "all", "label_ru": "Всё время"},
    {"id": "custom", "label_ru": "Свои даты"},
]

FUNNEL_STAGES: list[dict[str, Any]] = [
    {"id": "purchased", "label_ru": "Куплено", "statuses": ["WON", "PURCHASED", "AWAITING_PICKUP", "AUCTION"]},
    {"id": "in_transit", "label_ru": "В пути", "statuses": ["INLAND_TRANSPORT", "AT_ORIGIN_PORT", "IN_CONTAINER", "SEA_TRANSIT"]},
    {"id": "port", "label_ru": "Порт", "statuses": ["DESTINATION_PORT"]},
    {"id": "customs", "label_ru": "Таможня", "statuses": ["CUSTOMS", "CUSTOMS_CLEARED"]},
    {"id": "repair", "label_ru": "Ремонт", "statuses": ["PREPARATION", "IN_UKRAINE"]},
    {"id": "sale", "label_ru": "Продажа", "statuses": ["READY_FOR_SALE"]},
    {"id": "reserved", "label_ru": "Бронь", "statuses": ["RESERVED"]},
    {"id": "sold", "label_ru": "Продано", "statuses": ["SOLD"]},
]

ACCOUNT_TYPES: list[dict[str, str]] = [
    {"id": "BANK_UAH", "label_ru": "Банк UAH", "currency": "UAH"},
    {"id": "BANK_USD", "label_ru": "Банк USD", "currency": "USD"},
    {"id": "CASH_UAH", "label_ru": "Касса UAH", "currency": "UAH"},
    {"id": "CASH_USD", "label_ru": "Касса USD", "currency": "USD"},
    {"id": "GEORGIA", "label_ru": "Georgia account", "currency": "USD"},
    {"id": "USDT_LEDGER", "label_ru": "USDT wallet (учёт, не custody)", "currency": "USDT"},
    {"id": "OTHER", "label_ru": "Другое", "currency": "USD"},
]

READINESS_DOCS: list[tuple[str, str]] = [
    ("auction_invoice", "Auction invoice"),
    ("title", "Title"),
    ("bill_of_lading", "Bill of lading"),
    ("customs_declaration", "Customs declaration"),
    ("certificate", "Certification"),
    ("contract", "Client contract"),
    ("payment_confirmation", "Payment docs"),
]

COST_BUCKETS: dict[str, tuple[str, ...]] = {
    "purchase": tuple(FINANCE_KPI_GROUPS["purchase_cost"]),
    "logistics": tuple(FINANCE_KPI_GROUPS["logistics"]),
    "customs": tuple(FINANCE_KPI_GROUPS["customs"]),
    "repair": ("REPAIR", "PARTS"),
}

LOW_MARGIN_PCT = 10.0
SALE_STALE_DAYS = 60
REPAIR_OVER_DAYS = 21
MIN_COMPARE_N = 3

QUALITY = ("KNOWN", "PARTIAL", "UNKNOWN")


def parse_day(value: Any) -> date | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def days_between(start: Any, end: Any | None = None) -> int | None:
    a = parse_day(start)
    b = parse_day(end) or datetime.now(timezone.utc).date()
    if a is None:
        return None
    return max((b - a).days, 0)


def period_bounds(period: str, date_from: str | None = None, date_to: str | None = None, today: date | None = None) -> tuple[date | None, date | None]:
    today = today or datetime.now(timezone.utc).date()
    p = (period or "all").strip().lower()
    if p in {"custom", "range"}:
        return parse_day(date_from), parse_day(date_to) or today
    if p == "today":
        return today, today
    if p in {"7d", "7"}:
        return today - timedelta(days=6), today
    if p in {"30d", "30"}:
        return today - timedelta(days=29), today
    if p in {"quarter", "q"}:
        q_month = ((today.month - 1) // 3) * 3 + 1
        return date(today.year, q_month, 1), today
    if p in {"year", "y"}:
        return date(today.year, 1, 1), today
    return None, None


def in_period(value: Any, start: date | None, end: date | None) -> bool:
    if start is None and end is None:
        return True
    day = parse_day(value)
    if day is None:
        return False
    if start and day < start:
        return False
    if end and day > end:
        return False
    return True


def quality_of(*, known: int, required: int) -> str:
    if required <= 0:
        return "UNKNOWN"
    if known <= 0:
        return "UNKNOWN"
    if known >= required:
        return "KNOWN"
    return "PARTIAL"


def forecast_profit(*, invested: float, remaining: float, expected_sale: float | None) -> dict[str, Any]:
    invested = round(float(invested or 0), 2)
    remaining = round(float(remaining or 0), 2)
    total = round(invested + remaining, 2)
    if expected_sale is None:
        return {
            "label_ru": "ПРОГНОЗ",
            "actual": False,
            "expected_sale_price": None,
            "estimated_remaining_cost": remaining,
            "forecast_total_cost": total,
            "forecast_profit": None,
            "forecast_margin": None,
            "quality": "UNKNOWN" if invested == 0 else "PARTIAL",
            "note_ru": "Нет ожидаемой цены продажи — прогноз прибыли не считается.",
        }
    snap = profit_snapshot(cost=total, revenue=float(expected_sale))
    return {
        "label_ru": "ПРОГНОЗ",
        "actual": False,
        "expected_sale_price": round(float(expected_sale), 2),
        "estimated_remaining_cost": remaining,
        "forecast_total_cost": total,
        "forecast_profit": snap["profit"],
        "forecast_margin": snap["margin_pct"],
        "quality": "PARTIAL" if remaining or invested == 0 else "KNOWN",
        "note_ru": "Прогноз, не факт. Считается только из внесённых ожидаемой цены и расходов.",
    }


def recommend_price_cut(*, cost: float, current_price: float, target_price: float) -> dict[str, Any]:
    current = profit_snapshot(cost=cost, revenue=current_price)
    target = profit_snapshot(cost=cost, revenue=target_price)
    return {
        "current_price": round(current_price, 2),
        "target_price": round(target_price, 2),
        "cost": round(cost, 2),
        "current_margin_pct": current["margin_pct"],
        "target_margin_pct": target["margin_pct"],
        "current_profit": current["profit"],
        "target_profit": target["profit"],
        "from_records": True,
    }


def csv_bytes(headers: list[str], rows: list[list[Any]]) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(["" if c is None else c for c in row])
    return buf.getvalue().encode("utf-8-sig")


def matches_economics_filter(row: dict[str, Any], filt: str) -> bool:
    f = (filt or "all").strip().lower().replace("+", "_").replace("-", "_")
    sold = bool(row.get("sold"))
    profit = row.get("profit")
    margin = row.get("margin_pct")
    days = row.get("days_in_cycle")
    if f in {"", "all"}:
        return True
    if f == "sold":
        return sold
    if f == "unsold":
        return not sold
    if f == "profitable":
        return sold and profit is not None and float(profit) > 0
    if f in {"loss", "unprofitable"}:
        return sold and profit is not None and float(profit) < 0
    if f in {"low_margin", "lowmargin"}:
        return sold and margin is not None and float(margin) < LOW_MARGIN_PCT
    ages = {"age_30": 30, "30": 30, "age_60": 60, "60": 60, "age_90": 90, "90": 90, "age_120": 120, "120": 120}
    if f in ages:
        return days is not None and int(days) >= ages[f]
    return True


def sort_rows(rows: list[dict[str, Any]], sort: str, direction: str = "desc") -> list[dict[str, Any]]:
    key = (sort or "updated_at").strip()
    reverse = (direction or "desc").lower() != "asc"

    def val(row: dict[str, Any]) -> Any:
        v = row.get(key)
        if v is None:
            return "" if reverse else "\uffff"
        return v

    return sorted(rows, key=val, reverse=reverse)


def status_label(status: str) -> str:
    return STATUS_LABELS.get(status, status)


def doc_label(doc_type: str) -> str:
    return DOCUMENT_LABELS.get(doc_type, doc_type)
