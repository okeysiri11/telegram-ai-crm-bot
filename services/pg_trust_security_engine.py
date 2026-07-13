# Trust Security Engine v1 — access logs, audits, exports, approvals, revoke.

from __future__ import annotations

import uuid
from typing import Any

from config import OWNER_ID
from database.models.audit_log import AuditAction
from database.models.trust_security_engine import (
    AccessAction,
    ApiAccessResult,
    ContentApprovalStatus,
    PermissionAuditAction,
    RevokeScope,
    RevokeStatus,
)
from database.session import get_session
from repositories.audit_repository import AuditRepository
from repositories.trust_security_repository import (
    SecurityAccessLogRepository,
    SecurityApiAccessLogRepository,
    SecurityContentApprovalRepository,
    SecurityEmergencyRevokeRepository,
    SecurityExportLogRepository,
    SecurityPermissionAuditRepository,
)
from repositories.user_role_repository import UserRoleRepository
from services.pg_partner_tenant_engine import PartnerTenantEngineV1

SECURITY_ROLES = frozenset({"OWNER", "ADMIN", "LAWYER"})


class TrustSecurityEngineError(Exception):
    pass


class TrustSecurityAccessDenied(TrustSecurityEngineError):
    pass


class TrustSecurityEngineV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in SECURITY_ROLES for role in roles)

    @staticmethod
    async def _require_access(user_id: int) -> None:
        if not await TrustSecurityEngineV1.user_can_access(user_id):
            raise TrustSecurityAccessDenied("Security access denied")

    @staticmethod
    def _access_log_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "user_id": row.user_id,
            "tenant_id": str(row.tenant_id) if row.tenant_id else None,
            "company_id": str(row.company_id) if row.company_id else None,
            "resource_type": row.resource_type,
            "resource_id": row.resource_id,
            "action": row.action,
            "ip_address": row.ip_address,
            "created_at": row.created_at.isoformat(),
        }

    @staticmethod
    def _permission_audit_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "actor_id": row.actor_id,
            "subject_user_id": row.subject_user_id,
            "tenant_id": str(row.tenant_id) if row.tenant_id else None,
            "permission_code": row.permission_code,
            "audit_action": row.audit_action,
            "old_value": row.old_value,
            "new_value": row.new_value,
            "reason": row.reason,
            "created_at": row.created_at.isoformat(),
        }

    @staticmethod
    def _export_log_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "user_id": row.user_id,
            "tenant_id": str(row.tenant_id) if row.tenant_id else None,
            "resource_type": row.resource_type,
            "export_format": row.export_format,
            "record_count": row.record_count,
            "file_name": row.file_name,
            "created_at": row.created_at.isoformat(),
        }

    @staticmethod
    def _api_access_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "api_client_id": str(row.api_client_id) if row.api_client_id else None,
            "api_key_id": str(row.api_key_id) if row.api_key_id else None,
            "tenant_id": str(row.tenant_id) if row.tenant_id else None,
            "method": row.method,
            "path": row.path,
            "status_code": row.status_code,
            "result": row.result,
            "ip_address": row.ip_address,
            "created_at": row.created_at.isoformat(),
        }

    @staticmethod
    def _approval_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "tenant_id": str(row.tenant_id) if row.tenant_id else None,
            "content_type": row.content_type,
            "content_ref": row.content_ref,
            "title": row.title,
            "status": row.status,
            "submitted_by": row.submitted_by,
            "reviewed_by": row.reviewed_by,
            "review_notes": row.review_notes,
            "created_at": row.created_at.isoformat(),
            "updated_at": row.updated_at.isoformat(),
        }

    @staticmethod
    def _revoke_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "scope": row.scope,
            "target_ref": row.target_ref,
            "tenant_id": str(row.tenant_id) if row.tenant_id else None,
            "revoked_by": row.revoked_by,
            "reason": row.reason,
            "status": row.status,
            "released_by": row.released_by,
            "released_at": row.released_at.isoformat() if row.released_at else None,
            "actions_taken": row.actions_taken or {},
            "created_at": row.created_at.isoformat(),
        }

    @staticmethod
    async def log_access(
        *,
        resource_type: str,
        action: str,
        user_id: int | None = None,
        tenant_id: uuid.UUID | None = None,
        company_id: uuid.UUID | None = None,
        resource_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        async with get_session() as session:
            row = await SecurityAccessLogRepository(session).create(
                user_id=user_id,
                tenant_id=tenant_id,
                company_id=company_id,
                resource_type=resource_type,
                resource_id=resource_id,
                action=action,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata=metadata,
            )
            return TrustSecurityEngineV1._access_log_snapshot(row)

    @staticmethod
    async def audit_permission_change(
        actor_id: int,
        *,
        subject_user_id: int,
        permission_code: str,
        audit_action: str,
        tenant_id: uuid.UUID | None = None,
        company_id: uuid.UUID | None = None,
        old_value: dict | None = None,
        new_value: dict | None = None,
        reason: str | None = None,
    ) -> dict[str, Any]:
        async with get_session() as session:
            row = await SecurityPermissionAuditRepository(session).create(
                actor_id=actor_id,
                subject_user_id=subject_user_id,
                permission_code=permission_code,
                audit_action=audit_action,
                tenant_id=tenant_id,
                company_id=company_id,
                old_value=old_value,
                new_value=new_value,
                reason=reason,
            )
            await AuditRepository(session).create_log(
                user_id=actor_id,
                company_id=company_id,
                tenant_id=tenant_id,
                entity_type="permission",
                entity_id=str(subject_user_id),
                action=AuditAction.UPDATE.value,
                old_value=old_value,
                new_value=new_value,
            )
            return TrustSecurityEngineV1._permission_audit_snapshot(row)

    @staticmethod
    async def track_export(
        actor_id: int,
        *,
        resource_type: str,
        export_format: str,
        record_count: int = 0,
        tenant_id: uuid.UUID | None = None,
        company_id: uuid.UUID | None = None,
        file_name: str | None = None,
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        async with get_session() as session:
            row = await SecurityExportLogRepository(session).create(
                user_id=actor_id,
                resource_type=resource_type,
                export_format=export_format,
                record_count=record_count,
                tenant_id=tenant_id,
                company_id=company_id,
                file_name=file_name,
                metadata=metadata,
            )
            await SecurityAccessLogRepository(session).create(
                user_id=actor_id,
                tenant_id=tenant_id,
                company_id=company_id,
                resource_type=resource_type,
                action=AccessAction.EXPORT.value,
                metadata={"export_id": str(row.id), "format": export_format},
            )
            return TrustSecurityEngineV1._export_log_snapshot(row)

    @staticmethod
    async def track_api_access(
        *,
        method: str,
        path: str,
        result: str,
        api_client_id: uuid.UUID | None = None,
        api_key_id: uuid.UUID | None = None,
        tenant_id: uuid.UUID | None = None,
        company_id: uuid.UUID | None = None,
        status_code: int | None = None,
        ip_address: str | None = None,
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        async with get_session() as session:
            row = await SecurityApiAccessLogRepository(session).create(
                method=method,
                path=path,
                result=result,
                api_client_id=api_client_id,
                api_key_id=api_key_id,
                tenant_id=tenant_id,
                company_id=company_id,
                status_code=status_code,
                ip_address=ip_address,
                metadata=metadata,
            )
            return TrustSecurityEngineV1._api_access_snapshot(row)

    @staticmethod
    async def submit_content_for_approval(
        actor_id: int,
        *,
        content_type: str,
        content_ref: str,
        title: str | None = None,
        body_preview: str | None = None,
        tenant_id: uuid.UUID | None = None,
        company_id: uuid.UUID | None = None,
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        if tenant_id is not None:
            await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)

        async with get_session() as session:
            row = await SecurityContentApprovalRepository(session).create(
                content_type=content_type,
                content_ref=content_ref,
                submitted_by=actor_id,
                tenant_id=tenant_id,
                company_id=company_id,
                title=title,
                body_preview=body_preview,
                metadata=metadata,
            )
            await SecurityAccessLogRepository(session).create(
                user_id=actor_id,
                tenant_id=tenant_id,
                company_id=company_id,
                resource_type="content_approval",
                resource_id=str(row.id),
                action=AccessAction.WRITE.value,
            )
            return TrustSecurityEngineV1._approval_snapshot(row)

    @staticmethod
    async def review_content(
        actor_id: int,
        approval_id: uuid.UUID,
        *,
        approved: bool,
        review_notes: str | None = None,
    ) -> dict[str, Any]:
        await TrustSecurityEngineV1._require_access(actor_id)

        async with get_session() as session:
            repo = SecurityContentApprovalRepository(session)
            row = await repo.get_by_id(approval_id)
            if row is None:
                raise TrustSecurityEngineError(f"Approval not found: {approval_id}")
            if row.status != ContentApprovalStatus.PENDING.value:
                raise TrustSecurityEngineError("Content already reviewed")

            status = (
                ContentApprovalStatus.APPROVED.value
                if approved
                else ContentApprovalStatus.REJECTED.value
            )
            await repo.update(
                row,
                status=status,
                reviewed_by=actor_id,
                review_notes=review_notes,
            )
            await session.refresh(row)
            await AuditRepository(session).create_log(
                user_id=actor_id,
                company_id=row.company_id,
                tenant_id=row.tenant_id,
                entity_type="content_approval",
                entity_id=str(row.id),
                action=AuditAction.STATUS_CHANGE.value,
                new_value={"status": status, "review_notes": review_notes},
            )
            return TrustSecurityEngineV1._approval_snapshot(row)

    @staticmethod
    async def emergency_revoke_access(
        actor_id: int,
        *,
        scope: str,
        target_ref: str,
        reason: str,
        tenant_id: uuid.UUID | None = None,
        company_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        await TrustSecurityEngineV1._require_access(actor_id)
        if scope not in {s.value for s in RevokeScope}:
            raise TrustSecurityEngineError(f"Invalid scope: {scope}")

        actions: dict[str, Any] = {}

        async with get_session() as session:
            revoke_repo = SecurityEmergencyRevokeRepository(session)
            existing = await revoke_repo.get_active(scope, target_ref, tenant_id=tenant_id)
            if existing is not None:
                return TrustSecurityEngineV1._revoke_snapshot(existing)

            if scope == RevokeScope.TENANT_USER.value:
                from repositories.partner_tenant_repository import TenantUserRoleRepository

                tenant_uuid = uuid.UUID(target_ref.split(":")[0]) if ":" in target_ref else tenant_id
                user_id = int(target_ref.split(":")[1]) if ":" in target_ref else int(target_ref)
                if tenant_uuid is None:
                    raise TrustSecurityEngineError("tenant_id required for TENANT_USER revoke")
                removed = await TenantUserRoleRepository(session).remove(tenant_uuid, user_id)
                actions["tenant_user_removed"] = removed

            elif scope == RevokeScope.USER_GLOBAL.value:
                from repositories.user_role_repository import UserRoleRepository

                user_id = int(target_ref)
                roles = await UserRoleRepository(session).get_user_roles(user_id)
                removed_roles = []
                for role in roles:
                    if role.code not in {"OWNER"}:
                        await UserRoleRepository(session).remove_role(user_id, role.id)
                        removed_roles.append(role.code)
                actions["global_roles_removed"] = removed_roles

            elif scope == RevokeScope.API_KEY.value:
                from repositories.api_gateway_repository import ApiKeyRepository

                key_id = uuid.UUID(target_ref)
                revoked = await ApiKeyRepository(session).revoke(key_id)
                actions["api_key_revoked"] = revoked is not None

            elif scope == RevokeScope.API_CLIENT.value:
                from database.models.api_gateway import ApiClientStatus
                from repositories.api_gateway_repository import ApiClientRepository

                client_id = uuid.UUID(target_ref)
                client_repo = ApiClientRepository(session)
                client = await client_repo.get_by_id(client_id)
                if client is not None:
                    client.status = ApiClientStatus.REVOKED.value
                    actions["api_client_revoked"] = True
                else:
                    actions["api_client_revoked"] = False

            row = await revoke_repo.create(
                scope=scope,
                target_ref=target_ref,
                revoked_by=actor_id,
                reason=reason,
                tenant_id=tenant_id,
                company_id=company_id,
                actions_taken=actions,
            )

            await SecurityPermissionAuditRepository(session).create(
                actor_id=actor_id,
                subject_user_id=int(target_ref.split(":")[-1])
                if scope in {RevokeScope.TENANT_USER.value, RevokeScope.USER_GLOBAL.value}
                else actor_id,
                permission_code="EMERGENCY_REVOKE",
                audit_action=PermissionAuditAction.REVOKE.value,
                tenant_id=tenant_id,
                company_id=company_id,
                reason=reason,
                new_value={"scope": scope, "target_ref": target_ref, "actions": actions},
            )

            await AuditRepository(session).create_log(
                user_id=actor_id,
                company_id=company_id,
                tenant_id=tenant_id,
                entity_type="emergency_revoke",
                entity_id=str(row.id),
                action=AuditAction.STATUS_CHANGE.value,
                new_value={"scope": scope, "target_ref": target_ref, "reason": reason},
            )

            return TrustSecurityEngineV1._revoke_snapshot(row)

    @staticmethod
    async def release_emergency_revoke(
        actor_id: int,
        revoke_id: uuid.UUID,
    ) -> dict[str, Any]:
        await TrustSecurityEngineV1._require_access(actor_id)

        async with get_session() as session:
            repo = SecurityEmergencyRevokeRepository(session)
            row = await repo.get_by_id(revoke_id)
            if row is None:
                raise TrustSecurityEngineError(f"Revoke not found: {revoke_id}")
            if row.status != RevokeStatus.ACTIVE.value:
                raise TrustSecurityEngineError("Revoke is not active")

            await repo.release(row, released_by=actor_id)
            await session.refresh(row)
            return TrustSecurityEngineV1._revoke_snapshot(row)

    @staticmethod
    async def is_access_revoked(
        scope: str,
        target_ref: str,
        *,
        tenant_id: uuid.UUID | None = None,
    ) -> bool:
        async with get_session() as session:
            row = await SecurityEmergencyRevokeRepository(session).get_active(
                scope,
                target_ref,
                tenant_id=tenant_id,
            )
            return row is not None

    @staticmethod
    async def list_access_logs(
        actor_id: int,
        *,
        tenant_id: uuid.UUID | None = None,
        user_id: int | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        await TrustSecurityEngineV1._require_access(actor_id)
        async with get_session() as session:
            rows = await SecurityAccessLogRepository(session).list_recent(
                tenant_id=tenant_id,
                user_id=user_id,
                limit=limit,
            )
            return [TrustSecurityEngineV1._access_log_snapshot(r) for r in rows]

    @staticmethod
    async def list_permission_audits(
        actor_id: int,
        *,
        tenant_id: uuid.UUID | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        await TrustSecurityEngineV1._require_access(actor_id)
        async with get_session() as session:
            rows = await SecurityPermissionAuditRepository(session).list_recent(
                tenant_id=tenant_id,
                limit=limit,
            )
            return [TrustSecurityEngineV1._permission_audit_snapshot(r) for r in rows]

    @staticmethod
    async def list_export_logs(
        actor_id: int,
        *,
        tenant_id: uuid.UUID | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        await TrustSecurityEngineV1._require_access(actor_id)
        async with get_session() as session:
            rows = await SecurityExportLogRepository(session).list_recent(
                tenant_id=tenant_id,
                limit=limit,
            )
            return [TrustSecurityEngineV1._export_log_snapshot(r) for r in rows]

    @staticmethod
    async def list_api_access_logs(
        actor_id: int,
        *,
        tenant_id: uuid.UUID | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        await TrustSecurityEngineV1._require_access(actor_id)
        async with get_session() as session:
            rows = await SecurityApiAccessLogRepository(session).list_recent(
                tenant_id=tenant_id,
                limit=limit,
            )
            return [TrustSecurityEngineV1._api_access_snapshot(r) for r in rows]

    @staticmethod
    async def list_pending_approvals(
        actor_id: int,
        *,
        tenant_id: uuid.UUID | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        await TrustSecurityEngineV1._require_access(actor_id)
        async with get_session() as session:
            rows = await SecurityContentApprovalRepository(session).list_pending(
                tenant_id=tenant_id,
                limit=limit,
            )
            return [TrustSecurityEngineV1._approval_snapshot(r) for r in rows]

    @staticmethod
    async def list_active_revokes(
        actor_id: int,
        *,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        await TrustSecurityEngineV1._require_access(actor_id)
        async with get_session() as session:
            rows = await SecurityEmergencyRevokeRepository(session).list_active(limit=limit)
            return [TrustSecurityEngineV1._revoke_snapshot(r) for r in rows]
