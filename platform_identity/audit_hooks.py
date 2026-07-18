# IAM audit hooks — authentication, authorization, IAM changes.

from __future__ import annotations

import logging
from typing import Any

from platform_identity.models import ApiKeyRecord, Principal, ResourceRef

logger = logging.getLogger(__name__)


class IamAuditHooks:
    async def log_authentication(
        self,
        *,
        principal: Principal | None,
        method: str,
        success: bool,
        ip: str,
        details: dict[str, Any] | None = None,
    ) -> str | None:
        return await self._write(
            event_type="IAM_AUTHENTICATION",
            entity_type="identity",
            entity_id=principal.principal_id if principal else "anonymous",
            user_id=principal.telegram_id if principal else None,
            payload={
                "method": method,
                "success": success,
                "ip": ip,
                "details": details or {},
            },
        )

    async def log_authorization_failure(
        self,
        *,
        principal: Principal,
        permission: str,
        resource: ResourceRef | None = None,
    ) -> str | None:
        return await self._write(
            event_type="IAM_AUTHORIZATION_DENIED",
            entity_type="permission",
            entity_id=permission,
            user_id=principal.telegram_id,
            payload={
                "principal_id": principal.principal_id,
                "permission": permission,
                "resource": resource.__dict__ if resource else None,
            },
        )

    async def log_role_change(
        self,
        *,
        actor_id: int | None,
        target_telegram_id: int,
        old_roles: list[str],
        new_roles: list[str],
    ) -> str | None:
        return await self._write(
            event_type="IAM_ROLE_CHANGED",
            entity_type="user",
            entity_id=str(target_telegram_id),
            user_id=actor_id,
            payload={"old_roles": old_roles, "new_roles": new_roles},
        )

    async def log_permission_change(
        self,
        *,
        actor_id: int | None,
        target: str,
        permissions: list[str],
        action: str,
    ) -> str | None:
        return await self._write(
            event_type="IAM_PERMISSION_CHANGED",
            entity_type="permission",
            entity_id=target,
            user_id=actor_id,
            payload={"permissions": permissions, "action": action},
        )

    async def log_session_created(
        self,
        *,
        principal: Principal,
        session_id: str,
        ip: str,
        device: str,
    ) -> str | None:
        return await self._write(
            event_type="IAM_SESSION_CREATED",
            entity_type="session",
            entity_id=session_id,
            user_id=principal.telegram_id,
            payload={"ip": ip, "device": device, "auth_method": principal.auth_method.value},
        )

    async def log_api_key_usage(self, record: ApiKeyRecord) -> str | None:
        return await self._write(
            event_type="IAM_API_KEY_USED",
            entity_type="api_key",
            entity_id=record.key_id,
            user_id=record.telegram_id,
            payload={"name": record.name, "scopes": record.scopes},
        )

    async def log_api_key_created(
        self,
        *,
        actor_id: int | None,
        record: ApiKeyRecord,
    ) -> str | None:
        return await self._write(
            event_type="IAM_API_KEY_CREATED",
            entity_type="api_key",
            entity_id=record.key_id,
            user_id=actor_id,
            payload={"name": record.name, "scopes": record.scopes},
        )

    @staticmethod
    async def _write(
        *,
        event_type: str,
        entity_type: str,
        entity_id: str,
        user_id: int | None,
        payload: dict[str, Any],
    ) -> str | None:
        try:
            from platform_legacy import legacy

            return await legacy.audit.log(
                event_type=event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                user_id=user_id,
                payload=payload,
            )
        except Exception:
            logger.warning(
                "iam_audit_write_failed event=%s entity=%s:%s",
                event_type,
                entity_type,
                entity_id,
                exc_info=True,
            )
            return None


iam_audit = IamAuditHooks()
