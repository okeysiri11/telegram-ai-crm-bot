# Channel Integration Engine v1 repository.

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.channel_integration_engine import (
    CHANNEL_PERMISSIONS,
    INTEGRATION_CHANNEL_TYPES,
    ChannelIntegration,
    ChannelIntegrationStatus,
)


class ChannelIntegrationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        channel_id: str,
        channel_type: str,
        permissions: str,
        token_reference: str,
        display_name: str | None = None,
        status: str = ChannelIntegrationStatus.ACTIVE.value,
        metadata: dict | None = None,
    ) -> ChannelIntegration:
        if channel_type not in INTEGRATION_CHANNEL_TYPES:
            raise ValueError(f"Invalid channel_type: {channel_type}")
        if permissions not in CHANNEL_PERMISSIONS:
            raise ValueError(f"Invalid permissions: {permissions}")
        if status not in {s.value for s in ChannelIntegrationStatus}:
            raise ValueError(f"Invalid status: {status}")
        if not token_reference.strip():
            raise ValueError("token_reference is required")

        row = ChannelIntegration(
            tenant_id=tenant_id,
            company_id=company_id,
            channel_id=channel_id.strip(),
            channel_type=channel_type,
            permissions=permissions,
            token_reference=token_reference.strip(),
            display_name=display_name,
            status=status,
            metadata_=metadata,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_by_id(self, integration_id: uuid.UUID) -> ChannelIntegration | None:
        result = await self._session.execute(
            select(ChannelIntegration).where(ChannelIntegration.id == integration_id)
        )
        return result.scalar_one_or_none()

    async def get_by_channel(
        self,
        tenant_id: uuid.UUID,
        channel_type: str,
        channel_id: str,
    ) -> ChannelIntegration | None:
        result = await self._session.execute(
            select(ChannelIntegration).where(
                ChannelIntegration.tenant_id == tenant_id,
                ChannelIntegration.channel_type == channel_type,
                ChannelIntegration.channel_id == channel_id.strip(),
            )
        )
        return result.scalar_one_or_none()

    async def list_by_tenant(
        self,
        tenant_id: uuid.UUID,
        *,
        channel_type: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[ChannelIntegration]:
        stmt = (
            select(ChannelIntegration)
            .where(ChannelIntegration.tenant_id == tenant_id)
            .order_by(ChannelIntegration.created_at.desc())
            .limit(limit)
        )
        if channel_type is not None:
            stmt = stmt.where(ChannelIntegration.channel_type == channel_type)
        if status is not None:
            stmt = stmt.where(ChannelIntegration.status == status)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, row: ChannelIntegration, **fields: Any) -> ChannelIntegration:
        allowed = {"permissions", "token_reference", "display_name", "status", "metadata_"}
        unknown = set(fields) - allowed
        if unknown:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(unknown))}")
        if "permissions" in fields and fields["permissions"] not in CHANNEL_PERMISSIONS:
            raise ValueError(f"Invalid permissions: {fields['permissions']}")
        if "status" in fields and fields["status"] not in {
            s.value for s in ChannelIntegrationStatus
        }:
            raise ValueError(f"Invalid status: {fields['status']}")
        if "token_reference" in fields and not str(fields["token_reference"]).strip():
            raise ValueError("token_reference is required")

        if "metadata" in fields:
            fields["metadata_"] = fields.pop("metadata")

        for key, value in fields.items():
            setattr(row, key, value)
        await self._session.flush()
        return row
