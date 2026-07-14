# AI Sales Assistant v1 — Telegram customer handlers.

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from services.pg_ai_sales_assistant_engine import AiSalesAssistantEngineV1

logger = logging.getLogger(__name__)

ai_sales_router = Router()

sales_assistant_active: set[int] = set()


def _is_customer_message(message: Message) -> bool:
    if not message.from_user or not message.text:
        return False
    if message.text.startswith("/"):
        return False
    return message.from_user.id in sales_assistant_active


async def _block_entry_point_customers(message: Message) -> bool:
    from services.entry_point_routing import EntryPoint
    from services.pg_entry_point_engine import EntryPointEngineV1

    ctx = await EntryPointEngineV1.get_flow_context(message.from_user.id)
    return ctx.get("entry_point") == EntryPoint.AUTO_CLIENT.value


@ai_sales_router.message(Command("sales"))
async def cmd_sales(message: Message) -> None:
    user = message.from_user
    if await AiSalesAssistantEngineV1.is_staff(user.id):
        await message.answer("AI Sales Assistant предназначен для клиентов.")
        return

    sales_assistant_active.add(user.id)
    await AiSalesAssistantEngineV1.start_session(
        telegram_user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
    )
    await message.answer(
        "🤖 AI Sales Assistant\n\n"
        "Я помогу с:\n"
        "• информацией об автомобилях\n"
        "• расчётом финансирования\n"
        "• сбором контактов\n"
        "• записью на встречу\n"
        "• передачей менеджеру\n\n"
        "Напишите ваш вопрос."
    )


@ai_sales_router.message(_is_customer_message, F.text)
async def sales_assistant_message(message: Message) -> None:
    user = message.from_user
    if await _block_entry_point_customers(message):
        return
    try:
        reply = await AiSalesAssistantEngineV1.handle_message(
            telegram_user_id=user.id,
            text=message.text.strip(),
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
        )
    except Exception:
        logger.exception("AI Sales Assistant failed for user %s", user.id)
        await message.answer(
            "Извините, произошла ошибка. Напишите «менеджер» для связи с оператором."
        )
        return

    await message.answer(reply)
