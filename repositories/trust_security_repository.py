# Trust Security Engine v1 repositories.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.trust_security_engine import (
    ACCESS_ACTIONS,
    API_ACCESS_RESULTS,
    CONTENT_APPROVAL_STATUSES,
    EXPORT_FORMATS,
    PERMISSION_AUDIT_ACTIONS,
    REVOKE_SCOPES,
    RevokeStatus,
    SecurityAccessLog,
    SecurityApiAccessLog,
    SecurityContentApproval,
    SecurityEmergencyRevoke,
    SecurityExportLog,
    SecurityPermissionAudit,
)


class SecurityAccessLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
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
    ) -> SecurityAccessLog:
        if action not in ACCESS_ACTIONS:
            raise ValueError(f"Invalid action: {action}")

        row = SecurityAccessLog(
            user_id=user_id,
            tenant_id=tenant_id,
            company_id=company_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata_=metadata,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_recent(
        self,
        *,
        tenant_id: uuid.UUID | None = None,
        user_id: int | None = None,
        limit: int = 100,
    ) -> list[SecurityAccessLog]:
        stmt = select(SecurityAccessLog).order_by(SecurityAccessLog.created_at.desc()).limit(limit)
        if tenant_id is not None:
            stmt = stmt.where(SecurityAccessLog.tenant_id == tenant_id)
        if user_id is not None:
            stmt = stmt.where(SecurityAccessLog.user_id == user_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


class SecurityPermissionAuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        actor_id: int,
        subject_user_id: int,
        permission_code: str,
        audit_action: str,
        tenant_id: uuid.UUID | None = None,
        company_id: uuid.UUID | None = None,
        old_value: dict | None = None,
        new_value: dict | None = None,
        reason: str | None = None,
    ) -> SecurityPermissionAudit:
        if audit_action not in PERMISSION_AUDIT_ACTIONS:
            raise ValueError(f"Invalid audit_action: {audit_action}")

        row = SecurityPermissionAudit(
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
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_recent(
        self,
        *,
        tenant_id: uuid.UUID | None = None,
        subject_user_id: int | None = None,
        limit: int = 100,
    ) -> list[SecurityPermissionAudit]:
        stmt = (
            select(SecurityPermissionAudit)
            .order_by(SecurityPermissionAudit.created_at.desc())
            .limit(limit)
        )
        if tenant_id is not None:
            stmt = stmt.where(SecurityPermissionAudit.tenant_id == tenant_id)
        if subject_user_id is not None:
            stmt = stmt.where(SecurityPermissionAudit.subject_user_id == subject_user_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


class SecurityExportLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: int,
        resource_type: str,
        export_format: str,
        record_count: int = 0,
        tenant_id: uuid.UUID | None = None,
        company_id: uuid.UUID | None = None,
        file_name: str | None = None,
        metadata: dict | None = None,
    ) -> SecurityExportLog:
        if export_format not in EXPORT_FORMATS:
            raise ValueError(f"Invalid export_format: {export_format}")

        row = SecurityExportLog(
            user_id=user_id,
            resource_type=resource_type,
            export_format=export_format,
            record_count=record_count,
            tenant_id=tenant_id,
            company_id=company_id,
            file_name=file_name,
            metadata_=metadata,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_recent(
        self,
        *,
        tenant_id: uuid.UUID | None = None,
        user_id: int | None = None,
        limit: int = 100,
    ) -> list[SecurityExportLog]:
        stmt = select(SecurityExportLog).order_by(SecurityExportLog.created_at.desc()).limit(limit)
        if tenant_id is not None:
            stmt = stmt.where(SecurityExportLog.tenant_id == tenant_id)
        if user_id is not None:
            stmt = stmt.where(SecurityExportLog.user_id == user_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


class SecurityApiAccessLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
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
    ) -> SecurityApiAccessLog:
        if result not in API_ACCESS_RESULTS:
            raise ValueError(f"Invalid result: {result}")

        row = SecurityApiAccessLog(
            method=method.upper(),
            path=path,
            result=result,
            api_client_id=api_client_id,
            api_key_id=api_key_id,
            tenant_id=tenant_id,
            company_id=company_id,
            status_code=status_code,
            ip_address=ip_address,
            metadata_=metadata,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_recent(
        self,
        *,
        tenant_id: uuid.UUID | None = None,
        api_client_id: uuid.UUID | None = None,
        limit: int = 100,
    ) -> list[SecurityApiAccessLog]:
        stmt = (
            select(SecurityApiAccessLog)
            .order_by(SecurityApiAccessLog.created_at.desc())
            .limit(limit)
        )
        if tenant_id is not None:
            stmt = stmt.where(SecurityApiAccessLog.tenant_id == tenant_id)
        if api_client_id is not None:
            stmt = stmt.where(SecurityApiAccessLog.api_client_id == api_client_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


class SecurityContentApprovalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        content_type: str,
        content_ref: str,
        submitted_by: int,
        tenant_id: uuid.UUID | None = None,
        company_id: uuid.UUID | None = None,
        title: str | None = None,
        body_preview: str | None = None,
        metadata: dict | None = None,
    ) -> SecurityContentApproval:
        row = SecurityContentApproval(
            content_type=content_type,
            content_ref=content_ref,
            submitted_by=submitted_by,
            tenant_id=tenant_id,
            company_id=company_id,
            title=title,
            body_preview=body_preview,
            metadata_=metadata,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_by_id(self, approval_id: uuid.UUID) -> SecurityContentApproval | None:
        result = await self._session.execute(
            select(SecurityContentApproval).where(SecurityContentApproval.id == approval_id)
        )
        return result.scalar_one_or_none()

    async def list_pending(
        self,
        *,
        tenant_id: uuid.UUID | None = None,
        limit: int = 100,
    ) -> list[SecurityContentApproval]:
        from database.models.trust_security_engine import ContentApprovalStatus

        stmt = (
            select(SecurityContentApproval)
            .where(SecurityContentApproval.status == ContentApprovalStatus.PENDING.value)
            .order_by(SecurityContentApproval.created_at.asc())
            .limit(limit)
        )
        if tenant_id is not None:
            stmt = stmt.where(SecurityContentApproval.tenant_id == tenant_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, row: SecurityContentApproval, **fields: Any) -> SecurityContentApproval:
        allowed = {"status", "reviewed_by", "review_notes", "metadata_"}
        unknown = set(fields) - allowed
        if unknown:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(unknown))}")
        if "status" in fields and fields["status"] not in CONTENT_APPROVAL_STATUSES:
            raise ValueError(f"Invalid status: {fields['status']}")
        if "metadata" in fields:
            fields["metadata_"] = fields.pop("metadata")
        for key, value in fields.items():
            setattr(row, key, value)
        await self._session.flush()
        return row


class SecurityEmergencyRevokeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        scope: str,
        target_ref: str,
        revoked_by: int,
        reason: str,
        tenant_id: uuid.UUID | None = None,
        company_id: uuid.UUID | None = None,
        actions_taken: dict | None = None,
    ) -> SecurityEmergencyRevoke:
        if scope not in REVOKE_SCOPES:
            raise ValueError(f"Invalid scope: {scope}")

        row = SecurityEmergencyRevoke(
            scope=scope,
            target_ref=target_ref,
            revoked_by=revoked_by,
            reason=reason,
            tenant_id=tenant_id,
            company_id=company_id,
            actions_taken=actions_taken,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_by_id(self, revoke_id: uuid.UUID) -> SecurityEmergencyRevoke | None:
        result = await self._session.execute(
            select(SecurityEmergencyRevoke).where(SecurityEmergencyRevoke.id == revoke_id)
        )
        return result.scalar_one_or_none()

    async def get_active(
        self,
        scope: str,
        target_ref: str,
        *,
        tenant_id: uuid.UUID | None = None,
    ) -> SecurityEmergencyRevoke | None:
        stmt = select(SecurityEmergencyRevoke).where(
            SecurityEmergencyRevoke.scope == scope,
            SecurityEmergencyRevoke.target_ref == target_ref,
            SecurityEmergencyRevoke.status == RevokeStatus.ACTIVE.value,
        )
        if tenant_id is not None:
            stmt = stmt.where(SecurityEmergencyRevoke.tenant_id == tenant_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_active(self, *, limit: int = 100) -> list[SecurityEmergencyRevoke]:
        result = await self._session.execute(
            select(SecurityEmergencyRevoke)
            .where(SecurityEmergencyRevoke.status == RevokeStatus.ACTIVE.value)
            .order_by(SecurityEmergencyRevoke.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def release(
        self,
        row: SecurityEmergencyRevoke,
        *,
        released_by: int,
    ) -> SecurityEmergencyRevoke:
        row.status = RevokeStatus.RELEASED.value
        row.released_by = released_by
        row.released_at = datetime.now(timezone.utc)
        await self._session.flush()
        return row
