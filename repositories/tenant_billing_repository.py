# Tenant Billing Engine v1 repositories.

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.tenant_billing_engine import (
    BILLING_PLAN_CODES,
    USAGE_BILLING_TYPES,
    InvoiceStatus,
    SubscriptionStatus,
    TenantInvoice,
    TenantInvoiceLine,
    TenantSubscription,
    TenantUsageRecord,
)


class TenantSubscriptionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(
        self,
        *,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        plan_code: str,
        currency: str,
        current_period_start: date,
        current_period_end: date,
        status: str = SubscriptionStatus.ACTIVE.value,
        metadata: dict | None = None,
    ) -> TenantSubscription:
        if plan_code not in BILLING_PLAN_CODES:
            raise ValueError(f"Invalid plan_code: {plan_code}")
        if status not in {s.value for s in SubscriptionStatus}:
            raise ValueError(f"Invalid status: {status}")

        existing = await self.get_by_tenant(tenant_id)
        if existing is not None:
            existing.plan_code = plan_code
            existing.currency = currency
            existing.current_period_start = current_period_start
            existing.current_period_end = current_period_end
            existing.status = status
            existing.metadata_ = metadata
            await self._session.flush()
            return existing

        row = TenantSubscription(
            tenant_id=tenant_id,
            company_id=company_id,
            plan_code=plan_code,
            currency=currency,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            status=status,
            metadata_=metadata,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_by_tenant(self, tenant_id: uuid.UUID) -> TenantSubscription | None:
        result = await self._session.execute(
            select(TenantSubscription).where(TenantSubscription.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def list_active(self, *, limit: int = 200) -> list[TenantSubscription]:
        result = await self._session.execute(
            select(TenantSubscription)
            .where(TenantSubscription.status == SubscriptionStatus.ACTIVE.value)
            .order_by(TenantSubscription.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())


class TenantUsageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(
        self,
        *,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        billing_type: str,
        quantity: Decimal,
        unit_price: Decimal,
        amount: Decimal,
        recorded_at: datetime,
        reference_key: str | None = None,
        metadata: dict | None = None,
    ) -> TenantUsageRecord:
        if billing_type not in USAGE_BILLING_TYPES:
            raise ValueError(f"Invalid billing_type: {billing_type}")
        if quantity < 0 or amount < 0:
            raise ValueError("quantity and amount must be non-negative")

        if reference_key:
            existing = await self.get_by_reference(tenant_id, billing_type, reference_key)
            if existing is not None:
                return existing

        row = TenantUsageRecord(
            tenant_id=tenant_id,
            company_id=company_id,
            billing_type=billing_type,
            quantity=quantity,
            unit_price=unit_price,
            amount=amount,
            reference_key=reference_key,
            recorded_at=recorded_at,
            metadata_=metadata,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_by_reference(
        self,
        tenant_id: uuid.UUID,
        billing_type: str,
        reference_key: str,
    ) -> TenantUsageRecord | None:
        result = await self._session.execute(
            select(TenantUsageRecord).where(
                TenantUsageRecord.tenant_id == tenant_id,
                TenantUsageRecord.billing_type == billing_type,
                TenantUsageRecord.reference_key == reference_key,
            )
        )
        return result.scalar_one_or_none()

    async def list_uninvoiced(
        self,
        tenant_id: uuid.UUID,
        *,
        period_start: date,
        period_end: date,
    ) -> list[TenantUsageRecord]:
        result = await self._session.execute(
            select(TenantUsageRecord)
            .where(
                TenantUsageRecord.tenant_id == tenant_id,
                TenantUsageRecord.invoice_id.is_(None),
                func.date(TenantUsageRecord.recorded_at) >= period_start,
                func.date(TenantUsageRecord.recorded_at) <= period_end,
            )
            .order_by(TenantUsageRecord.recorded_at.asc())
        )
        return list(result.scalars().all())

    async def aggregate_uninvoiced(
        self,
        tenant_id: uuid.UUID,
        *,
        period_start: date,
        period_end: date,
    ) -> dict[str, dict[str, Decimal]]:
        result = await self._session.execute(
            select(
                TenantUsageRecord.billing_type,
                func.coalesce(func.sum(TenantUsageRecord.quantity), 0),
                func.coalesce(func.sum(TenantUsageRecord.amount), 0),
            )
            .where(
                TenantUsageRecord.tenant_id == tenant_id,
                TenantUsageRecord.invoice_id.is_(None),
                func.date(TenantUsageRecord.recorded_at) >= period_start,
                func.date(TenantUsageRecord.recorded_at) <= period_end,
            )
            .group_by(TenantUsageRecord.billing_type)
        )
        totals: dict[str, dict[str, Decimal]] = {}
        for billing_type, qty, amount in result.all():
            totals[billing_type] = {
                "quantity": Decimal(str(qty or 0)),
                "amount": Decimal(str(amount or 0)),
            }
        return totals

    async def attach_to_invoice(
        self,
        tenant_id: uuid.UUID,
        invoice_id: uuid.UUID,
        *,
        period_start: date,
        period_end: date,
    ) -> int:
        rows = await self.list_uninvoiced(
            tenant_id,
            period_start=period_start,
            period_end=period_end,
        )
        for row in rows:
            row.invoice_id = invoice_id
        await self._session.flush()
        return len(rows)


class TenantInvoiceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        invoice_number: str,
        period_start: date,
        period_end: date,
        currency: str,
        subtotal: Decimal,
        tax: Decimal,
        total: Decimal,
        issued_at: datetime,
        due_at: datetime | None = None,
        generated_by: int | None = None,
        status: str = InvoiceStatus.ISSUED.value,
        metadata: dict | None = None,
    ) -> TenantInvoice:
        if status not in {s.value for s in InvoiceStatus}:
            raise ValueError(f"Invalid status: {status}")

        invoice = TenantInvoice(
            tenant_id=tenant_id,
            company_id=company_id,
            invoice_number=invoice_number,
            period_start=period_start,
            period_end=period_end,
            currency=currency,
            subtotal=subtotal,
            tax=tax,
            total=total,
            issued_at=issued_at,
            due_at=due_at,
            generated_by=generated_by,
            status=status,
            metadata_=metadata,
        )
        self._session.add(invoice)
        await self._session.flush()
        return invoice

    async def get_by_id(self, invoice_id: uuid.UUID) -> TenantInvoice | None:
        result = await self._session.execute(
            select(TenantInvoice).where(TenantInvoice.id == invoice_id)
        )
        return result.scalar_one_or_none()

    async def get_by_number(self, invoice_number: str) -> TenantInvoice | None:
        result = await self._session.execute(
            select(TenantInvoice).where(TenantInvoice.invoice_number == invoice_number)
        )
        return result.scalar_one_or_none()

    async def list_by_tenant(
        self,
        tenant_id: uuid.UUID,
        *,
        limit: int = 50,
    ) -> list[TenantInvoice]:
        result = await self._session.execute(
            select(TenantInvoice)
            .where(TenantInvoice.tenant_id == tenant_id)
            .order_by(TenantInvoice.issued_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_for_period_prefix(self, prefix: str) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(TenantInvoice)
            .where(TenantInvoice.invoice_number.like(f"{prefix}%"))
        )
        return int(result.scalar_one() or 0)


class TenantInvoiceLineRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        invoice_id: uuid.UUID,
        line_type: str,
        description: str,
        quantity: Decimal,
        unit_price: Decimal,
        amount: Decimal,
        metadata: dict | None = None,
    ) -> TenantInvoiceLine:
        line = TenantInvoiceLine(
            invoice_id=invoice_id,
            line_type=line_type,
            description=description,
            quantity=quantity,
            unit_price=unit_price,
            amount=amount,
            metadata_=metadata,
        )
        self._session.add(line)
        await self._session.flush()
        return line

    async def list_by_invoice(self, invoice_id: uuid.UUID) -> list[TenantInvoiceLine]:
        result = await self._session.execute(
            select(TenantInvoiceLine)
            .where(TenantInvoiceLine.invoice_id == invoice_id)
            .order_by(TenantInvoiceLine.created_at.asc())
        )
        return list(result.scalars().all())
