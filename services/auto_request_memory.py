"""Sprint 46.1 — Auto request memory slots (conversation-first search)."""

from __future__ import annotations

import re
import threading
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AutoSearchSlots:
    brand: str | None = None
    model: str | None = None
    city: str | None = None
    country: str | None = None
    budget_max: float | None = None
    currency: str = "USD"
    fuel: str | None = None  # diesel|petrol|hybrid|electric
    year_min: int | None = None
    year_max: int | None = None
    delivery_channel: str = "telegram"
    mode: str = "fast"  # fast|deep|monitor
    query_raw: str = ""
    exclude_ask_phone: bool = True
    exclude_ask_vin: bool = True
    intent: str | None = None  # BUY_CAR | LEASING | SELL | …
    condition: str | None = None  # used | new
    down_payment: float | None = None
    term_months: int | None = None
    client_name: str | None = None
    client_phone: str | None = None
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "brand": self.brand,
            "model": self.model,
            "city": self.city,
            "country": self.country,
            "budget_max": self.budget_max,
            "currency": self.currency,
            "fuel": self.fuel,
            "year_min": self.year_min,
            "year_max": self.year_max,
            "delivery_channel": self.delivery_channel,
            "mode": self.mode,
            "query_raw": self.query_raw,
            "intent": self.intent,
            "condition": self.condition,
            "down_payment": self.down_payment,
            "term_months": self.term_months,
            "client_name": self.client_name,
            "client_phone": self.client_phone,
            "exclude_ask_phone": self.exclude_ask_phone,
            "exclude_ask_vin": self.exclude_ask_vin,
        }

    def label_ru(self) -> str:
        parts: list[str] = []
        if self.brand:
            parts.append(self.brand)
        if self.model:
            parts.append(self.model)
        if self.city:
            parts.append(self.city)
        if self.budget_max is not None:
            parts.append(f"до ${int(self.budget_max):,}".replace(",", " "))
        if self.fuel:
            fuel_ru = {
                "diesel": "дизель",
                "petrol": "бензин",
                "hybrid": "гибрид",
                "electric": "электро",
            }.get(self.fuel, self.fuel)
            parts.append(fuel_ru)
        if self.year_min:
            parts.append(f"от {self.year_min}")
        return ", ".join(parts) if parts else (self.query_raw or "поиск авто")


_BRANDS = (
    "bmw", "mercedes", "mercedes-benz", "audi", "volkswagen", "vw", "toyota", "honda",
    "lexus", "porsche", "ford", "chevrolet", "hyundai", "kia", "nissan", "mazda",
    "skoda", "renault", "peugeot", "opel", "volvo", "tesla", "land rover", "range rover",
)

_CITIES = (
    "одесса", "одеса", "киев", "київ", "харьков", "харків", "львов", "львів",
    "днепр", "дніпро", "запорожье", "винница", "николаев", "чернигов",
)


def parse_search_utterance(text: str, *, base: AutoSearchSlots | None = None) -> AutoSearchSlots:
    """Extract / merge slots from natural language. Never clears known slots unless overridden."""
    slots = AutoSearchSlots(**(base.to_dict() if base else {})) if base else AutoSearchSlots()
    raw = (text or "").strip()
    slots.query_raw = raw or slots.query_raw
    low = raw.lower()

    # refinements
    if re.search(r"только\s+дизел|дизел|diesel", low):
        slots.fuel = "diesel"
    if re.search(r"только\s+бензин|бензин|petrol|gasoline", low):
        slots.fuel = "petrol"
    if re.search(r"гибрид|hybrid", low):
        slots.fuel = "hybrid"
    if re.search(r"электро|electric|ev\b", low):
        slots.fuel = "electric"
    if re.search(r"дешевле|ниже\s+бюджет|меньше\s+бюджет", low) and slots.budget_max:
        slots.budget_max = float(slots.budget_max) * 0.9
    if re.search(r"глубок(ий|о)?\s+поиск|deep", low):
        slots.mode = "deep"
    if re.search(r"быстр(ый|о)?\s+поиск|быстро", low):
        slots.mode = "fast"
    if re.search(r"след(ить|и)|монитор|новые\s+объявл", low):
        slots.mode = "monitor"
    if re.search(r"не\s+задавай\s+вопрос|без\s+вопрос|сразу\s+ищи|просто\s+покажи|остальное\s+не\s+важн", low):
        slots.exclude_ask_phone = True
        slots.exclude_ask_vin = True

    if re.search(r"\bб/?у\b|б\.у\.|подержан|бу\b", low):
        slots.condition = "used"
    if re.search(r"лизинг|leasing", low) or re.search(r"взнос\s*\$?", low):
        slots.intent = "LEASING"
    m_down = re.search(r"взнос\s*\$?\s*([\d\s]{3,9})", low)
    if m_down:
        try:
            slots.down_payment = float(m_down.group(1).replace(" ", ""))
        except ValueError:
            pass
    m_term = re.search(r"на\s+(\d+)\s*(год|года|лет|мес)", low)
    if m_term:
        n = int(m_term.group(1))
        unit = m_term.group(2)
        slots.term_months = n if unit.startswith("мес") else n * 12
    elif re.search(r"на\s+год\b", low):
        slots.term_months = 12

    m_phone = re.search(r"(?:\+?38)?0\d{9}", low.replace(" ", "").replace("-", ""))
    if not m_phone:
        m_phone = re.search(r"0\d{2}[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}", low)
    if m_phone:
        digits = re.sub(r"\D", "", m_phone.group(0))
        slots.client_phone = digits
    m_name2 = re.search(
        r"([А-ЯЁ][а-яё]{2,15})\s+(?=0\d|\+?38)",
        text,
    )
    if m_name2:
        slots.client_name = m_name2.group(1)

    # Year: ignore amounts like $2000 / взнос 2000
    year_scrub = re.sub(r"\$\s*\d[\d\s]*", " ", low)
    year_scrub = re.sub(r"взнос\s*\$?\s*\d[\d\s]*", " ", year_scrub)
    m_year = re.search(r"(?:от\s+|с\s+|года?\s+)?(20[1-2]\d)\s*\+?", year_scrub)
    if m_year:
        slots.year_min = int(m_year.group(1))
    m_year2 = re.search(r"(20[1-2]\d)\s*[-–]\s*(20[1-2]\d)", year_scrub)
    if m_year2:
        slots.year_min = int(m_year2.group(1))
        slots.year_max = int(m_year2.group(2))

    # budget: «до $15000», «можно до $17000», «до 15000 долларов»
    m_budget = re.search(
        r"(?:можно\s+)?(?:до\s*|<=?\s*|≤\s*)\$?\s*([\d\s]{3,9})\s*(?:\$|usd|доллар(?:ов|а)?|бакс)?",
        low,
        re.I,
    )
    if not m_budget:
        m_budget = re.search(r"([\d\s]{4,9})\s*\$", low)
    if m_budget:
        try:
            slots.budget_max = float(m_budget.group(1).replace(" ", "").replace(",", ""))
        except ValueError:
            pass

    for city in _CITIES:
        if city in low:
            slots.city = "Одесса" if city in ("одесса", "одеса") else city.title()
            break

    # brand / model — keep existing unless new brand found
    for brand in _BRANDS:
        if brand in low:
            nice = {
                "vw": "Volkswagen",
                "mercedes-benz": "Mercedes",
                "mercedes": "Mercedes",
                "bmw": "BMW",
                "land rover": "Land Rover",
                "range rover": "Range Rover",
            }.get(brand, brand.title())
            slots.brand = nice
            break

    # common models after brand
    model_patterns = (
        r"\bx5\b", r"\bx3\b", r"\bx6\b", r"\bx7\b", r"\bgle\b", r"\bglc\b", r"\bc-?class\b",
        r"\ba4\b", r"\ba6\b", r"\bq5\b", r"\bq7\b", r"\bcamry\b", r"\braav4\b", r"\btucson\b",
    )
    for pat in model_patterns:
        m = re.search(pat, low, re.I)
        if m:
            slots.model = m.group(0).upper().replace("-", "")
            if slots.model.lower() == "x5" and not slots.brand:
                slots.brand = "BMW"
            break

    # "Найди X5" without brand
    if not slots.model and re.search(r"\bx5\b", low):
        slots.model = "X5"
        slots.brand = slots.brand or "BMW"

    slots.updated_at = time.time()
    return slots


def conversation_summary_ru(slots: AutoSearchSlots) -> str:
    bits = []
    if slots.brand or slots.model:
        bits.append(f"Клиент ищет {' '.join(x for x in (slots.brand, slots.model) if x)}")
    else:
        bits.append("Клиент ищет автомобиль")
    if slots.budget_max:
        bits.append(f"до ${int(slots.budget_max):,}".replace(",", " "))
    if slots.city:
        bits.append(f"в {slots.city}")
    line = " ".join(bits) + "."
    extras = []
    if not slots.year_min and not slots.year_max:
        extras.append("Год и пробег не принципиальны.")
    if not slots.fuel:
        extras.append("Предпочтения по топливу пока не указаны.")
    extras.append("Подборку хочет получать в Telegram.")
    return line + "\n" + "\n".join(extras)


class AutoRequestMemoryStore:
    """Per-user search request memory (one commercial thread = one request)."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._slots: dict[int, AutoSearchSlots] = {}
        self._results: dict[int, list[dict[str, Any]]] = {}
        self._lead_id: dict[int, str] = {}
        self._favorites: dict[int, list[dict[str, Any]]] = {}

    def get(self, user_id: int) -> AutoSearchSlots | None:
        with self._lock:
            return self._slots.get(user_id)

    def update(self, user_id: int, text: str) -> AutoSearchSlots:
        with self._lock:
            base = self._slots.get(user_id)
            slots = parse_search_utterance(text, base=base)
            self._slots[user_id] = slots
            return slots

    def set_results(self, user_id: int, cars: list[dict[str, Any]]) -> None:
        with self._lock:
            self._results[user_id] = list(cars)

    def results(self, user_id: int) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._results.get(user_id) or [])

    def get_lead_id(self, user_id: int) -> str | None:
        with self._lock:
            return self._lead_id.get(user_id)

    def ensure_lead(self, user_id: int) -> str:
        with self._lock:
            if user_id not in self._lead_id:
                self._lead_id[user_id] = f"lead_{user_id}_{int(time.time())}"
            return self._lead_id[user_id]

    def save_favorite(self, user_id: int, car: dict[str, Any]) -> None:
        with self._lock:
            fav = self._favorites.setdefault(user_id, [])
            fav.append(car)

    def clear(self, user_id: int | None = None) -> None:
        with self._lock:
            if user_id is None:
                self._slots.clear()
                self._results.clear()
                self._lead_id.clear()
                self._favorites.clear()
            else:
                self._slots.pop(user_id, None)
                self._results.pop(user_id, None)
                self._lead_id.pop(user_id, None)
                self._favorites.pop(user_id, None)


auto_request_memory = AutoRequestMemoryStore()
