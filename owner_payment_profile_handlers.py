# Owner Payment Profile v1 — Telegram handlers.

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from config import OWNER_ID
from database import log_audit
from keyboards import owner_panel_menu
from owner_panel_handlers import owner_panel_active
from services.pg_owner_payment_profile_v1 import (
    OwnerPaymentProfileEngineV1,
    OwnerPaymentProfileV1Error,
)

logger = logging.getLogger(__name__)

owner_payment_profile_router = Router()

owner_payment_edit_flow: dict[int, str] = {}


def _is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


async def _show_payment_profile(message: Message) -> None:
    profile = await OwnerPaymentProfileEngineV1.get_profile()
    await message.answer(
        OwnerPaymentProfileEngineV1.format_owner_profile(profile),
        reply_markup=OwnerPaymentProfileEngineV1.owner_settings_keyboard(profile),
    )


@owner_payment_profile_router.message(F.text == "💳 Payment Profile")
async def open_payment_profile(message: Message) -> None:
    user_id = message.from_user.id
    if not _is_owner(user_id):
        await message.answer("Нет доступа.")
        return
    owner_panel_active.add(user_id)
    log_audit(user_id, "open", "owner_payment_profile")
    await _show_payment_profile(message)


@owner_payment_profile_router.callback_query(F.data.startswith("owner:pay:edit:"))
async def payment_profile_edit_start(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    user_id = callback.from_user.id
    if not _is_owner(user_id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    field = callback.data.rsplit(":", 1)[-1]
    owner_payment_edit_flow[user_id] = field
    await callback.answer()
    await callback.message.answer(OwnerPaymentProfileEngineV1.edit_field_prompt(field))


@owner_payment_profile_router.callback_query(F.data.startswith("owner:pay:toggle:"))
async def payment_profile_toggle(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    user_id = callback.from_user.id
    if not _is_owner(user_id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    method = callback.data.rsplit(":", 1)[-1]
    try:
        await OwnerPaymentProfileEngineV1.toggle_method(method)
    except OwnerPaymentProfileV1Error as exc:
        await callback.answer(str(exc), show_alert=True)
        return
    await callback.answer("Обновлено")
    await _show_payment_profile(callback.message)
    log_audit(user_id, "toggle", "owner_payment_profile", method)


@owner_payment_profile_router.callback_query(F.data.startswith("owner:pay:default:"))
async def payment_profile_default(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    user_id = callback.from_user.id
    if not _is_owner(user_id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    method = callback.data.rsplit(":", 1)[-1]
    try:
        await OwnerPaymentProfileEngineV1.set_default_method(method)
    except OwnerPaymentProfileV1Error as exc:
        await callback.answer(str(exc), show_alert=True)
        return
    await callback.answer("Метод по умолчанию обновлён")
    await _show_payment_profile(callback.message)
    log_audit(user_id, "default", "owner_payment_profile", method)


@owner_payment_profile_router.callback_query(F.data == "owner:pay:back")
async def payment_profile_back(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    user_id = callback.from_user.id
    if not _is_owner(user_id):
        await callback.answer()
        return
    owner_payment_edit_flow.pop(user_id, None)
    await callback.answer()
    await callback.message.answer("👑 Owner Panel", reply_markup=owner_panel_menu())


@owner_payment_profile_router.message(
    lambda m: m.from_user.id in owner_payment_edit_flow and _is_owner(m.from_user.id)
)
async def payment_profile_edit_save(message: Message) -> None:
    user_id = message.from_user.id
    field = owner_payment_edit_flow.get(user_id)
    if not field:
        return
    text = (message.text or "").strip()
    if not text:
        await message.answer("Введите значение.")
        return
    try:
        await OwnerPaymentProfileEngineV1.update_field(field, text)
    except OwnerPaymentProfileV1Error as exc:
        await message.answer(str(exc))
        return
    owner_payment_edit_flow.pop(user_id, None)
    await message.answer("✅ Сохранено.", reply_markup=owner_panel_menu())
    await _show_payment_profile(message)
    log_audit(user_id, "update", "owner_payment_profile", field)
