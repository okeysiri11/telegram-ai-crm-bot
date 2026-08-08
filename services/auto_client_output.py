"""Sprint 46.1 — Client vs staff output sanitizer."""

from __future__ import annotations

import re
from typing import Any

STAFF_ROLES = frozenset({"owner", "manager", "admin", "dealer", "staff"})

_INTERNAL_PATTERNS = [
    re.compile(r"Score\s*:\s*\d+", re.I),
    re.compile(r"Priority\s*:\s*\w+", re.I),
    re.compile(r"Dept\s*:\s*\w+", re.I),
    re.compile(r"Intent\s*:\s*\w+", re.I),
    re.compile(r"📊\s*Score\s*:\s*\d+", re.I),
    re.compile(r"confidence\s*:\s*[\d.]+", re.I),
    re.compile(r"\btenant[_ ]?id\b", re.I),
    re.compile(r"\bruntime\b", re.I),
    re.compile(r"\bprovider\b", re.I),
    re.compile(r"\bworker\b", re.I),
    re.compile(r"No active tenant context", re.I),
    re.compile(r"Dealer rates not configured[^\n]*", re.I),
]


def is_staff_role(role: str | None) -> bool:
    return (role or "client").lower() in STAFF_ROLES


def sanitize_ai_reply_for_client(text: str, *, role: str = "client", debug: bool = False) -> str:
    if is_staff_role(role) and debug:
        return text
    out = text or ""
    for pat in _INTERNAL_PATTERNS:
        out = pat.sub("", out)
    # drop leftover meta blocks
    out = re.sub(r"\n{3,}", "\n\n", out).strip()
    return out


def format_car_card_ru(car: dict[str, Any]) -> str:
    title = car.get("title") or f"{car.get('brand') or car.get('make', '')} {car.get('model', '')}".strip() or "Автомобиль"
    year = car.get("year") or "—"
    price = car.get("price") or car.get("price_usd") or "—"
    try:
        price_s = f"${int(float(price)):,}".replace(",", " ")
    except (TypeError, ValueError):
        price_s = str(price)
    fuel = car.get("fuel") or "—"
    city = car.get("city") or car.get("location") or "—"
    mileage = car.get("mileage")
    mil_s = f"{int(mileage):,} км".replace(",", " ") if mileage else "—"
    url = car.get("url") or car.get("link") or car.get("listing_url") or ""
    lines = [
        f"🚗 {title}",
        f"📅 {year}",
        f"💰 {price_s}",
        f"📍 {city}",
        f"⛽ {fuel}",
        f"🛣 {mil_s}",
        "",
        "📸 Фото",
        "🔗 Открыть объявление" + (f"\n{url}" if url else ""),
        "⭐ Сохранить",
        "📞 Связаться",
    ]
    return "\n".join(lines)


def user_facing_tenant_error_ru() -> str:
    return "Не удалось определить организацию. Выберите рабочее пространство."


def user_facing_rates_missing_ru(*, is_owner: bool = False) -> str:
    if is_owner:
        return "Курсы дилера пока не настроены.\n\n[⚙ Настроить]"
    return ""  # clients should not see technical rates errors
