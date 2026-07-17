# Universal Lead Engine v1 — admin dashboard and manager assignment.

from __future__ import annotations

import logging
import uuid

from aiogram import F, Router
from aiogram.types import Message

from config import OWNER_ID
from services.handler_auth import has_permission_sync as has_permission, log_audit
from keyboards import admin_module_menu
from services.pg_lead_engine import LeadEngineV1

logger = logging.getLogger(__name__)

lead_engine_router = Router()

lead_assign_flow: dict[int, dict] = {}


def _can_access_admin(user_id: int) -> bool:
    return has_permission(user_id, "users_access") or user_id == OWNER_ID


@lead_engine_router.message(F.text == "📈 Lead Dashboard")
async def lead_dashboard(message: Message) -> None:
    user_id = message.from_user.id
    if not _can_access_admin(user_id):
        await message.answer("Нет доступа.")
        return
    try:
        dashboard = await LeadEngineV1.get_admin_dashboard()
        text = LeadEngineV1.format_admin_dashboard(dashboard)
    except Exception as exc:
        logger.exception("Lead dashboard failed user=%s", user_id)
        await message.answer(
            f"📈 Lead Dashboard\n\nОшибка загрузки: {exc}",
            reply_markup=admin_module_menu(),
        )
        return
    await message.answer(text, reply_markup=admin_module_menu())
    log_audit(user_id, "open", "admin", "lead_dashboard")


@lead_engine_router.message(F.text == "📋 Lead List")
async def lead_list(message: Message) -> None:
    user_id = message.from_user.id
    if not _can_access_admin(user_id):
        await message.answer("Нет доступа.")
        return
    dashboard = await LeadEngineV1.get_admin_dashboard()
    text = LeadEngineV1.format_lead_list(dashboard.get("recent") or [])
    await message.answer(
        text + "\n\nДля назначения менеджера: /assign_lead <lead_uuid> <manager_uuid>\n"
        "Конвертация в deal: /convert_lead <lead_uuid> [amount] [currency]",
        reply_markup=admin_module_menu(),
    )
    log_audit(user_id, "open", "admin", "lead_list")


@lead_engine_router.message(F.text.startswith("/assign_lead"))
async def assign_lead_command(message: Message) -> None:
    user_id = message.from_user.id
    if not _can_access_admin(user_id) and user_id != OWNER_ID:
        await message.answer("Нет доступа.")
        return
    parts = (message.text or "").split()
    if len(parts) < 3:
        await message.answer(
            "Формат: /assign_lead <lead_uuid> <manager_uuid>\n"
            "Для снятия менеджера: /assign_lead <lead_uuid> none"
        )
        return
    try:
        lead_id = uuid.UUID(parts[1])
        manager_id = None if parts[2].lower() == "none" else uuid.UUID(parts[2])
    except ValueError:
        await message.answer("Некорректный UUID.")
        return
    result = await LeadEngineV1.assign_manager(lead_id, manager_id)
    if result is None:
        await message.answer("Lead не найден.")
        return
    await message.answer(
        f"✅ Lead {result['id'][:8]}…\n"
        f"Manager: {result.get('assigned_manager_id') or '—'}"
    )
    log_audit(user_id, "assign", "lead_engine", str(lead_id))
