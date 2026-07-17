# AuditService — PostgreSQL audit logging (replaces SQLite log_audit).

from __future__ import annotations

from services.pg_platform_audit_engine import PlatformAuditEngineV1


class AuditService:
    @staticmethod
    async def log(
        user_id: int,
        action: str,
        module: str,
        details: str = "",
    ) -> None:
        await PlatformAuditEngineV1.log(
            event_type=action.upper(),
            entity_type=module,
            entity_id=details or str(user_id),
            user_id=user_id,
            payload={"action": action, "module": module, "details": details},
        )

    @staticmethod
    def log_sync(user_id: int, action: str, module: str, details: str = "") -> None:
        from database.async_bridge import fire_and_forget

        fire_and_forget(
            AuditService.log(user_id, action, module, details)
        )


audit_service = AuditService()

# Backward-compatible alias for handlers migrating off `from database import log_audit`.
log_audit = audit_service.log_sync
