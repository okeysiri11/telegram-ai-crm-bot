# AI Procurement Agent v1 repositories.

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.ai_procurement_agent import (
    PROCUREMENT_ANALYSIS_TYPES,
    PROCUREMENT_OPPORTUNITY_STATUSES,
    PROCUREMENT_SUBJECT_TYPES,
    ProcurementAnalysis,
    ProcurementOpportunity,
    ProcurementOpportunityStatus,
)


class ProcurementAnalysisRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        analysis_type: str,
        input_context: dict,
        result: dict,
        confidence_score: Decimal,
        model_version: str,
        subject_type: str | None = None,
        subject_id: str | None = None,
        summary: str | None = None,
        created_by: int | None = None,
        **extra: Any,
    ) -> ProcurementAnalysis:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if analysis_type not in PROCUREMENT_ANALYSIS_TYPES:
            raise ValueError(f"Invalid analysis_type: {analysis_type}")
        if subject_type is not None and subject_type not in PROCUREMENT_SUBJECT_TYPES:
            raise ValueError(f"Invalid subject_type: {subject_type}")

        row = ProcurementAnalysis(
            analysis_type=analysis_type,
            subject_type=subject_type,
            subject_id=subject_id,
            input_context=input_context,
            result=result,
            confidence_score=confidence_score,
            model_version=model_version,
            summary=summary,
            created_by=created_by,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_by_id(self, analysis_id: uuid.UUID) -> ProcurementAnalysis | None:
        result = await self._session.execute(
            select(ProcurementAnalysis).where(ProcurementAnalysis.id == analysis_id)
        )
        return result.scalar_one_or_none()

    async def list_by_type(
        self,
        analysis_type: str,
        *,
        limit: int = 50,
    ) -> list[ProcurementAnalysis]:
        result = await self._session.execute(
            select(ProcurementAnalysis)
            .where(ProcurementAnalysis.analysis_type == analysis_type)
            .order_by(ProcurementAnalysis.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_by_subject(
        self,
        subject_type: str,
        subject_id: str,
        *,
        limit: int = 20,
    ) -> list[ProcurementAnalysis]:
        result = await self._session.execute(
            select(ProcurementAnalysis)
            .where(
                ProcurementAnalysis.subject_type == subject_type,
                ProcurementAnalysis.subject_id == subject_id,
            )
            .order_by(ProcurementAnalysis.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class ProcurementOpportunityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        make: str,
        model: str,
        year: int,
        acquisition_price: Decimal,
        estimated_market_value: Decimal,
        discount_percent: Decimal,
        undervaluation_score: int,
        currency: str = "USD",
        auction_lot_id: uuid.UUID | None = None,
        vehicle_id: uuid.UUID | None = None,
        analysis_id: uuid.UUID | None = None,
        source: str | None = None,
        repair_cost_estimate: Decimal | None = None,
        sale_price_estimate: Decimal | None = None,
        roi_percent: Decimal | None = None,
        status: str = ProcurementOpportunityStatus.OPEN.value,
        notes: str | None = None,
        metadata: dict | None = None,
        **extra: Any,
    ) -> ProcurementOpportunity:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if status not in PROCUREMENT_OPPORTUNITY_STATUSES:
            raise ValueError(f"Invalid status: {status}")

        row = ProcurementOpportunity(
            auction_lot_id=auction_lot_id,
            vehicle_id=vehicle_id,
            analysis_id=analysis_id,
            make=make.strip(),
            model=model.strip(),
            year=year,
            source=source,
            acquisition_price=acquisition_price,
            estimated_market_value=estimated_market_value,
            discount_percent=discount_percent,
            undervaluation_score=undervaluation_score,
            repair_cost_estimate=repair_cost_estimate,
            sale_price_estimate=sale_price_estimate,
            roi_percent=roi_percent,
            currency=currency,
            status=status,
            notes=notes,
            metadata_=metadata,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_by_id(self, opportunity_id: uuid.UUID) -> ProcurementOpportunity | None:
        result = await self._session.execute(
            select(ProcurementOpportunity).where(ProcurementOpportunity.id == opportunity_id)
        )
        return result.scalar_one_or_none()

    async def get_by_auction_lot(
        self,
        auction_lot_id: uuid.UUID,
        *,
        status: str | None = None,
    ) -> ProcurementOpportunity | None:
        stmt = select(ProcurementOpportunity).where(
            ProcurementOpportunity.auction_lot_id == auction_lot_id
        )
        if status is not None:
            stmt = stmt.where(ProcurementOpportunity.status == status)
        stmt = stmt.order_by(ProcurementOpportunity.created_at.desc()).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_open(
        self,
        *,
        min_score: int | None = None,
        limit: int = 50,
    ) -> list[ProcurementOpportunity]:
        stmt = (
            select(ProcurementOpportunity)
            .where(ProcurementOpportunity.status == ProcurementOpportunityStatus.OPEN.value)
            .order_by(
                ProcurementOpportunity.undervaluation_score.desc(),
                ProcurementOpportunity.discount_percent.desc(),
            )
            .limit(limit)
        )
        if min_score is not None:
            stmt = stmt.where(ProcurementOpportunity.undervaluation_score >= min_score)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self,
        opportunity_id: uuid.UUID,
        *,
        status: str,
        notes: str | None = None,
    ) -> ProcurementOpportunity | None:
        row = await self.get_by_id(opportunity_id)
        if row is None:
            return None
        if status not in PROCUREMENT_OPPORTUNITY_STATUSES:
            raise ValueError(f"Invalid status: {status}")
        row.status = status
        if notes is not None:
            row.notes = notes
        await self._session.flush()
        return row
