# Manual Payment Verification Engine v1 — Telegram handlers.

from __future__ import annotations

import logging
import uuid
from decimal import Decimal

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from config import OWNER_ID
from services.handler_auth import has_permission_sync as has_permission, log_audit
from payment_engine_state import pending_payment_upload
from services.pg_cart_engine_v1 import CartEngineV1
from services.pg_financial_settlement_engine_v1 import FinancialSettlementEngineV1
from services.pg_payment_engine_v1 import (
    PAYMENT_CONFIRMED_MESSAGE,
    PAYMENT_REJECTED_MESSAGE,
    PAYMENT_UPLOADED_MESSAGE,
    PaymentEngineV1,
    PaymentEngineV1Error,
)

logger = logging.getLogger(__name__)

payment_engine_router = Router()


def _can_access_admin(user_id: int) -> bool:
    return has_permission(user_id, "users_access") or user_id == OWNER_ID


async def _resolve_manager_uuid(telegram_user_id: int, *, full_name: str = "", username: str = "") -> uuid.UUID:
    return await CartEngineV1.resolve_user_id(
        telegram_user_id,
        full_name=full_name,
        username=username,
    )


async def _notify_owner_review(message: Message, payment: dict) -> None:
    payment_id = uuid.UUID(payment["id"])
    try:
        await PaymentEngineV1.begin_verification(payment_id)
    except PaymentEngineV1Error:
        logger.exception("Failed to mark payment under verification %s", payment_id)

    text = PaymentEngineV1.format_manager_notification(payment)
    keyboard = PaymentEngineV1.manager_review_keyboard(uuid.UUID(payment["id"]))
    file_id = payment.get("screenshot_file_id")
    try:
        if file_id:
            await message.bot.send_photo(
                OWNER_ID,
                file_id,
                caption=text,
                reply_markup=keyboard,
            )
        else:
            await message.bot.send_message(OWNER_ID, text, reply_markup=keyboard)
    except Exception:
        logger.exception("Failed to notify owner about payment %s", payment.get("id"))


async def _notify_settlement_confirmed(bot, payment: dict) -> None:
    settlement = payment.get("settlement") or {}
    if not settlement:
        return
    manager_tid = settlement.get("manager_telegram_id") or payment.get("manager_telegram_id")
    try:
        await bot.send_message(
            OWNER_ID,
            FinancialSettlementEngineV1.format_owner_notification(settlement),
        )
    except Exception:
        logger.exception("Failed to notify owner about settlement %s", settlement.get("id"))

    if manager_tid and Decimal(str(settlement.get("manager_share", "0"))) > 0:
        try:
            await bot.send_message(
                manager_tid,
                FinancialSettlementEngineV1.format_manager_notification(settlement),
            )
        except Exception:
            logger.exception(
                "Failed to notify manager %s about settlement",
                manager_tid,
            )


@payment_engine_router.message(F.photo)
async def payment_screenshot_upload(message: Message) -> None:
    if message.from_user is None or not message.photo:
        return
    user_id = message.from_user.id
    payment_id = pending_payment_upload.get(user_id)
    if payment_id is None:
        return

    file_id = message.photo[-1].file_id
    try:
        payment = await PaymentEngineV1.upload_screenshot(payment_id, file_id)
    except PaymentEngineV1Error as exc:
        await message.answer(str(exc))
        return

    pending_payment_upload.pop(user_id, None)
    await message.answer(PAYMENT_UPLOADED_MESSAGE)
    await _notify_owner_review(message, payment)
    log_audit(user_id, "upload", "payment_engine", str(payment_id))


@payment_engine_router.callback_query(F.data.startswith("pay:confirm:"))
async def payment_confirm_callback(callback: CallbackQuery) -> None:
    if callback.from_user is None or callback.message is None:
        await callback.answer()
        return
    user_id = callback.from_user.id
    if not _can_access_admin(user_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    payment_id = uuid.UUID(callback.data.rsplit(":", 1)[-1])
    try:
        manager_uuid = await _resolve_manager_uuid(
            user_id,
            full_name=callback.from_user.full_name or "",
            username=callback.from_user.username or "",
        )
        payment = await PaymentEngineV1.confirm_payment(
            payment_id,
            manager_uuid,
            moved_by_telegram=user_id,
        )
    except PaymentEngineV1Error as exc:
        await callback.answer(str(exc), show_alert=True)
        return

    await callback.answer("Платёж подтверждён")
    await callback.message.answer(
        f"✅ Платёж {payment_id} подтверждён.\n"
        f"Сделка: {payment.get('deal', {}).get('id', '—')}"
    )
    log_audit(user_id, "confirm", "payment_engine", str(payment_id))
    await _notify_settlement_confirmed(callback.message.bot, payment)

    client_id = payment.get("client_id")
    if client_id:
        try:
            telegram_id = await PaymentEngineV1.resolve_client_telegram_id(client_id)
            if telegram_id:
                await callback.message.bot.send_message(telegram_id, PAYMENT_CONFIRMED_MESSAGE)
        except Exception:
            logger.exception("Failed to notify client about confirmed payment %s", payment_id)


@payment_engine_router.callback_query(F.data.startswith("pay:reject:"))
async def payment_reject_callback(callback: CallbackQuery) -> None:
    if callback.from_user is None or callback.message is None:
        await callback.answer()
        return
    user_id = callback.from_user.id
    if not _can_access_admin(user_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    payment_id = uuid.UUID(callback.data.rsplit(":", 1)[-1])
    try:
        manager_uuid = await _resolve_manager_uuid(
            user_id,
            full_name=callback.from_user.full_name or "",
            username=callback.from_user.username or "",
        )
        payment = await PaymentEngineV1.reject_payment(payment_id, manager_uuid)
    except PaymentEngineV1Error as exc:
        await callback.answer(str(exc), show_alert=True)
        return

    await callback.answer("Платёж отклонён")
    await callback.message.answer(f"❌ Платёж {payment_id} отклонён.")
    log_audit(user_id, "reject", "payment_engine", str(payment_id))

    client_id = payment.get("client_id")
    if client_id:
        try:
            telegram_id = await PaymentEngineV1.resolve_client_telegram_id(client_id)
            if telegram_id:
                await callback.message.bot.send_message(telegram_id, PAYMENT_REJECTED_MESSAGE)
                pending_payment_upload[telegram_id] = payment_id
        except Exception:
            logger.exception("Failed to notify client about rejected payment %s", payment_id)


@payment_engine_router.message(F.text.startswith("/confirm_payment"))
async def confirm_payment_command(message: Message) -> None:
    user_id = message.from_user.id
    if not _can_access_admin(user_id):
        await message.answer("Нет доступа.")
        return
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("Формат: /confirm_payment <payment_uuid>")
        return
    try:
        payment_id = uuid.UUID(parts[1])
        manager_uuid = await _resolve_manager_uuid(
            user_id,
            full_name=message.from_user.full_name or "",
            username=message.from_user.username or "",
        )
        payment = await PaymentEngineV1.confirm_payment(
            payment_id,
            manager_uuid,
            moved_by_telegram=user_id,
        )
    except (ValueError, PaymentEngineV1Error) as exc:
        await message.answer(f"Ошибка: {exc}")
        return
    await message.answer(
        f"✅ Платёж подтверждён.\nСделка: {payment.get('deal', {}).get('id', '—')}"
    )
    log_audit(user_id, "confirm", "payment_engine", str(payment_id))
    await _notify_settlement_confirmed(message.bot, payment)


@payment_engine_router.message(F.text.startswith("/reject_payment"))
async def reject_payment_command(message: Message) -> None:
    user_id = message.from_user.id
    if not _can_access_admin(user_id):
        await message.answer("Нет доступа.")
        return
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("Формат: /reject_payment <payment_uuid>")
        return
    try:
        payment_id = uuid.UUID(parts[1])
        manager_uuid = await _resolve_manager_uuid(
            user_id,
            full_name=message.from_user.full_name or "",
            username=message.from_user.username or "",
        )
        await PaymentEngineV1.reject_payment(payment_id, manager_uuid)
    except (ValueError, PaymentEngineV1Error) as exc:
        await message.answer(f"Ошибка: {exc}")
        return
    await message.answer("❌ Платёж отклонён.")
    log_audit(user_id, "reject", "payment_engine", str(payment_id))


@payment_engine_router.message(F.text == "/pending_payments")
async def pending_payments_command(message: Message) -> None:
    user_id = message.from_user.id
    if not _can_access_admin(user_id):
        await message.answer("Нет доступа.")
        return
    metrics = await PaymentEngineV1.get_owner_metrics()
    await message.answer(PaymentEngineV1.format_owner_payment_analytics(metrics))
    log_audit(user_id, "open", "payment_engine", "pending")
