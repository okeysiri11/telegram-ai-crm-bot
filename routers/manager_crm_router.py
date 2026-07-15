# Manager CRM dashboard — leads, status updates, client actions.

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from keyboards import crm_menu, manager_dashboard_menu
from services.pg_client_request_crm_engine import ClientRequestCrmEngineV1
from services.pg_manager_delivery_engine import ManagerDeliveryEngineV1
from services.pg_owner_analytics_engine import OwnerAnalyticsEngineV1

logger = logging.getLogger(__name__)

router = Router()


async def _require_manager(message_or_callback) -> bool:
    user = message_or_callback.from_user
    if user is None:
        return False
    return await ManagerDeliveryEngineV1.is_platform_manager(user.id)


@router.message(F.text == "📥 New Leads")
async def manager_new_leads(message: Message) -> None:
    if not await _require_manager(message):
        return
    leads = await ClientRequestCrmEngineV1.list_new_leads(limit=15)
    if not leads:
        await message.answer("📥 New Leads\n\nNo new leads.", reply_markup=manager_dashboard_menu())
        return
    lines = ["📥 New Leads", ""]
    for idx, lead in enumerate(leads, 1):
        lines.append(
            f"{idx}. {lead['request_type_label']}\n"
            f"   {lead['request_number']} | {lead['status_label']}\n"
            f"   {(lead.get('description') or '')[:60]}"
        )
    await message.answer("\n".join(lines), reply_markup=manager_dashboard_menu())


@router.message(F.text == "📋 My Leads")
async def manager_my_leads(message: Message) -> None:
    if not await _require_manager(message):
        return
    user = await ManagerDeliveryEngineV1.get_manager_user(telegram_id=message.from_user.id)
    if user is None:
        await message.answer("Manager profile not found.", reply_markup=manager_dashboard_menu())
        return
    leads = await ClientRequestCrmEngineV1.list_manager_leads(user.id, limit=15)
    if not leads:
        await message.answer("📋 My Leads\n\nNo assigned leads.", reply_markup=manager_dashboard_menu())
        return
    lines = ["📋 My Leads", ""]
    for idx, lead in enumerate(leads, 1):
        lines.append(
            f"{idx}. {lead['request_type_label']}\n"
            f"   Status: {lead['status_label']}\n"
            f"   {lead['request_number']}"
        )
    await message.answer("\n".join(lines), reply_markup=manager_dashboard_menu())


@router.message(F.text == "👥 Clients")
async def manager_clients(message: Message) -> None:
    if not await _require_manager(message):
        return
    leads = await ClientRequestCrmEngineV1.list_new_leads(limit=10)
    lines = ["👥 Clients", ""]
    seen: set[int] = set()
    for lead in leads:
        tid = lead.get("client_telegram_id")
        if tid in seen:
            continue
        seen.add(tid)
        uname = lead.get("client_username")
        phone = lead.get("client_phone") or "—"
        lines.append(f"• @{uname}" if uname else f"• ID {tid}")
        lines.append(f"  📞 {phone}")
    await message.answer("\n".join(lines) or "👥 Clients\n\nNo clients yet.", reply_markup=manager_dashboard_menu())


@router.message(F.text == "📊 Statistics")
async def manager_statistics(message: Message) -> None:
    if not await _require_manager(message):
        return
    metrics = await OwnerAnalyticsEngineV1.get_dashboard_metrics()
    await message.answer(
        OwnerAnalyticsEngineV1.format_dashboard(metrics),
        reply_markup=manager_dashboard_menu(),
    )


@router.callback_query(F.data.startswith("mgr:take:"))
async def manager_take_lead(callback: CallbackQuery) -> None:
    if not await _require_manager(callback):
        await callback.answer()
        return
    request_number = callback.data.removeprefix("mgr:take:")
    user = await ManagerDeliveryEngineV1.get_manager_user(telegram_id=callback.from_user.id)
    if user is None:
        await callback.answer("Manager not found", show_alert=True)
        return
    result = await ClientRequestCrmEngineV1.assign_manager(request_number, user.id)
    if result is None:
        await callback.answer("Request not found", show_alert=True)
        return
    await callback.answer("Lead assigned to you")
    if callback.message:
        await callback.message.answer(
            f"✅ Lead {request_number} assigned to you.\nStatus: {result['status_label']}",
            reply_markup=ManagerDeliveryEngineV1.request_action_keyboard(request_number),
        )


@router.callback_query(F.data.startswith("mgr:status:"))
async def manager_update_status(callback: CallbackQuery) -> None:
    if not await _require_manager(callback):
        await callback.answer()
        return
    parts = callback.data.split(":")
    if len(parts) < 4:
        await callback.answer()
        return
    request_number = parts[2]
    new_status = parts[3]
    try:
        result = await ClientRequestCrmEngineV1.update_status(
            request_number,
            new_status,
            actor_telegram_id=callback.from_user.id,
        )
    except ValueError as exc:
        await callback.answer(str(exc), show_alert=True)
        return
    if result is None:
        await callback.answer("Request not found", show_alert=True)
        return
    await callback.answer(f"Status: {result['status_label']}")
    if callback.message:
        await callback.message.answer(
            f"📋 {request_number}\nStatus updated: {result['status_label']}",
            reply_markup=ManagerDeliveryEngineV1.request_action_keyboard(request_number),
        )


@router.callback_query(F.data.startswith("mgr:call:"))
async def manager_call_client(callback: CallbackQuery) -> None:
    if not await _require_manager(callback):
        await callback.answer()
        return
    request_number = callback.data.removeprefix("mgr:call:")
    detail = await ClientRequestCrmEngineV1.get_request_detail(request_number)
    if detail is None:
        await callback.answer("Not found", show_alert=True)
        return
    phone = detail.get("client_phone") or "—"
    await callback.answer()
    if callback.message:
        await callback.message.answer(f"📞 Client phone for {request_number}:\n{phone}")


@router.callback_query(F.data.startswith("mgr:msg:"))
async def manager_message_client(callback: CallbackQuery) -> None:
    if not await _require_manager(callback):
        await callback.answer()
        return
    request_number = callback.data.removeprefix("mgr:msg:")
    detail = await ClientRequestCrmEngineV1.get_request_detail(request_number)
    if detail is None:
        await callback.answer("Not found", show_alert=True)
        return
    tid = detail.get("client_telegram_id")
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            f"💬 Message client for {request_number}:\n"
            f"Telegram ID: {tid}\n"
            f"Use tg://user?id={tid} or @{detail.get('client_username') or 'username'}"
        )


@router.callback_query(F.data.startswith("mgr:reassign:"))
async def manager_reassign(callback: CallbackQuery) -> None:
    if not await _require_manager(callback):
        await callback.answer()
        return
    request_number = callback.data.removeprefix("mgr:reassign:")
    from services.pg_auto_client_request_engine import AutoClientRequestEngineV1

    manager_info = await AutoClientRequestEngineV1.find_auto_manager()
    if manager_info is None:
        await callback.answer("No manager available", show_alert=True)
        return
    manager_uuid, _, manager_name = manager_info
    result = await ClientRequestCrmEngineV1.assign_manager(request_number, manager_uuid)
    await callback.answer("Reassigned")
    if callback.message and result:
        await callback.message.answer(
            f"🔄 {request_number} reassigned to {manager_name}",
            reply_markup=ManagerDeliveryEngineV1.request_action_keyboard(request_number),
        )
