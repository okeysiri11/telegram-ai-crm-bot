# Partner Cabinet v1 — Telegram handlers.

from __future__ import annotations

import logging
import uuid

from aiogram import F, Router
from aiogram.types import Message

from config import OWNER_ID
from database import has_permission, log_audit
from keyboards import owner_main_menu, partner_cabinet_menu
from services.pg_partner_cabinet_v1 import PartnerCabinetV1, PartnerCabinetV1Error

logger = logging.getLogger(__name__)

partner_cabinet_router = Router()

partner_cabinet_active: set[int] = set()


def _is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


def _can_access_admin(user_id: int) -> bool:
    return has_permission(user_id, "users_access") or user_id == OWNER_ID


@partner_cabinet_router.message(F.text == "🤝 Partner Cabinet")
async def open_partner_cabinet(message: Message) -> None:
    user_id = message.from_user.id
    try:
        if _is_owner(user_id):
            overview = await PartnerCabinetV1.get_owner_overview()
            text = PartnerCabinetV1.format_owner_overview(overview)
            partner_cabinet_active.add(user_id)
            await message.answer(text, reply_markup=partner_cabinet_menu(owner=True))
            log_audit(user_id, "open", "partner_cabinet", "owner")
            return

        data = await PartnerCabinetV1.get_partner_cabinet(user_id)
        text = PartnerCabinetV1.format_partner_cabinet(data)
        partner_cabinet_active.add(user_id)
        await message.answer(text, reply_markup=partner_cabinet_menu(owner=False))
        log_audit(user_id, "open", "partner_cabinet")
    except PartnerCabinetV1Error as exc:
        await message.answer(f"🤝 Partner Cabinet\n\n{exc}")
    except Exception as exc:
        logger.exception("Partner cabinet failed user=%s", user_id)
        await message.answer(f"🤝 Partner Cabinet\n\nОшибка: {exc}")


@partner_cabinet_router.message(
    lambda m: m.from_user.id in partner_cabinet_active
    and m.text in {"🔄 Обновить", "🤝 Partner Cabinet"}
)
async def refresh_partner_cabinet(message: Message) -> None:
    await open_partner_cabinet(message)


@partner_cabinet_router.message(
    lambda m: m.from_user.id in partner_cabinet_active and m.text == "⬅ Назад"
)
async def partner_cabinet_back(message: Message) -> None:
    user_id = message.from_user.id
    partner_cabinet_active.discard(user_id)
    await message.answer("Главное меню", reply_markup=owner_main_menu())


@partner_cabinet_router.message(F.text.startswith("/approve_payout"))
async def approve_payout_command(message: Message) -> None:
    user_id = message.from_user.id
    if not _can_access_admin(user_id):
        await message.answer("Нет доступа.")
        return
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("Формат: /approve_payout <commission_uuid>")
        return
    try:
        commission_id = uuid.UUID(parts[1])
    except ValueError:
        await message.answer("Некорректный UUID.")
        return
    try:
        result = await PartnerCabinetV1.approve_payout(
            commission_id,
            actor_telegram_id=user_id,
            mark_paid=True,
        )
    except PartnerCabinetV1Error as exc:
        await message.answer(f"❌ {exc}")
        return
    await message.answer(
        f"✅ Payout approved\n"
        f"Commission: {result['commission_id'][:8]}…\n"
        f"Amount: {result['amount']}\n"
        f"Status: {result['status']}"
    )
    log_audit(user_id, "approve", "partner_cabinet", result["commission_id"])


@partner_cabinet_router.message(F.text.startswith("/block_partner"))
async def block_partner_command(message: Message) -> None:
    user_id = message.from_user.id
    if not _can_access_admin(user_id):
        await message.answer("Нет доступа.")
        return
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("Формат: /block_partner <partner_code>")
        return
    try:
        result = await PartnerCabinetV1.block_partner(
            parts[1],
            actor_telegram_id=user_id,
            blocked=True,
        )
    except PartnerCabinetV1Error as exc:
        await message.answer(f"❌ {exc}")
        return
    await message.answer(f"🚫 Partner {result['partner_code']} blocked.")
    log_audit(user_id, "block", "partner_cabinet", result["partner_code"])


@partner_cabinet_router.message(F.text.startswith("/unblock_partner"))
async def unblock_partner_command(message: Message) -> None:
    user_id = message.from_user.id
    if not _can_access_admin(user_id):
        await message.answer("Нет доступа.")
        return
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("Формат: /unblock_partner <partner_code>")
        return
    try:
        result = await PartnerCabinetV1.block_partner(
            parts[1],
            actor_telegram_id=user_id,
            blocked=False,
        )
    except PartnerCabinetV1Error as exc:
        await message.answer(f"❌ {exc}")
        return
    await message.answer(f"✅ Partner {result['partner_code']} unblocked.")
    log_audit(user_id, "unblock", "partner_cabinet", result["partner_code"])


@partner_cabinet_router.message(F.text.startswith("/set_partner_rate"))
async def set_partner_rate_command(message: Message) -> None:
    user_id = message.from_user.id
    if not _can_access_admin(user_id):
        await message.answer("Нет доступа.")
        return
    parts = (message.text or "").split()
    if len(parts) < 3:
        await message.answer("Формат: /set_partner_rate <partner_code> <rate>\nПример: /set_partner_rate sgtas 0.28")
        return
    try:
        result = await PartnerCabinetV1.set_commission_rate(parts[1], parts[2])
    except PartnerCabinetV1Error as exc:
        await message.answer(f"❌ {exc}")
        return
    await message.answer(
        f"✅ Rate updated: {result['partner_code']} → {float(result['commission_rate']) * 100:.1f}%"
    )
    log_audit(user_id, "set_rate", "partner_cabinet", result["partner_code"])


@partner_cabinet_router.message(F.text.startswith("/link_partner"))
async def link_partner_command(message: Message) -> None:
    user_id = message.from_user.id
    if not _can_access_admin(user_id):
        await message.answer("Нет доступа.")
        return
    parts = (message.text or "").split()
    if len(parts) < 3:
        await message.answer("Формат: /link_partner <partner_code> <telegram_id>")
        return
    try:
        tg_id = int(parts[2])
    except ValueError:
        await message.answer("Некорректный telegram_id.")
        return
    try:
        result = await PartnerCabinetV1.link_partner_telegram(parts[1], tg_id)
    except PartnerCabinetV1Error as exc:
        await message.answer(f"❌ {exc}")
        return
    await message.answer(
        f"✅ Linked {result['partner_code']} → telegram {result['telegram_user_id']}"
    )
    log_audit(user_id, "link", "partner_cabinet", result["partner_code"])
