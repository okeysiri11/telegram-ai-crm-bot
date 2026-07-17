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

    async def get_by_number(self, request_number: str) -> AutoClientRequest | None:
        result = await self._session.execute(
            select(AutoClientRequest).where(
                AutoClientRequest.request_number == request_number
            )
        )
        return result.scalar_one_or_none()

    async def list_by_status(
        self,
        status: str,
        *,
        limit: int = 10,
    ) -> list[AutoClientRequest]:
        result = await self._session.execute(
            select(AutoClientRequest)
            .where(AutoClientRequest.status == status)
            .order_by(AutoClientRequest.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_for_manager(
        self,
        manager_id: uuid.UUID,
        *,
        statuses: tuple[str, ...] | None = None,
        limit: int = 20,
    ) -> list[AutoClientRequest]:
        q = select(AutoClientRequest).where(AutoClientRequest.manager_id == manager_id)
        if statuses:
            q = q.where(AutoClientRequest.status.in_(statuses))
        result = await self._session.execute(
            q.order_by(AutoClientRequest.updated_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def list_new_for_manager(
        self,
        manager_id: uuid.UUID,
        *,
        limit: int = 20,
    ) -> list[AutoClientRequest]:
        from sqlalchemy import or_

        result = await self._session.execute(
            select(AutoClientRequest)
            .where(
                AutoClientRequest.status == "NEW",
                or_(
                    AutoClientRequest.manager_id == manager_id,
                    AutoClientRequest.manager_id.is_(None),
                ),
            )
            .order_by(AutoClientRequest.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_overdue_for_manager(
        self,
        manager_id: uuid.UUID,
        *,
        before,
        limit: int = 20,
    ) -> list[AutoClientRequest]:
        open_statuses = ("NEW", "ASSIGNED", "IN_PROGRESS", "WAITING_CLIENT")
        result = await self._session.execute(
            select(AutoClientRequest)
            .where(
                AutoClientRequest.manager_id == manager_id,
                AutoClientRequest.status.in_(open_statuses),
                AutoClientRequest.created_at <= before,
            )
            .order_by(AutoClientRequest.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update(self, row: AutoClientRequest, **fields) -> AutoClientRequest:
        for key, value in fields.items():
            setattr(row, key, value)
        await self._session.flush()
        return row
