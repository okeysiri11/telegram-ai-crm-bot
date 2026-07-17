# Anti Loss Layer v1 — merge commands.

from __future__ import annotations

import logging
import uuid

from aiogram import F, Router
from aiogram.types import Message

from config import OWNER_ID
from services.handler_auth import has_permission_sync as has_permission, log_audit
from services.pg_anti_loss_layer_v1 import AntiLossLayerV1, AntiLossLayerV1Error

logger = logging.getLogger(__name__)

anti_loss_layer_router = Router()


def _can_access(user_id: int) -> bool:
    return has_permission(user_id, "users_access") or user_id == OWNER_ID


@anti_loss_layer_router.message(F.text.startswith("/merge_leads"))
async def merge_leads_command(message: Message) -> None:
    user_id = message.from_user.id
    if not _can_access(user_id):
        await message.answer("Нет доступа.")
        return
    parts = (message.text or "").split()
    if len(parts) < 3:
        await message.answer(
            "Формат: /merge_leads <primary_uuid> <duplicate_uuid>\n"
            "Primary lead сохраняется, duplicate помечается как merged."
        )
        return
    try:
        primary_id = uuid.UUID(parts[1])
        duplicate_id = uuid.UUID(parts[2])
    except ValueError:
        await message.answer("Некорректный UUID.")
        return
    try:
        result = await AntiLossLayerV1.merge_leads(
            primary_id,
            duplicate_id,
            actor_telegram_id=user_id,
        )
    except AntiLossLayerV1Error as exc:
        await message.answer(f"❌ {exc}")
        return
    except Exception as exc:
        logger.exception("merge_leads failed")
        await message.answer(f"Ошибка: {exc}")
        return
    await message.answer(
        f"✅ Leads merged\n"
        f"Primary: {result['primary_id'][:8]}…\n"
        f"Duplicate: {result['duplicate_id'][:8]}…\n"
        f"Vertical: {result['vertical']}\n"
        f"Fields copied: {', '.join(result['merged_fields']) or '—'}"
    )
    log_audit(user_id, "merge", "anti_loss", f"lead:{primary_id}:{duplicate_id}")


@anti_loss_layer_router.message(F.text.startswith("/merge_deals"))
async def merge_deals_command(message: Message) -> None:
    user_id = message.from_user.id
    if not _can_access(user_id):
        await message.answer("Нет доступа.")
        return
    parts = (message.text or "").split()
    if len(parts) < 3:
        await message.answer(
            "Формат: /merge_deals <primary_uuid> <duplicate_uuid>\n"
            "Primary deal остаётся активным, duplicate отменяется."
        )
        return
    try:
        primary_id = uuid.UUID(parts[1])
        duplicate_id = uuid.UUID(parts[2])
    except ValueError:
        await message.answer("Некорректный UUID.")
        return
    try:
        result = await AntiLossLayerV1.merge_deals(
            primary_id,
            duplicate_id,
            actor_telegram_id=user_id,
        )
    except AntiLossLayerV1Error as exc:
        await message.answer(f"❌ {exc}")
        return
    except Exception as exc:
        logger.exception("merge_deals failed")
        await message.answer(f"Ошибка: {exc}")
        return
    await message.answer(
        f"✅ Deals merged\n"
        f"Primary: {result['primary_id'][:8]}…\n"
        f"Duplicate: {result['duplicate_id'][:8]}…\n"
        f"Vertical: {result['vertical']}"
    )
    log_audit(user_id, "merge", "anti_loss", f"deal:{primary_id}:{duplicate_id}")
