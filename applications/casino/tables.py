"""Premium floor catalog — illustrated lobby areas and live tables.

No new persistence. Coming-soon areas are presentation only.
"""

from __future__ import annotations

from typing import Any

DEFAULT_LIVE_ROOM_ID = "roulette-royale"

FLOOR_AREAS: tuple[dict[str, Any], ...] = (
    {
        "id": "reception",
        "label": "RECEPTION",
        "label_ru": "РЕЦЕПЦИЯ",
        "status": "soon",
        "status_label": "Скоро",
        "coming_soon": True,
    },
    {
        "id": "bar",
        "label": "BAR",
        "label_ru": "БАР",
        "status": "soon",
        "status_label": "Скоро",
        "coming_soon": True,
    },
    {
        "id": "roulette",
        "label": "ROULETTE",
        "label_ru": "РУЛЕТКА",
        "status": "open",
        "status_label": "Идет прием ставок",
        "coming_soon": False,
        "game": "roulette",
        "room_id": DEFAULT_LIVE_ROOM_ID,
        "route": "/casino/venues/odessa-prime/roulette",
    },
    {
        "id": "blackjack",
        "label": "BLACKJACK",
        "label_ru": "БЛЭКДЖЕК",
        "status": "soon",
        "status_label": "Скоро",
        "coming_soon": True,
    },
    {
        "id": "poker",
        "label": "POKER",
        "label_ru": "ПОКЕР",
        "status": "soon",
        "status_label": "Скоро",
        "coming_soon": True,
    },
    {
        "id": "slots",
        "label": "SLOTS",
        "label_ru": "СЛОТЫ",
        "status": "soon",
        "status_label": "Скоро",
        "coming_soon": True,
    },
    {
        "id": "vip",
        "label": "VIP",
        "label_ru": "VIP",
        "status": "soon",
        "status_label": "Скоро",
        "coming_soon": True,
    },
)

TABLES: tuple[dict[str, Any], ...] = (
    {
        "room_id": DEFAULT_LIVE_ROOM_ID,
        "table": "Roulette Royale",
        "game": "roulette",
        "seats": 6,
        "coming_soon": False,
        "status_open": "Идет прием ставок",
        "status_idle": "Ожидание игроков",
        "route": "/casino/venues/odessa-prime/roulette",
    },
    {
        "room_id": "blackjack-salon",
        "table": "Blackjack Salon",
        "game": "blackjack",
        "seats": 5,
        "coming_soon": True,
        "status_open": "Скоро",
        "status_idle": "Скоро",
        "route": None,
    },
    {
        "room_id": "poker-room",
        "table": "Poker Room",
        "game": "poker",
        "seats": 8,
        "coming_soon": True,
        "status_open": "Скоро",
        "status_idle": "Скоро",
        "route": None,
    },
)


def get_table(room_id: str) -> dict[str, Any] | None:
    rid = (room_id or "").strip().lower()
    for table in TABLES:
        if table["room_id"] == rid:
            return dict(table)
    return None


def live_room_id(room_id: str | None) -> str:
    rid = (room_id or "").strip().lower()
    if not rid or rid in {"default", "main", "venue"}:
        return DEFAULT_LIVE_ROOM_ID
    return rid
