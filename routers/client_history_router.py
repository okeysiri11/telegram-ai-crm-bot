# Client request history — «📂 My Requests» menu.

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from keyboards import auto_client_menu
from services.automotive_localization import btn, normalize_language
from services.entry_point_routing import EntryPoint
from services.pg_client_request_crm_engine import ClientRequestCrmEngineV1
from services.pg_entry_point_engine import EntryPointEngineV1
from services.pg_manager_delivery_engine import ManagerDeliveryEngineV1
from services.pg_vertical_onboarding_engine import VerticalOnboardingEngineV1

logger = logging.getLogger(__name__)

router = Router()


async def _is_auto_client_user(user_id: int) -> bool:
    ctx = await EntryPointEngineV1.get_flow_context(user_id)
    return ctx.get("entry_point") == EntryPoint.AUTO_CLIENT.value or ctx.get("source_link") == "auto_client"


def _my_requests_filter(message: Message) -> bool:
    if not message.from_user or not message.text:
        return False
    text = message.text.strip()
    for lang in ("ru", "uk"):
        if text == btn("client_my_requests", lang):
            return True
    return False


@router.message(_my_requests_filter)
async def client_my_requests(message: Message) -> None:
    if message.from_user is None:
        return
    if not await _is_auto_client_user(message.from_user.id):
        return

    lang = await VerticalOnboardingEngineV1.get_language(message.from_user.id)
    history = await ClientRequestCrmEngineV1.list_client_history(message.from_user.id, limit=15)

    if not history:
        await message.answer(
            "📂 Мои заявки\n\nУ вас пока нет заявок.",
            reply_markup=auto_client_menu(lang),
        )
        return

    lines = ["📂 Мои заявки", ""]
    for idx, item in enumerate(history, 1):
        lines.append(
            f"{idx}. {item['request_type_label']}\n"
            f"   Status: {item['status_label']}\n"
            f"   {item['request_number']}"
        )
    lines.append("")
    lines.append("Нажмите номер заявки в списке ниже для деталей.")

    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    rows = [
        [InlineKeyboardButton(text=item["request_number"], callback_data=f"client:req:{item['request_number']}")]
        for item in history[:10]
    ]
    await message.answer(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )


@router.callback_query(F.data.startswith("client:req:"))
async def client_request_detail(callback: CallbackQuery) -> None:
    if callback.from_user is None or callback.message is None:
        await callback.answer()
        return

    request_number = callback.data.removeprefix("client:req:")
    detail = await ClientRequestCrmEngineV1.get_request_detail(request_number)
    if detail is None:
        await callback.answer("Заявка не найдена", show_alert=True)
        return

    if detail.get("client_telegram_id") != callback.from_user.id:
        if not await ManagerDeliveryEngineV1.is_platform_manager(callback.from_user.id):
            await callback.answer("Нет доступа", show_alert=True)
            return

    text = (
        f"📋 {detail['request_number']}\n\n"
        f"Тип: {detail['request_type_label']}\n"
        f"Статус: {detail['status_label']}\n"
        f"Этап: {detail.get('funnel_label', '—')}\n"
    )
    if detail.get("brand"):
        text += f"\n{detail['brand']} {detail.get('model') or ''} {detail.get('year') or ''}".strip()
        text += "\n"
    if detail.get("description"):
        text += f"\nОписание:\n{detail['description'][:500]}\n"
    if detail.get("photo_count"):
        text += f"\nФото: {detail['photo_count']}\n"
    if detail.get("created_at"):
        text += f"\nСоздана: {detail['created_at'][:10]}"

    await callback.message.answer(text)
    await callback.answer()
