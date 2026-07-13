# Channel Integration Engine v1 — connect and manage tenant channels.

from __future__ import annotations

import uuid
from typing import Any, Literal

from config import OWNER_ID
from database.models.audit_log import AuditAction
from database.models.channel_integration_engine import (
    CHANNEL_PERMISSIONS,
    INTEGRATION_CHANNEL_TYPES,
    ChannelIntegrationStatus,
    ChannelPermission,
)
from database.models.partner_tenant_engine import TenantResourceType
from database.session import get_session
from repositories.audit_repository import AuditRepository
from repositories.channel_integration_repository import ChannelIntegrationRepository
from repositories.partner_tenant_repository import PartnerTenantRepository
from repositories.user_role_repository import UserRoleRepository
from services.pg_partner_tenant_engine import (
    PartnerTenantEngineV1,
    TenantAccessDeniedError,
)

PLATFORM_ADMIN_ROLES = frozenset({"OWNER", "ADMIN"})
ChannelAction = Literal["read", "post", "analytics"]


class ChannelIntegrationEngineError(Exception):
    pass


class ChannelIntegrationEngineV1:
    @staticmethod
    async def is_platform_admin(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in PLATFORM_ADMIN_ROLES for role in roles)

    @staticmethod
    def _snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "tenant_id": str(row.tenant_id),
            "company_id": str(row.company_id),
            "channel_id": row.channel_id,
            "channel_type": row.channel_type,
            "permissions": row.permissions,
            "token_reference": row.token_reference,
            "status": row.status,
            "display_name": row.display_name,
            "metadata": row.metadata_ or {},
            "created_at": row.created_at.isoformat(),
            "updated_at": row.updated_at.isoformat(),
        }

    @staticmethod
    def permission_allows(permissions: str, action: ChannelAction) -> bool:
        if permissions not in CHANNEL_PERMISSIONS:
            return False
        if action == "read":
            return True
        if action == "post":
            return permissions in {
                ChannelPermission.POST_ONLY.value,
                ChannelPermission.POST_AND_ANALYTICS.value,
            }
        if action == "analytics":
            return permissions == ChannelPermission.POST_AND_ANALYTICS.value
        return False

    @staticmethod
    async def _audit(
        session,
        *,
        actor_id: int,
        action: str,
        entity_id: str,
        company_id: uuid.UUID,
        tenant_id: uuid.UUID,
        old_value: dict | None = None,
        new_value: dict | None = None,
    ) -> None:
        await AuditRepository(session).create_log(
            user_id=actor_id,
            company_id=company_id,
            tenant_id=tenant_id,
            entity_type="channel_integration",
            entity_id=entity_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
        )

    @staticmethod
    async def connect_channel(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        channel_id: str,
        channel_type: str,
        permissions: str,
        token_reference: str,
        display_name: str | None = None,
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        ctx = await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)
        if not await ChannelIntegrationEngineV1.is_platform_admin(actor_id):
            await PartnerTenantEngineV1.assert_tenant_write(ctx)

        if channel_type not in INTEGRATION_CHANNEL_TYPES:
            raise ChannelIntegrationEngineError(f"Unsupported channel type: {channel_type}")
        if permissions not in CHANNEL_PERMISSIONS:
            raise ChannelIntegrationEngineError(f"Invalid permissions: {permissions}")

        async with get_session() as session:
            repo = ChannelIntegrationRepository(session)
            existing = await repo.get_by_channel(tenant_id, channel_type, channel_id)
            if existing is not None:
                if existing.status == ChannelIntegrationStatus.DISCONNECTED.value:
                    old = ChannelIntegrationEngineV1._snapshot(existing)
                    await repo.update(
                        existing,
                        permissions=permissions,
                        token_reference=token_reference,
                        display_name=display_name,
                        status=ChannelIntegrationStatus.ACTIVE.value,
                        metadata=metadata,
                    )
                    await ChannelIntegrationEngineV1._audit(
                        session,
                        actor_id=actor_id,
                        action=AuditAction.UPDATE.value,
                        entity_id=str(existing.id),
                        company_id=ctx.company_id,
                        tenant_id=tenant_id,
                        old_value=old,
                        new_value=ChannelIntegrationEngineV1._snapshot(existing),
                    )
                    return ChannelIntegrationEngineV1._snapshot(existing)
                raise ChannelIntegrationEngineError(
                    f"Channel already connected: {channel_type}:{channel_id}"
                )

            row = await repo.create(
                tenant_id=tenant_id,
                company_id=ctx.company_id,
                channel_id=channel_id,
                channel_type=channel_type,
                permissions=permissions,
                token_reference=token_reference,
                display_name=display_name,
                metadata=metadata,
            )
            await PartnerTenantEngineV1.bind_resource(
                actor_id,
                tenant_id,
                resource_type=TenantResourceType.CHANNEL.value,
                resource_id=str(row.id),
                notes=f"{channel_type}:{channel_id}",
            )
            try:
                from services.pg_tenant_billing_engine import TenantBillingEngineV1

                await TenantBillingEngineV1.record_channel(
                    actor_id,
                    tenant_id,
                    channel_key=f"{channel_type}:{channel_id}",
                    metadata={"integration_id": str(row.id)},
                )
            except Exception:
                pass

            await ChannelIntegrationEngineV1._audit(
                session,
                actor_id=actor_id,
                action=AuditAction.CREATE.value,
                entity_id=str(row.id),
                company_id=ctx.company_id,
                tenant_id=tenant_id,
                new_value=ChannelIntegrationEngineV1._snapshot(row),
            )
            return ChannelIntegrationEngineV1._snapshot(row)

    @staticmethod
    async def update_channel(
        actor_id: int,
        integration_id: uuid.UUID,
        *,
        permissions: str | None = None,
        token_reference: str | None = None,
        display_name: str | None = None,
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        async with get_session() as session:
            repo = ChannelIntegrationRepository(session)
            row = await repo.get_by_id(integration_id)
            if row is None:
                raise ChannelIntegrationEngineError(f"Integration not found: {integration_id}")

            ctx = await PartnerTenantEngineV1.resolve_context(actor_id, row.tenant_id)
            if not await ChannelIntegrationEngineV1.is_platform_admin(actor_id):
                await PartnerTenantEngineV1.assert_tenant_write(ctx)

            old = ChannelIntegrationEngineV1._snapshot(row)
            updates: dict[str, Any] = {}
            if permissions is not None:
                if permissions not in CHANNEL_PERMISSIONS:
                    raise ChannelIntegrationEngineError(f"Invalid permissions: {permissions}")
                updates["permissions"] = permissions
            if token_reference is not None:
                updates["token_reference"] = token_reference
            if display_name is not None:
                updates["display_name"] = display_name
            if metadata is not None:
                updates["metadata"] = metadata

            if not updates:
                return old

            await repo.update(row, **updates)
            await ChannelIntegrationEngineV1._audit(
                session,
                actor_id=actor_id,
                action=AuditAction.UPDATE.value,
                entity_id=str(row.id),
                company_id=row.company_id,
                tenant_id=row.tenant_id,
                old_value=old,
                new_value=ChannelIntegrationEngineV1._snapshot(row),
            )
            return ChannelIntegrationEngineV1._snapshot(row)

    @staticmethod
    async def disconnect_channel(
        actor_id: int,
        integration_id: uuid.UUID,
    ) -> dict[str, Any]:
        async with get_session() as session:
            repo = ChannelIntegrationRepository(session)
            row = await repo.get_by_id(integration_id)
            if row is None:
                raise ChannelIntegrationEngineError(f"Integration not found: {integration_id}")

            ctx = await PartnerTenantEngineV1.resolve_context(actor_id, row.tenant_id)
            if not await ChannelIntegrationEngineV1.is_platform_admin(actor_id):
                await PartnerTenantEngineV1.assert_tenant_write(ctx)

            old = ChannelIntegrationEngineV1._snapshot(row)
            await repo.update(row, status=ChannelIntegrationStatus.DISCONNECTED.value)
            await ChannelIntegrationEngineV1._audit(
                session,
                actor_id=actor_id,
                action=AuditAction.STATUS_CHANGE.value,
                entity_id=str(row.id),
                company_id=row.company_id,
                tenant_id=row.tenant_id,
                old_value=old,
                new_value=ChannelIntegrationEngineV1._snapshot(row),
            )
            return ChannelIntegrationEngineV1._snapshot(row)

    @staticmethod
    async def get_channel(
        actor_id: int,
        integration_id: uuid.UUID,
    ) -> dict[str, Any]:
        async with get_session() as session:
            row = await ChannelIntegrationRepository(session).get_by_id(integration_id)
            if row is None:
                raise ChannelIntegrationEngineError(f"Integration not found: {integration_id}")
            await PartnerTenantEngineV1.resolve_context(actor_id, row.tenant_id)
            return ChannelIntegrationEngineV1._snapshot(row)

    @staticmethod
    async def list_channels(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        channel_type: str | None = None,
        status: str | None = ChannelIntegrationStatus.ACTIVE.value,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)
        async with get_session() as session:
            rows = await ChannelIntegrationRepository(session).list_by_tenant(
                tenant_id,
                channel_type=channel_type,
                status=status,
                limit=limit,
            )
            return [ChannelIntegrationEngineV1._snapshot(row) for row in rows]

    @staticmethod
    async def resolve_active_channel(
        tenant_id: uuid.UUID,
        channel_type: str,
        channel_id: str,
        *,
        required_action: ChannelAction = "read",
    ) -> dict[str, Any]:
        async with get_session() as session:
            row = await ChannelIntegrationRepository(session).get_by_channel(
                tenant_id,
                channel_type,
                channel_id,
            )
            if row is None:
                raise ChannelIntegrationEngineError(
                    f"Channel not connected: {channel_type}:{channel_id}"
                )
            if row.status != ChannelIntegrationStatus.ACTIVE.value:
                raise ChannelIntegrationEngineError("Channel integration is not active")
            if not ChannelIntegrationEngineV1.permission_allows(
                row.permissions,
                required_action,
            ):
                raise TenantAccessDeniedError(
                    f"Permission {row.permissions} does not allow {required_action}"
                )
            return ChannelIntegrationEngineV1._snapshot(row)

    @staticmethod
    async def list_supported_channels() -> list[dict[str, str]]:
        labels = {
            "TELEGRAM_CHANNEL": "Telegram Channel",
            "TELEGRAM_GROUP": "Telegram Group",
            "INSTAGRAM": "Instagram",
            "FACEBOOK": "Facebook",
            "TIKTOK": "TikTok",
            "WHATSAPP_BUSINESS": "WhatsApp Business",
        }
        return [
            {"code": code, "label": labels.get(code, code)}
            for code in sorted(INTEGRATION_CHANNEL_TYPES)
        ]

    @staticmethod
    async def list_permissions() -> list[dict[str, str]]:
        labels = {
            "READ_ONLY": "Read only",
            "POST_ONLY": "Post only",
            "POST_AND_ANALYTICS": "Post and analytics",
        }
        return [
            {"code": code, "label": labels.get(code, code)}
            for code in sorted(CHANNEL_PERMISSIONS)
        ]

    @staticmethod
    async def check_channel_access(
        actor_id: int,
        integration_id: uuid.UUID,
        *,
        action: ChannelAction,
    ) -> dict[str, Any]:
        channel = await ChannelIntegrationEngineV1.get_channel(actor_id, integration_id)
        allowed = ChannelIntegrationEngineV1.permission_allows(channel["permissions"], action)
        return {"integration_id": channel["id"], "action": action, "allowed": allowed}
