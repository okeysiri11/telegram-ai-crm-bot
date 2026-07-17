# Owner Dashboard v1 — unified owner analytics handlers.

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import Message

from config import OWNER_ID
from services.handler_auth import log_audit
from keyboards import owner_main_menu, owner_dashboard_menu
from services.pg_owner_dashboard_engine import OwnerDashboardEngineV1

logger = logging.getLogger(__name__)

owner_dashboard_router = Router()

owner_dashboard_active: set[int] = set()

_ANALYTICS_HANDLERS = {
    "📈 Marketing Analytics": OwnerDashboardEngineV1.format_marketing_analytics,
    "💰 Revenue Analytics": OwnerDashboardEngineV1.format_revenue_analytics,
    "👥 Manager Analytics": OwnerDashboardEngineV1.format_manager_analytics,
    "🤝 Partner Analytics": OwnerDashboardEngineV1.format_partner_analytics,
    "📋 Pipeline Analytics": OwnerDashboardEngineV1.format_pipeline_analytics,
    "⏱ SLA Analytics": OwnerDashboardEngineV1.format_sla_analytics,
    "🛡 Anti Loss Analytics": OwnerDashboardEngineV1.format_anti_loss_analytics,
    "💳 Payment Analytics": OwnerDashboardEngineV1.format_payment_analytics,
    "🏦 Settlement Analytics": OwnerDashboardEngineV1.format_settlement_analytics,
}


def _is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


@owner_dashboard_router.message(F.text == "📊 Owner Dashboard")
async def open_owner_dashboard(message: Message) -> None:
    user_id = message.from_user.id
    if not _is_owner(user_id):
        await message.answer("Нет доступа.", reply_markup=owner_main_menu())
        return
    owner_dashboard_active.add(user_id)
    log_audit(user_id, "open", "owner_dashboard")
    try:
        data = await OwnerDashboardEngineV1.get_dashboard()
        text = OwnerDashboardEngineV1.format_main_dashboard(data)
    except Exception as exc:
        logger.exception("Owner dashboard failed user=%s", user_id)
        await message.answer(f"📊 Owner Dashboard\n\nОшибка: {exc}")
        return
    await message.answer(text, reply_markup=owner_dashboard_menu())


@owner_dashboard_router.message(
    lambda m: m.from_user.id in owner_dashboard_active
    and m.text in _ANALYTICS_HANDLERS.keys() | {"⬅ Назад"}
)
async def owner_dashboard_analytics(message: Message) -> None:
    user_id = message.from_user.id
    if not _is_owner(user_id):
        return

    if message.text == "⬅ Назад":
        owner_dashboard_active.discard(user_id)
        await message.answer("Главное меню", reply_markup=owner_main_menu())
        return

    formatter = _ANALYTICS_HANDLERS.get(message.text or "")
    if formatter is None:
        return

    try:
        data = await OwnerDashboardEngineV1.get_dashboard()
        text = formatter(data)
    except Exception as exc:
        logger.exception("Owner analytics failed user=%s section=%s", user_id, message.text)
        await message.answer(f"{message.text}\n\nОшибка: {exc}")
        return

    await message.answer(text, reply_markup=owner_dashboard_menu())
    log_audit(user_id, "open", "owner_dashboard", message.text)
