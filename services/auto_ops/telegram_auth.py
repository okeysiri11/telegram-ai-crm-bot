"""AUTO 1.4 Telegram auth helpers — menus, command parse, callback ownership.

No new bot. Commands are private. Callbacks are bound to the Telegram user who received them.
"""

from __future__ import annotations

import hashlib
import hmac
import re
from typing import Any

from services.auto_ops.rbac import can, normalize_role

DENIED_TEXT_RU = "Авто — закрытое рабочее пространство. Доступ только для сотрудников компании."

COMMAND_ALIASES = {
    "/start": "menu",
    "/auto": "menu",
    "/vin": "vin",
    "/logistics": "logistics",
    "/container": "container",
    "/eta": "eta",
    "/expense": "expense",
    "/task": "task",
    "/customs": "customs",
    "/vat": "vat",
    "/broker": "broker",
    "/customspay": "customspay",
    "/customsdoc": "customsdoc",
    "/customsstatus": "customsstatus",
    "/client": "client",
    "/deal": "deal",
    "/sale": "sale",
    "/pay": "pay",
    "/photo": "photo",
    "/doc": "doc",
    "/document": "doc",
    "/docs": "docs",
    "/reserve": "reserve",
    "/report": "report",
    "/analytics": "analytics",
    "/risks": "risks",
    "/cashflow": "cashflow",
    "/botstatus": "botstatus",
    "/status": "vehicle_status",
}

# Slash commands this module always intercepts (unauthorized users get a deny, not public search).
# /start is excluded so unbound users still reach the existing ADOS bot.
INTERCEPT_COMMANDS = frozenset(cmd for cmd in COMMAND_ALIASES if cmd != "/start")

ROLE_MENU: dict[str, list[dict[str, str]]] = {
    "auto_director": [
        {"id": "vin", "label_ru": "VIN"},
        {"id": "vehicles", "label_ru": "Автомобили"},
        {"id": "logistics", "label_ru": "Логистика"},
        {"id": "customs", "label_ru": "Растаможка"},
        {"id": "clients", "label_ru": "Клиенты"},
        {"id": "deals", "label_ru": "Сделки"},
        {"id": "pay", "label_ru": "Платежи"},
        {"id": "expense", "label_ru": "Расходы"},
        {"id": "tasks", "label_ru": "Задачи"},
        {"id": "docs", "label_ru": "Документы"},
        {"id": "report", "label_ru": "Отчёт"},
        {"id": "botstatus", "label_ru": "Статус бота"},
    ],
    "auto_manager": [
        {"id": "vin", "label_ru": "VIN"},
        {"id": "vehicles", "label_ru": "Автомобили"},
        {"id": "logistics", "label_ru": "Логистика"},
        {"id": "customs", "label_ru": "Растаможка"},
        {"id": "clients", "label_ru": "Клиенты"},
        {"id": "deals", "label_ru": "Сделки"},
        {"id": "reserve", "label_ru": "Резерв"},
        {"id": "expense", "label_ru": "Расход"},
        {"id": "tasks", "label_ru": "Задачи"},
        {"id": "photo", "label_ru": "Фото"},
        {"id": "docs", "label_ru": "Документы"},
    ],
    "auto_accountant": [
        {"id": "vin", "label_ru": "VIN"},
        {"id": "pay", "label_ru": "Платежи"},
        {"id": "customspay", "label_ru": "Растаможка — оплата"},
        {"id": "expense", "label_ru": "Расходы"},
        {"id": "sale", "label_ru": "Продажа"},
        {"id": "report", "label_ru": "Отчёт"},
        {"id": "docs", "label_ru": "Документы"},
    ],
    "auto_admin": [
        {"id": "botstatus", "label_ru": "Статус бота"},
        {"id": "members", "label_ru": "Сотрудники"},
        {"id": "vin", "label_ru": "VIN (просмотр)"},
    ],
}

TELEGRAM_LIVE_INTENTS: list[dict[str, str]] = [
    {"command": "/auto", "intent": "open_desk", "note_ru": "Меню Авто для сотрудника"},
    {"command": "/pay <VIN> <amount>", "intent": "add_receipt", "note_ru": "Поступление (бухгалтер)"},
    {"command": "/photo <VIN>", "intent": "add_photo", "note_ru": "Фото автомобиля"},
        {"command": "/doc <VIN>", "intent": "add_document", "note_ru": "Документ"},
    {"command": "/docs <VIN>", "intent": "docs_completeness", "note_ru": "Комплектность документов"},
    {"command": "/reserve <VIN>", "intent": "reserve", "note_ru": "Резерв"},
    {"command": "/report", "intent": "director_report", "note_ru": "Сводка директора"},
    {"command": "/analytics", "intent": "director_analytics", "note_ru": "Аналитика"},
    {"command": "/risks", "intent": "director_risks", "note_ru": "Риски"},
    {"command": "/cashflow", "intent": "director_cashflow", "note_ru": "Cash Flow"},
    {"command": "/botstatus", "intent": "bot_status", "note_ru": "Статус бота (админ)"},
]


def menu_for_role(role: str | None) -> list[dict[str, str]]:
    rid = normalize_role(role)
    return list(ROLE_MENU.get(rid) or ROLE_MENU["auto_manager"])


def parse_auto_command(text: str) -> dict[str, Any]:
    raw = (text or "").strip()
    if not raw:
        return {"cmd": "", "args": [], "raw": raw}
    first = raw.split(maxsplit=1)[0].lower().split("@")[0]
    cmd = COMMAND_ALIASES.get(first, first.lstrip("/"))
    rest = raw[len(raw.split(maxsplit=1)[0]) :].strip()
    args = rest.split() if rest else []
    return {"cmd": cmd, "args": args, "rest": rest, "raw": raw, "slash": first}


def looks_like_intercept(text: str) -> bool:
    first = (text or "").strip().split(maxsplit=1)[0].lower().split("@")[0]
    return first in INTERCEPT_COMMANDS


def callback_token(telegram_id: int, action: str, entity_id: str = "") -> str:
    """Short owned callback id. Telegram limit is 64 bytes."""
    raw = f"{int(telegram_id)}|{action}|{entity_id}"
    digest = hashlib.sha256(raw.encode()).hexdigest()[:10]
    return f"ao:{digest}"


def verify_callback_owner(telegram_id: int, stored_owner: int | None) -> bool:
    if stored_owner is None:
        return False
    return int(telegram_id) == int(stored_owner)


def idempotency_key(telegram_id: int, text: str) -> str:
    norm = re.sub(r"\s+", " ", (text or "").strip().lower())
    return hmac.new(str(telegram_id).encode(), norm.encode(), hashlib.sha256).hexdigest()[:24]


def command_allowed(role: str | None, cmd: str) -> bool:
    rid = normalize_role(role)
    if cmd in {"menu"}:
        return True
    if cmd in {"botstatus", "members"}:
        return can(rid, "admin") or can(rid, "audit")
    if cmd in {"pay", "report", "analytics", "risks", "cashflow"}:
        return can(rid, "finance") or can(rid, "finance_write") or can(rid, "reports")
    if cmd in {"customspay"}:
        return can(rid, "finance_write") or can(rid, "create") or can(rid, "edit")
    if cmd in {"expense"}:
        return can(rid, "finance_write") or can(rid, "create")
    if cmd in {"photo"}:
        return can(rid, "photos") or can(rid, "create")
    if cmd in {"doc", "docs", "customsdoc"}:
        return can(rid, "documents")
    if cmd in {"deal", "client", "sale"}:
        return can(rid, "view")
    if cmd in {"reserve", "task", "vehicle_status", "customsstatus"}:
        return can(rid, "create") or can(rid, "clients") or can(rid, "edit")
    if cmd in {"vin", "logistics", "container", "eta", "customs", "vat", "broker", "vehicles"}:
        return can(rid, "list")
    return can(rid, "view")
