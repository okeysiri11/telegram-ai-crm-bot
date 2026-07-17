# Application bootstrap — Bot instance, FSM storage, Dispatcher wiring.

from __future__ import annotations

import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.base import BaseStorage

from config import BOT_TOKEN
from fsm_storage import close_fsm_storage, create_fsm_storage
from startup import register_routers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)


def build_dispatcher(storage: BaseStorage) -> Dispatcher:
    dp = Dispatcher(storage=storage)
    from middleware.tenant_middleware import TenantMiddleware
    from middleware.entry_point_middleware import EntryPointMiddleware

    dp.update.middleware(EntryPointMiddleware())
    dp.update.middleware(TenantMiddleware())
    from middleware.error_tracking_middleware import ErrorTrackingMiddleware

    dp.update.middleware(ErrorTrackingMiddleware())
    register_routers(dp)
    return dp


__all__ = ["bot", "build_dispatcher", "close_fsm_storage", "create_fsm_storage"]
