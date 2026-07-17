# Client request CRM repository.

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.client_request import ClientRequest


class ClientRequestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def count_all(self) -> int:
        result = await self._session.execute(select(func.count()).select_from(ClientRequest))
        return int(result.scalar_one())

    async def create(self, **fields) -> ClientRequest:
        row = ClientRequest(**fields)
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_by_id(self, request_id: uuid.UUID) -> ClientRequest | None:
        result = await self._session.execute(
            select(ClientRequest).where(ClientRequest.id == request_id)
        )
        return result.scalar_one_or_none()

    async def get_by_number(self, request_number: str) -> ClientRequest | None:
        result = await self._session.execute(
            select(ClientRequest).where(ClientRequest.request_number == request_number)
        )
        return result.scalar_one_or_none()

    async def list_for_client(
        self,
        client_telegram_id: int,
        *,
        limit: int = 20,
    ) -> list[ClientRequest]:
        result = await self._session.execute(
            select(ClientRequest)
            .where(ClientRequest.client_telegram_id == client_telegram_id)
            .order_by(ClientRequest.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_for_manager(
        self,
        manager_id: uuid.UUID,
        *,
        status: str | None = None,
        limit: int = 20,
    ) -> list[ClientRequest]:
        q = select(ClientRequest).where(ClientRequest.manager_id == manager_id)
        if status:
            q = q.where(ClientRequest.status == status)
        result = await self._session.execute(q.order_by(ClientRequest.created_at.desc()).limit(limit))
        return list(result.scalars().all())

    async def list_new(self, *, limit: int = 20) -> list[ClientRequest]:
        result = await self._session.execute(
            select(ClientRequest)
            .where(ClientRequest.status == "NEW")
            .order_by(ClientRequest.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_new_for_manager(
        self,
        manager_id: uuid.UUID,
        *,
        limit: int = 20,
    ) -> list[ClientRequest]:
        from sqlalchemy import or_

        result = await self._session.execute(
            select(ClientRequest)
            .where(
                ClientRequest.status == "NEW",
                or_(
                    ClientRequest.manager_id == manager_id,
                    ClientRequest.manager_id.is_(None),
                ),
            )
            .order_by(ClientRequest.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_active_for_manager(
        self,
        manager_id: uuid.UUID,
        *,
        limit: int = 20,
    ) -> list[ClientRequest]:
        active = ("ASSIGNED", "IN_PROGRESS", "WAITING_CLIENT")
        result = await self._session.execute(
            select(ClientRequest)
            .where(
                ClientRequest.manager_id == manager_id,
                ClientRequest.status.in_(active),
            )
            .order_by(ClientRequest.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_completed_for_manager(
        self,
        manager_id: uuid.UUID,
        *,
        limit: int = 20,
    ) -> list[ClientRequest]:
        result = await self._session.execute(
            select(ClientRequest)
            .where(
                ClientRequest.manager_id == manager_id,
                ClientRequest.status.in_(("COMPLETED", "CANCELLED")),
            )
            .order_by(ClientRequest.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_overdue_for_manager(
        self,
        manager_id: uuid.UUID,
        *,
        before,
        limit: int = 20,
    ) -> list[ClientRequest]:
        open_statuses = ("NEW", "ASSIGNED", "IN_PROGRESS", "WAITING_CLIENT")
        result = await self._session.execute(
            select(ClientRequest)
            .where(
                ClientRequest.manager_id == manager_id,
                ClientRequest.status.in_(open_statuses),
                ClientRequest.created_at <= before,
            )
            .order_by(ClientRequest.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update(self, row: ClientRequest, **fields) -> ClientRequest:
        for key, value in fields.items():
            setattr(row, key, value)
        await self._session.flush()
        return row
