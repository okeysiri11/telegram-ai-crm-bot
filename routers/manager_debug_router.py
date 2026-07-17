# Manager debug commands and lead card callbacks.

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from keyboards import crm_menu
from services.pg_auto_client_request_engine import AutoClientRequestEngineV1
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
    summary = await AutoClientRequestEngineV1.get_request_summary(request_number)

    if summary is None:
        await callback.answer("Заявка не найдена", show_alert=True)
        return

    if not await ManagerDeliveryEngineV1.is_platform_manager(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    text = ManagerDeliveryEngineV1.format_auto_client_request_card(summary)
    await callback.message.answer(
        text,
        reply_markup=ManagerDeliveryEngineV1.request_action_keyboard(summary["request_number"]),
    )
    await callback.answer()


@router.message(F.text == "🆕 Новые заявки")
async def manager_new_requests(message: Message) -> None:
    if not await ManagerDeliveryEngineV1.is_platform_manager(message.from_user.id):
        return

    summaries = await AutoClientRequestEngineV1.list_new_request_summaries(limit=10)
    text = ManagerDeliveryEngineV1.format_new_auto_client_requests(summaries)
    if not summaries:
        await message.answer(text, reply_markup=crm_menu())
        return

    await message.answer(text, reply_markup=crm_menu())
