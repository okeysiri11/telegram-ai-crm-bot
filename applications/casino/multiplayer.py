"""Redis-backed room presence — multiplayer foundation (not a full game socket)."""

from __future__ import annotations

import logging
from typing import Any

from applications.casino.identity import display_identity
from applications.casino.tables import TABLES, get_table, live_room_id
from applications.casino.tenant import current_casino_tenant

logger = logging.getLogger(__name__)

_MEMORY_ROOMS: dict[tuple[str, str, str], set[str]] = {}


def _mem_key(venue_id: str, room_id: str) -> tuple[str, str, str]:
    return (current_casino_tenant(), venue_id, live_room_id(room_id))


def _redis_key(venue_id: str, room_id: str) -> str:
    return f"casino:room:{current_casino_tenant()}:{venue_id}:{live_room_id(room_id)}:members"


def _seat_view(members: list[str], seats: int) -> list[dict[str, Any]]:
    taken = list(members)
    rows: list[dict[str, Any]] = []
    for index in range(seats):
        if index < len(taken):
            rows.append(
                {
                    "seat": index + 1,
                    "occupied": True,
                    "display_name": display_identity(taken[index]),
                }
            )
        else:
            rows.append({"seat": index + 1, "occupied": False, "display_name": None})
    return rows


def _public_presence(
    *,
    venue_id: str,
    room_id: str,
    members: list[str],
    backend: str,
    reconnected: bool = False,
) -> dict[str, Any]:
    table = get_table(live_room_id(room_id)) or {
        "room_id": live_room_id(room_id),
        "table": live_room_id(room_id),
        "game": "roulette",
        "seats": 6,
        "coming_soon": False,
        "status_open": "Идет прием ставок",
        "status_idle": "Ожидание игроков",
        "route": None,
    }
    seats = int(table.get("seats") or 6)
    count = len(members)
    coming_soon = bool(table.get("coming_soon"))
    if coming_soon:
        status_label = "Скоро"
        status = "soon"
    elif count:
        status_label = str(table.get("status_open") or "Идет прием ставок")
        status = "betting"
    else:
        status_label = str(table.get("status_idle") or "Ожидание игроков")
        status = "idle"
    return {
        "venue_id": venue_id,
        "room_id": table["room_id"],
        "table": table["table"],
        "game": table.get("game"),
        "backend": backend,
        "count": count,
        "seats_total": seats,
        "seats_taken": min(count, seats),
        "online_count": count,
        "status": status,
        "status_label": status_label,
        "coming_soon": coming_soon,
        "reconnected": reconnected,
        "play_money_only": True,
        "players": [row for row in _seat_view(members, seats) if row["occupied"]],
        "seats": _seat_view(members, seats),
        "route": table.get("route"),
        "min_bet": int(table.get("min_bet") or 10),
        "max_bet": int(table.get("max_bet") or 5000),
    }


async def _redis():
    try:
        from config import REDIS_URL
        from redis.asyncio import Redis

        if not REDIS_URL:
            return None
        return Redis.from_url(REDIS_URL, decode_responses=True)
    except Exception:
        logger.debug("casino redis unavailable")
        return None


async def _members(venue_id: str, room_id: str) -> tuple[list[str], str]:
    rid = live_room_id(room_id)
    client = await _redis()
    if client is not None:
        try:
            members = sorted(await client.smembers(_redis_key(venue_id, rid)))
            await client.aclose()
            return members, "redis"
        except Exception:
            logger.debug("casino redis presence failed; using memory", exc_info=True)
            try:
                await client.aclose()
            except Exception:
                pass
    members = sorted(_MEMORY_ROOMS.get(_mem_key(venue_id, rid), set()))
    return members, "memory"


async def join_room(venue_id: str, player_id: str, room_id: str | None = None) -> dict[str, Any]:
    rid = live_room_id(room_id)
    table = get_table(rid)
    if table and table.get("coming_soon"):
        from applications.casino.exceptions import ValidationError

        raise ValidationError("table coming soon")
    client = await _redis()
    if client is not None:
        try:
            key = _redis_key(venue_id, rid)
            already = bool(await client.sismember(key, player_id))
            await client.sadd(key, player_id)
            await client.expire(key, 3600)
            members = sorted(await client.smembers(key))
            await client.aclose()
            return _public_presence(
                venue_id=venue_id,
                room_id=rid,
                members=members,
                backend="redis",
                reconnected=already,
            )
        except Exception:
            logger.debug("casino redis join failed; using memory", exc_info=True)
            try:
                await client.aclose()
            except Exception:
                pass
    room = _MEMORY_ROOMS.setdefault(_mem_key(venue_id, rid), set())
    already = player_id in room
    room.add(player_id)
    members = sorted(room)
    return _public_presence(
        venue_id=venue_id,
        room_id=rid,
        members=members,
        backend="memory",
        reconnected=already,
    )


async def leave_room(venue_id: str, player_id: str, room_id: str | None = None) -> dict[str, Any]:
    rid = live_room_id(room_id)
    client = await _redis()
    if client is not None:
        try:
            key = _redis_key(venue_id, rid)
            await client.srem(key, player_id)
            members = sorted(await client.smembers(key))
            await client.aclose()
            return _public_presence(
                venue_id=venue_id,
                room_id=rid,
                members=members,
                backend="redis",
            )
        except Exception:
            try:
                await client.aclose()
            except Exception:
                pass
    room = _MEMORY_ROOMS.setdefault(_mem_key(venue_id, rid), set())
    room.discard(player_id)
    members = sorted(room)
    return _public_presence(
        venue_id=venue_id,
        room_id=rid,
        members=members,
        backend="memory",
    )


async def room_presence(venue_id: str, room_id: str | None = None) -> dict[str, Any]:
    rid = live_room_id(room_id)
    members, backend = await _members(venue_id, rid)
    return _public_presence(venue_id=venue_id, room_id=rid, members=members, backend=backend)


async def rooms_for_venue(venue_id: str) -> dict[str, Any]:
    tables: list[dict[str, Any]] = []
    online = 0
    backend = "memory"
    for spec in TABLES:
        presence = await room_presence(venue_id, spec["room_id"])
        backend = presence.get("backend") or backend
        tables.append(presence)
        if not spec.get("coming_soon"):
            online += int(presence.get("count") or 0)
    return {
        "venue_id": venue_id,
        "backend": backend,
        "tables": tables,
        "count": online,
        "online_count": online,
        "play_money_only": True,
    }


def reset_rooms() -> None:
    _MEMORY_ROOMS.clear()
