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
        if REDIS_REQUIRED:
            logger.error(
                "REDIS_URL is not set and REDIS_REQUIRED=true — aborting startup"
            )
            sys.exit(1)
        logger.warning("Redis unavailable, falling back to MemoryStorage")
        logger.info("Storage backend: MemoryStorage")
        return MemoryStorage(), None

    try:
        from aiogram.fsm.storage.redis import RedisStorage

        storage = RedisStorage.from_url(REDIS_URL)
        await storage.redis.ping()
        logger.info("Storage backend: RedisStorage")
        return storage, storage
    except Exception as exc:
        if REDIS_REQUIRED:
            logger.error(
                "Redis is required (REDIS_REQUIRED=true) but unavailable at %s: %s",
                REDIS_URL,
                exc,
            )
            sys.exit(1)
        logger.warning("Redis unavailable, falling back to MemoryStorage")
        logger.info("Storage backend: MemoryStorage")
        return MemoryStorage(), None


async def close_fsm_storage(closable: BaseStorage | None) -> None:
    if closable is not None:
        await closable.close()
