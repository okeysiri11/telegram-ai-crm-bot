# Universal Deal Engine v1 — admin/owner views and lead conversion.

from __future__ import annotations

import logging
import uuid
from decimal import Decimal, InvalidOperation

from aiogram import F, Router
from aiogram.types import Message

from config import OWNER_ID
from database import has_permission, log_audit
from keyboards import admin_module_menu
from services.pg_deal_engine_v1 import DealEngineV1, DealEngineV1Error

logger = logging.getLogger(__name__)

deal_engine_router = Router()


def _can_access_admin(user_id: int) -> bool:
    return has_permission(user_id, "users_access") or user_id == OWNER_ID


@deal_engine_router.message(F.text == "🤝 Deal Dashboard")
async def deal_dashboard(message: Message) -> None:
    user_id = message.from_user.id
    if not _can_access_admin(user_id):
        await message.answer("Нет доступа.")
        return
    try:
        dashboard = await DealEngineV1.get_owner_dashboard()
        text = DealEngineV1.format_owner_dashboard(dashboard)
    except Exception as exc:
        logger.exception("Deal dashboard failed user=%s", user_id)
        await message.answer(
            f"🤝 Deal Dashboard\n\nОшибка загрузки: {exc}",
            reply_markup=admin_module_menu(),
        )
        return
    await message.answer(text, reply_markup=admin_module_menu())
    log_audit(user_id, "open", "admin", "deal_dashboard")


@deal_engine_router.message(F.text == "📋 Deal List")
async def deal_list(message: Message) -> None:
    user_id = message.from_user.id
    if not _can_access_admin(user_id):
        await message.answer("Нет доступа.")
        return
    dashboard = await DealEngineV1.get_owner_dashboard()
    text = DealEngineV1.format_deal_list(dashboard.get("recent") or [])
    await message.answer(
        text
        + "\n\nКоманды:\n"
        "/convert_lead <lead_uuid> [amount] [currency]\n"
        "/deal_status <deal_uuid> <status>\n"
        "/deal_partner <deal_uuid> <partner_uuid|none>",
        reply_markup=admin_module_menu(),
    )
    log_audit(user_id, "open", "admin", "deal_list")


@deal_engine_router.message(F.text.startswith("/convert_lead"))
async def convert_lead_command(message: Message) -> None:
    user_id = message.from_user.id
    if not _can_access_admin(user_id):
        await message.answer("Нет доступа.")
        return
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer(
            "Формат: /convert_lead <lead_uuid> [amount] [currency]\n"
            "Пример: /convert_lead abc-... 15000 USD"
        )
        return
    try:
        lead_id = uuid.UUID(parts[1])
        amount = Decimal(parts[2]) if len(parts) > 2 else Decimal("0")
        currency = parts[3].upper() if len(parts) > 3 else "USD"
    except (ValueError, InvalidOperation):
        await message.answer("Некорректные параметры.")
        return

    try:
        deal = await DealEngineV1.create_from_lead(lead_id, amount=amount, currency=currency)
    except DealEngineV1Error as exc:
        await message.answer(f"❌ {exc}")
        return

    await message.answer(
        f"✅ Deal создан\n\n"
        f"ID: {deal['id'][:8]}…\n"
        f"Vertical: {deal['vertical']}\n"
        f"Title: {deal['title']}\n"
        f"Amount: {deal['amount']} {deal['currency']}\n"
        f"Status: {deal['status']}"
    )
    log_audit(user_id, "create", "deal_engine", deal["id"])


@deal_engine_router.message(F.text.startswith("/deal_status"))
async def deal_status_command(message: Message) -> None:
    user_id = message.from_user.id
    if not _can_access_admin(user_id):
        await message.answer("Нет доступа.")
        return
    parts = (message.text or "").split()
    if len(parts) < 3:
        await message.answer(
            "Формат: /deal_status <deal_uuid> <status>\n"
            "Statuses: NEW, IN_PROGRESS, PAYMENT_PENDING, PAYMENT_RECEIVED, COMPLETED, CANCELLED"
        )
        return
    try:
        deal_id = uuid.UUID(parts[1])
    except ValueError:
        await message.answer("Некорректный UUID.")
        return
    status = parts[2].upper()
    try:
        deal = await DealEngineV1.update_status(deal_id, status)
    except DealEngineV1Error as exc:
        await message.answer(f"❌ {exc}")
        return
    if deal is None:
        await message.answer("Deal не найден.")
        return
    await message.answer(f"✅ Deal {deal['id'][:8]}… → {deal['status']}")
    if deal.get("revenue_entry_id"):
        await message.answer(f"💰 Revenue entry: {deal['revenue_entry_id'][:8]}…")
    log_audit(user_id, "update", "deal_engine", f"{deal_id}:{status}")


@deal_engine_router.message(F.text.startswith("/deal_partner"))
async def deal_partner_command(message: Message) -> None:
    user_id = message.from_user.id
    if not _can_access_admin(user_id):
        await message.answer("Нет доступа.")
        return
    parts = (message.text or "").split()
    if len(parts) < 3:
        await message.answer("Формат: /deal_partner <deal_uuid> <partner_uuid|none>")
        return
    try:
        deal_id = uuid.UUID(parts[1])
        partner_id = None if parts[2].lower() == "none" else uuid.UUID(parts[2])
    except ValueError:
        await message.answer("Некорректный UUID.")
        return
    deal = await DealEngineV1.attach_partner(deal_id, partner_id)
    if deal is None:
        await message.answer("Deal не найден.")
        return
    await message.answer(
        f"✅ Partner attached\nDeal: {deal['id'][:8]}…\nPartner: {deal.get('partner_id') or '—'}"
    )
    log_audit(user_id, "attach", "deal_engine", str(deal_id))
