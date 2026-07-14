# Cart and Payment Engine v1 repository.

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.cart_engine_v1 import CartEngineV1Order, CartEngineV1OrderItem


class CartEngineV1Repository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_order(self, **fields) -> CartEngineV1Order:
        row = CartEngineV1Order(**fields)
        self._session.add(row)
        await self._session.flush()
        return row

    async def add_item(self, **fields) -> CartEngineV1OrderItem:
        row = CartEngineV1OrderItem(**fields)
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_order(self, order_id: uuid.UUID) -> CartEngineV1Order | None:
        result = await self._session.execute(
            select(CartEngineV1Order).where(CartEngineV1Order.id == order_id)
        )
        return result.scalar_one_or_none()

    async def list_items(self, order_id: uuid.UUID) -> list[CartEngineV1OrderItem]:
        result = await self._session.execute(
            select(CartEngineV1OrderItem)
            .where(CartEngineV1OrderItem.order_id == order_id)
            .order_by(CartEngineV1OrderItem.created_at)
        )
        return list(result.scalars().all())

    async def update_order(self, order_id: uuid.UUID, **fields) -> CartEngineV1Order | None:
        row = await self.get_order(order_id)
        if row is None:
            return None
        for key, value in fields.items():
            setattr(row, key, value)
        await self._session.flush()
        return row

    async def list_recent(self, *, limit: int = 20) -> list[CartEngineV1Order]:
        result = await self._session.execute(
            select(CartEngineV1Order)
            .order_by(CartEngineV1Order.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_status(self, status: str, *, since: datetime | None = None) -> int:
        stmt = select(func.count()).select_from(CartEngineV1Order).where(CartEngineV1Order.status == status)
        if since is not None:
            stmt = stmt.where(CartEngineV1Order.created_at >= since)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    @staticmethod
    def start_of_today() -> datetime:
        now = datetime.now(timezone.utc)
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
