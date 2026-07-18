# Persistent memory store — in-memory with scope indexing.

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from platform_ai.memory.exceptions import MemoryNotFoundError
from platform_ai.memory.models import MemoryRecord, MemoryType


class MemoryStore:
    def __init__(self) -> None:
        self._records: dict[str, MemoryRecord] = {}
        self._by_key: dict[str, str] = {}

    def reset(self) -> None:
        self._records.clear()
        self._by_key.clear()

    def save(self, record: MemoryRecord) -> MemoryRecord:
        record.updated_at = datetime.now(timezone.utc).isoformat()
        self._records[record.memory_id] = record
        if record.key:
            scope_key = self._scope_key(record)
            self._by_key[scope_key] = record.memory_id
        return record

    def get(self, memory_id: str) -> MemoryRecord:
        if memory_id not in self._records:
            raise MemoryNotFoundError(memory_id)
        return self._records[memory_id]

    def get_by_key(self, key: str, **scope: Any) -> MemoryRecord | None:
        memory_id = self._by_key.get(self._scope_key_from_parts(key, scope))
        return self._records.get(memory_id) if memory_id else None

    def delete(self, memory_id: str) -> bool:
        record = self._records.pop(memory_id, None)
        if record and record.key:
            self._by_key.pop(self._scope_key(record), None)
        return record is not None

    def list_all(self, **filters: Any) -> list[MemoryRecord]:
        results = list(self._records.values())
        if memory_type := filters.get("memory_type"):
            results = [r for r in results if r.memory_type == memory_type]
        if plugin_id := filters.get("plugin_id"):
            results = [r for r in results if r.plugin_id == plugin_id]
        if user_id := filters.get("user_id"):
            results = [r for r in results if r.user_id == user_id]
        if workflow_id := filters.get("workflow_id"):
            results = [r for r in results if r.workflow_id == workflow_id]
        if session_id := filters.get("session_id"):
            results = [r for r in results if r.session_id == session_id]
        return sorted(results, key=lambda r: r.updated_at, reverse=True)

    def count(self) -> int:
        return len(self._records)

    def stats(self) -> dict[str, Any]:
        by_type: dict[str, int] = {}
        for r in self._records.values():
            by_type[r.memory_type] = by_type.get(r.memory_type, 0) + 1
        return {"total": len(self._records), "by_type": by_type}

    def _scope_key(self, record: MemoryRecord) -> str:
        return self._scope_key_from_parts(
            record.key,
            {
                "plugin_id": record.plugin_id,
                "user_id": record.user_id,
                "workflow_id": record.workflow_id,
                "session_id": record.session_id,
            },
        )

    def _scope_key_from_parts(self, key: str, scope: dict[str, Any]) -> str:
        parts = [key]
        for k in ("plugin_id", "user_id", "workflow_id", "session_id"):
            if scope.get(k):
                parts.append(f"{k}={scope[k]}")
        return ":".join(parts)


memory_store = MemoryStore()
