"""Redis-backed room presence — multiplayer foundation (not a full game socket)."""

from __future__ import annotations

import logging
from typing import Any

from applications.casino.tenant import current_casino_tenant

logger = logging.getLogger(__name__)

_MEMORY_ROOMS: dict[tuple[str, str], set[str]] = {}


def _mem_key(venue_id: str) -> tuple[str, str]:
    return (current_casino_tenant(), venue_id)


def _redis_key(venue_id: str) -> str:
    return f"casino:room:{current_casino_tenant()}:{venue_id}:members"


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


async def join_room(venue_id: str, player_id: str) -> dict[str, Any]:
    client = await _redis()
    if client is not None:
        try:
            await client.sadd(_redis_key(venue_id), player_id)
            await client.expire(_redis_key(venue_id), 3600)
            members = sorted(await client.smembers(_redis_key(venue_id)))
            await client.aclose()
            return {"venue_id": venue_id, "backend": "redis", "members": members, "count": len(members)}
        except Exception:
            logger.debug("casino redis join failed; using memory", exc_info=True)
            try:
                await client.aclose()
            except Exception:
                pass
    room = _MEMORY_ROOMS.setdefault(_mem_key(venue_id), set())
    room.add(player_id)
    members = sorted(room)
    return {"venue_id": venue_id, "backend": "memory", "members": members, "count": len(members)}


async def leave_room(venue_id: str, player_id: str) -> dict[str, Any]:
    client = await _redis()
    if client is not None:
        try:
            await client.srem(_redis_key(venue_id), player_id)
            members = sorted(await client.smembers(_redis_key(venue_id)))
            await client.aclose()
            return {"venue_id": venue_id, "backend": "redis", "members": members, "count": len(members)}
        except Exception:
            try:
                await client.aclose()
            except Exception:
                pass
    room = _MEMORY_ROOMS.setdefault(_mem_key(venue_id), set())
    room.discard(player_id)
    members = sorted(room)
    return {"venue_id": venue_id, "backend": "memory", "members": members, "count": len(members)}


async def room_presence(venue_id: str) -> dict[str, Any]:
    client = await _redis()
    if client is not None:
        try:
            members = sorted(await client.smembers(_redis_key(venue_id)))
            await client.aclose()
            return {"venue_id": venue_id, "backend": "redis", "members": members, "count": len(members)}
        except Exception:
            try:
                await client.aclose()
            except Exception:
                pass
    members = sorted(_MEMORY_ROOMS.get(_mem_key(venue_id), set()))
    return {"venue_id": venue_id, "backend": "memory", "members": members, "count": len(members)}


def reset_rooms() -> None:
    _MEMORY_ROOMS.clear()
