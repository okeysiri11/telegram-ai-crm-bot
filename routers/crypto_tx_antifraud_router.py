# Crypto/OTC transaction idempotency — Telegram bot integration — Sprint 48.0/48.1.
# SECURITY-CRITICAL. This router is thin by design: every decision (is this
# a duplicate? what does the audit trail say? is override available?) comes
# from services.crypto_payout_orchestrator.CryptoPayoutOrchestrator — the
# SAME canonical service the management API (Web/Operator UI) calls. Do not
# add duplicate-detection or state-transition logic here; this module only
# collects operator input, calls the orchestrator, and renders its decision.
#
# Sprint 48.1 real flow (see docs/SPRINT_48_1_RESULT.md):
#   handlers.py's deal-detail screen offers "confirm payout" only when
#   viewing a real, non-terminal crypto/OTC deal -> start_payout_confirmation()
#   collects network/tx_hash/token/amount/wallet -> CryptoPayoutOrchestrator
#   .confirm_payout() -> render ALLOW / DUPLICATE(WARN+BLOCK) result.
#
# Override is disabled in production this sprint (no real step-up
# authentication provider exists — see CryptoTxOverrideUnavailableError);
# the button offering it has been removed, and the FSM path that used to
# collect a "confirmation" for it has been removed with it. Cancel and
# Send-for-review remain fully available.

from __future__ import annotations

import logging
import uuid
from decimal import Decimal, InvalidOperation
from typing import Any

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from services.crypto_payout_orchestrator import (
    CryptoAntifraudError,
    CryptoDealInvalidStateError,
    CryptoDealNotFoundError,
    CryptoPayoutOrchestrator,
    CryptoPayoutResultStatus,
)
from services.pg_crypto_tx_antifraud_engine import DuplicateWarning
from services.vertical_role_registry import vertical_role_registry

logger = logging.getLogger(__name__)

router = Router()

CB_CANCEL = "crypto_tx:cancel:"
CB_REVIEW = "crypto_tx:review:"
CB_PAYOUT_CONFIRM = "crypto_tx:payout_confirm:"
CB_PAYOUT_ABORT = "crypto_tx:payout_abort"


class CryptoPayoutConfirmFlow(StatesGroup):
    awaiting_details = State()
    awaiting_confirmation = State()


def format_duplicate_warning_ru(warning: DuplicateWarning, *, viewer_role: str) -> str:
    """Requirement 4/11 — the mandatory warning fields, rendered for
    Telegram/Web alike (the Web modal renders the same JSON shape). Override
    is intentionally not offered — see module docstring."""
    lines = [
        "🛑 ВНИМАНИЕ: возможен дублирующий платёж",
        "",
        f"Хэш транзакции: {warning.tx_hash}",
        f"Сеть: {warning.network}",
        f"Токен: {warning.token}",
        f"Сумма: {warning.amount}",
        f"Кошелёк: {warning.wallet_address}",
        f"Текущий статус: {warning.previous_status}",
        f"Впервые зарегистрирована: {warning.first_seen_at.isoformat()}",
    ]
    if warning.previous_legacy_deal_id:
        lines.append(f"Предыдущая сделка: #{warning.previous_legacy_deal_id}")
    if warning.previous_legacy_payment_id:
        lines.append(f"Предыдущий платёж: #{warning.previous_legacy_payment_id}")
    lines.append(f"Предыдущий оператор: {warning.previous_operator_id}")
    if warning.previous_customer_id is not None:
        lines.append(f"Предыдущий клиент: {warning.previous_customer_id}")
    if warning.anomalies:
        ru_anomalies = {
            "resubmitted_after_cancellation": "повторная подача после отмены",
            "same_wallet_amount_short_window": "тот же кошелёк/сумма за короткое время",
            "linked_to_multiple_customers": "связано с несколькими клиентами",
            "repeated_operator_attempts": "повторные попытки того же оператора",
        }
        lines.append("")
        lines.append("Аномалии: " + ", ".join(ru_anomalies.get(a, a) for a in warning.anomalies))
    lines.append("")
    lines.append(
        "Эта транзакция уже использована. Автоматическая обработка ЗАБЛОКИРОВАНА."
    )
    lines.append(
        "⚠️ Override недоступен: требуется реальная повторная аутентификация, "
        "которая пока не реализована. Доступно: Отмена / На проверку."
    )
    return "\n".join(lines)


def duplicate_action_keyboard(tx_id: uuid.UUID | str) -> InlineKeyboardMarkup:
    """Requirement 5 — Cancel / Send-for-review. Override is not offered:
    disabled in production until real step-up authentication exists (see
    module docstring) — showing a button that always fails server-side
    would be a worse UX than not offering it."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data=f"{CB_CANCEL}{tx_id}")],
            [InlineKeyboardButton(text="🔍 На проверку", callback_data=f"{CB_REVIEW}{tx_id}")],
        ]
    )


async def start_payout_confirmation(message: Message, state: FSMContext, *, deal_id: int) -> None:
    """Called from handlers.py when an operator presses "confirm payout"
    while viewing a specific real deal. handlers.py decides *when* to call
    this (presentation concern only); everything from here on — validation,
    the anti-fraud gate, the state transition — lives behind
    CryptoPayoutOrchestrator, not in handlers.py or this function."""
    await state.set_state(CryptoPayoutConfirmFlow.awaiting_details)
    await state.update_data(crypto_payout_deal_id=deal_id)
    await message.answer(
        f"💳 Подтверждение платежа по сделке #{deal_id}\n\n"
        "Отправьте одной строкой: СЕТЬ TX_HASH ТОКЕН СУММА АДРЕС_КОШЕЛЬКА\n"
        "Например: TRC20 3f8c9e...ab12 USDT 1000 TQn9Y2example"
    )


@router.message(CryptoPayoutConfirmFlow.awaiting_details)
async def on_payout_details(message: Message, state: FSMContext) -> None:
    parts = (message.text or "").split()
    if len(parts) < 5:
        await message.answer(
            "Нужно 5 значений через пробел: СЕТЬ TX_HASH ТОКЕН СУММА АДРЕС_КОШЕЛЬКА. Повторите."
        )
        return
    network, tx_hash, token, amount_str, wallet_address = parts[0], parts[1], parts[2], parts[3], parts[4]
    try:
        amount = Decimal(amount_str)
    except InvalidOperation:
        await message.answer("Сумма должна быть числом. Повторите ввод.")
        return

    data = await state.get_data()
    deal_id = data["crypto_payout_deal_id"]
    await state.update_data(
        network=network, tx_hash=tx_hash, token=token, amount=amount_str, wallet_address=wallet_address
    )
    await state.set_state(CryptoPayoutConfirmFlow.awaiting_confirmation)
    await message.answer(
        "Проверьте данные:\n"
        f"Сделка: #{deal_id}\n"
        f"Сеть: {network}\n"
        f"TX hash: {tx_hash}\n"
        f"Токен: {token}\n"
        f"Сумма: {amount}\n"
        f"Кошелёк: {wallet_address}\n\n"
        "Подтвердить платёж?",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Подтвердить платёж", callback_data=f"{CB_PAYOUT_CONFIRM}{deal_id}"
                    ),
                    InlineKeyboardButton(text="Отмена", callback_data=CB_PAYOUT_ABORT),
                ]
            ]
        ),
    )


@router.callback_query(F.data.startswith(CB_PAYOUT_CONFIRM))
async def on_payout_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()
    user_id = callback.from_user.id
    sess = vertical_role_registry.get(user_id)

    try:
        deal_id = int(data["crypto_payout_deal_id"])
        result = await CryptoPayoutOrchestrator.confirm_payout(
            deal_id=deal_id,
            network=data["network"],
            tx_hash=data["tx_hash"],
            token=data["token"],
            amount=Decimal(data["amount"]),
            wallet_address=data["wallet_address"],
            actor_id=user_id,
            actor_role=sess.authenticated_role,
        )
    except (CryptoDealNotFoundError, CryptoDealInvalidStateError) as exc:
        await callback.message.answer(f"Невозможно подтвердить платёж: {exc}")
        await callback.answer()
        return
    except CryptoAntifraudError as exc:
        await callback.message.answer(str(exc))
        await callback.answer()
        return

    if result.status == CryptoPayoutResultStatus.DUPLICATE:
        await callback.message.answer(
            format_duplicate_warning_ru(result.warning, viewer_role=sess.authenticated_role),
            reply_markup=duplicate_action_keyboard(result.transaction.id),
        )
    elif result.status == CryptoPayoutResultStatus.ALREADY_CONFIRMED:
        await callback.message.answer(
            f"ℹ️ Платёж по сделке #{result.deal_id} уже был подтверждён ранее этим же tx_hash "
            "(повторный вызов — без повторного выполнения)."
        )
    else:
        await callback.message.answer(
            f"✅ Платёж подтверждён. Сделка #{result.deal_id}, платёж #{result.payment_id}, "
            f"статус транзакции: {result.transaction.status}."
        )
    await callback.answer()


@router.callback_query(F.data == CB_PAYOUT_ABORT)
async def on_payout_abort(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer("Подтверждение платежа отменено.")
    await callback.answer()


@router.callback_query(F.data.startswith(CB_CANCEL))
async def on_cancel(callback: CallbackQuery) -> None:
    tx_id = uuid.UUID(callback.data[len(CB_CANCEL):])
    user_id = callback.from_user.id
    try:
        await CryptoPayoutOrchestrator.cancel(tx_id, actor_id=user_id, reason="cancelled_by_operator_via_bot")
    except CryptoAntifraudError as exc:
        await callback.answer(str(exc), show_alert=True)
        return
    await callback.message.edit_text(f"{callback.message.text}\n\n❌ Отменено оператором {user_id}.")
    await callback.answer("Отменено.")


@router.callback_query(F.data.startswith(CB_REVIEW))
async def on_review(callback: CallbackQuery) -> None:
    tx_id = uuid.UUID(callback.data[len(CB_REVIEW):])
    user_id = callback.from_user.id
    try:
        await CryptoPayoutOrchestrator.request_review(tx_id, actor_id=user_id, reason="sent_via_bot")
    except CryptoAntifraudError as exc:
        await callback.answer(str(exc), show_alert=True)
        return
    await callback.message.edit_text(
        f"{callback.message.text}\n\n🔍 Отправлено на ручную проверку оператором {user_id}."
    )
    await callback.answer("Отправлено на проверку.")
