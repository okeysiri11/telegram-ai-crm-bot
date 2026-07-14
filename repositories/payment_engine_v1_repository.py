# Manual Payment Verification Engine v1 repository.

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.payment_engine_v1 import (
    PAYMENT_ENGINE_PENDING_STATUSES,
    PaymentEngineV1Payment,
)


class PaymentEngineV1Repository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, **fields) -> PaymentEngineV1Payment:
        row = PaymentEngineV1Payment(**fields)
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_by_id(self, payment_id: uuid.UUID) -> PaymentEngineV1Payment | None:
        result = await self._session.execute(
            select(PaymentEngineV1Payment).where(PaymentEngineV1Payment.id == payment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_order(self, order_id: uuid.UUID) -> PaymentEngineV1Payment | None:
        result = await self._session.execute(
            select(PaymentEngineV1Payment)
            .where(PaymentEngineV1Payment.order_id == order_id)
            .order_by(PaymentEngineV1Payment.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def update(self, payment_id: uuid.UUID, **fields) -> PaymentEngineV1Payment | None:
        row = await self.get_by_id(payment_id)
        if row is None:
            return None
        for key, value in fields.items():
            setattr(row, key, value)
        await self._session.flush()
        return row

    async def count_by_status(self, status: str) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(PaymentEngineV1Payment)
            .where(PaymentEngineV1Payment.status == status)
        )
        return int(result.scalar_one())

    async def count_pending(self) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(PaymentEngineV1Payment)
            .where(PaymentEngineV1Payment.status.in_(tuple(PAYMENT_ENGINE_PENDING_STATUSES)))
        )
        return int(result.scalar_one())

    async def list_by_status(
        self,
        status: str,
        *,
        limit: int = 10,
    ) -> list[PaymentEngineV1Payment]:
        result = await self._session.execute(
            select(PaymentEngineV1Payment)
            .where(PaymentEngineV1Payment.status == status)
            .order_by(PaymentEngineV1Payment.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_pending_review(self, *, limit: int = 10) -> list[PaymentEngineV1Payment]:
        result = await self._session.execute(
            select(PaymentEngineV1Payment)
            .where(
                PaymentEngineV1Payment.status.in_(
                    ("SCREENSHOT_UPLOADED", "UNDER_VERIFICATION")
                )
            )
            .order_by(PaymentEngineV1Payment.uploaded_at.asc().nullslast())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_recent(self, *, limit: int = 10) -> list[PaymentEngineV1Payment]:
        result = await self._session.execute(
            select(PaymentEngineV1Payment)
            .order_by(PaymentEngineV1Payment.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_active_for_client(self, client_id: uuid.UUID) -> PaymentEngineV1Payment | None:
        result = await self._session.execute(
            select(PaymentEngineV1Payment)
            .where(
                PaymentEngineV1Payment.client_id == client_id,
                PaymentEngineV1Payment.status.in_(("WAITING_PAYMENT", "SCREENSHOT_UPLOADED")),
            )
            .order_by(PaymentEngineV1Payment.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
