# Application bootstrap — Bot instance, FSM storage, Dispatcher wiring.

from __future__ import annotations

import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.base import BaseStorage
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, REDIS_REQUIRED, REDIS_URL
from auto_vertical_handlers import auto_vertical_router as auto_router
from handlers import router
from middleware.tenant_middleware import TenantMiddleware
from middleware.entry_point_middleware import EntryPointMiddleware
from routers.auto_client_router import router as auto_client_entry_router
from routers.auto_dealer_router import router as auto_dealer_entry_router
from routers.manager_debug_router import router as manager_debug_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)


async def create_fsm_storage() -> tuple[BaseStorage, BaseStorage | None]:
    """Return (storage, closable_redis_storage). closable is set when Redis is used."""
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


def build_dispatcher(storage: BaseStorage) -> Dispatcher:
    dp = Dispatcher(storage=storage)
    dp.update.middleware(EntryPointMiddleware())
    dp.update.middleware(TenantMiddleware())
    dp.include_router(auto_client_entry_router)
    dp.include_router(auto_dealer_entry_router)
    dp.include_router(manager_debug_router)
    dp.include_router(auto_router)
    dp.include_router(router)
    return dp
