# Application bootstrap — Bot instance, FSM storage, Dispatcher wiring.

from __future__ import annotations

import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.base import BaseStorage

from config import BOT_TOKEN
from fsm_storage import close_fsm_storage, create_fsm_storage
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


__all__ = ["bot", "build_dispatcher", "close_fsm_storage", "create_fsm_storage"]
