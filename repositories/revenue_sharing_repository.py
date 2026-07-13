# Revenue Sharing Engine v1 repositories.

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.revenue_sharing_engine import (
    REVENUE_SHARE_MODELS,
    AgreementStatus,
    ReportStatus,
    RevenueShareAgreement,
    RevenueShareCalculation,
    RevenueShareReport,
    RevenueShareSettlement,
    SettlementStatus,
)


class RevenueShareAgreementRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        partner_ref: str,
        partner_name: str,
        model_type: str,
        terms: dict,
        currency: str = "USD",
        status: str = AgreementStatus.ACTIVE.value,
        metadata: dict | None = None,
    ) -> RevenueShareAgreement:
        if model_type not in REVENUE_SHARE_MODELS:
            raise ValueError(f"Invalid model_type: {model_type}")

        row = RevenueShareAgreement(
            tenant_id=tenant_id,
            company_id=company_id,
            partner_ref=partner_ref.strip(),
            partner_name=partner_name.strip(),
            model_type=model_type,
            terms=terms,
            currency=currency,
            status=status,
            metadata_=metadata,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_by_id(self, agreement_id: uuid.UUID) -> RevenueShareAgreement | None:
        result = await self._session.execute(
            select(RevenueShareAgreement).where(RevenueShareAgreement.id == agreement_id)
        )
        return result.scalar_one_or_none()

    async def get_by_partner(
        self,
        tenant_id: uuid.UUID,
        partner_ref: str,
    ) -> RevenueShareAgreement | None:
        result = await self._session.execute(
            select(RevenueShareAgreement).where(
                RevenueShareAgreement.tenant_id == tenant_id,
                RevenueShareAgreement.partner_ref == partner_ref.strip(),
            )
        )
        return result.scalar_one_or_none()

    async def list_by_tenant(
        self,
        tenant_id: uuid.UUID,
        *,
        status: str | None = None,
        limit: int = 100,
    ) -> list[RevenueShareAgreement]:
        stmt = (
            select(RevenueShareAgreement)
            .where(RevenueShareAgreement.tenant_id == tenant_id)
            .order_by(RevenueShareAgreement.created_at.desc())
            .limit(limit)
        )
        if status is not None:
            stmt = stmt.where(RevenueShareAgreement.status == status)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_active(self, *, limit: int = 200) -> list[RevenueShareAgreement]:
        result = await self._session.execute(
            select(RevenueShareAgreement)
            .where(RevenueShareAgreement.status == AgreementStatus.ACTIVE.value)
            .order_by(RevenueShareAgreement.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())


class RevenueShareCalculationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(
        self,
        *,
        agreement_id: uuid.UUID,
        period_start: date,
        period_end: date,
        metrics: dict,
        breakdown: dict,
        total_amount: Decimal,
    ) -> RevenueShareCalculation:
        result = await self._session.execute(
            select(RevenueShareCalculation).where(
                RevenueShareCalculation.agreement_id == agreement_id,
                RevenueShareCalculation.period_start == period_start,
                RevenueShareCalculation.period_end == period_end,
            )
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            existing.metrics = metrics
            existing.breakdown = breakdown
            existing.total_amount = total_amount
            await self._session.flush()
            return existing

        row = RevenueShareCalculation(
            agreement_id=agreement_id,
            period_start=period_start,
            period_end=period_end,
            metrics=metrics,
            breakdown=breakdown,
            total_amount=total_amount,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_by_id(self, calculation_id: uuid.UUID) -> RevenueShareCalculation | None:
        result = await self._session.execute(
            select(RevenueShareCalculation).where(
                RevenueShareCalculation.id == calculation_id
            )
        )
        return result.scalar_one_or_none()


class RevenueShareReportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(
        self,
        *,
        agreement_id: uuid.UUID,
        calculation_id: uuid.UUID,
        report_month: date,
        summary: dict,
        status: str = ReportStatus.GENERATED.value,
    ) -> RevenueShareReport:
        result = await self._session.execute(
            select(RevenueShareReport).where(
                RevenueShareReport.agreement_id == agreement_id,
                RevenueShareReport.report_month == report_month,
            )
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            existing.calculation_id = calculation_id
            existing.summary = summary
            existing.status = status
            await self._session.flush()
            return existing

        row = RevenueShareReport(
            agreement_id=agreement_id,
            calculation_id=calculation_id,
            report_month=report_month,
            summary=summary,
            status=status,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_by_agreement(
        self,
        agreement_id: uuid.UUID,
        *,
        limit: int = 24,
    ) -> list[RevenueShareReport]:
        result = await self._session.execute(
            select(RevenueShareReport)
            .where(RevenueShareReport.agreement_id == agreement_id)
            .order_by(RevenueShareReport.report_month.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id(self, report_id: uuid.UUID) -> RevenueShareReport | None:
        result = await self._session.execute(
            select(RevenueShareReport).where(RevenueShareReport.id == report_id)
        )
        return result.scalar_one_or_none()


class RevenueShareSettlementRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        agreement_id: uuid.UUID,
        report_id: uuid.UUID,
        amount: Decimal,
        currency: str,
        status: str = SettlementStatus.PENDING.value,
        reference: str | None = None,
        notes: str | None = None,
        metadata: dict | None = None,
    ) -> RevenueShareSettlement:
        row = RevenueShareSettlement(
            agreement_id=agreement_id,
            report_id=report_id,
            amount=amount,
            currency=currency,
            status=status,
            reference=reference,
            notes=notes,
            metadata_=metadata,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_by_agreement(
        self,
        agreement_id: uuid.UUID,
        *,
        limit: int = 50,
    ) -> list[RevenueShareSettlement]:
        result = await self._session.execute(
            select(RevenueShareSettlement)
            .where(RevenueShareSettlement.agreement_id == agreement_id)
            .order_by(RevenueShareSettlement.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id(self, settlement_id: uuid.UUID) -> RevenueShareSettlement | None:
        result = await self._session.execute(
            select(RevenueShareSettlement).where(RevenueShareSettlement.id == settlement_id)
        )
        return result.scalar_one_or_none()

    async def mark_paid(
        self,
        settlement: RevenueShareSettlement,
        *,
        reference: str | None = None,
    ) -> RevenueShareSettlement:
        settlement.status = SettlementStatus.PAID.value
        if reference:
            settlement.reference = reference
        await self._session.flush()
        return settlement
