# Audit trail repository — PostgreSQL persistence.

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from audit.audit_event import AuditRecord
from database.models.audit_events import AuditEventRow
from src.platform.layers.base_repository import BaseRepository


class AuditRepository(BaseRepository):
    async def insert(self, record: AuditRecord) -> AuditEventRow:
        row = AuditEventRow(
            event_type=record.event_type,
            entity_type=record.entity_type,
            entity_id=record.entity_id,
            actor_id=record.actor_id,
            old_value=record.old_value,
            new_value=record.new_value,
            metadata_json=record.metadata_json,
            created_at=record.created_at,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def list_by_request_id(
        self,
        request_id: str,
        *,
        limit: int = 200,
    ) -> list[AuditEventRow]:
        result = await self.session.execute(
            select(AuditEventRow)
            .where(
                AuditEventRow.entity_type == "client_request",
                AuditEventRow.entity_id == str(request_id),
            )
            .order_by(AuditEventRow.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_by_request_number(
        self,
        request_number: str,
        *,
        limit: int = 200,
    ) -> list[AuditEventRow]:
        result = await self.session.execute(
            select(AuditEventRow)
            .where(
                AuditEventRow.metadata_json["request_number"].as_string() == request_number,
            )
            .order_by(AuditEventRow.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_by_manager_id(
        self,
        manager_id: str,
        *,
        limit: int = 200,
    ) -> list[AuditEventRow]:
        result = await self.session.execute(
            select(AuditEventRow)
            .where(
                AuditEventRow.metadata_json["manager_id"].as_string() == str(manager_id),
            )
            .order_by(AuditEventRow.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def search(
        self,
        *,
        event_type: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        limit: int = 100,
    ) -> list[AuditEventRow]:
        stmt = select(AuditEventRow).order_by(AuditEventRow.created_at.desc()).limit(limit)
        if event_type:
            stmt = stmt.where(AuditEventRow.event_type == event_type)
        if entity_type:
            stmt = stmt.where(AuditEventRow.entity_type == entity_type)
        if entity_id:
            stmt = stmt.where(AuditEventRow.entity_id == str(entity_id))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    def snapshot(row: AuditEventRow) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "event_type": row.event_type,
            "entity_type": row.entity_type,
            "entity_id": row.entity_id,
            "actor_id": row.actor_id,
            "old_value": row.old_value,
            "new_value": row.new_value,
            "metadata_json": row.metadata_json,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
