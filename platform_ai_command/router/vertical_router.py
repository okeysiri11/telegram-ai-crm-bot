"""Vertical router — detect industry vertical from natural language."""

from __future__ import annotations

import re

VERTICALS: tuple[str, ...] = (
    "beauty",
    "auto",
    "crypto",
    "agro",
    "drone",
    "construction",
    "travel",
    "legal",
    "marketplace",
    "medical",
    "production",
    "owner",
    "crm",
    "erp",
    "knowledge",
)

_RULES: list[tuple[re.Pattern[str], str]] = [
    # Auto before Beauty — "auto" must not lose to sticky beauty tags (also stripped)
    (re.compile(r"авто|машин|vin|автосалон|autoria|olx|\bauto\b", re.I), "auto"),
    (re.compile(r"красот|салон|маникюр|beauty|косметолог|барбер|spa", re.I), "beauty"),
    (re.compile(r"crypto|крипт|otc|биткоин|btc", re.I), "crypto"),
    (re.compile(r"агро|зерн|урожа|ферм|пшениц", re.I), "agro"),
    (re.compile(r"дрон|uav|бпла", re.I), "drone"),
    (re.compile(r"строител|бетон|объект\s*строи", re.I), "construction"),
    (re.compile(r"тур|путешеств|отел|travel", re.I), "travel"),
    (re.compile(r"договор|юридич|претензи|иск|legal", re.I), "legal"),
    (re.compile(r"маркетплейс|товар|карточка\s*товар", re.I), "marketplace"),
    (re.compile(r"медицин|клиник|пациент|врач", re.I), "medical"),
    (re.compile(r"производств|завод|цех", re.I), "production"),
    (re.compile(r"прибыл|кп\b|владел|owner|проанализир\s*продаж", re.I), "owner"),
    (re.compile(r"crm|клиент|сделк|лид", re.I), "crm"),
    (re.compile(r"erp|склад|закупк|накладн", re.I), "erp"),
    (re.compile(r"знание|knowledge|баз[аы]\s*знан", re.I), "knowledge"),
]

CLARIFY_RU = (
    "Уточните отрасль: Beauty, Auto, Crypto, Агро, Дроны, Строительство, "
    "Travel, Юриспруденция, Marketplace, Медицина, Производство, Owner, CRM, ERP или Knowledge?"
)

CLARIFY_MARKETING_RU = (
    "Понял. Могу подготовить рекламную концепцию.\n\n"
    "Чтобы начать, мне достаточно:\n"
    "• название;\n"
    "• город;\n"
    "• что хотите продвигать.\n\n"
    "Или напишите одной строкой:\n"
    "«Сделай рекламу кофейни в Одессе.»"
)


def detect_vertical(text: str, *, preferred: str | None = None) -> tuple[str | None, float]:
    """Detect industry vertical from NL.

    Sprint 46.5: ignore sticky ``[контекст: …]`` tags so Beauty cannot poison Auto.
    ``preferred`` (from VerticalSession) always wins.
    """
    if preferred:
        return preferred, 1.0
    raw = text or ""
    # Strip memory enrichment so "vertical=beauty" in context never overrides intent
    clean = re.sub(r"\[контекст:[^\]]*\]", " ", raw, flags=re.I)
    clean = re.sub(r"vertical\s*=\s*\w+", " ", clean, flags=re.I)
    for pattern, vertical in _RULES:
        if pattern.search(clean):
            return vertical, 0.9
    return None, 0.0


def needs_clarify(text: str, *, task_implies_vertical: bool = False) -> bool:
    vert, _conf = detect_vertical(text)
    if vert:
        return False
    q = (text or "").lower()
    # Enough marketing substance → draft immediately (Sprint 46.3)
    if "реклам" in q and (
        any(x in q for x in ("одесс", "киев", "львов", "харьков", "город"))
        or any(x in q for x in ("назван", "black", "кофейн", "кафе ", "салон"))
        or len(q.split()) >= 6
    ):
        return False
    if task_implies_vertical:
        return True
    # short marketing asks without domain
    if any(x in q for x in ("реклам", "создай", "сделай", "хочу")) and len(q.split()) <= 5:
        return True
    return False
