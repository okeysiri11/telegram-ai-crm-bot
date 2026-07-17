# FSM storage factory — Redis required in production (no MemoryStorage fallback).

from __future__ import annotations

import logging
import sys

from aiogram.fsm.storage.base import BaseStorage

from config import IS_PRODUCTION, REDIS_REQUIRED, REDIS_URL

logger = logging.getLogger(__name__)


async def create_fsm_storage() -> tuple[BaseStorage, BaseStorage | None]:
    """
    Build aiogram FSM storage.

    Production / POSTGRES_ONLY: Redis is mandatory — bot exits if unavailable.
    Development: MemoryStorage fallback only when REDIS_REQUIRED=false.

    Returns (storage, closable). closable must be closed on shutdown when Redis is used.
    """
    if not REDIS_URL:
        if REDIS_REQUIRED:
            logger.error(
                "REDIS_URL is not set and REDIS_REQUIRED=true (production=%s) — aborting",
                IS_PRODUCTION,
            )
            sys.exit(1)
        from aiogram.fsm.storage.memory import MemoryStorage

        logger.warning(
            "Redis unavailable — using MemoryStorage (dev only). "
            "Set REDIS_URL for persistent FSM."
        )
        return MemoryStorage(), None

    try:
        from aiogram.fsm.storage.redis import RedisStorage

        storage = RedisStorage.from_url(REDIS_URL)
        await storage.redis.ping()
        logger.info("FSM storage: RedisStorage (%s)", REDIS_URL.split("@")[-1])
        return storage, storage
    except Exception as exc:
        if REDIS_REQUIRED:
            logger.error(
                "Redis required but unavailable at %s: %s",
                REDIS_URL,
                exc,
            )
            sys.exit(1)
        from aiogram.fsm.storage.memory import MemoryStorage

        logger.warning("Redis ping failed, falling back to MemoryStorage: %s", exc)
        return MemoryStorage(), None


async def close_fsm_storage(closable: BaseStorage | None) -> None:
    if closable is not None:
        await closable.close()
