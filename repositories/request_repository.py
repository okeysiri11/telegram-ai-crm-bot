# Request repository — unified client/auto request persistence.

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.auto_client_request import AutoClientRequest
from database.models.client_request import ClientRequest
from repositories.auto_client_request_repository import AutoClientRequestRepository
from repositories.client_request_repository import ClientRequestRepository
from src.platform.layers.base_repository import BaseRepository


class RequestRepository(BaseRepository):
    """All SQL for client requests lives here."""

    def _crm(self) -> ClientRequestRepository:
        return ClientRequestRepository(self.session)

    def _auto(self) -> AutoClientRequestRepository:
        return AutoClientRequestRepository(self.session)

    async def next_crm_number(self, *, prefix: str = "REQ") -> str:
        count = await self._crm().count_all()
        return f"{prefix}-{count + 1:05d}"

    async def next_auto_number(self) -> str:
        count = await self._auto().count_all()
        return f"AUTO-{count + 1:04d}"

    async def create_crm(self, **fields: Any) -> ClientRequest:
        return await self._crm().create(**fields)

    async def create_auto(self, **fields: Any) -> AutoClientRequest:
        return await self._auto().create(**fields)

    async def get_crm_by_number(self, request_number: str) -> ClientRequest | None:
        return await self._crm().get_by_number(request_number)

    async def get_auto_by_number(self, request_number: str) -> AutoClientRequest | None:
        return await self._auto().get_by_number(request_number)

    async def get_auto_by_id(self, request_id: uuid.UUID) -> AutoClientRequest | None:
        return await self._auto().get_by_id(request_id)

    async def get_crm_by_id(self, request_id: uuid.UUID) -> ClientRequest | None:
        return await self._crm().get_by_id(request_id)

    async def update_crm(self, row: ClientRequest, **fields: Any) -> ClientRequest:
        return await self._crm().update(row, **fields)

    async def list_crm_new(self, *, limit: int = 20) -> list[ClientRequest]:
        return await self._crm().list_new(limit=limit)

    async def list_auto_by_status(
        self,
        status: str,
        *,
        limit: int = 10,
    ) -> list[AutoClientRequest]:
        return await self._auto().list_by_status(status, limit=limit)

    async def count_by_vertical(self, vertical: str) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(ClientRequest)
            .where(ClientRequest.request_type.ilike(f"{vertical}%"))
        )
        return int(result.scalar_one())

    async def list_new_for_manager(self, manager_id: uuid.UUID, *, limit: int = 20):
        crm = await self._crm().list_new_for_manager(manager_id, limit=limit)
        auto = await self._auto().list_new_for_manager(manager_id, limit=limit)
        return crm, auto

    async def list_active_for_manager(self, manager_id: uuid.UUID, *, limit: int = 20):
        active = ("ASSIGNED", "IN_PROGRESS", "WAITING_CLIENT")
        crm = await self._crm().list_active_for_manager(manager_id, limit=limit)
        auto = await self._auto().list_for_manager(manager_id, statuses=active, limit=limit)
        return crm, auto

    async def list_completed_for_manager(self, manager_id: uuid.UUID, *, limit: int = 20):
        crm = await self._crm().list_completed_for_manager(manager_id, limit=limit)
        auto = await self._auto().list_for_manager(
            manager_id,
            statuses=("COMPLETED", "DONE", "CANCELLED"),
            limit=limit,
        )
        return crm, auto

    async def list_overdue_for_manager(
        self,
        manager_id: uuid.UUID,
        *,
        before,
        limit: int = 20,
    ):
        crm = await self._crm().list_overdue_for_manager(manager_id, before=before, limit=limit)
        auto = await self._auto().list_overdue_for_manager(manager_id, before=before, limit=limit)
        return crm, auto
