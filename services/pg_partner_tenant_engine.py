# Partner Tenant Engine v1 — company/tenant isolation for partners.

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from config import OWNER_ID
from database.models.audit_log import AuditAction
from database.models.partner_tenant_engine import (
    TenantBillingAccountType,
    TenantResourceType,
    TenantRoleCode,
    TenantStatus,
)
from database.models.treasury import TreasuryAccountType
from database.session import get_session
from repositories.audit_repository import AuditRepository
from repositories.multi_company_repository import CompanyRepository
from repositories.partner_tenant_repository import (
    PartnerTenantRepository,
    TenantBillingAccountRepository,
    TenantResourceBindingRepository,
    TenantUserRoleRepository,
)
from repositories.treasury_repository import TreasuryRepository
from repositories.user_role_repository import UserRoleRepository

PLATFORM_ADMIN_ROLES = frozenset({"OWNER", "ADMIN"})
TENANT_WRITE_ROLES = frozenset(
    {TenantRoleCode.TENANT_ADMIN.value, TenantRoleCode.TENANT_MANAGER.value}
)
DEFAULT_BILLING_ASSETS = ("USD", "EUR", "USDT")
DEFAULT_BILLING_PLAN = "standard"


@dataclass(frozen=True)
class TenantContext:
    company_id: uuid.UUID
    tenant_id: uuid.UUID
    actor_id: int
    role_code: str | None = None


class PartnerTenantEngineError(Exception):
    pass


class TenantAccessDeniedError(PartnerTenantEngineError):
    pass


class PartnerTenantEngineV1:
    @staticmethod
    async def is_platform_admin(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in PLATFORM_ADMIN_ROLES for role in roles)

    @staticmethod
    def _tenant_snapshot(tenant) -> dict[str, Any]:
        return {
            "tenant_id": str(tenant.id),
            "company_id": str(tenant.company_id),
            "code": tenant.code,
            "name": tenant.name,
            "status": tenant.status,
            "settings": tenant.settings or {},
            "created_at": tenant.created_at.isoformat(),
            "updated_at": tenant.updated_at.isoformat(),
        }

    @staticmethod
    def _user_role_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "tenant_id": str(row.tenant_id),
            "company_id": str(row.company_id),
            "user_id": row.user_id,
            "role_code": row.role_code,
        }

    @staticmethod
    def _binding_snapshot(binding) -> dict[str, Any]:
        return {
            "id": str(binding.id),
            "tenant_id": str(binding.tenant_id),
            "company_id": str(binding.company_id),
            "resource_type": binding.resource_type,
            "resource_id": binding.resource_id,
            "notes": binding.notes,
        }

    @staticmethod
    def _billing_snapshot(account) -> dict[str, Any]:
        return {
            "id": str(account.id),
            "tenant_id": str(account.tenant_id),
            "company_id": str(account.company_id),
            "account_type": account.account_type,
            "asset": account.asset,
            "treasury_code": account.treasury_code,
            "treasury_account_id": str(account.treasury_account_id)
            if account.treasury_account_id
            else None,
            "billing_plan": account.billing_plan,
            "metadata": account.metadata_ or {},
        }

    @staticmethod
    def _audit_snapshot(entry) -> dict[str, Any]:
        return {
            "id": str(entry.id),
            "user_id": entry.user_id,
            "company_id": str(entry.company_id) if entry.company_id else None,
            "tenant_id": str(entry.tenant_id) if entry.tenant_id else None,
            "entity_type": entry.entity_type,
            "entity_id": entry.entity_id,
            "action": entry.action,
            "old_value": entry.old_value,
            "new_value": entry.new_value,
            "created_at": entry.created_at.isoformat(),
        }

    @staticmethod
    async def _audit(
        session,
        *,
        actor_id: int,
        action: str,
        entity_id: str,
        company_id: uuid.UUID | None = None,
        tenant_id: uuid.UUID | None = None,
        old_value: dict | None = None,
        new_value: dict | None = None,
    ) -> None:
        await AuditRepository(session).create_log(
            user_id=actor_id,
            company_id=company_id,
            tenant_id=tenant_id,
            entity_type="tenant",
            entity_id=entity_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
        )

    @staticmethod
    async def resolve_context(
        actor_id: int,
        tenant_id: uuid.UUID,
    ) -> TenantContext:
        async with get_session() as session:
            tenant = await PartnerTenantRepository(session).get_by_id(tenant_id)
            if tenant is None:
                raise PartnerTenantEngineError(f"Tenant not found: {tenant_id}")
            if tenant.status != TenantStatus.ACTIVE.value:
                raise TenantAccessDeniedError(f"Tenant is not active: {tenant.code}")

            if await PartnerTenantEngineV1.is_platform_admin(actor_id):
                return TenantContext(
                    company_id=tenant.company_id,
                    tenant_id=tenant.id,
                    actor_id=actor_id,
                    role_code=TenantRoleCode.TENANT_ADMIN.value,
                )

            assignment = await TenantUserRoleRepository(session).get(tenant_id, actor_id)
            if assignment is None:
                raise TenantAccessDeniedError("No tenant membership")

            return TenantContext(
                company_id=tenant.company_id,
                tenant_id=tenant.id,
                actor_id=actor_id,
                role_code=assignment.role_code,
            )

    @staticmethod
    async def user_can_access_tenant(actor_id: int, tenant_id: uuid.UUID) -> bool:
        try:
            await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)
            return True
        except (PartnerTenantEngineError, TenantAccessDeniedError):
            return False

    @staticmethod
    async def assert_tenant_write(ctx: TenantContext) -> None:
        if await PartnerTenantEngineV1.is_platform_admin(ctx.actor_id):
            return
        if ctx.role_code not in TENANT_WRITE_ROLES:
            raise TenantAccessDeniedError("Tenant write access denied")

    @staticmethod
    async def assert_resource_access(
        ctx: TenantContext,
        resource_type: str,
        resource_id: str,
    ) -> None:
        async with get_session() as session:
            bound = await TenantResourceBindingRepository(session).is_bound(
                ctx.tenant_id,
                resource_type,
                resource_id,
            )
            if not bound:
                raise TenantAccessDeniedError(
                    f"Resource not in tenant scope: {resource_type}:{resource_id}"
                )

    @staticmethod
    async def create_tenant(
        actor_id: int,
        *,
        company_id: uuid.UUID,
        code: str,
        name: str,
        settings: dict | None = None,
        provision_billing: bool = True,
    ) -> dict[str, Any]:
        if not await PartnerTenantEngineV1.is_platform_admin(actor_id):
            raise TenantAccessDeniedError("Platform admin access required")

        async with get_session() as session:
            company = await CompanyRepository(session).get_by_id(company_id)
            if company is None:
                raise PartnerTenantEngineError(f"Company not found: {company_id}")

            tenant_repo = PartnerTenantRepository(session)
            if await tenant_repo.get_by_code(company_id, code) is not None:
                raise PartnerTenantEngineError(f"Tenant code already exists: {code}")

            tenant = await tenant_repo.create(
                company_id=company_id,
                code=code,
                name=name,
                settings=settings,
            )
            await TenantUserRoleRepository(session).assign(
                tenant_id=tenant.id,
                company_id=company_id,
                user_id=actor_id,
                role_code=TenantRoleCode.TENANT_ADMIN.value,
            )
            billing: list[dict[str, Any]] = []
            if provision_billing:
                billing = await PartnerTenantEngineV1._provision_billing_accounts(
                    session,
                    tenant=tenant,
                )

            await PartnerTenantEngineV1._audit(
                session,
                actor_id=actor_id,
                action=AuditAction.CREATE_TENANT.value,
                entity_id=str(tenant.id),
                company_id=company_id,
                tenant_id=tenant.id,
                new_value=PartnerTenantEngineV1._tenant_snapshot(tenant),
            )
            await session.refresh(tenant)
            snapshot = PartnerTenantEngineV1._tenant_snapshot(tenant)
            snapshot["billing_accounts"] = billing
            sync_payload = {
                "tenant_id": tenant.id,
                "company_id": tenant.company_id,
                "code": tenant.code,
                "name": tenant.name,
                "member_user_id": actor_id,
            }

        from services.pg_multi_tenant_foundation_engine import MultiTenantFoundationEngineV1

        await MultiTenantFoundationEngineV1.sync_tenant_from_partner(**sync_payload)
        return snapshot

    @staticmethod
    async def _provision_billing_accounts(session, *, tenant) -> list[dict[str, Any]]:
        treasury_repo = TreasuryRepository(session)
        billing_repo = TenantBillingAccountRepository(session)
        created: list[dict[str, Any]] = []

        for asset in DEFAULT_BILLING_ASSETS:
            for account_type in (
                TenantBillingAccountType.OPERATING,
                TenantBillingAccountType.SETTLEMENT,
            ):
                treasury_type = (
                    TreasuryAccountType.OPERATING.value
                    if account_type == TenantBillingAccountType.OPERATING
                    else TreasuryAccountType.SETTLEMENT.value
                )
                code = f"{tenant.code}-{account_type.value.lower()}-{asset}".lower()
                treasury_account = await treasury_repo.create_account(
                    code=code,
                    name=f"{tenant.name} {account_type.value} {asset}",
                    asset=asset,
                    account_type=treasury_type,
                    balance=Decimal("0"),
                )
                billing = await billing_repo.create(
                    tenant_id=tenant.id,
                    company_id=tenant.company_id,
                    account_type=account_type.value,
                    asset=asset,
                    treasury_code=code,
                    treasury_account_id=treasury_account.id,
                    billing_plan=DEFAULT_BILLING_PLAN,
                    metadata={"isolated": True},
                )
                created.append(PartnerTenantEngineV1._billing_snapshot(billing))

        await PartnerTenantEngineV1._audit(
            session,
            actor_id=OWNER_ID,
            action=AuditAction.TENANT_BILLING_PROVISION.value,
            entity_id=str(tenant.id),
            company_id=tenant.company_id,
            tenant_id=tenant.id,
            new_value={"accounts": created},
        )
        return created

    @staticmethod
    async def assign_user(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        user_id: int,
        role_code: str,
    ) -> dict[str, Any]:
        ctx = await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)
        await PartnerTenantEngineV1.assert_tenant_write(ctx)

        async with get_session() as session:
            tenant = await PartnerTenantRepository(session).get_by_id(tenant_id)
            if tenant is None:
                raise PartnerTenantEngineError(f"Tenant not found: {tenant_id}")

            row = await TenantUserRoleRepository(session).assign(
                tenant_id=tenant_id,
                company_id=tenant.company_id,
                user_id=user_id,
                role_code=role_code,
            )
            await PartnerTenantEngineV1._audit(
                session,
                actor_id=actor_id,
                action=AuditAction.ASSIGN_TENANT_USER.value,
                entity_id=str(tenant_id),
                company_id=tenant.company_id,
                tenant_id=tenant_id,
                new_value=PartnerTenantEngineV1._user_role_snapshot(row),
            )
            return PartnerTenantEngineV1._user_role_snapshot(row)

    @staticmethod
    async def bind_resource(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        resource_type: str,
        resource_id: str,
        notes: str | None = None,
    ) -> dict[str, Any]:
        ctx = await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)
        await PartnerTenantEngineV1.assert_tenant_write(ctx)

        async with get_session() as session:
            binding = await TenantResourceBindingRepository(session).bind(
                tenant_id=ctx.tenant_id,
                company_id=ctx.company_id,
                resource_type=resource_type,
                resource_id=resource_id,
                notes=notes,
            )
            await PartnerTenantEngineV1._audit(
                session,
                actor_id=actor_id,
                action=AuditAction.TENANT_RESOURCE_BIND.value,
                entity_id=str(ctx.tenant_id),
                company_id=ctx.company_id,
                tenant_id=ctx.tenant_id,
                new_value=PartnerTenantEngineV1._binding_snapshot(binding),
            )
            return PartnerTenantEngineV1._binding_snapshot(binding)

    @staticmethod
    async def list_resources(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        resource_type: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        ctx = await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)

        async with get_session() as session:
            rows = await TenantResourceBindingRepository(session).list_by_tenant(
                ctx.tenant_id,
                resource_type=resource_type,
                limit=limit,
            )
            return [PartnerTenantEngineV1._binding_snapshot(r) for r in rows]

    @staticmethod
    async def list_tenant_users(
        actor_id: int,
        tenant_id: uuid.UUID,
    ) -> list[dict[str, Any]]:
        await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)

        async with get_session() as session:
            rows = await TenantUserRoleRepository(session).list_by_tenant(tenant_id)
            return [PartnerTenantEngineV1._user_role_snapshot(r) for r in rows]

    @staticmethod
    async def list_billing_accounts(
        actor_id: int,
        tenant_id: uuid.UUID,
    ) -> list[dict[str, Any]]:
        await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)

        async with get_session() as session:
            rows = await TenantBillingAccountRepository(session).list_by_tenant(tenant_id)
            return [PartnerTenantEngineV1._billing_snapshot(r) for r in rows]

    @staticmethod
    async def list_tenant_audit(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)

        async with get_session() as session:
            rows = await AuditRepository(session).list_by_tenant(tenant_id, limit=limit)
            return [PartnerTenantEngineV1._audit_snapshot(r) for r in rows]

    @staticmethod
    async def list_tenants(
        actor_id: int,
        *,
        company_id: uuid.UUID | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if not await PartnerTenantEngineV1.is_platform_admin(actor_id):
            async with get_session() as session:
                memberships = await TenantUserRoleRepository(session).list_by_user(actor_id)
                tenant_ids = {m.tenant_id for m in memberships}
                tenants: list[dict[str, Any]] = []
                repo = PartnerTenantRepository(session)
                for tenant_id in tenant_ids:
                    tenant = await repo.get_by_id(tenant_id)
                    if tenant is None:
                        continue
                    if company_id is not None and tenant.company_id != company_id:
                        continue
                    tenants.append(PartnerTenantEngineV1._tenant_snapshot(tenant))
                return tenants[:limit]

        async with get_session() as session:
            repo = PartnerTenantRepository(session)
            if company_id is not None:
                rows = await repo.list_by_company(company_id, limit=limit)
            else:
                rows = await repo.list_active(limit=limit)
            return [PartnerTenantEngineV1._tenant_snapshot(t) for t in rows]

    @staticmethod
    async def update_tenant_status(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        status: str,
    ) -> dict[str, Any]:
        if not await PartnerTenantEngineV1.is_platform_admin(actor_id):
            raise TenantAccessDeniedError("Platform admin access required")
        if status not in {s.value for s in TenantStatus}:
            raise PartnerTenantEngineError(f"Invalid status: {status}")

        async with get_session() as session:
            repo = PartnerTenantRepository(session)
            tenant = await repo.get_by_id(tenant_id)
            if tenant is None:
                raise PartnerTenantEngineError(f"Tenant not found: {tenant_id}")

            old_status = tenant.status
            await repo.update(tenant, status=status)
            action = (
                AuditAction.SUSPEND_TENANT.value
                if status == TenantStatus.SUSPENDED.value
                else AuditAction.UPDATE_TENANT.value
            )
            await PartnerTenantEngineV1._audit(
                session,
                actor_id=actor_id,
                action=action,
                entity_id=str(tenant_id),
                company_id=tenant.company_id,
                tenant_id=tenant_id,
                old_value={"status": old_status},
                new_value={"status": status},
            )
            await session.refresh(tenant)
            return PartnerTenantEngineV1._tenant_snapshot(tenant)

    @staticmethod
    async def bind_partner(
        actor_id: int,
        tenant_id: uuid.UUID,
        partner_id: uuid.UUID,
        *,
        notes: str | None = None,
    ) -> dict[str, Any]:
        return await PartnerTenantEngineV1.bind_resource(
            actor_id,
            tenant_id,
            resource_type=TenantResourceType.PARTNER.value,
            resource_id=str(partner_id),
            notes=notes,
        )

    @staticmethod
    async def ensure_default_tenant(
        actor_id: int,
        *,
        company_code: str = "DEFAULT",
        tenant_code: str = "DEFAULT",
        tenant_name: str = "Default Partner Tenant",
    ) -> dict[str, Any]:
        if not await PartnerTenantEngineV1.is_platform_admin(actor_id):
            raise TenantAccessDeniedError("Platform admin access required")

        async with get_session() as session:
            company = await CompanyRepository(session).get_by_code(company_code)
            if company is None:
                raise PartnerTenantEngineError(f"Company not found: {company_code}")

            existing = await PartnerTenantRepository(session).get_by_code(
                company.id,
                tenant_code,
            )
            if existing is not None:
                return PartnerTenantEngineV1._tenant_snapshot(existing)

        return await PartnerTenantEngineV1.create_tenant(
            actor_id,
            company_id=company.id,
            code=tenant_code,
            name=tenant_name,
            provision_billing=True,
        )
