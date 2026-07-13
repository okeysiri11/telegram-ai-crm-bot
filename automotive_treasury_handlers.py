# Automotive Treasury Engine v1 — Telegram dealer rates channel handler.

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import Message

from config import DEALER_RATES_TELEGRAM_CHANNEL_ID
from services.pg_automotive_treasury_engine import (
    AutomotiveTreasuryEngineError,
    AutomotiveTreasuryEngineV1,
)

logger = logging.getLogger(__name__)

automotive_treasury_router = Router()


def _channel_chat_id(message: Message) -> str | None:
    if message.chat:
        return str(message.chat.id)
    return None


@automotive_treasury_router.channel_post(F.text)
async def dealer_rates_channel_post(message: Message) -> None:
    chat_id = _channel_chat_id(message)
    if not chat_id or not AutomotiveTreasuryEngineV1.is_dealer_rates_channel(chat_id):
        return
    try:
        sheet = await AutomotiveTreasuryEngineV1.ingest_from_telegram(
            message.text or "",
            channel_id=chat_id,
            message_id=message.message_id,
        )
        logger.info(
            "Dealer rates updated from channel %s message %s sheet %s",
            chat_id,
            message.message_id,
            sheet.get("id"),
        )
    except AutomotiveTreasuryEngineError as exc:
        logger.warning(
            "Failed to parse dealer rates from channel %s: %s",
            chat_id,
            exc,
        )


@automotive_treasury_router.edited_channel_post(F.text)
async def dealer_rates_channel_edit(message: Message) -> None:
    await dealer_rates_channel_post(message)


@automotive_treasury_router.message(F.text == "💱 Курсы дилера")
async def show_dealer_rates(message: Message) -> None:
    from services.automotive_telegram_access import can_access_automotive_ui

    user_id = message.from_user.id
    if not await can_access_automotive_ui(user_id):
        await message.answer("Нет доступа к Automotive модулю.")
        return
    try:
        report = await AutomotiveTreasuryEngineV1.get_rates_report()
    except AutomotiveTreasuryEngineError as exc:
        await message.answer(
            f"💱 Курсы дилера\n\n{exc}\n\n"
            f"Канал: {DEALER_RATES_TELEGRAM_CHANNEL_ID or 'не настроен'}"
        )
        return
    await message.answer(report)
