"""Odessa Prime floor catalog — tables and hall zones. No new persistence."""

from __future__ import annotations

from typing import Any

DEFAULT_LIVE_ROOM_ID = "roulette-royale-1"
LEGACY_LIVE_ROOM_ID = "roulette-royale"

FLOOR_AREAS: tuple[dict[str, Any], ...] = (
    {
        "id": "lobby",
        "label": "LOBBY",
        "label_ru": "ЛОББИ",
        "status": "open",
        "status_label": "Открыто",
        "coming_soon": False,
        "route": "/casino/floor",
        "zone": "lobby",
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
        "route": "/casino/rooms/roulette",
        "zone": "roulette",
    },
    {
        "id": "blackjack",
        "label": "BLACKJACK",
        "label_ru": "BLACKJACK",
        "status": "open",
        "status_label": "Идет прием ставок",
        "coming_soon": False,
        "game": "blackjack",
        "room_id": "blackjack-salon",
        "route": "/casino/rooms/blackjack",
        "zone": "blackjack",
    },
    {
        "id": "poker",
        "label": "POKER",
        "label_ru": "ПОКЕР",
        "status": "soon",
        "status_label": "Скоро",
        "coming_soon": True,
        "zone": "poker",
    },
    {
        "id": "slots",
        "label": "SLOTS",
        "label_ru": "АВТОМАТЫ",
        "status": "open",
        "status_label": "Идет прием ставок",
        "coming_soon": False,
        "game": "slots",
        "room_id": "slots-odessa-gold",
        "route": "/casino/rooms/slots",
        "zone": "slots",
    },
    {
        "id": "vip",
        "label": "VIP",
        "label_ru": "VIP ЗОНА",
        "status": "soon",
        "status_label": "Скоро",
        "coming_soon": True,
        "zone": "vip",
    },
    {
        "id": "bar",
        "label": "BAR",
        "label_ru": "БАР",
        "status": "soon",
        "status_label": "Скоро",
        "coming_soon": True,
        "zone": "bar",
    },
    {
        "id": "restaurant",
        "label": "RESTAURANT",
        "label_ru": "РЕСТОРАН",
        "status": "soon",
        "status_label": "Скоро",
        "coming_soon": True,
        "zone": "restaurant",
    },
)

TABLES: tuple[dict[str, Any], ...] = (
    {
        "room_id": DEFAULT_LIVE_ROOM_ID,
        "table": "Roulette Royale 1",
        "game": "roulette",
        "seats": 6,
        "coming_soon": False,
        "min_bet": 10,
        "max_bet": 5_000,
        "status_open": "Идет прием ставок",
        "status_idle": "Ожидание игроков",
        "route": "/casino/roulette/roulette-royale-1",
    },
    {
        "room_id": "roulette-classic",
        "table": "Roulette Classic",
        "game": "roulette",
        "seats": 6,
        "coming_soon": True,
        "min_bet": 10,
        "max_bet": 1_000,
        "status_open": "Скоро",
        "status_idle": "Скоро",
        "route": None,
    },
    {
        "room_id": "roulette-monaco",
        "table": "Roulette Monaco",
        "game": "roulette",
        "seats": 8,
        "coming_soon": True,
        "min_bet": 50,
        "max_bet": 5_000,
        "status_open": "Скоро",
        "status_idle": "Скоро",
        "route": None,
    },
    {
        "room_id": "roulette-vip",
        "table": "Roulette VIP",
        "game": "roulette",
        "seats": 4,
        "coming_soon": True,
        "min_bet": 500,
        "max_bet": 5_000,
        "status_open": "Скоро",
        "status_idle": "Скоро",
        "route": None,
    },
    {
        "room_id": "blackjack-salon",
        "table": "Blackjack Salon",
        "game": "blackjack",
        "seats": 5,
        "coming_soon": False,
        "min_bet": 25,
        "max_bet": 2_000,
        "status_open": "Идет прием ставок",
        "status_idle": "Ожидание игроков",
        "route": "/casino/rooms/blackjack",
    },
    {
        "room_id": "slots-odessa-gold",
        "table": "Odessa Gold",
        "game": "slots",
        "seats": 3,
        "coming_soon": False,
        "min_bet": 10,
        "max_bet": 5_000,
        "status_open": "Идет прием ставок",
        "status_idle": "Ожидание игроков",
        "route": "/casino/slots/odessa-gold",
    },
    {
        "room_id": "poker-room",
        "table": "Poker Room",
        "game": "poker",
        "seats": 8,
        "coming_soon": True,
        "min_bet": 50,
        "max_bet": 5_000,
        "status_open": "Скоро",
        "status_idle": "Скоро",
        "route": None,
    },
)

_ALIASES = {
    LEGACY_LIVE_ROOM_ID: DEFAULT_LIVE_ROOM_ID,
    "royale": DEFAULT_LIVE_ROOM_ID,
    "odessa-gold": "slots-odessa-gold",
    "blackjack": "blackjack-salon",
}


def live_room_id(room_id: str | None) -> str:
    rid = (room_id or "").strip().lower()
    if not rid or rid in {"default", "main", "venue"}:
        return DEFAULT_LIVE_ROOM_ID
    return _ALIASES.get(rid, rid)


def get_table(room_id: str) -> dict[str, Any] | None:
    rid = live_room_id(room_id)
    for table in TABLES:
        if table["room_id"] == rid:
            return dict(table)
    return None


def roulette_tables() -> list[dict[str, Any]]:
    return [dict(t) for t in TABLES if t.get("game") == "roulette"]


def blackjack_tables() -> list[dict[str, Any]]:
    return [dict(t) for t in TABLES if t.get("game") == "blackjack"]


def slot_machines() -> list[dict[str, Any]]:
    return [dict(t) for t in TABLES if t.get("game") == "slots"]
