# Commercial Billing Engine v1 — onboarding payments, receipts, activation.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from config import OWNER_ID
from database.models.commercial_billing_engine import (
    BillingEventType,
    PaymentMethod,
    PaymentStatus,
    PricingModel,
)
from database.models.tenant_billing_engine import BillingPlanCode
from database.session import get_session
from repositories.commercial_billing_repository import (
    BillingEventRepository,
    CommercialPaymentRepository,
    PaymentReceiptRepository,
    SubscriptionHistoryRepository,
)
from services.automotive_telegram_access import is_billing_owner
from services.pg_multi_tenant_foundation_engine import MultiTenantFoundationEngineV1
from services.pg_partner_tenant_engine import PartnerTenantEngineV1
from services.pg_tenant_billing_engine import PLAN_CATALOG, TenantBillingEngineV1

PLAN_MARKETING: dict[str, str] = {
    BillingPlanCode.STARTER.value: (
        "STARTER\n"
        "• 1 channel\n"
        "• up to 20 leads/month"
    ),
    BillingPlanCode.PRO.value: (
        "PRO\n"
        "• up to 5 channels\n"
        "• AI Sales Agent\n"
        "• Analytics"
    ),
    BillingPlanCode.BUSINESS.value: (
        "BUSINESS\n"
        "• unlimited channels\n"
        "• AI ecosystem access"
    ),
    BillingPlanCode.ENTERPRISE.value: (
        "ENTERPRISE\n"
        "• custom plan\n"
        "• dedicated support"
    ),
}

PRICING_MODEL_LABELS: dict[str, str] = {
    PricingModel.SUBSCRIPTION.value: "Subscription",
    PricingModel.PER_LEAD.value: "Per Lead",
    PricingModel.REVENUE_SHARE.value: "Revenue Share",
    PricingModel.HYBRID.value: "Hybrid",
    PricingModel.CUSTOM.value: "Custom Plan",
}

PAYMENT_METHOD_LABELS: dict[str, str] = {
    PaymentMethod.BANK_CARD.value: "Bank Card",
    PaymentMethod.BANK_TRANSFER.value: "Bank Transfer",
    PaymentMethod.USDT_TRC20.value: "USDT TRC20",
    PaymentMethod.USDT_ERC20.value: "USDT ERC20",
}


class CommercialBillingEngineError(Exception):
    pass


class CommercialBillingEngineV1:
    @staticmethod
    def list_plans_text() -> str:
        return "\n\n".join(PLAN_MARKETING[code] for code in PLAN_MARKETING)

    @staticmethod
    def _payment_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "user_id": row.user_id,
            "tenant_id": str(row.tenant_id) if row.tenant_id else None,
            "plan_code": row.plan_code,
            "pricing_model": row.pricing_model,
            "payment_method": row.payment_method,
            "amount": str(row.amount) if row.amount is not None else None,
            "currency": row.currency,
            "status": row.status,
            "created_at": row.created_at.isoformat(),
        }

    @staticmethod
    async def create_payment_intent(
        user_id: int,
        *,
        plan_code: str,
        pricing_model: str,
        payment_method: str,
        tenant_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        if plan_code not in PLAN_CATALOG:
            raise CommercialBillingEngineError(f"Unknown plan: {plan_code}")
        amount = PLAN_CATALOG[plan_code].monthly_fee

        async with get_session() as session:
            payment = await CommercialPaymentRepository(session).create(
                user_id=user_id,
                plan_code=plan_code,
                pricing_model=pricing_model,
                payment_method=payment_method,
                amount=amount,
                tenant_id=tenant_id,
            )
            await BillingEventRepository(session).create(
                event_type=BillingEventType.PAYMENT_SUBMITTED.value,
                entity_type="payment",
                entity_id=str(payment.id),
                actor_id=user_id,
                payload={"plan_code": plan_code, "pricing_model": pricing_model},
            )
            await session.refresh(payment)
            return CommercialBillingEngineV1._payment_snapshot(payment)

    @staticmethod
    async def attach_receipt(
        user_id: int,
        payment_id: uuid.UUID,
        *,
        telegram_file_id: str,
        telegram_file_unique_id: str | None = None,
        mime_type: str | None = None,
    ) -> dict[str, Any]:
        async with get_session() as session:
            payment = await CommercialPaymentRepository(session).get_by_id(payment_id)
            if payment is None or payment.user_id != user_id:
                raise CommercialBillingEngineError("Payment not found")
            if payment.status != PaymentStatus.PENDING.value:
                raise CommercialBillingEngineError("Payment is not pending")

            receipt = await PaymentReceiptRepository(session).create(
                payment_id=payment_id,
                uploaded_by=user_id,
                telegram_file_id=telegram_file_id,
                telegram_file_unique_id=telegram_file_unique_id,
                mime_type=mime_type,
            )
            await BillingEventRepository(session).create(
                event_type=BillingEventType.PAYMENT_SUBMITTED.value,
                entity_type="payment_receipt",
                entity_id=str(receipt.id),
                actor_id=user_id,
                payload={"payment_id": str(payment_id)},
            )
            await session.refresh(receipt)
            return {
                "payment_id": str(payment_id),
                "receipt_id": str(receipt.id),
                "status": payment.status,
            }

    @staticmethod
    async def get_user_subscription_view(user_id: int) -> dict[str, Any]:
        async with get_session() as session:
            payments = await CommercialPaymentRepository(session).list_by_user(user_id, limit=5)
        active = next((p for p in payments if p.status == PaymentStatus.APPROVED.value), None)
        pending = next((p for p in payments if p.status == PaymentStatus.PENDING.value), None)
        return {
            "payments": [CommercialBillingEngineV1._payment_snapshot(p) for p in payments],
            "active_payment": (
                CommercialBillingEngineV1._payment_snapshot(active) if active else None
            ),
            "pending_payment": (
                CommercialBillingEngineV1._payment_snapshot(pending) if pending else None
            ),
        }

    @staticmethod
    async def approve_payment(actor_id: int, payment_id: uuid.UUID) -> dict[str, Any]:
        if not await is_billing_owner(actor_id):
            raise CommercialBillingEngineError("Owner approval required")

        now = datetime.now(timezone.utc)
        async with get_session() as session:
            payment = await CommercialPaymentRepository(session).get_by_id(payment_id)
            if payment is None:
                raise CommercialBillingEngineError("Payment not found")
            if payment.status != PaymentStatus.PENDING.value:
                raise CommercialBillingEngineError(f"Payment status: {payment.status}")

            tenant_id = payment.tenant_id
            company_id = payment.company_id
            if tenant_id is None:
                tenant = await PartnerTenantEngineV1.create_tenant(
                    actor_id,
                    company_id=await CommercialBillingEngineV1._default_company_id(session),
                    code=f"client_{payment.user_id}",
                    name=f"Automotive Client {payment.user_id}",
                    provision_billing=True,
                )
                tenant_id = uuid.UUID(tenant["tenant_id"])
                company_id = uuid.UUID(tenant["company_id"])

            subscription = await TenantBillingEngineV1.subscribe_tenant(
                actor_id,
                tenant_id,
                plan_code=payment.plan_code,
            )

            updated = await CommercialPaymentRepository(session).update_fields(
                payment_id,
                status=PaymentStatus.APPROVED.value,
                tenant_id=tenant_id,
                company_id=company_id,
                subscription_id=uuid.UUID(subscription["id"]),
                reviewed_by=actor_id,
                reviewed_at=now,
            )
            await SubscriptionHistoryRepository(session).create(
                event_type=BillingEventType.SUBSCRIPTION_ACTIVATED.value,
                subscription_id=uuid.UUID(subscription["id"]),
                tenant_id=tenant_id,
                new_value=subscription,
                actor_id=actor_id,
                notes="Activated via Telegram payment approval",
            )
            await BillingEventRepository(session).create(
                event_type=BillingEventType.PAYMENT_APPROVED.value,
                entity_type="payment",
                entity_id=str(payment_id),
                tenant_id=tenant_id,
                actor_id=actor_id,
                payload={"subscription_id": subscription["id"]},
            )
            await BillingEventRepository(session).create(
                event_type=BillingEventType.TENANT_ACTIVATED.value,
                entity_type="tenant",
                entity_id=str(tenant_id),
                tenant_id=tenant_id,
                actor_id=actor_id,
            )
            await session.refresh(updated)
            result = {
                "payment": CommercialBillingEngineV1._payment_snapshot(updated),
                "subscription": subscription,
                "tenant_id": str(tenant_id),
                "client_user_id": payment.user_id,
                "plan_code": payment.plan_code,
                "company_id": str(company_id),
            }

        await MultiTenantFoundationEngineV1.sync_tenant_from_partner(
            tenant_id=tenant_id,
            company_id=company_id,
            code=f"client_{result['client_user_id']}",
            name=f"Automotive Client {result['client_user_id']}",
            plan_code=result["plan_code"],
            member_user_id=result["client_user_id"],
        )
        return {
            "payment": result["payment"],
            "subscription": result["subscription"],
            "tenant_id": result["tenant_id"],
        }

    @staticmethod
    async def reject_payment(
        actor_id: int,
        payment_id: uuid.UUID,
        *,
        notes: str | None = None,
    ) -> dict[str, Any]:
        if not await is_billing_owner(actor_id):
            raise CommercialBillingEngineError("Owner approval required")

        now = datetime.now(timezone.utc)
        async with get_session() as session:
            payment = await CommercialPaymentRepository(session).get_by_id(payment_id)
            if payment is None:
                raise CommercialBillingEngineError("Payment not found")
            updated = await CommercialPaymentRepository(session).update_fields(
                payment_id,
                status=PaymentStatus.REJECTED.value,
                reviewed_by=actor_id,
                reviewed_at=now,
                review_notes=notes,
            )
            await BillingEventRepository(session).create(
                event_type=BillingEventType.PAYMENT_REJECTED.value,
                entity_type="payment",
                entity_id=str(payment_id),
                actor_id=actor_id,
                payload={"notes": notes},
            )
            await session.refresh(updated)
            return CommercialBillingEngineV1._payment_snapshot(updated)

    @staticmethod
    async def _default_company_id(session) -> uuid.UUID:
        from sqlalchemy import select

        from database.models.multi_company import Company

        result = await session.execute(select(Company).limit(1))
        company = result.scalar_one_or_none()
        if company is None:
            raise CommercialBillingEngineError("No company configured")
        return company.id

    @staticmethod
    async def list_pending_for_owner(actor_id: int) -> list[dict[str, Any]]:
        if not await is_billing_owner(actor_id):
            raise CommercialBillingEngineError("Owner access required")
        async with get_session() as session:
            rows = await CommercialPaymentRepository(session).list_pending()
            return [CommercialBillingEngineV1._payment_snapshot(r) for r in rows]
