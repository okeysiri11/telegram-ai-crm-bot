# Tenant context resolution and per-user active tenant session.

from __future__ import annotations

import uuid
from dataclasses import dataclass

from config import OWNER_ID
from database.session import get_session
from repositories.partner_tenant_repository import TenantUserRoleRepository


@dataclass(frozen=True)
class ActiveTenantContext:
    tenant_id: uuid.UUID
    company_id: uuid.UUID
    user_id: int
    role_code: str | None = None


_active_tenant_by_user: dict[int, uuid.UUID] = {}


class TenantContextService:
    @staticmethod
    def set_active_tenant(user_id: int, tenant_id: uuid.UUID) -> None:
        _active_tenant_by_user[user_id] = tenant_id

    @staticmethod
    def clear_active_tenant(user_id: int) -> None:
        _active_tenant_by_user.pop(user_id, None)

    @staticmethod
    def get_cached_tenant_id(user_id: int) -> uuid.UUID | None:
        return _active_tenant_by_user.get(user_id)

    @staticmethod
    async def list_user_tenant_ids(user_id: int) -> list[uuid.UUID]:
        async with get_session() as session:
            roles = await TenantUserRoleRepository(session).list_by_user(user_id)
            return [role.tenant_id for role in roles]

    @staticmethod
    async def resolve_for_user(user_id: int) -> ActiveTenantContext | None:
        if user_id == OWNER_ID:
            from sqlalchemy import select

            from database.models.multi_tenant_foundation import Tenant

            async with get_session() as session:
                result = await session.execute(
                    select(Tenant).where(Tenant.status == "ACTIVE").order_by(Tenant.code).limit(1)
                )
                tenant = result.scalar_one_or_none()
                if tenant is None:
                    return None
                return ActiveTenantContext(
                    tenant_id=tenant.id,
                    company_id=tenant.company_id,
                    user_id=user_id,
                    role_code="PLATFORM_OWNER",
                )

        cached = TenantContextService.get_cached_tenant_id(user_id)
        if cached is not None:
            async with get_session() as session:
                assignment = await TenantUserRoleRepository(session).get(cached, user_id)
                if assignment is not None:
                    return ActiveTenantContext(
                        tenant_id=assignment.tenant_id,
                        company_id=assignment.company_id,
                        user_id=user_id,
                        role_code=assignment.role_code,
                    )

        async with get_session() as session:
            roles = await TenantUserRoleRepository(session).list_by_user(user_id)
            if not roles:
                return None
            primary = roles[0]
            TenantContextService.set_active_tenant(user_id, primary.tenant_id)
            return ActiveTenantContext(
                tenant_id=primary.tenant_id,
                company_id=primary.company_id,
                user_id=user_id,
                role_code=primary.role_code,
            )

    @staticmethod
    async def require_tenant_id(user_id: int) -> uuid.UUID:
        ctx = await TenantContextService.resolve_for_user(user_id)
        if ctx is None:
            raise PermissionError("No active tenant context")
        return ctx.tenant_id
