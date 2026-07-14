# Cart and Payment Engine v1 — cart session, checkout, payment instructions.

from __future__ import annotations

import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select

from database import ensure_user
from database.models.cart_engine_v1 import CartOrderStatus, CartPaymentMethod
from database.models.users import User
from database.session import get_session
from repositories.cart_engine_v1_repository import CartEngineV1Repository
from services.automotive_localization import normalize_language
from services.cart_service_catalog import (
    CartService,
    service_by_code,
    service_title,
    services_for_vertical,
)
from services.pg_tenant_entry_registry_engine import TenantRoutingEngineV1
from services.pg_vertical_onboarding_engine import VerticalOnboardingEngineV1

_MONEY = Decimal("0.01")

PAYMENT_SUCCESS_MESSAGE = (
    "Оплата успешно получена.\n"
    "Наш менеджер свяжется с вами в ближайшее время и приступит к обработке вашего заказа."
)

_PAYMENT_METHOD_LABELS: dict[str, dict[str, str]] = {
    "CARD": {"ru": "💳 Карта", "uk": "💳 Картка"},
    "IBAN": {"ru": "🏦 IBAN", "uk": "🏦 IBAN"},
    "USDT": {"ru": "💎 USDT", "uk": "💎 USDT"},
    "CASH": {"ru": "💵 Наличные", "uk": "💵 Готівка"},
}


class CartEngineV1Error(Exception):
    pass


class CartEngineV1:
    @staticmethod
    async def get_user_vertical(telegram_user_id: int) -> str:
        ctx = await TenantRoutingEngineV1.get_tenant_context(telegram_user_id)
        vertical = (ctx.get("vertical") or "auto").lower()
        if vertical not in {"auto", "agro"}:
            return "auto"
        return vertical

    @staticmethod
    async def resolve_user_id(telegram_user_id: int, *, full_name: str = "", username: str = "") -> uuid.UUID:
        ensure_user(telegram_user_id, full_name=full_name, username=username)
        async with get_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_user_id)
            )
            user = result.scalar_one_or_none()
        if user is None:
            raise CartEngineV1Error("User record not found")
        return user.id

    @staticmethod
    def new_cart_session(*, vertical: str) -> dict[str, Any]:
        return {"vertical": vertical.lower(), "items": {}}

    @staticmethod
    def toggle_service(cart: dict[str, Any], service: CartService) -> dict[str, Any]:
        items: dict[str, dict] = cart.setdefault("items", {})
        if service.code in items:
            items.pop(service.code, None)
        else:
            items[service.code] = {
                "code": service.code,
                "title": service.title_ru,
                "unit_price": str(service.price),
                "quantity": 1,
                "currency": service.currency,
            }
        return cart

    @staticmethod
    def cart_total(cart: dict[str, Any]) -> Decimal:
        total = Decimal("0")
        for item in cart.get("items", {}).values():
            total += Decimal(item["unit_price"]) * int(item.get("quantity", 1))
        return total.quantize(_MONEY, rounding=ROUND_HALF_UP)

    @staticmethod
    def format_cart_text(cart: dict[str, Any], *, lang: str | None = None) -> str:
        language = normalize_language(lang)
        items = cart.get("items", {})
        vertical = cart.get("vertical", "auto")
        title = "🛒 Корзина" if language != "uk" else "🛒 Кошик"
        if not items:
            empty = "Выберите услуги:" if language != "uk" else "Оберіть послуги:"
            return f"{title}\n\n{empty}"

        lines = [title, ""]
        for code, item in items.items():
            svc = service_by_code(vertical, code)
            label = service_title(svc, language) if svc else item.get("title", code)
            qty = int(item.get("quantity", 1))
            price = Decimal(item["unit_price"])
            lines.append(f"• {label} × {qty} = {price * qty} {item.get('currency', 'USD')}")
        total = CartEngineV1.cart_total(cart)
        currency = next(iter(items.values()), {}).get("currency", "USD")
        sum_label = "Итого" if language != "uk" else "Разом"
        lines.append("")
        lines.append(f"{sum_label}: {total} {currency}")
        return "\n".join(lines)

    @staticmethod
    def services_keyboard(cart: dict[str, Any], *, lang: str | None = None) -> InlineKeyboardMarkup:
        language = normalize_language(lang)
        vertical = cart.get("vertical", "auto")
        selected = set(cart.get("items", {}).keys())
        rows: list[list[InlineKeyboardButton]] = []
        for svc in services_for_vertical(vertical):
            mark = "✅ " if svc.code in selected else ""
            label = f"{mark}{service_title(svc, language)} — {svc.price} {svc.currency}"
            rows.append([
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"cart:toggle:{svc.code}",
                )
            ])
        checkout_label = "💳 Оформить" if language != "uk" else "💳 Оформити"
        rows.append([InlineKeyboardButton(text=checkout_label, callback_data="cart:checkout")])
        rows.append([InlineKeyboardButton(text="🗑 Очистить", callback_data="cart:clear")])
        return InlineKeyboardMarkup(inline_keyboard=rows)

    @staticmethod
    def payment_methods_keyboard(*, lang: str | None = None) -> InlineKeyboardMarkup:
        language = normalize_language(lang)
        rows = []
        for method in CartPaymentMethod:
            label = _PAYMENT_METHOD_LABELS[method.value].get(language, method.value)
            rows.append([
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"cart:pay:{method.value}",
                )
            ])
        return InlineKeyboardMarkup(inline_keyboard=rows)

    @staticmethod
    def payment_instructions(method: str, *, amount: Decimal, currency: str) -> str:
        method = method.upper()
        if method == CartPaymentMethod.CARD.value:
            return (
                f"💳 Оплата картой\n\n"
                f"Сумма: {amount} {currency}\n"
                f"Карта: 5375 4141 0000 0000\n"
                f"Получатель: Platform Services LLC\n"
                f"Назначение: Order payment\n\n"
                f"После оплаты нажмите «✅ Я оплатил»."
            )
        if method == CartPaymentMethod.IBAN.value:
            return (
                f"🏦 Банковский перевод (IBAN)\n\n"
                f"Сумма: {amount} {currency}\n"
                f"IBAN: UA21322313000002600723356601\n"
                f"Получатель: Platform Services LLC\n"
                f"Назначение: Order payment\n\n"
                f"После оплаты нажмите «✅ Я оплатил»."
            )
        if method == CartPaymentMethod.USDT.value:
            return (
                f"💎 USDT (TRC20)\n\n"
                f"Сумма: {amount} {currency}\n"
                f"Адрес: TXYZplatformWalletTRC20Example\n"
                f"Сеть: TRON (TRC20)\n\n"
                f"После оплаты нажмите «✅ Я оплатил»."
            )
        if method == CartPaymentMethod.CASH.value:
            return (
                f"💵 Наличные\n\n"
                f"Сумма: {amount} {currency}\n"
                f"Офис: Киев, ул. Примерная 1\n"
                f"Часы: Пн–Пт 10:00–18:00\n\n"
                f"После оплаты нажмите «✅ Я оплатил»."
            )
        return f"Сумма: {amount} {currency}"

    @staticmethod
    def confirm_payment_keyboard(order_id: uuid.UUID) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Я оплатил",
                        callback_data=f"cart:confirm:{order_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Отменить",
                        callback_data=f"cart:cancel:{order_id}",
                    )
                ],
            ]
        )

    @staticmethod
    async def checkout(
        *,
        telegram_user_id: int,
        cart: dict[str, Any],
        payment_method: str,
        full_name: str = "",
        username: str = "",
    ) -> dict[str, Any]:
        if payment_method not in {m.value for m in CartPaymentMethod}:
            raise CartEngineV1Error(f"Unsupported payment method: {payment_method}")

        items = cart.get("items", {})
        if not items:
            raise CartEngineV1Error("Cart is empty")

        vertical = cart.get("vertical", "auto").lower()
        total = CartEngineV1.cart_total(cart)
        currency = next(iter(items.values()), {}).get("currency", "USD")
        user_id = await CartEngineV1.resolve_user_id(
            telegram_user_id,
            full_name=full_name,
            username=username,
        )
        instructions = CartEngineV1.payment_instructions(
            payment_method,
            amount=total,
            currency=currency,
        )

        async with get_session() as session:
            repo = CartEngineV1Repository(session)
            order = await repo.create_order(
                user_id=user_id,
                vertical=vertical,
                total_amount=total,
                currency=currency,
                payment_method=payment_method,
                status=CartOrderStatus.WAITING_PAYMENT.value,
                payment_instructions=instructions,
            )
            for item in items.values():
                unit_price = Decimal(item["unit_price"])
                qty = int(item.get("quantity", 1))
                await repo.add_item(
                    order_id=order.id,
                    service_code=item["code"],
                    title=item["title"],
                    unit_price=unit_price,
                    quantity=qty,
                    line_total=(unit_price * qty).quantize(_MONEY, rounding=ROUND_HALF_UP),
                )

        snapshot = await CartEngineV1._order_snapshot(order.id)
        snapshot["payment_instructions"] = instructions
        return snapshot

    @staticmethod
    async def confirm_payment(order_id: uuid.UUID) -> dict[str, Any] | None:
        async with get_session() as session:
            repo = CartEngineV1Repository(session)
            row = await repo.update_order(
                order_id,
                status=CartOrderStatus.PAID.value,
            )
        if row is None:
            return None
        return await CartEngineV1._order_snapshot(order_id)

    @staticmethod
    async def cancel_order(order_id: uuid.UUID) -> dict[str, Any] | None:
        async with get_session() as session:
            repo = CartEngineV1Repository(session)
            row = await repo.update_order(
                order_id,
                status=CartOrderStatus.CANCELLED.value,
            )
        if row is None:
            return None
        return await CartEngineV1._order_snapshot(order_id)

    @staticmethod
    async def get_owner_dashboard() -> dict[str, Any]:
        today = CartEngineV1Repository.start_of_today()
        async with get_session() as session:
            repo = CartEngineV1Repository(session)
            waiting = await repo.count_by_status(CartOrderStatus.WAITING_PAYMENT.value)
            paid_today = await repo.count_by_status(CartOrderStatus.PAID.value, since=today)
            recent = await repo.list_recent(limit=10)
        return {
            "waiting_payment": waiting,
            "paid_today": paid_today,
            "recent": [await CartEngineV1._order_snapshot(row.id) for row in recent],
        }

    @staticmethod
    def format_owner_dashboard(data: dict[str, Any]) -> str:
        lines = [
            "🛒 Cart Engine Dashboard",
            "",
            f"⏳ Waiting payment: {data['waiting_payment']}",
            f"✅ Paid today: {data['paid_today']}",
        ]
        recent = data.get("recent") or []
        if recent:
            lines.append("")
            lines.append("Recent orders:")
            for order in recent[:5]:
                lines.append(
                    f"  • {order['id'][:8]}… | {order['vertical']} | "
                    f"{order['total_amount']} {order['currency']} | {order['status']}"
                )
        return "\n".join(lines)

    @staticmethod
    async def _order_snapshot(order_id: uuid.UUID) -> dict[str, Any]:
        async with get_session() as session:
            repo = CartEngineV1Repository(session)
            order = await repo.get_order(order_id)
            if order is None:
                raise CartEngineV1Error(f"Order {order_id} not found")
            items = await repo.list_items(order_id)
        return {
            "id": str(order.id),
            "user_id": str(order.user_id),
            "vertical": order.vertical,
            "total_amount": str(order.total_amount),
            "currency": order.currency,
            "payment_method": order.payment_method,
            "status": order.status,
            "payment_instructions": order.payment_instructions,
            "items": [
                {
                    "service_code": item.service_code,
                    "title": item.title,
                    "unit_price": str(item.unit_price),
                    "quantity": item.quantity,
                    "line_total": str(item.line_total),
                }
                for item in items
            ],
            "created_at": order.created_at.isoformat() if order.created_at else None,
        }
