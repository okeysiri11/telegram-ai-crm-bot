# Audit side effects — delegates to AuditService (legacy import path).

from __future__ import annotations

from audit.audit_service import AuditService
from events.base_event import BaseEvent


class AuditEventHandler:
    @staticmethod
    async def handle(event: BaseEvent) -> None:
        await AuditService.handle_event(event)
