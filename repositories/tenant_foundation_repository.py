# Multi-Tenant Foundation v1 repositories.

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.multi_tenant_foundation import Tenant, TenantLimits, TenantSettings


class TenantFoundationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, tenant_id: uuid.UUID) -> Tenant | None:
        result = await self._session.execute(select(Tenant).where(Tenant.id == tenant_id))
        return result.scalar_one_or_none()

    async def get_by_code(self, company_id: uuid.UUID, code: str) -> Tenant | None:
        result = await self._session.execute(
            select(Tenant).where(
                Tenant.company_id == company_id,
                Tenant.code == code.strip().upper(),
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        tenant_id: uuid.UUID | None = None,
        company_id: uuid.UUID,
        code: str,
        name: str,
        status: str = "ACTIVE",
        **extra: Any,
    ) -> Tenant:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        tenant = Tenant(
            id=tenant_id or uuid.uuid4(),
            company_id=company_id,
            code=code.strip().upper(),
            name=name.strip(),
            status=status,
        )
        self._session.add(tenant)
        await self._session.flush()
        return tenant

    async def list_active(self, *, limit: int = 200) -> list[Tenant]:
        result = await self._session.execute(
            select(Tenant).where(Tenant.status == "ACTIVE").order_by(Tenant.code).limit(limit)
        )
        return list(result.scalars().all())


class TenantSettingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_for_tenant(self, tenant_id: uuid.UUID) -> TenantSettings | None:
        result = await self._session.execute(
            select(TenantSettings).where(TenantSettings.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def create_default(self, tenant_id: uuid.UUID, *, plan_code: str | None = None) -> TenantSettings:
        settings = TenantSettings(tenant_id=tenant_id, features={"plan_code": plan_code} if plan_code else None)
        self._session.add(settings)
        await self._session.flush()
        return settings


class TenantLimitsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_for_tenant(self, tenant_id: uuid.UUID) -> TenantLimits | None:
        result = await self._session.execute(
            select(TenantLimits).where(TenantLimits.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def create_default(self, tenant_id: uuid.UUID, *, plan_code: str | None = None) -> TenantLimits:
        limits = TenantLimits(tenant_id=tenant_id, plan_code=plan_code)
        self._session.add(limits)
        await self._session.flush()
        return limits
