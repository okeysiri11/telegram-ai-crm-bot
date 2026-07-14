# Manual Payment Verification Engine v1 — instructions, workflow, deal + revenue hook.

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.models.cart_engine_v1 import CartOrderStatus
from database.models.crm_pipeline_boards_v1 import CrmPipelineEntityType
from database.models.deal_engine_v1 import DealEngineV1Status
from database.models.payment_engine_v1 import (
    PAYMENT_ENGINE_METHODS,
    PaymentEngineMethod,
    PaymentEngineStatus,
)
from database.session import get_session
from repositories.cart_engine_v1_repository import CartEngineV1Repository
from repositories.payment_engine_v1_repository import PaymentEngineV1Repository

logger = logging.getLogger(__name__)

_PAYMENT_METHOD_LABELS: dict[str, dict[str, str]] = {
    "CARD": {"ru": "💳 Карта", "uk": "💳 Картка"},
    "IBAN": {"ru": "🏦 IBAN", "uk": "🏦 IBAN"},
    "USDT_TRC20": {"ru": "💎 USDT TRC20", "uk": "💎 USDT TRC20"},
    "USDT_ERC20": {"ru": "💎 USDT ERC20", "uk": "💎 USDT ERC20"},
    "CASH": {"ru": "💵 Наличные", "uk": "💵 Готівка"},
}

PAYMENT_UPLOADED_MESSAGE = (
    "Скриншот оплаты получен.\n"
    "Менеджер проверит платёж и подтвердит заказ в ближайшее время."
)

PAYMENT_CONFIRMED_MESSAGE = (
    "Оплата подтверждена.\n"
    "Наш менеджер свяжется с вами в ближайшее время и приступит к обработке заказа."
)

PAYMENT_REJECTED_MESSAGE = (
    "Оплата не подтверждена.\n"
    "Пожалуйста, проверьте реквизиты и отправьте скриншот повторно или свяжитесь с менеджером."
)


class PaymentEngineV1Error(Exception):
    pass


class PaymentEngineV1:
    @staticmethod
    def payment_methods_keyboard(*, lang: str | None = None) -> InlineKeyboardMarkup:
        from services.automotive_localization import normalize_language

        language = normalize_language(lang)
        rows = []
        for method in PaymentEngineMethod:
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
        if method == PaymentEngineMethod.CARD.value:
            return (
                f"💳 Оплата картой\n\n"
                f"Сумма: {amount} {currency}\n"
                f"Карта: 5375 4141 0000 0000\n"
                f"Получатель: Platform Services LLC\n"
                f"Назначение: Order payment\n\n"
                f"После оплаты отправьте скриншот перевода в этот чат."
            )
        if method == PaymentEngineMethod.IBAN.value:
            return (
                f"🏦 Банковский перевод (IBAN)\n\n"
                f"Сумма: {amount} {currency}\n"
                f"IBAN: UA21322313000002600723356601\n"
                f"Получатель: Platform Services LLC\n"
                f"Назначение: Order payment\n\n"
                f"После оплаты отправьте скриншот перевода в этот чат."
            )
        if method == PaymentEngineMethod.USDT_TRC20.value:
            return (
                f"💎 USDT (TRC20)\n\n"
                f"Сумма: {amount} {currency}\n"
                f"Адрес: TXYZplatformWalletTRC20Example\n"
                f"Сеть: TRON (TRC20)\n\n"
                f"После оплаты отправьте скриншот перевода в этот чат."
            )
        if method == PaymentEngineMethod.USDT_ERC20.value:
            return (
                f"💎 USDT (ERC20)\n\n"
                f"Сумма: {amount} {currency}\n"
                f"Адрес: 0xPlatformWalletERC20Example\n"
                f"Сеть: Ethereum (ERC20)\n\n"
                f"После оплаты отправьте скриншот перевода в этот чат."
            )
        if method == PaymentEngineMethod.CASH.value:
            return (
                f"💵 Наличные\n\n"
                f"Сумма: {amount} {currency}\n"
                f"Офис: Киев, ул. Примерная 1\n"
                f"Часы: Пн–Пт 10:00–18:00\n\n"
                f"После оплаты отправьте фото чека или квитанции в этот чат."
            )
        return f"Сумма: {amount} {currency}"

    @staticmethod
    def manager_review_keyboard(payment_id: uuid.UUID) -> InlineKeyboardMarkup:
        pid = str(payment_id)
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Подтвердить",
                        callback_data=f"pay:confirm:{pid}",
                    ),
                    InlineKeyboardButton(
                        text="❌ Отклонить",
                        callback_data=f"pay:reject:{pid}",
                    ),
                ],
            ]
        )

    @staticmethod
    async def create_from_order(order_id: uuid.UUID) -> dict[str, Any]:
        async with get_session() as session:
            cart_repo = CartEngineV1Repository(session)
            pay_repo = PaymentEngineV1Repository(session)

            order = await cart_repo.get_order(order_id)
            if order is None:
                raise PaymentEngineV1Error(f"Order {order_id} not found")
            if not order.payment_method or order.payment_method not in PAYMENT_ENGINE_METHODS:
                raise PaymentEngineV1Error(f"Unsupported payment method: {order.payment_method}")

            existing = await pay_repo.get_by_order(order_id)
            if existing is not None:
                return PaymentEngineV1._snapshot(existing)

            row = await pay_repo.create(
                order_id=order.id,
                client_id=order.user_id,
                amount=order.total_amount,
                currency=order.currency,
                payment_method=order.payment_method,
                status=PaymentEngineStatus.WAITING_PAYMENT.value,
            )
        return PaymentEngineV1._snapshot(row)

    @staticmethod
    async def upload_screenshot(
        payment_id: uuid.UUID,
        screenshot_file_id: str,
        *,
        payment_reference: str | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        async with get_session() as session:
            repo = PaymentEngineV1Repository(session)
            row = await repo.get_by_id(payment_id)
            if row is None:
                raise PaymentEngineV1Error(f"Payment {payment_id} not found")
            if row.status not in {
                PaymentEngineStatus.WAITING_PAYMENT.value,
                PaymentEngineStatus.PAYMENT_UPLOADED.value,
                PaymentEngineStatus.UNDER_REVIEW.value,
                PaymentEngineStatus.REJECTED.value,
            }:
                raise PaymentEngineV1Error(f"Payment cannot accept upload in status {row.status}")

            row = await repo.update(
                payment_id,
                screenshot_file_id=screenshot_file_id,
                payment_reference=payment_reference,
                uploaded_at=now,
                status=PaymentEngineStatus.PAYMENT_UPLOADED.value,
            )
        if row is None:
            raise PaymentEngineV1Error(f"Payment {payment_id} not found")
        snapshot = PaymentEngineV1._snapshot(row)
        snapshot["order"] = await PaymentEngineV1._order_context(row.order_id)
        return snapshot

    @staticmethod
    async def confirm_payment(
        payment_id: uuid.UUID,
        verified_by: uuid.UUID,
        *,
        moved_by_telegram: int,
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        async with get_session() as session:
            pay_repo = PaymentEngineV1Repository(session)
            cart_repo = CartEngineV1Repository(session)

            payment = await pay_repo.get_by_id(payment_id)
            if payment is None:
                raise PaymentEngineV1Error(f"Payment {payment_id} not found")
            if payment.status not in {
                PaymentEngineStatus.PAYMENT_UPLOADED.value,
                PaymentEngineStatus.UNDER_REVIEW.value,
            }:
                raise PaymentEngineV1Error(f"Payment cannot be confirmed from status {payment.status}")

            order = await cart_repo.get_order(payment.order_id)
            if order is None:
                raise PaymentEngineV1Error(f"Order {payment.order_id} not found")

            await cart_repo.update_order(
                payment.order_id,
                status=CartOrderStatus.PAID.value,
            )
            payment = await pay_repo.update(
                payment_id,
                status=PaymentEngineStatus.CONFIRMED.value,
                verified_at=now,
                verified_by=verified_by,
            )

        deal_snapshot = await PaymentEngineV1._complete_order_deal(
            order_id=payment.order_id,
            client_id=payment.client_id,
            amount=payment.amount,
            currency=payment.currency,
            moved_by_telegram=moved_by_telegram,
        )

        async with get_session() as session:
            payment = await PaymentEngineV1Repository(session).update(
                payment_id,
                deal_id=uuid.UUID(deal_snapshot["id"]),
            )

        snapshot = PaymentEngineV1._snapshot(payment)
        snapshot["deal"] = deal_snapshot
        return snapshot

    @staticmethod
    async def reject_payment(
        payment_id: uuid.UUID,
        verified_by: uuid.UUID,
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        async with get_session() as session:
            repo = PaymentEngineV1Repository(session)
            payment = await repo.get_by_id(payment_id)
            if payment is None:
                raise PaymentEngineV1Error(f"Payment {payment_id} not found")
            if payment.status not in {
                PaymentEngineStatus.PAYMENT_UPLOADED.value,
                PaymentEngineStatus.UNDER_REVIEW.value,
            }:
                raise PaymentEngineV1Error(f"Payment cannot be rejected from status {payment.status}")

            row = await repo.update(
                payment_id,
                status=PaymentEngineStatus.REJECTED.value,
                verified_at=now,
                verified_by=verified_by,
            )
        return PaymentEngineV1._snapshot(row)

    @staticmethod
    async def get_by_id(payment_id: uuid.UUID) -> dict[str, Any] | None:
        async with get_session() as session:
            row = await PaymentEngineV1Repository(session).get_by_id(payment_id)
        if row is None:
            return None
        snapshot = PaymentEngineV1._snapshot(row)
        snapshot["order"] = await PaymentEngineV1._order_context(row.order_id)
        return snapshot

    @staticmethod
    async def get_owner_metrics() -> dict[str, Any]:
        async with get_session() as session:
            repo = PaymentEngineV1Repository(session)
            pending = await repo.count_pending()
            confirmed = await repo.count_by_status(PaymentEngineStatus.CONFIRMED.value)
            rejected = await repo.count_by_status(PaymentEngineStatus.REJECTED.value)
            pending_list = await repo.list_pending_review(limit=8)
            confirmed_list = await repo.list_by_status(
                PaymentEngineStatus.CONFIRMED.value,
                limit=5,
            )
            rejected_list = await repo.list_by_status(
                PaymentEngineStatus.REJECTED.value,
                limit=5,
            )
        return {
            "pending": pending,
            "confirmed": confirmed,
            "rejected": rejected,
            "pending_list": [PaymentEngineV1._snapshot(p) for p in pending_list],
            "confirmed_list": [PaymentEngineV1._snapshot(p) for p in confirmed_list],
            "rejected_list": [PaymentEngineV1._snapshot(p) for p in rejected_list],
        }

    @staticmethod
    def format_owner_payment_analytics(metrics: dict[str, Any]) -> str:
        lines = [
            "💳 Payment Analytics",
            "",
            f"⏳ Pending: {metrics['pending']}",
            f"✅ Confirmed: {metrics['confirmed']}",
            f"❌ Rejected: {metrics['rejected']}",
        ]
        pending = metrics.get("pending_list") or []
        if pending:
            lines.append("")
            lines.append("Pending review:")
            for p in pending[:5]:
                lines.append(
                    f"  • {p['id'][:8]}… | {p['amount']} {p['currency']} | {p['payment_method']}"
                )
        return "\n".join(lines)

    @staticmethod
    def format_manager_notification(payment: dict[str, Any]) -> str:
        order = payment.get("order") or {}
        items = order.get("items") or []
        item_lines = "\n".join(f"  • {i['title']} × {i['quantity']}" for i in items[:5])
        return (
            "💳 Новый платёж на проверку\n\n"
            f"ID: {payment['id']}\n"
            f"Сумма: {payment['amount']} {payment['currency']}\n"
            f"Метод: {payment['payment_method']}\n"
            f"Клиент: {payment['client_id'][:8]}…\n"
            f"Заказ: {payment['order_id'][:8]}…\n"
            f"{item_lines or '  • —'}"
        )

    @staticmethod
    async def _complete_order_deal(
        *,
        order_id: uuid.UUID,
        client_id: uuid.UUID,
        amount: Decimal,
        currency: str,
        moved_by_telegram: int,
    ) -> dict[str, Any]:
        from services.pg_crm_pipeline_boards_engine import CrmPipelineBoardsEngineV1
        from services.pg_deal_engine_v1 import DealEngineV1

        order_ctx = await PaymentEngineV1._order_context(order_id)
        vertical = order_ctx.get("vertical", "auto")
        items = order_ctx.get("items") or []
        title = ", ".join(i["title"] for i in items[:3]) or f"Cart order {str(order_id)[:8]}"

        deal = await DealEngineV1.create_deal(
            vertical=vertical,
            client_id=client_id,
            title=title,
            amount=amount,
            currency=currency,
            description=f"Payment confirmed for cart order {order_id}",
        )
        deal_id = uuid.UUID(deal["id"])

        win_stage = "WON" if vertical == "auto" else "CLOSED"
        try:
            await CrmPipelineBoardsEngineV1.move_entity(
                vertical=vertical,
                entity_type=CrmPipelineEntityType.DEAL.value,
                entity_id=deal_id,
                new_stage=win_stage,
                moved_by=moved_by_telegram,
            )
        except Exception:
            logger.exception("Pipeline move failed for deal %s", deal_id)

        completed = await DealEngineV1.update_status(deal_id, DealEngineV1Status.COMPLETED.value)
        if completed is None:
            raise PaymentEngineV1Error(f"Failed to complete deal {deal_id}")
        return completed

    @staticmethod
    async def _order_context(order_id: uuid.UUID) -> dict[str, Any]:
        async with get_session() as session:
            cart_repo = CartEngineV1Repository(session)
            order = await cart_repo.get_order(order_id)
            if order is None:
                return {}
            items = await cart_repo.list_items(order_id)
        return {
            "id": str(order.id),
            "vertical": order.vertical,
            "total_amount": str(order.total_amount),
            "currency": order.currency,
            "payment_method": order.payment_method,
            "status": order.status,
            "items": [
                {
                    "service_code": item.service_code,
                    "title": item.title,
                    "quantity": item.quantity,
                    "line_total": str(item.line_total),
                }
                for item in items
            ],
        }

    @staticmethod
    def _snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "order_id": str(row.order_id),
            "client_id": str(row.client_id),
            "deal_id": str(row.deal_id) if row.deal_id else None,
            "amount": str(row.amount),
            "currency": row.currency,
            "payment_method": row.payment_method,
            "payment_reference": row.payment_reference,
            "screenshot_file_id": row.screenshot_file_id,
            "uploaded_at": row.uploaded_at.isoformat() if row.uploaded_at else None,
            "verified_at": row.verified_at.isoformat() if row.verified_at else None,
            "verified_by": str(row.verified_by) if row.verified_by else None,
            "status": row.status,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
