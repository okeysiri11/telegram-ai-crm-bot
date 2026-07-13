# Dealer Quote Authority Engine v1 — handlers.

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import Message

from config import BIDEX_TELEGRAM_CHANNEL_USERNAME
from services.pg_dealer_quote_authority_engine import (
    DealerQuoteAuthorityEngineError,
    DealerQuoteAuthorityEngineV1,
)

logger = logging.getLogger(__name__)

dealer_quote_authority_router = Router()


def _channel_chat_id(message: Message) -> str | None:
    if message.chat:
        return str(message.chat.id)
    return None


@dealer_quote_authority_router.channel_post(F.text)
async def foma_rates_channel_post(message: Message) -> None:
    chat_id = _channel_chat_id(message)
    if not chat_id or not DealerQuoteAuthorityEngineV1.is_foma_rates_channel(chat_id):
        return
    try:
        sheet = await DealerQuoteAuthorityEngineV1.ingest_foma_rates(
            message.text or "",
            channel_id=chat_id,
            message_id=message.message_id,
        )
        logger.info(
            "Foma Rates updated channel=%s message=%s sheet=%s",
            chat_id,
            message.message_id,
            sheet.get("id"),
        )
    except (DealerQuoteAuthorityEngineError, Exception) as exc:
        logger.warning("Foma Rates parse failed channel=%s: %s", chat_id, exc)


@dealer_quote_authority_router.edited_channel_post(F.text)
async def foma_rates_channel_edit(message: Message) -> None:
    await foma_rates_channel_post(message)


@dealer_quote_authority_router.message(F.text == "🏦 Treasury Dashboard")
async def treasury_dashboard(message: Message) -> None:
    from services.automotive_telegram_access import can_access_automotive_ui

    user_id = message.from_user.id
    if not await can_access_automotive_ui(user_id):
        await message.answer("Нет доступа.")
        return
    try:
        dashboard = await DealerQuoteAuthorityEngineV1.get_treasury_dashboard()
        await message.answer(DealerQuoteAuthorityEngineV1.format_treasury_dashboard(dashboard))
    except DealerQuoteAuthorityEngineError as exc:
        await message.answer(
            f"🏦 Treasury Dashboard\n\n{exc}\n\n"
            f"BidEx channel: @{BIDEX_TELEGRAM_CHANNEL_USERNAME}"
        )


@dealer_quote_authority_router.message(F.text == "💱 Курсы дилера")
async def show_dealer_rates(message: Message) -> None:
    from services.automotive_telegram_access import can_access_automotive_ui
    from services.pg_automotive_treasury_engine import AutomotiveTreasuryEngineV1

    user_id = message.from_user.id
    if not await can_access_automotive_ui(user_id):
        await message.answer("Нет доступа к Automotive модулю.")
        return
    try:
        sheet = await DealerQuoteAuthorityEngineV1.get_authoritative_quotes()
        report = AutomotiveTreasuryEngineV1.format_rates_report(sheet)
        await message.answer(
            f"{report}\n\nAuthority: @bidex_Odesa (Telegram)\n"
            "External sources are reference-only."
        )
    except DealerQuoteAuthorityEngineError as exc:
        await message.answer(f"💱 Курсы дилера\n\n{exc}")
