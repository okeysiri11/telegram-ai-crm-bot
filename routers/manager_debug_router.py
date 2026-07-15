# Manager debug commands and lead card callbacks.

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from keyboards import crm_menu
from database.session import get_session
from services.pg_manager_delivery_engine import ManagerDeliveryEngineV1

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("debug_manager"))
async def cmd_debug_manager(message: Message) -> None:
    user_id = message.from_user.id
    text = await ManagerDeliveryEngineV1.debug_report(user_id)
    await message.answer(text)


@router.callback_query(F.data.startswith("mgr:req:"))
async def open_auto_client_request_card(callback: CallbackQuery) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return

    request_number = callback.data.removeprefix("mgr:req:")
    from sqlalchemy import select
    from database.models.auto_client_request import AutoClientRequest

    async with get_session() as session:
        result = await session.execute(
            select(AutoClientRequest).where(
                AutoClientRequest.request_number == request_number
            )
        )
        row = result.scalar_one_or_none()

    if row is None:
        await callback.answer("Заявка не найдена", show_alert=True)
        return

    if not await ManagerDeliveryEngineV1.is_platform_manager(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    client = row.client_username or row.client_full_name or str(row.client_telegram_id)
    text = (
        f"📋 Заявка {row.request_number}\n\n"
        f"Тип: {row.request_type}\n"
        f"Статус: {row.status}\n"
        f"Клиент: {client}\n"
        f"Telegram ID: {row.client_telegram_id}\n\n"
        f"Описание:\n{row.description or '—'}"
    )
    await callback.message.answer(text, reply_markup=crm_menu())
    await callback.answer()


@router.message(F.text == "🆕 Новые заявки")
async def manager_new_requests(message: Message) -> None:
    if not await ManagerDeliveryEngineV1.is_platform_manager(message.from_user.id):
        return

    from sqlalchemy import select
    from database.models.auto_client_request import AutoClientRequest, AutoClientRequestStatus
    from database.session import get_session

    async with get_session() as session:
        result = await session.execute(
            select(AutoClientRequest)
            .where(AutoClientRequest.status == AutoClientRequestStatus.NEW.value)
            .order_by(AutoClientRequest.created_at.desc())
            .limit(10)
        )
        rows = list(result.scalars().all())

    if not rows:
        await message.answer("Новых заявок нет.", reply_markup=crm_menu())
        return

    lines = ["🆕 Новые заявки", ""]
    for row in rows:
        client = row.client_username or row.client_full_name or row.client_telegram_id
        lines.append(
            f"• {row.request_number} | {row.request_type}\n"
            f"  {client}: {(row.description or '')[:80]}"
        )
    await message.answer("\n".join(lines), reply_markup=crm_menu())
