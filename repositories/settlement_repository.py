# Settlement Engine v1 repositories — PostgreSQL async data access.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.settlement import (
    Settlement,
    SettlementRoute,
    SettlementStatus,
    SettlementStatusHistory,
    SettlementStep,
    SettlementStepType,
    SettlementType,
)


class SettlementRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        settlement_type: str,
        asset: str,
        amount: Decimal,
        deal_id: uuid.UUID | None = None,
        reference: str | None = None,
        notes: str | None = None,
        **extra: Any,
    ) -> Settlement:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if settlement_type not in {t.value for t in SettlementType}:
            raise ValueError(f"Invalid settlement_type: {settlement_type}")
        if amount <= 0:
            raise ValueError("amount must be positive")

        settlement = Settlement(
            deal_id=deal_id,
            settlement_type=settlement_type,
            asset=asset,
            amount=amount,
            status=SettlementStatus.CREATED.value,
            reference=reference,
            notes=notes,
        )
        self._session.add(settlement)
        await self._session.flush()
        return settlement

    async def get_by_id(self, settlement_id: uuid.UUID) -> Settlement | None:
        result = await self._session.execute(
            select(Settlement).where(Settlement.id == settlement_id)
        )
        return result.scalar_one_or_none()

    async def update_status(
        self,
        settlement_id: uuid.UUID,
        status: str,
        *,
        completed_at: datetime | None = None,
    ) -> Settlement | None:
        settlement = await self.get_by_id(settlement_id)
        if settlement is None:
            return None
        if status not in {s.value for s in SettlementStatus}:
            raise ValueError(f"Invalid status: {status}")

        settlement.status = status
        if completed_at is not None:
            settlement.completed_at = completed_at
        elif status == SettlementStatus.COMPLETED.value:
            settlement.completed_at = datetime.now(timezone.utc)
        await self._session.flush()
        return settlement

    async def list_by_deal(self, deal_id: uuid.UUID) -> list[Settlement]:
        result = await self._session.execute(
            select(Settlement)
            .where(Settlement.deal_id == deal_id)
            .order_by(Settlement.created_at.asc())
        )
        return list(result.scalars().all())


class SettlementRouteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        settlement_id: uuid.UUID,
        name: str,
        description: str | None = None,
        step_count: int = 0,
        **extra: Any,
    ) -> SettlementRoute:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")

        route = SettlementRoute(
            settlement_id=settlement_id,
            name=name,
            description=description,
            step_count=step_count,
        )
        self._session.add(route)
        await self._session.flush()
        return route

    async def get_by_id(self, route_id: uuid.UUID) -> SettlementRoute | None:
        result = await self._session.execute(
            select(SettlementRoute).where(SettlementRoute.id == route_id)
        )
        return result.scalar_one_or_none()

    async def get_by_settlement(self, settlement_id: uuid.UUID) -> SettlementRoute | None:
        result = await self._session.execute(
            select(SettlementRoute).where(
                SettlementRoute.settlement_id == settlement_id
            )
        )
        return result.scalar_one_or_none()


class SettlementStepRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        route_id: uuid.UUID,
        step_order: int,
        step_type: str,
        asset: str,
        amount: Decimal,
        source_location: str | None = None,
        destination_location: str | None = None,
        external_ref: str | None = None,
        notes: str | None = None,
        **extra: Any,
    ) -> SettlementStep:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if step_type not in {t.value for t in SettlementStepType}:
            raise ValueError(f"Invalid step_type: {step_type}")
        if amount <= 0:
            raise ValueError("amount must be positive")

        step = SettlementStep(
            route_id=route_id,
            step_order=step_order,
            step_type=step_type,
            asset=asset,
            amount=amount,
            source_location=source_location,
            destination_location=destination_location,
            external_ref=external_ref,
            notes=notes,
        )
        self._session.add(step)
        await self._session.flush()
        return step

    async def get_by_id(self, step_id: uuid.UUID) -> SettlementStep | None:
        result = await self._session.execute(
            select(SettlementStep).where(SettlementStep.id == step_id)
        )
        return result.scalar_one_or_none()

    async def list_by_route(self, route_id: uuid.UUID) -> list[SettlementStep]:
        result = await self._session.execute(
            select(SettlementStep)
            .where(SettlementStep.route_id == route_id)
            .order_by(SettlementStep.step_order.asc())
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        step_id: uuid.UUID,
        status: str,
        *,
        external_ref: str | None = None,
    ) -> SettlementStep | None:
        step = await self.get_by_id(step_id)
        if step is None:
            return None
        if status not in {s.value for s in SettlementStatus}:
            raise ValueError(f"Invalid status: {status}")

        step.status = status
        if external_ref is not None:
            step.external_ref = external_ref
        if status == SettlementStatus.COMPLETED.value:
            step.completed_at = datetime.now(timezone.utc)
        await self._session.flush()
        return step

    async def get_settlement_id(self, step_id: uuid.UUID) -> uuid.UUID | None:
        result = await self._session.execute(
            select(SettlementRoute.settlement_id)
            .join(SettlementStep, SettlementStep.route_id == SettlementRoute.id)
            .where(SettlementStep.id == step_id)
        )
        return result.scalar_one_or_none()

    async def next_pending(self, route_id: uuid.UUID) -> SettlementStep | None:
        result = await self._session.execute(
            select(SettlementStep)
            .where(
                SettlementStep.route_id == route_id,
                SettlementStep.status == SettlementStatus.CREATED.value,
            )
            .order_by(SettlementStep.step_order.asc())
            .limit(1)
        )
        return result.scalar_one_or_none()


class SettlementStatusHistoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(
        self,
        *,
        settlement_id: uuid.UUID,
        to_status: str,
        from_status: str | None = None,
        step_id: uuid.UUID | None = None,
        changed_by: int | None = None,
        notes: str | None = None,
    ) -> SettlementStatusHistory:
        entry = SettlementStatusHistory(
            settlement_id=settlement_id,
            step_id=step_id,
            from_status=from_status,
            to_status=to_status,
            changed_by=changed_by,
            notes=notes,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def list_by_settlement(
        self,
        settlement_id: uuid.UUID,
    ) -> list[SettlementStatusHistory]:
        result = await self._session.execute(
            select(SettlementStatusHistory)
            .where(SettlementStatusHistory.settlement_id == settlement_id)
            .order_by(SettlementStatusHistory.created_at.asc())
        )
        return list(result.scalars().all())
