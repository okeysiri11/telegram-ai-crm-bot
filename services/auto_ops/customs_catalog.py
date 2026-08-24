"""AUTO 1.2 customs catalogs — cases, VAT, checklist, org-configured rates.

Rates are organization settings, never claimed as live Гостаможня / НБУ APIs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

CASE_STATUSES: list[tuple[str, str]] = [
    ("AWAITING_ARRIVAL", "Ожидает прибытия"),
    ("DOCUMENTS_PREP", "Сбор документов"),
    ("SUBMITTED", "Подано брокеру / таможне"),
    ("INSPECTION", "Осмотр"),
    ("DUTY_CALCULATION", "Расчёт платежей"),
    ("PAYMENT_PENDING", "К оплате"),
    ("PAID", "Оплачено"),
    ("CLEARED", "Выпущено / растаможено"),
    ("CERTIFICATION", "Сертификация"),
    ("REGISTRATION_PREP", "Подготовка к регистрации"),
    ("REGISTERED", "Зарегистрировано"),
    ("ON_HOLD", "На паузе"),
    ("REJECTED", "Отказ"),
]

CASE_STATUS_LABELS = dict(CASE_STATUSES)
CASE_STATUS_IDS = frozenset(CASE_STATUS_LABELS)

CUSTOMS_TABS: list[dict[str, Any]] = [
    {"id": "all", "label_ru": "Все дела", "statuses": None, "exclude": []},
    {"id": "docs", "label_ru": "Ожидают документы", "statuses": ["AWAITING_ARRIVAL", "DOCUMENTS_PREP"]},
    {"id": "calc", "label_ru": "На расчёте", "statuses": ["SUBMITTED", "INSPECTION", "DUTY_CALCULATION"]},
    {"id": "pay", "label_ru": "К оплате", "statuses": ["PAYMENT_PENDING"]},
    {"id": "release", "label_ru": "Оплачено / выпуск", "statuses": ["PAID", "CLEARED"]},
    {"id": "cert", "label_ru": "Сертификация", "statuses": ["CERTIFICATION"]},
    {"id": "reg", "label_ru": "Подготовка к регистрации", "statuses": ["REGISTRATION_PREP"]},
    {"id": "done", "label_ru": "Завершённые", "statuses": ["REGISTERED"]},
    {"id": "problems", "label_ru": "Проблемные", "statuses": ["ON_HOLD", "REJECTED"], "problems": True},
]

CUSTOMS_PIPELINE: list[dict[str, Any]] = [
    {"id": "docs", "label_ru": "Документы", "statuses": ["AWAITING_ARRIVAL", "DOCUMENTS_PREP"]},
    {"id": "submit", "label_ru": "Подача", "statuses": ["SUBMITTED"]},
    {"id": "inspect", "label_ru": "Осмотр", "statuses": ["INSPECTION"]},
    {"id": "calc", "label_ru": "Расчёт", "statuses": ["DUTY_CALCULATION"]},
    {"id": "pay", "label_ru": "Оплата", "statuses": ["PAYMENT_PENDING", "PAID"]},
    {"id": "clear", "label_ru": "Выпуск", "statuses": ["CLEARED"]},
    {"id": "cert", "label_ru": "Сертификация", "statuses": ["CERTIFICATION"]},
    {"id": "reg", "label_ru": "Регистрация", "statuses": ["REGISTRATION_PREP", "REGISTERED"]},
]

NEXT_STAGE: dict[str, str] = {
    "AWAITING_ARRIVAL": "DOCUMENTS_PREP",
    "DOCUMENTS_PREP": "SUBMITTED",
    "SUBMITTED": "INSPECTION",
    "INSPECTION": "DUTY_CALCULATION",
    "DUTY_CALCULATION": "PAYMENT_PENDING",
    "PAYMENT_PENDING": "PAID",
    "PAID": "CLEARED",
    "CLEARED": "CERTIFICATION",
    "CERTIFICATION": "REGISTRATION_PREP",
    "REGISTRATION_PREP": "REGISTERED",
    "REGISTERED": "REGISTERED",
    "ON_HOLD": "DOCUMENTS_PREP",
    "REJECTED": "DOCUMENTS_PREP",
}

# Spec names from AUTO 1.8. Canonical storage remains 1.2 CASE_STATUS_IDS.
STATUS_ALIASES: dict[str, str] = {
    "NOT_STARTED": "AWAITING_ARRIVAL",
    "PREPARING_DOCUMENTS": "DOCUMENTS_PREP",
    "BROKER_ASSIGNED": "SUBMITTED",
    "DECLARATION_PREPARATION": "DUTY_CALCULATION",
    "DECLARATION_SUBMITTED": "SUBMITTED",
}

PIPELINE_ORDER: list[str] = [
    "AWAITING_ARRIVAL",
    "DOCUMENTS_PREP",
    "SUBMITTED",
    "INSPECTION",
    "DUTY_CALCULATION",
    "PAYMENT_PENDING",
    "PAID",
    "CLEARED",
    "CERTIFICATION",
    "REGISTRATION_PREP",
    "REGISTERED",
]

HOLD_STATUSES = frozenset({"ON_HOLD", "REJECTED"})

CUSTOMS_CHARGE_CATEGORIES: list[tuple[str, str]] = [
    ("DUTY", "Мито"),
    ("EXCISE", "Акциз"),
    ("IMPORT_VAT", "НДС на импорт"),
    ("BROKER", "Брокер"),
    ("CERTIFICATION", "Сертификация"),
    ("REGISTRATION", "Регистрация"),
    ("CUSTOMS", "Таможенные платежи"),
    ("CUSTOMS_PENALTY", "Штраф таможни"),
    ("CERT_LAB", "Орган сертификации"),
    ("MREO", "МРЕО"),
]

CHARGE_IDS = frozenset(dict(CUSTOMS_CHARGE_CATEGORIES))

LANDED_LINES: list[tuple[str, str, tuple[str, ...]]] = [
    ("purchase", "Покупка", ("PURCHASE",)),
    ("auction_fee", "Комиссия аукциона", ("AUCTION_FEE",)),
    ("logistics", "Логистика", ()),  # filled from logistics expense ids at runtime
    ("customs_duty", "Мито", ("DUTY",)),
    ("excise", "Акциз", ("EXCISE",)),
    ("vat", "НДС", ("IMPORT_VAT",)),
    ("broker", "Брокер", ("BROKER",)),
    ("certification", "Сертификация", ("CERTIFICATION", "CERT_LAB")),
    ("registration", "Регистрация", ("REGISTRATION", "MREO")),
]

SELLING_COST_IDS = frozenset({"REPAIR", "PARTS"})


def normalize_case_status(value: Any) -> str:
    raw = str(value or "").strip().upper()
    return STATUS_ALIASES.get(raw, raw)


def pipeline_index(status: str) -> int | None:
    st = normalize_case_status(status)
    try:
        return PIPELINE_ORDER.index(st)
    except ValueError:
        return None


def is_backward_transition(current: str, target: str) -> bool:
    ci = pipeline_index(current)
    ni = pipeline_index(target)
    if ci is None or ni is None:
        return False
    return ni < ci


def transition_allowed(current: str, target: str, *, telegram: bool = False) -> bool:
    """HTTP allows forward skips. Telegram allows only the immediate next stage (+ hold/reject)."""
    cur = normalize_case_status(current)
    nxt = normalize_case_status(target)
    if nxt not in CASE_STATUS_IDS:
        return False
    if cur == nxt:
        return True
    if nxt in HOLD_STATUSES:
        return True
    if cur in HOLD_STATUSES:
        if telegram:
            return nxt == NEXT_STAGE.get(cur, "DOCUMENTS_PREP")
        return nxt in PIPELINE_ORDER
    ci = pipeline_index(cur)
    ni = pipeline_index(nxt)
    if ci is None or ni is None:
        return False
    if ni < ci:
        return False
    if telegram:
        return nxt == NEXT_STAGE.get(cur)
    return ni >= ci


def allowed_next_statuses(current: str, *, telegram: bool = False) -> list[str]:
    cur = normalize_case_status(current)
    out: list[str] = []
    for st, _label in CASE_STATUSES:
        if st == cur:
            continue
        if transition_allowed(cur, st, telegram=telegram):
            out.append(st)
    return out

CERT_STATUSES: list[tuple[str, str]] = [
    ("NOT_STARTED", "Не начата"),
    ("IN_PROGRESS", "В работе"),
    ("CERTIFIED", "Сертификат получен"),
    ("FAILED", "Отказ"),
]

REG_STATUSES: list[tuple[str, str]] = [
    ("NOT_READY", "Пакет не готов"),
    ("DOCS_READY", "Документы собраны"),
    ("SUBMITTED", "Подано в МРЕО"),
    ("REGISTERED", "Зарегистрировано"),
]

BROKER_TYPES: list[tuple[str, str]] = [
    ("customs_broker", "Таможенный брокер"),
    ("certification_lab", "Орган сертификации"),
    ("mreo_agent", "Представитель МРЕО"),
    ("other", "Другое"),
]

CHECKLIST: list[dict[str, str]] = [
    {"id": "invoice", "document_type": "invoice", "label_ru": "Инвойс / счёт"},
    {"id": "title", "document_type": "title", "label_ru": "Title / техпаспорт"},
    {"id": "title_copy", "document_type": "title_copy", "label_ru": "Копия Title"},
    {"id": "bl", "document_type": "bill_of_lading", "label_ru": "Коносамент (B/L)"},
    {"id": "packing", "document_type": "packing_list", "label_ru": "Упаковочный лист"},
    {"id": "export", "document_type": "export_document", "label_ru": "Экспортный документ"},
    {"id": "md", "document_type": "customs_declaration", "label_ru": "Таможенная декларация (МД)"},
    {"id": "broker", "document_type": "broker", "label_ru": "Документы брокера"},
    {"id": "payment", "document_type": "payment_confirmation", "label_ru": "Подтверждение оплаты"},
    {"id": "certificate", "document_type": "certificate", "label_ru": "Сертификат соответствия"},
    {"id": "registration", "document_type": "registration", "label_ru": "Документы МРЕО"},
]

CUSTOMS_EXPENSE_IDS = frozenset(
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

# Organization-configurable defaults. Not live law, not НБУ, not Гостаможня.
DEFAULT_RATES: dict[str, Any] = {
    "duty_rate": 0.10,
    "vat_rate": 0.20,
    "excise_petrol_per_cc": 50.0,
    "excise_diesel_per_cc": 75.0,
    "excise_hybrid_per_cc": 25.0,
    "excise_electric": 0.0,
    "age_coeff_under_5": 1.0,
    "age_coeff_5_8": 1.2,
    "age_coeff_over_8": 1.5,
    "base_currency": "UAH",
    "disclaimer_ru": "Расчёт по ставкам организации. Это не официальный калькулятор Гостаможни и не live-курс НБУ.",
}

TELEGRAM_CUSTOMS_INTENTS: list[dict[str, str]] = [
    {"command": "/customs <VIN>", "intent": "customs_by_vin", "note_ru": "Дело растаможки"},
    {"command": "/vat <VIN>", "intent": "vat_by_vin", "note_ru": "НДС и платежи"},
    {"command": "/broker <VIN>", "intent": "broker_by_vin", "note_ru": "Брокер и статус"},
    {"command": "/customspay <VIN>", "intent": "customs_pay", "note_ru": "Платёж растаможки (не подтверждается молча)"},
    {"command": "/customsdoc <VIN>", "intent": "customs_document", "note_ru": "Документ в дело растаможки"},
    {"command": "/customsstatus <VIN>", "intent": "customs_status", "note_ru": "Следующий допустимый этап"},
]


def _pairs(items: list[tuple[str, str]]) -> list[dict[str, str]]:
    return [{"id": i, "label_ru": l} for i, l in items]


def customs_catalogs() -> dict[str, Any]:
    return {
        "customs_case_statuses": _pairs(CASE_STATUSES),
        "customs_tabs": CUSTOMS_TABS,
        "customs_pipeline": CUSTOMS_PIPELINE,
        "certification_statuses": _pairs(CERT_STATUSES),
        "registration_statuses": _pairs(REG_STATUSES),
        "broker_types": _pairs(BROKER_TYPES),
        "customs_checklist": CHECKLIST,
        "customs_rates": DEFAULT_RATES,
        "customs_policy": {
            "live_customs_api": False,
            "live_nbu_fx": False,
            "official_calculator": False,
            "manual_label_ru": "Введено вручную",
            "org_rate_label_ru": "Ставка организации",
            "disclaimer_ru": DEFAULT_RATES["disclaimer_ru"],
            "correction_requires_reason": True,
            "telegram_status_skips": False,
        },
        "customs_status_aliases": [{"id": k, "maps_to": v} for k, v in STATUS_ALIASES.items()],
        "customs_pipeline_order": PIPELINE_ORDER,
        "customs_charges": _pairs(CUSTOMS_CHARGE_CATEGORIES),
    }


def _num(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def age_years(year: Any, today_year: int | None = None) -> int | None:
    if year in (None, ""):
        return None
    try:
        y = int(year)
    except (TypeError, ValueError):
        return None
    now_y = today_year or datetime.now(timezone.utc).year
    age = now_y - y
    return age if age >= 0 else 0


def age_coeff(age: int | None, rates: dict[str, Any] | None = None) -> float:
    r = {**DEFAULT_RATES, **(rates or {})}
    if age is None:
        return float(r["age_coeff_under_5"])
    if age < 5:
        return float(r["age_coeff_under_5"])
    if age < 8:
        return float(r["age_coeff_5_8"])
    return float(r["age_coeff_over_8"])


def excise_per_cc(fuel_type: str | None, rates: dict[str, Any] | None = None) -> float:
    r = {**DEFAULT_RATES, **(rates or {})}
    fuel = (fuel_type or "petrol").strip().lower()
    if fuel in {"diesel", "дизель"}:
        return float(r["excise_diesel_per_cc"])
    if fuel in {"hybrid", "гибрид"}:
        return float(r["excise_hybrid_per_cc"])
    if fuel in {"electric", "ev", "электро"}:
        return float(r["excise_electric"])
    return float(r["excise_petrol_per_cc"])


def calculate_customs(
    *,
    customs_value: Any,
    currency: str | None = "USD",
    fx_rate_to_uah: Any = None,
    engine_cc: Any = None,
    fuel_type: str | None = None,
    year: Any = None,
    broker_fee_uah: Any = 0,
    rates: dict[str, Any] | None = None,
    today_year: int | None = None,
) -> dict[str, Any]:
    """Transparent org-rate calculation. Never invents a value or an FX rate."""
    r = {**DEFAULT_RATES, **(rates or {})}
    value = _num(customs_value)
    fx = _num(fx_rate_to_uah)
    cc = _num(engine_cc)
    broker = _num(broker_fee_uah) or 0.0
    cur = (currency or "USD").upper()
    if cur == "UAH" and fx is None:
        fx = 1.0
    incomplete: list[str] = []
    if value is None:
        incomplete.append("customs_value")
    if fx is None:
        incomplete.append("fx_rate_to_uah")
    if cc is None:
        incomplete.append("engine_cc")
    age = age_years(year, today_year)
    if age is None:
        incomplete.append("year")
    if incomplete:
        return {
            "ok": False,
            "incomplete": incomplete,
            "source": "org_rates",
            "disclaimer_ru": r["disclaimer_ru"],
            "currency": "UAH",
            "input_currency": cur,
        }
    assert value is not None and fx is not None and cc is not None
    value_uah = round(value * fx, 2)
    duty_rate = float(r["duty_rate"])
    vat_rate = float(r["vat_rate"])
    duty = round(value_uah * duty_rate, 2)
    per_cc = excise_per_cc(fuel_type, r)
    coeff = age_coeff(age, r)
    excise = round(cc * per_cc * coeff, 2)
    vat_base = round(value_uah + duty + excise, 2)
    vat = round(vat_base * vat_rate, 2)
    state_total = round(duty + excise + vat, 2)
    grand = round(state_total + broker, 2)
    return {
        "ok": True,
        "incomplete": [],
        "source": "org_rates",
        "disclaimer_ru": r["disclaimer_ru"],
        "fx_source_label_ru": "Введено вручную",
        "rate_source_label_ru": "Ставка организации",
        "input_currency": cur,
        "currency": "UAH",
        "customs_value": value,
        "fx_rate_to_uah": fx,
        "customs_value_uah": value_uah,
        "engine_cc": cc,
        "fuel_type": fuel_type,
        "year": year,
        "age_years": age,
        "age_coeff": coeff,
        "duty_rate": duty_rate,
        "duty_uah": duty,
        "excise_per_cc": per_cc,
        "excise_uah": excise,
        "vat_rate": vat_rate,
        "vat_base_uah": vat_base,
        "import_vat_uah": vat,
        "state_total_uah": state_total,
        "broker_fee_uah": broker,
        "grand_total_uah": grand,
        "lines": [
            {"id": "duty", "label_ru": "Мито", "amount_uah": duty},
            {"id": "excise", "label_ru": "Акциз", "amount_uah": excise},
            {"id": "import_vat", "label_ru": "НДС на импорт", "amount_uah": vat},
            {"id": "broker", "label_ru": "Брокер", "amount_uah": broker},
        ],
    }


def pipeline_for_case(status: str) -> list[dict[str, Any]]:
    st = (status or "").upper()
    current_idx = -1
    for i, step in enumerate(CUSTOMS_PIPELINE):
        if st in step["statuses"]:
            current_idx = i
            break
    out: list[dict[str, Any]] = []
    for i, step in enumerate(CUSTOMS_PIPELINE):
        if st in {"REJECTED", "ON_HOLD"} and current_idx < 0:
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
