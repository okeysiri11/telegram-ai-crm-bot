# Automotive Revenue Engine v1 — admin dashboard handlers.

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import Message

from config import OWNER_ID
from services.handler_auth import has_permission_sync as has_permission, log_audit
from keyboards import admin_module_menu
from services.pg_automotive_revenue_engine import AutomotiveRevenueEngineV1

logger = logging.getLogger(__name__)

automotive_revenue_router = Router()


def _can_access_admin(user_id: int) -> bool:
    return has_permission(user_id, "users_access") or user_id == OWNER_ID


@automotive_revenue_router.message(F.text == "💰 Revenue Dashboard")
async def revenue_dashboard(message: Message) -> None:
    user_id = message.from_user.id
    if not _can_access_admin(user_id):
        await message.answer("Нет доступа.")
        return
    try:
        dashboard = await AutomotiveRevenueEngineV1.get_admin_dashboard()
        text = AutomotiveRevenueEngineV1.format_admin_dashboard(dashboard)
    except Exception as exc:
        logger.warning("Revenue dashboard failed user=%s: %s", user_id, exc)
        await message.answer(
            f"💰 Revenue Dashboard\n\nUnable to load dashboard: {exc}",
            reply_markup=admin_module_menu(),
        )
        return
    await message.answer(text, reply_markup=admin_module_menu())
    log_audit(user_id, "open", "admin", "revenue_dashboard")
