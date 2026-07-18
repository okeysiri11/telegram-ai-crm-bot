# Manager pool repository — PostgreSQL persistence for dynamic assignment.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import func, select, update

from database.models.auto_client_request import AutoClientRequest
from database.models.client_request import ClientRequest
from database.models.manager_pool import ManagerPoolEntry
from database.models.users import User
from models.manager_pool import ManagerPoolSnapshot
from src.platform.layers.base_repository import BaseRepository


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _snapshot(row: ManagerPoolEntry) -> ManagerPoolSnapshot:
    return ManagerPoolSnapshot(
        id=str(row.id),
        telegram_id=int(row.telegram_id),
        name=row.name,
        vertical=row.vertical,
        priority=int(row.priority),
        weight=int(row.weight),
        is_active=bool(row.is_active),
        current_load=int(row.current_load),
        last_assigned_at=row.last_assigned_at,
    )


class ManagerPoolRepository(BaseRepository):
    async def list_all(self, *, vertical: str | None = None) -> list[ManagerPoolSnapshot]:
        stmt = select(ManagerPoolEntry)
        if vertical:
            stmt = stmt.where(ManagerPoolEntry.vertical == vertical)
        stmt = stmt.order_by(ManagerPoolEntry.vertical, ManagerPoolEntry.priority.desc())
        result = await self.session.execute(stmt)
        return [_snapshot(row) for row in result.scalars().all()]

    async def get_available_managers(
        self,
        vertical: str,
        *,
        for_update: bool = False,
        skip_locked: bool = False,
    ) -> list[ManagerPoolSnapshot]:
        stmt = (
            select(ManagerPoolEntry)
            .where(
                ManagerPoolEntry.vertical == vertical,
                ManagerPoolEntry.is_active.is_(True),
            )
            .order_by(
                ManagerPoolEntry.current_load.asc(),
                ManagerPoolEntry.priority.desc(),
                ManagerPoolEntry.last_assigned_at.asc().nullsfirst(),
            )
        )
        if for_update:
            stmt = stmt.with_for_update(skip_locked=skip_locked)
        result = await self.session.execute(stmt)
        return [_snapshot(row) for row in result.scalars().all()]

    async def get_manager_by_id(self, manager_id: uuid.UUID | str) -> ManagerPoolSnapshot | None:
        rid = uuid.UUID(str(manager_id))
        result = await self.session.execute(
            select(ManagerPoolEntry).where(ManagerPoolEntry.id == rid)
        )
        row = result.scalar_one_or_none()
        return _snapshot(row) if row else None

    async def get_by_telegram_and_vertical(
        self,
        telegram_id: int,
        vertical: str,
    ) -> ManagerPoolSnapshot | None:
        result = await self.session.execute(
            select(ManagerPoolEntry).where(
                ManagerPoolEntry.telegram_id == telegram_id,
                ManagerPoolEntry.vertical == vertical,
            )
        )
        row = result.scalar_one_or_none()
        return _snapshot(row) if row else None

    async def upsert_manager(
        self,
        *,
        telegram_id: int,
        name: str,
        vertical: str,
        priority: int = 100,
        weight: int = 100,
        is_active: bool = True,
    ) -> ManagerPoolSnapshot:
        result = await self.session.execute(
            select(ManagerPoolEntry).where(
                ManagerPoolEntry.telegram_id == telegram_id,
                ManagerPoolEntry.vertical == vertical,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = ManagerPoolEntry(
                telegram_id=telegram_id,
                name=name,
                vertical=vertical,
                priority=priority,
                weight=weight,
                is_active=is_active,
                current_load=0,
            )
            self.session.add(row)
        else:
            row.name = name
            row.priority = priority
            row.weight = weight
            row.is_active = is_active
        await self.session.flush()
        return _snapshot(row)

    async def update_load(
        self,
        manager_id: uuid.UUID | str,
        *,
        delta: int = 0,
        absolute: int | None = None,
    ) -> ManagerPoolSnapshot | None:
        rid = uuid.UUID(str(manager_id))
        result = await self.session.execute(
            select(ManagerPoolEntry).where(ManagerPoolEntry.id == rid).with_for_update()
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        if absolute is not None:
            row.current_load = max(0, int(absolute))
        else:
            row.current_load = max(0, int(row.current_load) + int(delta))
        await self.session.flush()
        return _snapshot(row)

    async def touch_last_assigned(self, manager_id: uuid.UUID | str) -> ManagerPoolSnapshot | None:
        rid = uuid.UUID(str(manager_id))
        result = await self.session.execute(
            select(ManagerPoolEntry).where(ManagerPoolEntry.id == rid).with_for_update()
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        row.last_assigned_at = _utcnow()
        await self.session.flush()
        return _snapshot(row)

    async def enable_manager(self, manager_id: uuid.UUID | str) -> ManagerPoolSnapshot | None:
        rid = uuid.UUID(str(manager_id))
        result = await self.session.execute(
            select(ManagerPoolEntry).where(ManagerPoolEntry.id == rid)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        row.is_active = True
        await self.session.flush()
        return _snapshot(row)

    async def disable_manager(self, manager_id: uuid.UUID | str) -> ManagerPoolSnapshot | None:
        rid = uuid.UUID(str(manager_id))
        result = await self.session.execute(
            select(ManagerPoolEntry).where(ManagerPoolEntry.id == rid)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        row.is_active = False
        await self.session.flush()
        return _snapshot(row)

    async def count_active_for_telegram(self, telegram_id: int) -> int:
        user = (
            await self.session.execute(select(User).where(User.telegram_id == telegram_id))
        ).scalar_one_or_none()
        if user is None:
            return 0

        active_statuses = ("ASSIGNED", "IN_PROGRESS", "WAITING_CLIENT", "NEW")
        crm_count = (
            await self.session.execute(
                select(func.count())
                .select_from(ClientRequest)
                .where(
                    ClientRequest.manager_id == user.id,
                    ClientRequest.status.in_(active_statuses),
                )
            )
        ).scalar_one()

        auto_count = (
            await self.session.execute(
                select(func.count())
                .select_from(AutoClientRequest)
                .where(
                    AutoClientRequest.manager_id == user.id,
                    AutoClientRequest.status.in_(active_statuses),
                )
            )
        ).scalar_one()

        return int(crm_count or 0) + int(auto_count or 0)

    async def count_active_requests(self) -> int:
        active_statuses = ("ASSIGNED", "IN_PROGRESS", "WAITING_CLIENT", "NEW")
        crm_count = (
            await self.session.execute(
                select(func.count())
                .select_from(ClientRequest)
                .where(ClientRequest.status.in_(active_statuses))
            )
        ).scalar_one()
        auto_count = (
            await self.session.execute(
                select(func.count())
                .select_from(AutoClientRequest)
                .where(AutoClientRequest.status.in_(active_statuses))
            )
        ).scalar_one()
        return int(crm_count or 0) + int(auto_count or 0)

    async def average_response_seconds_for_pool(
        self,
        telegram_ids: Sequence[int],
    ) -> float | None:
        if not telegram_ids:
            return None
        from database.models.platform_metrics import RequestMetric

        result = await self.session.execute(
            select(func.avg(RequestMetric.time_to_first_response_seconds)).where(
                RequestMetric.manager_id.in_(
                    select(User.id).where(User.telegram_id.in_(telegram_ids))
                ),
                RequestMetric.time_to_first_response_seconds.is_not(None),
            )
        )
        avg_val = result.scalar_one_or_none()
        return float(avg_val) if avg_val is not None else None

    async def set_loads_bulk(self, loads: dict[uuid.UUID, int]) -> None:
        for pool_id, load in loads.items():
            await self.session.execute(
                update(ManagerPoolEntry)
                .where(ManagerPoolEntry.id == pool_id)
                .values(current_load=max(0, int(load)))
            )
        await self.session.flush()
