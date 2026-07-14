# Auto Client request repository.

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.auto_client_request import AutoClientRequest


class AutoClientRequestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def count_all(self) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(AutoClientRequest)
        )
        return int(result.scalar_one())

    async def create(self, **fields) -> AutoClientRequest:
        row = AutoClientRequest(**fields)
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_by_id(self, request_id: uuid.UUID) -> AutoClientRequest | None:
        result = await self._session.execute(
            select(AutoClientRequest).where(AutoClientRequest.id == request_id)
        )
        return result.scalar_one_or_none()
