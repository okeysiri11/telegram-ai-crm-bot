# Automotive Revenue Engine v1 repository.

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.automotive_revenue_engine import (
    AutomotiveDealCommission,
    AutomotiveDealProfit,
    AutomotiveDealerReferral,
    AutomotivePartnerCommission,
    AutomotivePartnerLead,
    AutomotivePartnerSettlement,
    CommissionStatus,
    SettlementStatus,
)


class AutomotiveRevenueRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_partner_lead(
        self,
        *,
        tenant_id: uuid.UUID | None,
        partner_id: uuid.UUID,
        lead_id: uuid.UUID,
        source_id: str | None,
        vertical: str,
        commission_amount: Decimal,
        commission_status: str = CommissionStatus.PENDING.value,
        payload: dict | None = None,
    ) -> AutomotivePartnerLead:
        row = AutomotivePartnerLead(
            tenant_id=tenant_id,
            partner_id=partner_id,
            lead_id=lead_id,
            source_id=source_id,
            vertical=vertical,
            commission_amount=commission_amount,
            commission_status=commission_status,
            payload=payload,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def create_partner_commission(
        self,
        *,
        tenant_id: uuid.UUID | None,
        partner_id: uuid.UUID,
        lead_id: uuid.UUID | None,
        partner_lead_id: uuid.UUID | None,
        source_id: str | None,
        service_type: str,
        commission_amount: Decimal,
        commission_status: str = CommissionStatus.PENDING.value,
        rate_pct: Decimal | None = None,
        deal_id: uuid.UUID | None = None,
        payload: dict | None = None,
    ) -> AutomotivePartnerCommission:
        row = AutomotivePartnerCommission(
            tenant_id=tenant_id,
            partner_id=partner_id,
            lead_id=lead_id,
            partner_lead_id=partner_lead_id,
            source_id=source_id,
            service_type=service_type,
            commission_amount=commission_amount,
            commission_status=commission_status,
            rate_pct=rate_pct,
            deal_id=deal_id,
            payload=payload,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def create_dealer_referral(
        self,
        *,
        tenant_id: uuid.UUID | None,
        partner_id: uuid.UUID,
        lead_id: uuid.UUID,
        source_id: str | None,
        referrer_user_id: int | None,
        customer_name: str,
        commission_amount: Decimal,
        payload: dict | None = None,
    ) -> AutomotiveDealerReferral:
        row = AutomotiveDealerReferral(
            tenant_id=tenant_id,
            partner_id=partner_id,
            lead_id=lead_id,
            source_id=source_id,
            referrer_user_id=referrer_user_id,
            customer_name=customer_name,
            commission_amount=commission_amount,
            payload=payload,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def upsert_deal_profit(
        self,
        *,
        tenant_id: uuid.UUID | None,
        deal_id: uuid.UUID | None,
        lead_id: uuid.UUID | None,
        revenue: Decimal,
        cost: Decimal,
        period_month: str | None,
        payload: dict | None = None,
    ) -> AutomotiveDealProfit:
        profit = revenue - cost
        margin = (profit / revenue * Decimal("100")) if revenue > 0 else Decimal("0")
        row = AutomotiveDealProfit(
            tenant_id=tenant_id,
            deal_id=deal_id,
            lead_id=lead_id,
            revenue=revenue,
            cost=cost,
            profit=profit,
            margin_pct=margin,
            period_month=period_month,
            payload=payload,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def create_deal_commission(
        self,
        *,
        tenant_id: uuid.UUID | None,
        deal_id: uuid.UUID | None,
        partner_id: uuid.UUID | None,
        lead_id: uuid.UUID | None,
        source_id: str | None,
        service_type: str,
        commission_amount: Decimal,
        payload: dict | None = None,
    ) -> AutomotiveDealCommission:
        row = AutomotiveDealCommission(
            tenant_id=tenant_id,
            deal_id=deal_id,
            partner_id=partner_id,
            lead_id=lead_id,
            source_id=source_id,
            service_type=service_type,
            commission_amount=commission_amount,
            payload=payload,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_pending_commissions(
        self,
        *,
        tenant_id: uuid.UUID | None = None,
        limit: int = 50,
    ) -> list[AutomotivePartnerCommission]:
        stmt = (
            select(AutomotivePartnerCommission)
            .where(AutomotivePartnerCommission.commission_status == CommissionStatus.PENDING.value)
            .order_by(AutomotivePartnerCommission.created_at.desc())
            .limit(limit)
        )
        if tenant_id:
            stmt = stmt.where(AutomotivePartnerCommission.tenant_id == tenant_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_settlements(
        self,
        *,
        tenant_id: uuid.UUID | None = None,
        limit: int = 20,
    ) -> list[AutomotivePartnerSettlement]:
        stmt = (
            select(AutomotivePartnerSettlement)
            .order_by(AutomotivePartnerSettlement.created_at.desc())
            .limit(limit)
        )
        if tenant_id:
            stmt = stmt.where(AutomotivePartnerSettlement.tenant_id == tenant_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create_settlement(
        self,
        *,
        tenant_id: uuid.UUID | None,
        partner_id: uuid.UUID,
        period_start: datetime,
        period_end: datetime,
        total_amount: Decimal,
        currency: str = "UAH",
    ) -> AutomotivePartnerSettlement:
        row = AutomotivePartnerSettlement(
            tenant_id=tenant_id,
            partner_id=partner_id,
            period_start=period_start,
            period_end=period_end,
            total_amount=total_amount,
            currency=currency,
            status=SettlementStatus.OPEN.value,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def sum_commissions_by_partner(
        self,
        *,
        tenant_id: uuid.UUID | None = None,
    ) -> list[tuple[uuid.UUID, Decimal]]:
        stmt = select(
            AutomotivePartnerCommission.partner_id,
            func.coalesce(func.sum(AutomotivePartnerCommission.commission_amount), 0),
        ).group_by(AutomotivePartnerCommission.partner_id)
        if tenant_id:
            stmt = stmt.where(AutomotivePartnerCommission.tenant_id == tenant_id)
        result = await self._session.execute(stmt)
        return [(row[0], Decimal(str(row[1]))) for row in result.all()]

    async def sum_commissions_by_service(
        self,
        *,
        tenant_id: uuid.UUID | None = None,
    ) -> list[tuple[str, Decimal]]:
        stmt = select(
            AutomotivePartnerCommission.service_type,
            func.coalesce(func.sum(AutomotivePartnerCommission.commission_amount), 0),
        ).group_by(AutomotivePartnerCommission.service_type)
        if tenant_id:
            stmt = stmt.where(AutomotivePartnerCommission.tenant_id == tenant_id)
        result = await self._session.execute(stmt)
        return [(row[0], Decimal(str(row[1]))) for row in result.all()]

    async def sum_profit_by_month(
        self,
        *,
        tenant_id: uuid.UUID | None = None,
    ) -> list[tuple[str | None, Decimal]]:
        stmt = select(
            AutomotiveDealProfit.period_month,
            func.coalesce(func.sum(AutomotiveDealProfit.profit), 0),
        ).group_by(AutomotiveDealProfit.period_month)
        if tenant_id:
            stmt = stmt.where(AutomotiveDealProfit.tenant_id == tenant_id)
        result = await self._session.execute(stmt)
        return [(row[0], Decimal(str(row[1]))) for row in result.all()]

    async def count_completed_deals(self, *, tenant_id: uuid.UUID | None = None) -> int:
        stmt = select(func.count()).select_from(AutomotiveDealProfit)
        if tenant_id:
            stmt = stmt.where(AutomotiveDealProfit.tenant_id == tenant_id)
        result = await self._session.execute(stmt)
        return int(result.scalar_one() or 0)

    async def lifetime_value(self, *, tenant_id: uuid.UUID | None = None) -> Decimal:
        stmt = select(func.coalesce(func.sum(AutomotiveDealProfit.profit), 0))
        if tenant_id:
            stmt = stmt.where(AutomotiveDealProfit.tenant_id == tenant_id)
        result = await self._session.execute(stmt)
        return Decimal(str(result.scalar_one() or 0))
