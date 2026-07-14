# Cart and Payment Engine v1 — Telegram cart and checkout flow.

from __future__ import annotations

import logging
import uuid

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from config import OWNER_ID
from database import has_permission, log_audit
from keyboards import admin_module_menu
from services.automotive_localization import normalize_language
from services.cart_service_catalog import service_by_code
from services.pg_cart_engine_v1 import (
    PAYMENT_SUCCESS_MESSAGE,
    CartEngineV1,
    CartEngineV1Error,
)
from services.pg_vertical_onboarding_engine import VerticalOnboardingEngineV1

logger = logging.getLogger(__name__)

cart_engine_router = Router()

cart_sessions: dict[int, dict] = {}
pending_checkout: dict[int, uuid.UUID] = {}


def _can_access_admin(user_id: int) -> bool:
    return has_permission(user_id, "users_access") or user_id == OWNER_ID


async def _lang(user_id: int) -> str:
    return await VerticalOnboardingEngineV1.get_language(user_id)


async def _ensure_cart(user_id: int) -> dict:
    if user_id not in cart_sessions:
        vertical = await CartEngineV1.get_user_vertical(user_id)
        cart_sessions[user_id] = CartEngineV1.new_cart_session(vertical=vertical)
    return cart_sessions[user_id]


@cart_engine_router.message(F.text.in_({"🛒 Корзина", "🛒 Кошик"}))
async def open_cart(message: Message) -> None:
    user_id = message.from_user.id
    lang = await _lang(user_id)
    cart = await _ensure_cart(user_id)
    await message.answer(
        CartEngineV1.format_cart_text(cart, lang=lang),
        reply_markup=CartEngineV1.services_keyboard(cart, lang=lang),
    )


@cart_engine_router.callback_query(F.data.startswith("cart:toggle:"))
async def cart_toggle_service(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    user_id = callback.from_user.id
    lang = await _lang(user_id)
    cart = await _ensure_cart(user_id)
    code = callback.data.rsplit(":", 1)[-1]
    svc = service_by_code(cart.get("vertical", "auto"), code)
    if svc is None:
        await callback.answer("Услуга не найдена", show_alert=True)
        return
    CartEngineV1.toggle_service(cart, svc)
    await callback.answer()
    await callback.message.edit_text(
        CartEngineV1.format_cart_text(cart, lang=lang),
        reply_markup=CartEngineV1.services_keyboard(cart, lang=lang),
    )


@cart_engine_router.callback_query(F.data == "cart:clear")
async def cart_clear(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    user_id = callback.from_user.id
    lang = await _lang(user_id)
    vertical = await CartEngineV1.get_user_vertical(user_id)
    cart_sessions[user_id] = CartEngineV1.new_cart_session(vertical=vertical)
    cart = cart_sessions[user_id]
    await callback.answer("Корзина очищена")
    await callback.message.edit_text(
        CartEngineV1.format_cart_text(cart, lang=lang),
        reply_markup=CartEngineV1.services_keyboard(cart, lang=lang),
    )


@cart_engine_router.callback_query(F.data == "cart:checkout")
async def cart_checkout(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    user_id = callback.from_user.id
    lang = await _lang(user_id)
    cart = await _ensure_cart(user_id)
    if not cart.get("items"):
        await callback.answer("Добавьте услуги в корзину", show_alert=True)
        return
    await callback.answer()
    pick = "Выберите способ оплаты:" if lang != "uk" else "Оберіть спосіб оплати:"
    await callback.message.answer(
        f"{CartEngineV1.format_cart_text(cart, lang=lang)}\n\n{pick}",
        reply_markup=CartEngineV1.payment_methods_keyboard(lang=lang),
    )


@cart_engine_router.callback_query(F.data.startswith("cart:pay:"))
async def cart_select_payment(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    user = callback.from_user
    user_id = user.id
    method = callback.data.rsplit(":", 1)[-1]
    cart = await _ensure_cart(user_id)
    try:
        order = await CartEngineV1.checkout(
            telegram_user_id=user_id,
            cart=cart,
            payment_method=method,
            full_name=user.full_name or "",
            username=user.username or "",
        )
    except CartEngineV1Error as exc:
        await callback.answer(str(exc), show_alert=True)
        return

    pending_checkout[user_id] = uuid.UUID(order["id"])
    cart_sessions.pop(user_id, None)
    await callback.answer()
    await callback.message.answer(order["payment_instructions"])
    await callback.message.answer(
        "После перевода подтвердите оплату:",
        reply_markup=CartEngineV1.confirm_payment_keyboard(uuid.UUID(order["id"])),
    )
    log_audit(user_id, "checkout", "cart_engine", order["id"])


@cart_engine_router.callback_query(F.data.startswith("cart:confirm:"))
async def cart_confirm_payment(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    user_id = callback.from_user.id
    order_id = uuid.UUID(callback.data.rsplit(":", 1)[-1])
    order = await CartEngineV1.confirm_payment(order_id)
    if order is None:
        await callback.answer("Заказ не найден", show_alert=True)
        return
    pending_checkout.pop(user_id, None)
    await callback.answer("Оплата подтверждена")
    await callback.message.answer(PAYMENT_SUCCESS_MESSAGE)
    log_audit(user_id, "paid", "cart_engine", str(order_id))


@cart_engine_router.callback_query(F.data.startswith("cart:cancel:"))
async def cart_cancel_order(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    user_id = callback.from_user.id
    order_id = uuid.UUID(callback.data.rsplit(":", 1)[-1])
    await CartEngineV1.cancel_order(order_id)
    pending_checkout.pop(user_id, None)
    await callback.answer("Заказ отменён")
    await callback.message.answer("❌ Заказ отменён.")


@cart_engine_router.message(F.text == "🛒 Cart Dashboard")
async def cart_admin_dashboard(message: Message) -> None:
    user_id = message.from_user.id
    if not _can_access_admin(user_id) and user_id != OWNER_ID:
        await message.answer("Нет доступа.")
        return
    dashboard = await CartEngineV1.get_owner_dashboard()
    await message.answer(
        CartEngineV1.format_owner_dashboard(dashboard),
        reply_markup=admin_module_menu(),
    )
    log_audit(user_id, "open", "admin", "cart_dashboard")
