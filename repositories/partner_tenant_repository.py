# Partner Tenant Engine v1 repositories.

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.partner_tenant_engine import (
    PartnerTenant,
    TenantBillingAccount,
    TenantBillingAccountType,
    TenantResourceBinding,
    TenantResourceType,
    TenantRoleCode,
    TenantStatus,
    TenantUserRole,
)


class PartnerTenantRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        company_id: uuid.UUID,
        code: str,
        name: str,
        status: str = TenantStatus.ACTIVE.value,
        settings: dict | None = None,
        **extra: Any,
    ) -> PartnerTenant:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if status not in {s.value for s in TenantStatus}:
            raise ValueError(f"Invalid status: {status}")

        tenant = PartnerTenant(
            company_id=company_id,
            code=code.strip().upper(),
            name=name.strip(),
            status=status,
            settings=settings,
        )
        self._session.add(tenant)
        await self._session.flush()
        return tenant

    async def get_by_id(self, tenant_id: uuid.UUID) -> PartnerTenant | None:
        result = await self._session.execute(
            select(PartnerTenant).where(PartnerTenant.id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(
        self,
        company_id: uuid.UUID,
        code: str,
    ) -> PartnerTenant | None:
        result = await self._session.execute(
            select(PartnerTenant).where(
                PartnerTenant.company_id == company_id,
                PartnerTenant.code == code.strip().upper(),
            )
        )
        return result.scalar_one_or_none()

    async def list_by_company(
        self,
        company_id: uuid.UUID,
        *,
        status: str | None = None,
        limit: int = 100,
    ) -> list[PartnerTenant]:
        stmt = (
            select(PartnerTenant)
            .where(PartnerTenant.company_id == company_id)
            .order_by(PartnerTenant.code.asc())
            .limit(limit)
        )
        if status is not None:
            stmt = stmt.where(PartnerTenant.status == status)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_active(self, *, limit: int = 200) -> list[PartnerTenant]:
        result = await self._session.execute(
            select(PartnerTenant)
            .where(PartnerTenant.status == TenantStatus.ACTIVE.value)
            .order_by(PartnerTenant.code.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update(self, tenant: PartnerTenant, **fields: Any) -> PartnerTenant:
        if not fields:
            return tenant
        unknown = set(fields) - {"name", "status", "settings"}
        if unknown:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(unknown))}")
        if "status" in fields and fields["status"] not in {s.value for s in TenantStatus}:
            raise ValueError(f"Invalid status: {fields['status']}")

        for key, value in fields.items():
            setattr(tenant, key, value)
        await self._session.flush()
        return tenant


class TenantUserRoleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def assign(
        self,
        *,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        user_id: int,
        role_code: str,
    ) -> TenantUserRole:
        if role_code not in {r.value for r in TenantRoleCode}:
            raise ValueError(f"Invalid role_code: {role_code}")

        existing = await self.get(tenant_id, user_id)
        if existing is not None:
            existing.role_code = role_code
            await self._session.flush()
            return existing

        row = TenantUserRole(
            tenant_id=tenant_id,
            company_id=company_id,
            user_id=user_id,
            role_code=role_code,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get(self, tenant_id: uuid.UUID, user_id: int) -> TenantUserRole | None:
        result = await self._session.execute(
            select(TenantUserRole).where(
                TenantUserRole.tenant_id == tenant_id,
                TenantUserRole.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_tenant(self, tenant_id: uuid.UUID) -> list[TenantUserRole]:
        result = await self._session.execute(
            select(TenantUserRole)
            .where(TenantUserRole.tenant_id == tenant_id)
            .order_by(TenantUserRole.user_id.asc())
        )
        return list(result.scalars().all())

    async def list_by_user(self, user_id: int) -> list[TenantUserRole]:
        result = await self._session.execute(
            select(TenantUserRole)
            .where(TenantUserRole.user_id == user_id)
            .order_by(TenantUserRole.created_at.desc())
        )
        return list(result.scalars().all())

    async def remove(self, tenant_id: uuid.UUID, user_id: int) -> bool:
        row = await self.get(tenant_id, user_id)
        if row is None:
            return False
        await self._session.delete(row)
        await self._session.flush()
        return True


class TenantResourceBindingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def bind(
        self,
        *,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        resource_type: str,
        resource_id: str,
        notes: str | None = None,
    ) -> TenantResourceBinding:
        if resource_type not in {t.value for t in TenantResourceType}:
            raise ValueError(f"Invalid resource_type: {resource_type}")

        existing = await self.get_binding(tenant_id, resource_type, resource_id)
        if existing is not None:
            return existing

        binding = TenantResourceBinding(
            tenant_id=tenant_id,
            company_id=company_id,
            resource_type=resource_type,
            resource_id=resource_id,
            notes=notes,
        )
        self._session.add(binding)
        await self._session.flush()
        return binding

    async def get_binding(
        self,
        tenant_id: uuid.UUID,
        resource_type: str,
        resource_id: str,
    ) -> TenantResourceBinding | None:
        result = await self._session.execute(
            select(TenantResourceBinding).where(
                TenantResourceBinding.tenant_id == tenant_id,
                TenantResourceBinding.resource_type == resource_type,
                TenantResourceBinding.resource_id == resource_id,
            )
        )
        return result.scalar_one_or_none()

    async def is_bound(
        self,
        tenant_id: uuid.UUID,
        resource_type: str,
        resource_id: str,
    ) -> bool:
        return (await self.get_binding(tenant_id, resource_type, resource_id)) is not None

    async def list_by_tenant(
        self,
        tenant_id: uuid.UUID,
        *,
        resource_type: str | None = None,
        limit: int = 200,
    ) -> list[TenantResourceBinding]:
        stmt = (
            select(TenantResourceBinding)
            .where(TenantResourceBinding.tenant_id == tenant_id)
            .order_by(TenantResourceBinding.created_at.desc())
            .limit(limit)
        )
        if resource_type is not None:
            stmt = stmt.where(TenantResourceBinding.resource_type == resource_type)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


class TenantBillingAccountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        account_type: str,
        asset: str,
        treasury_code: str,
        treasury_account_id: uuid.UUID | None = None,
        billing_plan: str | None = None,
        metadata: dict | None = None,
    ) -> TenantBillingAccount:
        if account_type not in {t.value for t in TenantBillingAccountType}:
            raise ValueError(f"Invalid account_type: {account_type}")

        account = TenantBillingAccount(
            tenant_id=tenant_id,
            company_id=company_id,
            account_type=account_type,
            asset=asset,
            treasury_code=treasury_code,
            treasury_account_id=treasury_account_id,
            billing_plan=billing_plan,
            metadata_=metadata,
        )
        self._session.add(account)
        await self._session.flush()
        return account

    async def list_by_tenant(self, tenant_id: uuid.UUID) -> list[TenantBillingAccount]:
        result = await self._session.execute(
            select(TenantBillingAccount)
            .where(TenantBillingAccount.tenant_id == tenant_id)
            .order_by(TenantBillingAccount.account_type.asc())
        )
        return list(result.scalars().all())

    async def get_by_type_asset(
        self,
        tenant_id: uuid.UUID,
        account_type: str,
        asset: str,
    ) -> TenantBillingAccount | None:
        result = await self._session.execute(
            select(TenantBillingAccount).where(
                TenantBillingAccount.tenant_id == tenant_id,
                TenantBillingAccount.account_type == account_type,
                TenantBillingAccount.asset == asset,
            )
        )
        return result.scalar_one_or_none()
