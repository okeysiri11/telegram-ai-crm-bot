# Escalation repository — request_sla persistence with row locking.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.auto_client_request import AutoClientRequest
from database.models.client_request import ClientRequest
from database.models.request_sla import RequestSla
from database.models.users import User
from models.request_sla import RequestEscalationContext, RequestSlaSnapshot
from src.platform.layers.base_repository import BaseRepository


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EscalationRepository(BaseRepository):
    async def get_by_request_id(self, request_id: uuid.UUID | str) -> RequestSla | None:
        rid = uuid.UUID(str(request_id))
        result = await self.session.execute(
            select(RequestSla).where(RequestSla.request_id == rid)
        )
        return result.scalar_one_or_none()

    async def create_sla(
        self,
        *,
        request_id: uuid.UUID | str,
        manager_telegram_id: int | None,
        first_response_deadline: datetime,
        completion_deadline: datetime,
        assigned_at: datetime | None = None,
    ) -> RequestSla | None:
        rid = uuid.UUID(str(request_id))
        existing = await self.get_by_request_id(rid)
        if existing is not None:
            return existing

        row = RequestSla(
            request_id=rid,
            manager_id=manager_telegram_id,
            first_response_deadline=first_response_deadline,
            completion_deadline=completion_deadline,
            escalation_level=0,
            created_at=assigned_at or _utcnow(),
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def mark_first_response(
        self,
        request_id: uuid.UUID | str,
        *,
        responded_at: datetime | None = None,
    ) -> RequestSla | None:
        row = await self.get_by_request_id(request_id)
        if row is None or row.first_response_at is not None:
            return row
        row.first_response_at = responded_at or _utcnow()
        await self.session.flush()
        return row

    async def mark_completed(
        self,
        request_id: uuid.UUID | str,
        *,
        completed_at: datetime | None = None,
    ) -> RequestSla | None:
        row = await self.get_by_request_id(request_id)
        if row is None or row.completed_at is not None:
            return row
        row.completed_at = completed_at or _utcnow()
        await self.session.flush()
        return row

    async def lock_due_for_escalation(
        self,
        *,
        now: datetime,
        limit: int = 50,
    ) -> list[RequestSla]:
        """Fetch open SLA rows eligible for escalation with SKIP LOCKED."""
        result = await self.session.execute(
            select(RequestSla)
            .where(
                RequestSla.completed_at.is_(None),
                RequestSla.first_response_at.is_(None),
                RequestSla.first_response_deadline <= now,
            )
            .order_by(RequestSla.first_response_deadline.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        return list(result.scalars().all())

    async def advance_escalation_level(
        self,
        row: RequestSla,
        *,
        new_level: int,
        manager_telegram_id: int | None = None,
    ) -> bool:
        if row.escalation_level >= new_level:
            return False
        row.escalation_level = new_level
        if manager_telegram_id is not None:
            row.manager_id = manager_telegram_id
        await self.session.flush()
        return True

    async def load_request_context(self, request_id: uuid.UUID | str) -> RequestEscalationContext | None:
        rid = uuid.UUID(str(request_id))
        crm = (
            await self.session.execute(select(ClientRequest).where(ClientRequest.id == rid))
        ).scalar_one_or_none()
        if crm is not None:
            manager_uuid = str(crm.manager_id) if crm.manager_id else None
            manager_telegram_id = await self._telegram_for_manager(crm.manager_id)
            return RequestEscalationContext(
                request_id=str(crm.id),
                request_number=crm.request_number,
                vertical=(crm.request_type or "").split("_")[0].lower(),
                request_type=crm.request_type or "",
                manager_uuid=manager_uuid,
                manager_telegram_id=manager_telegram_id,
                client_telegram_id=crm.client_telegram_id,
            )

        auto = (
            await self.session.execute(select(AutoClientRequest).where(AutoClientRequest.id == rid))
        ).scalar_one_or_none()
        if auto is not None:
            manager_uuid = str(auto.manager_id) if auto.manager_id else None
            manager_telegram_id = await self._telegram_for_manager(auto.manager_id)
            return RequestEscalationContext(
                request_id=str(auto.id),
                request_number=auto.request_number,
                vertical="auto",
                request_type=auto.request_type or "AUTO_REQUEST",
                manager_uuid=manager_uuid,
                manager_telegram_id=manager_telegram_id,
                client_telegram_id=auto.client_telegram_id,
            )
        return None

    async def _telegram_for_manager(self, manager_uuid: uuid.UUID | None) -> int | None:
        if manager_uuid is None:
            return None
        user = (
            await self.session.execute(select(User).where(User.id == manager_uuid))
        ).scalar_one_or_none()
        return user.telegram_id if user else None

    @staticmethod
    def snapshot(row: RequestSla) -> RequestSlaSnapshot:
        return RequestSlaSnapshot(
            request_id=str(row.request_id),
            manager_id=row.manager_id,
            first_response_deadline=row.first_response_deadline,
            completion_deadline=row.completion_deadline,
            escalation_level=row.escalation_level,
            first_response_at=row.first_response_at,
            completed_at=row.completed_at,
            created_at=row.created_at,
        )

    @staticmethod
    def overdue_seconds(row: RequestSla, now: datetime) -> int:
        return max(0, int((now - row.first_response_deadline).total_seconds()))
