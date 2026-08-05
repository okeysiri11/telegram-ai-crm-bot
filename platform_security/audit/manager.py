# AuditManager — authentication, authorization, tool, workflow, config, security events.

from __future__ import annotations

import logging

from platform_security.config import DEFAULT_SECURITY_CONFIG, SecurityConfig
from platform_security.models import AuditEventType, AuditRecord, SecurityPrincipal

logger = logging.getLogger(__name__)


class AuditManager:
    def __init__(self, *, config: SecurityConfig | None = None) -> None:
        self._config = config or DEFAULT_SECURITY_CONFIG
        self._records: list[AuditRecord] = []

    def reset(self) -> None:
        self._records.clear()

    @property
    def records(self) -> list[AuditRecord]:
        return list(self._records)

    def _append(self, record: AuditRecord) -> AuditRecord:
        self._records.append(record)
        if len(self._records) > self._config.audit_retention_limit:
            self._records = self._records[-self._config.audit_retention_limit :]
        return record

    async def log_authentication(
        self,
        principal: SecurityPrincipal | None,
        *,
        method: str,
        success: bool,
        ip: str = "",
        details: dict | None = None,
    ) -> AuditRecord:
        record = AuditRecord(
            event_type=AuditEventType.AUTHENTICATION,
            principal_id=principal.principal_id if principal else None,
            action=f"auth.{method}",
            success=success,
            details={"ip": ip, **(details or {})},
        )
        self._append(record)
        await self._bridge_iam_auth(principal, method, success, ip, details)
        return record

    async def log_authorization(
        self,
        principal: SecurityPrincipal,
        *,
        permission: str,
        resource: str | None = None,
        granted: bool,
    ) -> AuditRecord:
        record = AuditRecord(
            event_type=AuditEventType.AUTHORIZATION,
            principal_id=principal.principal_id,
            action=f"authz.{permission}",
            resource=resource,
            success=granted,
        )
        return self._append(record)

    async def log_tool_access(
        self,
        principal: SecurityPrincipal,
        tool_id: str,
        *,
        success: bool,
        action: str = "execute",
    ) -> AuditRecord:
        return self._append(AuditRecord(
            event_type=AuditEventType.TOOL_ACCESS,
            principal_id=principal.principal_id,
            action=f"tool.{action}",
            resource=tool_id,
            success=success,
        ))

    async def log_workflow_access(
        self,
        principal: SecurityPrincipal,
        workflow_id: str,
        *,
        success: bool,
        action: str = "execute",
    ) -> AuditRecord:
        return self._append(AuditRecord(
            event_type=AuditEventType.WORKFLOW_ACCESS,
            principal_id=principal.principal_id,
            action=f"workflow.{action}",
            resource=workflow_id,
            success=success,
        ))

    async def log_config_change(
        self,
        principal: SecurityPrincipal,
        config_key: str,
        *,
        old_value: str | None = None,
        new_value: str | None = None,
    ) -> AuditRecord:
        return self._append(AuditRecord(
            event_type=AuditEventType.CONFIG_CHANGE,
            principal_id=principal.principal_id,
            action="config.change",
            resource=config_key,
            details={"old": old_value, "new": new_value},
        ))

    async def log_security_event(
        self,
        action: str,
        *,
        principal_id: str | None = None,
        details: dict | None = None,
        success: bool = True,
    ) -> AuditRecord:
        return self._append(AuditRecord(
            event_type=AuditEventType.SECURITY,
            principal_id=principal_id,
            action=action,
            success=success,
            details=details or {},
        ))

    async def log_secret_access(self, principal_id: str, secret_name: str, *, success: bool) -> AuditRecord:
        return self._append(AuditRecord(
            event_type=AuditEventType.SECRET_ACCESS,
            principal_id=principal_id,
            action="secret.retrieve",
            resource=secret_name,
            success=success,
        ))

    def query(self, *, event_type: AuditEventType | None = None, limit: int = 100) -> list[AuditRecord]:
        records = self._records
        if event_type:
            records = [r for r in records if r.event_type == event_type]
        return records[-limit:]

    async def _bridge_iam_auth(
        self,
        principal: SecurityPrincipal | None,
        method: str,
        success: bool,
        ip: str,
        details: dict | None,
    ) -> None:
        try:
            from platform_identity.audit_hooks import iam_audit
            from platform_identity.models import AuthMethod, Principal

            identity = None
            if principal:
                identity = Principal(
                    principal_id=principal.principal_id,
                    auth_method=AuthMethod.JWT,
                    roles=principal.roles,
                    permissions=principal.permissions,
                )
            await iam_audit.log_authentication(
                principal=identity,
                method=method,
                success=success,
                ip=ip,
                details=details,
            )
        except Exception:
            logger.debug("iam audit bridge unavailable")


audit_manager = AuditManager()
