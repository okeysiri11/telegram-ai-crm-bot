# Universal Revenue Engine v1 — owner dashboard.

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import Message

from config import OWNER_ID
from database import has_permission, log_audit
from keyboards import admin_module_menu
from services.pg_revenue_engine_v1 import RevenueEngineV1

logger = logging.getLogger(__name__)

revenue_engine_router = Router()


def _can_access_admin(user_id: int) -> bool:
    return has_permission(user_id, "users_access") or user_id == OWNER_ID


@revenue_engine_router.message(F.text == "💵 Revenue Engine")
async def revenue_engine_dashboard(message: Message) -> None:
    user_id = message.from_user.id
    if not _can_access_admin(user_id):
        await message.answer("Нет доступа.")
        return
    try:
        dashboard = await RevenueEngineV1.get_owner_dashboard()
        text = RevenueEngineV1.format_owner_dashboard(dashboard)
    except Exception as exc:
        logger.exception("Revenue dashboard failed user=%s", user_id)
        await message.answer(
            f"💵 Revenue Engine\n\nОшибка загрузки: {exc}",
            reply_markup=admin_module_menu(),
        )
        return
    await message.answer(text, reply_markup=admin_module_menu())
    log_audit(user_id, "open", "admin", "revenue_dashboard")
