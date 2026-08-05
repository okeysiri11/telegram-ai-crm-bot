"""Service audit trail — who / when / state transitions / result."""

from __future__ import annotations

import time
from typing import Any

from platform_service_builder.models import ServiceLogEntry


class ServiceAuditLogger:
    def __init__(self) -> None:
        self._logs: list[ServiceLogEntry] = []

    def reset(self) -> None:
        self._logs.clear()

    def log(
        self,
        service_id: str,
        *,
        message: str,
        actor: str = "system",
        operation: str | None = None,
        old_state: str | None = None,
        new_state: str | None = None,
        duration_ms: float | None = None,
        result: str = "ok",
        level: str = "info",
        details: dict[str, Any] | None = None,
    ) -> ServiceLogEntry:
        entry = ServiceLogEntry(
            service_id=service_id,
            level=level,
            message=message,
            actor=actor,
            operation=operation,
            old_state=old_state,
            new_state=new_state,
            duration_ms=duration_ms,
            result=result,
            details=details or {},
            created_at=time.time(),
        )
        self._logs.append(entry)
        return entry

    def for_service(self, service_id: str, *, limit: int = 100) -> list[ServiceLogEntry]:
        rows = [e for e in self._logs if e.service_id == service_id]
        return rows[-limit:]

    def all(self, *, limit: int = 500) -> list[ServiceLogEntry]:
        return self._logs[-limit:]


service_audit = ServiceAuditLogger()
