# Liquidity Engine v1 repositories — PostgreSQL async data access.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.liquidity import (
    LiquidityAlert,
    LiquidityAlertType,
    LiquidityPool,
    LiquidityReservation,
    LiquidityReservationStatus,
    LiquidityLocation,
)


class LiquidityPoolRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        asset: str,
        location: str,
        available_amount: Decimal = Decimal("0"),
        **extra: Any,
    ) -> LiquidityPool:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if location not in {loc.value for loc in LiquidityLocation}:
            raise ValueError(f"Invalid location: {location}")
        if available_amount < 0:
            raise ValueError("available_amount must be non-negative")

        pool = LiquidityPool(
            asset=asset,
            location=location,
            available_amount=available_amount,
            reserved_amount=Decimal("0"),
            updated_at=datetime.now(timezone.utc),
        )
        self._session.add(pool)
        await self._session.flush()
        return pool

    async def get_by_id(self, pool_id: uuid.UUID) -> LiquidityPool | None:
        result = await self._session.execute(
            select(LiquidityPool).where(LiquidityPool.id == pool_id)
        )
        return result.scalar_one_or_none()

    async def get_for_update(self, pool_id: uuid.UUID) -> LiquidityPool | None:
        result = await self._session.execute(
            select(LiquidityPool)
            .where(LiquidityPool.id == pool_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def get_by_asset_location(
        self,
        asset: str,
        location: str,
    ) -> LiquidityPool | None:
        result = await self._session.execute(
            select(LiquidityPool).where(
                LiquidityPool.asset == asset,
                LiquidityPool.location == location,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_asset(self, asset: str) -> list[LiquidityPool]:
        result = await self._session.execute(
            select(LiquidityPool)
            .where(LiquidityPool.asset == asset)
            .order_by(LiquidityPool.location.asc())
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[LiquidityPool]:
        result = await self._session.execute(
            select(LiquidityPool).order_by(LiquidityPool.asset, LiquidityPool.location)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self._session.scalar(select(func.count()).select_from(LiquidityPool))
        return int(result or 0)

    async def find_best_pool(
        self,
        asset: str,
        amount: Decimal,
        location: str | None = None,
    ) -> LiquidityPool | None:
        stmt = select(LiquidityPool).where(LiquidityPool.asset == asset)
        if location is not None:
            stmt = stmt.where(LiquidityPool.location == location)
        result = await self._session.execute(stmt.order_by(LiquidityPool.location.asc()))
        pools = list(result.scalars().all())
        for pool in pools:
            if pool.free_amount >= amount:
                return pool
        return pools[0] if pools else None

    async def deposit(self, pool_id: uuid.UUID, amount: Decimal) -> LiquidityPool | None:
        pool = await self.get_for_update(pool_id)
        if pool is None:
            return None
        pool.available_amount += amount
        pool.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return pool


class LiquidityReservationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        deal_id: uuid.UUID,
        pool_id: uuid.UUID,
        asset: str,
        amount: Decimal,
        **extra: Any,
    ) -> LiquidityReservation:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if amount <= 0:
            raise ValueError("amount must be positive")

        reservation = LiquidityReservation(
            deal_id=deal_id,
            pool_id=pool_id,
            asset=asset,
            amount=amount,
            status=LiquidityReservationStatus.ACTIVE.value,
        )
        self._session.add(reservation)
        await self._session.flush()
        return reservation

    async def get_by_id(self, reservation_id: uuid.UUID) -> LiquidityReservation | None:
        result = await self._session.execute(
            select(LiquidityReservation).where(LiquidityReservation.id == reservation_id)
        )
        return result.scalar_one_or_none()

    async def list_by_deal(self, deal_id: uuid.UUID) -> list[LiquidityReservation]:
        result = await self._session.execute(
            select(LiquidityReservation)
            .where(LiquidityReservation.deal_id == deal_id)
            .order_by(LiquidityReservation.created_at.asc())
        )
        return list(result.scalars().all())

    async def list_active_by_asset(self, asset: str) -> list[LiquidityReservation]:
        result = await self._session.execute(
            select(LiquidityReservation).where(
                LiquidityReservation.asset == asset,
                LiquidityReservation.status == LiquidityReservationStatus.ACTIVE.value,
            )
        )
        return list(result.scalars().all())


class LiquidityAlertRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        alert_type: str,
        message: str,
        pool_id: uuid.UUID | None = None,
        asset: str | None = None,
        deal_id: uuid.UUID | None = None,
    ) -> LiquidityAlert:
        if alert_type not in {a.value for a in LiquidityAlertType}:
            raise ValueError(f"Invalid alert_type: {alert_type}")

        alert = LiquidityAlert(
            alert_type=alert_type,
            pool_id=pool_id,
            asset=asset,
            deal_id=deal_id,
            message=message,
        )
        self._session.add(alert)
        await self._session.flush()
        return alert

    async def list_unresolved(self, *, limit: int = 50) -> list[LiquidityAlert]:
        result = await self._session.execute(
            select(LiquidityAlert)
            .where(LiquidityAlert.is_resolved.is_(False))
            .order_by(LiquidityAlert.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
