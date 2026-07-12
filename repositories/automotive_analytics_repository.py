# Automotive Analytics Engine v1 repositories — PostgreSQL async data access.

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.automotive_analytics import (
    InventoryMetrics,
    ProfitabilityMetrics,
    SalesMetrics,
)


class InventoryMetricsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(
        self,
        *,
        metric_date: date,
        vehicle_id: uuid.UUID | None = None,
        days_in_inventory: int | None = None,
        aging_bucket: str | None = None,
        vehicle_status: str | None = None,
        inventory_value: Decimal | None = None,
        in_stock_count: int | None = None,
        sold_count: int | None = None,
        turnover_rate: Decimal | None = None,
        currency: str = "USD",
        notes: str | None = None,
        **extra: Any,
    ) -> InventoryMetrics:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")

        row = InventoryMetrics(
            metric_date=metric_date,
            vehicle_id=vehicle_id,
            days_in_inventory=days_in_inventory,
            aging_bucket=aging_bucket,
            vehicle_status=vehicle_status,
            inventory_value=inventory_value,
            in_stock_count=in_stock_count,
            sold_count=sold_count,
            turnover_rate=turnover_rate,
            currency=currency,
            notes=notes,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def clear_for_date(self, metric_date: date) -> None:
        await self._session.execute(
            delete(InventoryMetrics).where(InventoryMetrics.metric_date == metric_date)
        )

    async def list_by_date(self, metric_date: date) -> list[InventoryMetrics]:
        result = await self._session.execute(
            select(InventoryMetrics)
            .where(InventoryMetrics.metric_date == metric_date)
            .order_by(InventoryMetrics.days_in_inventory.desc().nullslast())
        )
        return list(result.scalars().all())

    async def get_fleet_summary(self, metric_date: date) -> InventoryMetrics | None:
        result = await self._session.execute(
            select(InventoryMetrics)
            .where(
                InventoryMetrics.metric_date == metric_date,
                InventoryMetrics.vehicle_id.is_(None),
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_latest_fleet_summaries(self, *, limit: int = 30) -> list[InventoryMetrics]:
        result = await self._session.execute(
            select(InventoryMetrics)
            .where(InventoryMetrics.vehicle_id.is_(None))
            .order_by(InventoryMetrics.metric_date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class SalesMetricsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(
        self,
        *,
        metric_date: date,
        total_leads: int = 0,
        new_leads: int = 0,
        contacted_count: int = 0,
        test_drive_count: int = 0,
        negotiation_count: int = 0,
        reserved_count: int = 0,
        contract_signed_count: int = 0,
        paid_count: int = 0,
        delivered_count: int = 0,
        conversion_rate: Decimal = Decimal("0"),
        total_pipeline_budget: Decimal | None = None,
        currency: str = "USD",
        **extra: Any,
    ) -> SalesMetrics:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")

        row = SalesMetrics(
            metric_date=metric_date,
            total_leads=total_leads,
            new_leads=new_leads,
            contacted_count=contacted_count,
            test_drive_count=test_drive_count,
            negotiation_count=negotiation_count,
            reserved_count=reserved_count,
            contract_signed_count=contract_signed_count,
            paid_count=paid_count,
            delivered_count=delivered_count,
            conversion_rate=conversion_rate,
            total_pipeline_budget=total_pipeline_budget,
            currency=currency,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def replace_for_date(self, metric_date: date, **fields: Any) -> SalesMetrics:
        await self._session.execute(
            delete(SalesMetrics).where(SalesMetrics.metric_date == metric_date)
        )
        return await self.save(metric_date=metric_date, **fields)

    async def get_by_date(self, metric_date: date) -> SalesMetrics | None:
        result = await self._session.execute(
            select(SalesMetrics)
            .where(SalesMetrics.metric_date == metric_date)
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_latest(self, *, limit: int = 30) -> list[SalesMetrics]:
        result = await self._session.execute(
            select(SalesMetrics)
            .order_by(SalesMetrics.metric_date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class ProfitabilityMetricsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(
        self,
        *,
        vehicle_id: uuid.UUID,
        metric_date: date,
        total_cost: Decimal,
        margin_amount: Decimal,
        margin_percent: Decimal,
        roi_percent: Decimal,
        sale_price: Decimal | None = None,
        target_price: Decimal | None = None,
        currency: str = "USD",
        **extra: Any,
    ) -> ProfitabilityMetrics:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")

        row = ProfitabilityMetrics(
            vehicle_id=vehicle_id,
            metric_date=metric_date,
            total_cost=total_cost,
            sale_price=sale_price,
            target_price=target_price,
            margin_amount=margin_amount,
            margin_percent=margin_percent,
            roi_percent=roi_percent,
            currency=currency,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def clear_for_date(self, metric_date: date) -> None:
        await self._session.execute(
            delete(ProfitabilityMetrics).where(
                ProfitabilityMetrics.metric_date == metric_date
            )
        )

    async def list_by_date(self, metric_date: date) -> list[ProfitabilityMetrics]:
        result = await self._session.execute(
            select(ProfitabilityMetrics)
            .where(ProfitabilityMetrics.metric_date == metric_date)
            .order_by(ProfitabilityMetrics.roi_percent.desc())
        )
        return list(result.scalars().all())

    async def get_fleet_averages(self, metric_date: date) -> dict[str, Decimal]:
        rows = await self.list_by_date(metric_date)
        if not rows:
            return {
                "avg_margin_percent": Decimal("0"),
                "avg_roi_percent": Decimal("0"),
                "total_margin": Decimal("0"),
            }
        count = Decimal(len(rows))
        return {
            "avg_margin_percent": sum(r.margin_percent for r in rows) / count,
            "avg_roi_percent": sum(r.roi_percent for r in rows) / count,
            "total_margin": sum(r.margin_amount for r in rows),
        }
