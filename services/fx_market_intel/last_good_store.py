"""Persistent last-good FX candles. Redis when REDIS_URL is set; always keep process memory."""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)

PERSISTENT_BACKEND = "redis" if (os.environ.get("REDIS_URL") or "").strip() else "memory"

_memory: dict[str, dict[str, Any]] = {}
_TTL_SEC = 7 * 24 * 3600


def reset_last_good_store() -> None:
    _memory.clear()


def persistent_backend_name() -> str:
    return "redis" if (os.environ.get("REDIS_URL") or "").strip() else "memory"


def _key(symbol: str, resolution: str) -> str:
    return f"fx:last_good:{symbol}:{resolution}"


def compact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    bars = []
    for b in payload.get("bars") or []:
        bars.append(
            {
                "time": b.get("time"),
                "o": b.get("o", b.get("open")),
                "h": b.get("h", b.get("high")),
                "l": b.get("l", b.get("low")),
                "c": b.get("c", b.get("close")),
                "t": b.get("t"),
                "source": b.get("source") or payload.get("provider") or "yahoo",
                "source_resolution": b.get("source_resolution") or payload.get("source_resolution"),
            }
        )
    return {
        "symbol": payload.get("symbol"),
        "timeframe": payload.get("timeframe"),
        "requested_timeframe": payload.get("requested_timeframe") or payload.get("timeframe"),
        "provider": payload.get("provider") or "yahoo",
        "source": payload.get("source"),
        "source_resolution": payload.get("source_resolution"),
        "base_resolution": payload.get("base_resolution") or payload.get("source_resolution"),
        "displayed_timeframe": payload.get("displayed_timeframe") or payload.get("timeframe"),
        "aggregated": payload.get("aggregated", False),
        "chart_engine": payload.get("chart_engine") or "lightweight_charts",
        "supported_timeframes": payload.get("supported_timeframes"),
        "provider_symbol": payload.get("provider_symbol"),
        "bars": bars,
        "status": payload.get("status") or "connected",
        "source_status": payload.get("source_status") or "cached",
        "saved_at": payload.get("saved_at") or payload.get("fetched_at"),
        "fetched_at": payload.get("fetched_at"),
        "last_close": payload.get("last_close"),
        "last_bar_at": payload.get("last_bar_at"),
        "quality": payload.get("quality"),
    }


def memory_get(symbol: str, resolution: str) -> dict[str, Any] | None:
    row = _memory.get(_key(symbol, resolution))
    if not row:
        return None
    return dict(row["payload"])


def memory_put(symbol: str, resolution: str, payload: dict[str, Any]) -> None:
    if not payload.get("bars"):
        return
    _memory[_key(symbol, resolution)] = {"payload": compact_payload(payload), "stored_at": time.time()}


async def save_last_good(symbol: str, resolution: str, payload: dict[str, Any]) -> None:
    if not payload.get("bars"):
        return
    stored = compact_payload(payload)
    stored["saved_at"] = stored.get("saved_at") or stored.get("fetched_at")
    _memory[_key(symbol, resolution)] = {"payload": stored, "stored_at": time.time()}
    url = (os.environ.get("REDIS_URL") or "").strip()
    if not url:
        return
    try:
        from redis.asyncio import Redis
        from redis.asyncio.retry import Retry
        from redis.backoff import NoBackoff

        client = Redis.from_url(
            url,
            decode_responses=True,
            socket_timeout=0.6,
            socket_connect_timeout=0.6,
            retry=Retry(NoBackoff(), 0),
            retry_on_timeout=False,
        )
        await client.set(_key(symbol, resolution), json.dumps(stored, default=str), ex=_TTL_SEC)
        await client.aclose()
    except Exception:
        logger.warning("fx last-good redis save failed", exc_info=True)


async def load_last_good(symbol: str, resolution: str) -> dict[str, Any] | None:
    hit = memory_get(symbol, resolution)
    if hit and hit.get("bars"):
        return hit
    url = (os.environ.get("REDIS_URL") or "").strip()
    if not url:
        return None
    try:
        from redis.asyncio import Redis
        from redis.asyncio.retry import Retry
        from redis.backoff import NoBackoff

        client = Redis.from_url(
            url,
            decode_responses=True,
            socket_timeout=0.6,
            socket_connect_timeout=0.6,
            retry=Retry(NoBackoff(), 0),
            retry_on_timeout=False,
        )
        raw = await client.get(_key(symbol, resolution))
        await client.aclose()
        if not raw:
            return None
        payload = json.loads(raw)
        if payload.get("bars"):
            _memory[_key(symbol, resolution)] = {"payload": payload, "stored_at": time.time()}
            return payload
    except Exception:
        logger.warning("fx last-good redis load failed", exc_info=True)
    return None
