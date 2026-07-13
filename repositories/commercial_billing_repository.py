# Commercial Billing Engine v1 repositories.

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.commercial_billing_engine import (
    PAYMENT_METHODS,
    PAYMENT_STATUSES,
    PRICING_MODELS,
    BillingEvent,
    CommercialPayment,
    PaymentReceipt,
    PaymentStatus,
    SubscriptionHistory,
)


class CommercialPaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: int,
        plan_code: str,
        pricing_model: str,
        payment_method: str,
        amount: Decimal | None = None,
        currency: str = "USD",
        tenant_id: uuid.UUID | None = None,
        company_id: uuid.UUID | None = None,
        metadata: dict | None = None,
        **extra: Any,
    ) -> CommercialPayment:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if pricing_model not in PRICING_MODELS:
            raise ValueError(f"Invalid pricing_model: {pricing_model}")
        if payment_method not in PAYMENT_METHODS:
            raise ValueError(f"Invalid payment_method: {payment_method}")

        row = CommercialPayment(
            user_id=user_id,
            tenant_id=tenant_id,
            company_id=company_id,
            plan_code=plan_code,
            pricing_model=pricing_model,
            payment_method=payment_method,
            amount=amount,
            currency=currency,
            metadata_=metadata,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_by_id(self, payment_id: uuid.UUID) -> CommercialPayment | None:
        result = await self._session.execute(
            select(CommercialPayment).where(CommercialPayment.id == payment_id)
        )
        return result.scalar_one_or_none()

    async def list_pending(self, *, limit: int = 50) -> list[CommercialPayment]:
        result = await self._session.execute(
            select(CommercialPayment)
            .where(CommercialPayment.status == PaymentStatus.PENDING.value)
            .order_by(CommercialPayment.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_by_user(self, user_id: int, *, limit: int = 20) -> list[CommercialPayment]:
        result = await self._session.execute(
            select(CommercialPayment)
            .where(CommercialPayment.user_id == user_id)
            .order_by(CommercialPayment.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_fields(self, payment_id: uuid.UUID, **fields: Any) -> CommercialPayment | None:
        row = await self.get_by_id(payment_id)
        if row is None:
            return None
        allowed = {
            "status",
            "tenant_id",
            "company_id",
            "subscription_id",
            "reviewed_by",
            "reviewed_at",
            "review_notes",
            "metadata_",
        }
        for key, value in fields.items():
            attr = "metadata_" if key == "metadata" else key
            if attr not in allowed:
                raise TypeError(f"Unsupported field: {key}")
            setattr(row, attr, value)
        await self._session.flush()
        return row


class PaymentReceiptRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        payment_id: uuid.UUID,
        uploaded_by: int,
        telegram_file_id: str,
        telegram_file_unique_id: str | None = None,
        mime_type: str | None = None,
        storage_path: str | None = None,
        metadata: dict | None = None,
    ) -> PaymentReceipt:
        row = PaymentReceipt(
            payment_id=payment_id,
            uploaded_by=uploaded_by,
            telegram_file_id=telegram_file_id,
            telegram_file_unique_id=telegram_file_unique_id,
            mime_type=mime_type,
            storage_path=storage_path,
            metadata_=metadata,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_by_payment(self, payment_id: uuid.UUID) -> PaymentReceipt | None:
        result = await self._session.execute(
            select(PaymentReceipt).where(PaymentReceipt.payment_id == payment_id)
        )
        return result.scalar_one_or_none()


class SubscriptionHistoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        event_type: str,
        subscription_id: uuid.UUID | None = None,
        tenant_id: uuid.UUID | None = None,
        old_value: dict | None = None,
        new_value: dict | None = None,
        actor_id: int | None = None,
        notes: str | None = None,
    ) -> SubscriptionHistory:
        row = SubscriptionHistory(
            subscription_id=subscription_id,
            tenant_id=tenant_id,
            event_type=event_type,
            old_value=old_value,
            new_value=new_value,
            actor_id=actor_id,
            notes=notes,
        )
        self._session.add(row)
        await self._session.flush()
        return row


class BillingEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        event_type: str,
        entity_type: str,
        entity_id: str,
        tenant_id: uuid.UUID | None = None,
        actor_id: int | None = None,
        payload: dict | None = None,
    ) -> BillingEvent:
        row = BillingEvent(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            tenant_id=tenant_id,
            actor_id=actor_id,
            payload=payload,
        )
        self._session.add(row)
        await self._session.flush()
        return row
