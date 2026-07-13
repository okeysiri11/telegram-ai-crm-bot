# BidEx Telegram Quote Parser v1 — @bidex_Odesa channel handler.

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import Message

from config import BIDEX_TELEGRAM_CHANNEL_USERNAME
from services.bidex_telegram_quote_parser import (
    BidExQuoteParserError,
    BidExTelegramQuoteParserV1,
)

logger = logging.getLogger(__name__)

bidex_quote_router = Router()


def _channel_context(message: Message) -> tuple[str | None, str | None]:
    if not message.chat:
        return None, None
    return str(message.chat.id), message.chat.username


@bidex_quote_router.channel_post(F.text)
async def bidex_rates_channel_post(message: Message) -> None:
    chat_id, username = _channel_context(message)
    if not chat_id or not BidExTelegramQuoteParserV1.is_bidex_channel(chat_id, username):
        return
    text = message.text or ""
    if not BidExTelegramQuoteParserV1.should_parse(text):
        return
    try:
        sheet = await BidExTelegramQuoteParserV1.ingest_channel_message(
            text,
            channel_id=chat_id,
            message_id=message.message_id,
        )
        if sheet:
            logger.info(
                "BidEx rates updated channel=%s message=%s sheet=%s",
                chat_id,
                message.message_id,
                sheet.get("id"),
            )
    except BidExQuoteParserError as exc:
        logger.warning("BidEx parse failed channel=%s: %s", chat_id, exc)


@bidex_quote_router.edited_channel_post(F.text)
async def bidex_rates_channel_edit(message: Message) -> None:
    await bidex_rates_channel_post(message)
