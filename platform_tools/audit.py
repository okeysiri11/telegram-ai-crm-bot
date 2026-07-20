# Tool execution audit log.

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AuditEntry:
    execution_id: str
    tool_id: str
    agent_id: str | None
    user_id: str | None
    success: bool
    error: str | None = None
    execution_time_ms: float = 0.0
    retries: int = 0
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


class ToolAuditLog:
    def __init__(self, *, limit: int = 1000) -> None:
        self._entries: list[AuditEntry] = []
        self._limit = limit

    def reset(self) -> None:
        self._entries.clear()

    def record(
        self,
        *,
        execution_id: str,
        tool_id: str,
        agent_id: str | None,
        user_id: str | None,
        success: bool,
        error: str | None = None,
        execution_time_ms: float = 0.0,
        retries: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        entry = AuditEntry(
            execution_id=execution_id,
            tool_id=tool_id,
            agent_id=agent_id,
            user_id=user_id,
            success=success,
            error=error,
            execution_time_ms=execution_time_ms,
            retries=retries,
            metadata=metadata or {},
        )
        self._entries.append(entry)
        if len(self._entries) > self._limit:
            self._entries = self._entries[-self._limit :]
        logger.info(
            "tool_audit tool=%s success=%s agent=%s time_ms=%.1f",
            tool_id,
            success,
            agent_id,
            execution_time_ms,
        )

    def history(self, *, tool_id: str | None = None, limit: int = 100) -> list[AuditEntry]:
        entries = self._entries
        if tool_id:
            entries = [e for e in entries if e.tool_id == tool_id]
        return entries[-limit:]


tool_audit_log = ToolAuditLog()
