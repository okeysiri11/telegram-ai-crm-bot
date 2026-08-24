"""AGRO Ops repository — generic kind-discriminated registry (AGRO Production 1.0)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.agro_ops import AgroOpsRecord


def record_to_dict(row: AgroOpsRecord) -> dict[str, Any]:
    data = dict(row.payload or {})
    data["id"] = str(row.id)
    data["organization_id"] = row.organization_id
    data["tenant_id"] = row.tenant_id
    data["status"] = row.status
    data["created_at"] = row.created_at.isoformat() if row.created_at else data.get("created_at")
    data["updated_at"] = row.updated_at.isoformat() if row.updated_at else data.get("updated_at")
    if row.archived_at:
        data["archived_at"] = row.archived_at.isoformat()
        data["archived_by"] = row.archived_by
        data["archive_reason"] = row.archive_reason
    return data


class AgroOpsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_kind(self, organization_id: str, kind: str) -> list[AgroOpsRecord]:
        result = await self.session.execute(
            select(AgroOpsRecord)
            .where(AgroOpsRecord.organization_id == organization_id, AgroOpsRecord.kind == kind)
            .order_by(AgroOpsRecord.created_at.desc())
        )
        return list(result.scalars().all())

    async def get(self, organization_id: str, item_id: str) -> AgroOpsRecord | None:
        try:
            uid = uuid.UUID(str(item_id))
        except ValueError:
            return None
        result = await self.session.execute(
            select(AgroOpsRecord).where(
                AgroOpsRecord.organization_id == organization_id, AgroOpsRecord.id == uid
            )
        )
        return result.scalar_one_or_none()

    async def insert(self, kind: str, data: dict[str, Any]) -> AgroOpsRecord:
        payload = {k: v for k, v in data.items() if k not in {"id", "created_at", "updated_at"}}
        row = AgroOpsRecord(
            id=uuid.UUID(str(data.get("id") or uuid.uuid4())),
            organization_id=str(data.get("organization_id") or "default"),
            tenant_id=str(data.get("tenant_id") or data.get("organization_id") or "default"),
            kind=kind,
            status=str(data.get("status") or "active"),
            payload=payload,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def update(self, row: AgroOpsRecord, patch: dict[str, Any]) -> AgroOpsRecord:
        payload = dict(row.payload or {})
        for key, value in patch.items():
            if key in {"id", "organization_id", "tenant_id", "created_at"}:
                continue
            payload[key] = value
        if "status" in patch:
            row.status = str(patch["status"])
        row.payload = payload
        await self.session.flush()
        return row

    async def archive(self, row: AgroOpsRecord, *, by: str | None, reason: str | None) -> AgroOpsRecord:
        row.archived_at = datetime.now(timezone.utc)
        row.archived_by = by
        row.archive_reason = reason
        payload = dict(row.payload or {})
        payload["archived_at"] = row.archived_at.isoformat()
        row.payload = payload
        await self.session.flush()
        return row

    async def restore(self, row: AgroOpsRecord) -> AgroOpsRecord:
        row.archived_at = None
        row.archived_by = None
        row.archive_reason = None
        payload = dict(row.payload or {})
        payload.pop("archived_at", None)
        row.payload = payload
        await self.session.flush()
        return row
