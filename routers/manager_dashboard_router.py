# Manager Dashboard — inline tabs for request buckets and actions.

from __future__ import annotations

import logging
import uuid

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from services.dashboard_service import dashboard_service
from services.pg_manager_delivery_engine import ManagerDeliveryEngineV1

logger = logging.getLogger(__name__)

router = Router(name="manager_dashboard")

PREFIX = "dash:"
TAB_NEW = f"{PREFIX}tab:new"
TAB_ACTIVE = f"{PREFIX}tab:active"
TAB_OVERDUE = f"{PREFIX}tab:overdue"
TAB_COMPLETED = f"{PREFIX}tab:completed"
TAKE_PREFIX = f"{PREFIX}take:"
COMPLETE_PREFIX = f"{PREFIX}complete:"


def dashboard_tabs_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📥 Новые", callback_data=TAB_NEW),
                InlineKeyboardButton(text="⚙️ В работе", callback_data=TAB_ACTIVE),
            ],
            [
                InlineKeyboardButton(text="⏰ Просрочено", callback_data=TAB_OVERDUE),
                InlineKeyboardButton(text="✅ Завершено", callback_data=TAB_COMPLETED),
            ],
        ]
    )


def _request_actions_keyboard(requests: list[dict], *, action: str = "take") -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    prefix = TAKE_PREFIX if action == "take" else COMPLETE_PREFIX
    for req in requests[:8]:
        number = req.get("request_number")
        if not number:
            continue
        label = f"{'📥' if action == 'take' else '✅'} {number}"
        rows.append([InlineKeyboardButton(text=label, callback_data=f"{prefix}{number}")])
    rows.append(
        [
            InlineKeyboardButton(text="📥 Новые", callback_data=TAB_NEW),
            InlineKeyboardButton(text="⚙️ В работе", callback_data=TAB_ACTIVE),
        ]
    )
    rows.append(
        [
            InlineKeyboardButton(text="⏰ Просрочено", callback_data=TAB_OVERDUE),
            InlineKeyboardButton(text="✅ Завершено", callback_data=TAB_COMPLETED),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _require_manager(user_id: int | None) -> bool:
    if user_id is None:
        return False
    return await ManagerDeliveryEngineV1.is_platform_manager(user_id)


async def _manager_uuid(telegram_id: int) -> uuid.UUID | None:
    user = await ManagerDeliveryEngineV1.get_manager_user(telegram_id=telegram_id)
    if user is None:
        return None
    return user.id


@router.message(F.text.in_({"📊 Dashboard", "📊 Manager Dashboard", "/manager_dashboard"}))
async def open_dashboard(message: Message) -> None:
    if not await _require_manager(message.from_user.id if message.from_user else None):
        return
    await message.answer(
        "📊 Manager Dashboard\n\nВыберите раздел:",
        reply_markup=dashboard_tabs_keyboard(),
    )


@router.callback_query(F.data == TAB_NEW)
async def dashboard_new(callback: CallbackQuery) -> None:
    if callback.from_user is None or not await _require_manager(callback.from_user.id):
        await callback.answer()
        return
    manager_id = await _manager_uuid(callback.from_user.id)
    if manager_id is None:
        await callback.answer("Manager profile not found", show_alert=True)
        return

    requests = await dashboard_service.get_new_requests(manager_id)
    text = dashboard_service.format_request_lines("📥 Новые заявки", requests)
    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=_request_actions_keyboard(requests, action="take"),
        )
    await callback.answer()


@router.callback_query(F.data == TAB_ACTIVE)
async def dashboard_active(callback: CallbackQuery) -> None:
    if callback.from_user is None or not await _require_manager(callback.from_user.id):
        await callback.answer()
        return
    manager_id = await _manager_uuid(callback.from_user.id)
    if manager_id is None:
        await callback.answer("Manager profile not found", show_alert=True)
        return

    requests = await dashboard_service.get_active_requests(manager_id)
    text = dashboard_service.format_request_lines("⚙️ Заявки в работе", requests)
    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=_request_actions_keyboard(requests, action="complete"),
        )
    await callback.answer()


@router.callback_query(F.data == TAB_OVERDUE)
async def dashboard_overdue(callback: CallbackQuery) -> None:
    if callback.from_user is None or not await _require_manager(callback.from_user.id):
        await callback.answer()
        return
    manager_id = await _manager_uuid(callback.from_user.id)
    if manager_id is None:
        await callback.answer("Manager profile not found", show_alert=True)
        return

    requests = await dashboard_service.get_overdue_requests(manager_id)
    text = dashboard_service.format_request_lines("⏰ Просроченные заявки", requests)
    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=_request_actions_keyboard(requests, action="complete"),
        )
    await callback.answer()


@router.callback_query(F.data == TAB_COMPLETED)
async def dashboard_completed(callback: CallbackQuery) -> None:
    if callback.from_user is None or not await _require_manager(callback.from_user.id):
        await callback.answer()
        return
    manager_id = await _manager_uuid(callback.from_user.id)
    if manager_id is None:
        await callback.answer("Manager profile not found", show_alert=True)
        return

    requests = await dashboard_service.get_completed_requests(manager_id)
    text = dashboard_service.format_request_lines("✅ Завершённые заявки", requests)
    if callback.message:
        await callback.message.edit_text(text, reply_markup=dashboard_tabs_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith(TAKE_PREFIX))
async def dashboard_take_request(callback: CallbackQuery) -> None:
    if callback.from_user is None or not await _require_manager(callback.from_user.id):
        await callback.answer()
        return
    manager_id = await _manager_uuid(callback.from_user.id)
    if manager_id is None:
        await callback.answer("Manager profile not found", show_alert=True)
        return

    request_number = (callback.data or "").removeprefix(TAKE_PREFIX)
    result = await dashboard_service.take_request(request_number, manager_id)
    if result is None:
        await callback.answer("Заявка не найдена", show_alert=True)
        return

    await callback.answer("Заявка взята в работу")
    if callback.message:
        await callback.message.answer(
            f"✅ Заявка #{result.get('request_number')} назначена вам.\n"
            f"Статус: {result.get('status')}",
            reply_markup=dashboard_tabs_keyboard(),
        )


@router.callback_query(F.data.startswith(COMPLETE_PREFIX))
async def dashboard_complete_request(callback: CallbackQuery) -> None:
    if callback.from_user is None or not await _require_manager(callback.from_user.id):
        await callback.answer()
        return

    request_number = (callback.data or "").removeprefix(COMPLETE_PREFIX)
    result = await dashboard_service.complete_request(request_number)
    if result is None:
        await callback.answer("Не удалось завершить заявку", show_alert=True)
        return

    await callback.answer("Заявка завершена")
    if callback.message:
        await callback.message.answer(
            f"✅ Заявка #{result.get('request_number')} завершена.",
            reply_markup=dashboard_tabs_keyboard(),
        )
