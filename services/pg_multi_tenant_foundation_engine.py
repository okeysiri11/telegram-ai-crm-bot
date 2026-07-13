# Multi-Tenant Foundation v1 — tenant registry, onboarding, settings, limits.

from __future__ import annotations

import uuid
from typing import Any

from config import OWNER_ID
from database.models.partner_tenant_engine import TenantRoleCode
from database.session import get_session
from repositories.partner_tenant_repository import TenantUserRoleRepository
from repositories.tenant_foundation_repository import (
    TenantFoundationRepository,
    TenantLimitsRepository,
    TenantSettingsRepository,
)
from services.tenant_context import TenantContextService


class MultiTenantFoundationError(Exception):
    pass


class MultiTenantFoundationEngineV1:
    @staticmethod
    async def sync_tenant_from_partner(
        *,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        code: str,
        name: str,
        status: str = "ACTIVE",
        plan_code: str | None = None,
        member_user_id: int | None = None,
    ) -> dict[str, Any]:
        """Register partner tenant in foundation tables with settings/limits."""
        async with get_session() as session:
            tenant_repo = TenantFoundationRepository(session)
            existing = await tenant_repo.get_by_id(tenant_id)
            if existing is None:
                tenant = await tenant_repo.create(
                    tenant_id=tenant_id,
                    company_id=company_id,
                    code=code,
                    name=name,
                    status=status,
                )
            else:
                tenant = existing

            settings_repo = TenantSettingsRepository(session)
            if await settings_repo.get_for_tenant(tenant.id) is None:
                await settings_repo.create_default(tenant.id, plan_code=plan_code)

            limits_repo = TenantLimitsRepository(session)
            if await limits_repo.get_for_tenant(tenant.id) is None:
                await limits_repo.create_default(tenant.id, plan_code=plan_code)

            if member_user_id is not None:
                role_repo = TenantUserRoleRepository(session)
                if await role_repo.get(tenant.id, member_user_id) is None:
                    await role_repo.assign(
                        tenant_id=tenant.id,
                        company_id=company_id,
                        user_id=member_user_id,
                        role_code=TenantRoleCode.TENANT_ADMIN.value,
                    )
                TenantContextService.set_active_tenant(member_user_id, tenant.id)

            return {
                "tenant_id": str(tenant.id),
                "company_id": str(tenant.company_id),
                "code": tenant.code,
                "name": tenant.name,
            }

    @staticmethod
    async def onboard_client_user(
        user_id: int,
        *,
        company_id: uuid.UUID,
        code: str,
        name: str,
        plan_code: str | None = None,
    ) -> dict[str, Any]:
        """Create foundation tenant during client onboarding."""
        from services.pg_partner_tenant_engine import PartnerTenantEngineV1

        partner = await PartnerTenantEngineV1.create_tenant(
            OWNER_ID,
            company_id=company_id,
            code=code,
            name=name,
            provision_billing=True,
        )
        tenant_id = uuid.UUID(partner["tenant_id"])
        return await MultiTenantFoundationEngineV1.sync_tenant_from_partner(
            tenant_id=tenant_id,
            company_id=uuid.UUID(partner["company_id"]),
            code=partner["code"],
            name=partner["name"],
            plan_code=plan_code,
            member_user_id=user_id,
        )

    @staticmethod
    async def get_settings(tenant_id: uuid.UUID) -> dict[str, Any] | None:
        async with get_session() as session:
            row = await TenantSettingsRepository(session).get_for_tenant(tenant_id)
            if row is None:
                return None
            return {
                "tenant_id": str(row.tenant_id),
                "timezone": row.timezone,
                "locale": row.locale,
                "branding": row.branding,
                "features": row.features,
                "onboarding_completed": row.onboarding_completed,
            }

    @staticmethod
    async def get_limits(tenant_id: uuid.UUID) -> dict[str, Any] | None:
        async with get_session() as session:
            row = await TenantLimitsRepository(session).get_for_tenant(tenant_id)
            if row is None:
                return None
            return {
                "tenant_id": str(row.tenant_id),
                "max_users": row.max_users,
                "max_cars": row.max_cars,
                "max_leads": row.max_leads,
                "max_campaigns": row.max_campaigns,
                "max_documents": row.max_documents,
                "plan_code": row.plan_code,
            }
