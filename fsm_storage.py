# FSM storage factory — RedisStorage with MemoryStorage fallback.

from __future__ import annotations

import logging
import sys

from aiogram.fsm.storage.base import BaseStorage
from aiogram.fsm.storage.memory import MemoryStorage

from config import REDIS_REQUIRED, REDIS_URL

logger = logging.getLogger(__name__)


async def create_fsm_storage() -> tuple[BaseStorage, BaseStorage | None]:
    """
    Build aiogram FSM storage.

    Returns (storage, closable). closable is the RedisStorage instance when Redis
    is used and must be closed on shutdown; otherwise None.
    """
    if not REDIS_URL:
        message = "REDIS_URL is not set"
        if REDIS_REQUIRED:
            logger.error("%s and REDIS_REQUIRED=True — aborting startup", message)
            sys.exit(1)
        logger.warning("%s — using MemoryStorage (FSM will not survive restarts)", message)
        return MemoryStorage(), None

    try:
        from aiogram.fsm.storage.redis import RedisStorage

        storage = RedisStorage.from_url(REDIS_URL)
        await storage.redis.ping()
        logger.info("FSM storage: Redis (%s)", REDIS_URL)
        return storage, storage
    except Exception as exc:
        if REDIS_REQUIRED:
            logger.error(
                "Redis is required (REDIS_REQUIRED=True) but unavailable at %s: %s",
                REDIS_URL,
                exc,
            )
            sys.exit(1)
        logger.warning(
            "Redis unavailable at %s (%s) — falling back to MemoryStorage",
            REDIS_URL,
            exc,
        )
        return MemoryStorage(), None


async def close_fsm_storage(closable: BaseStorage | None) -> None:
    if closable is not None:
        await closable.close()
