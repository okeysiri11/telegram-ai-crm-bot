"""Enterprise Memory — Sprint 24.2."""

from __future__ import annotations

from typing import Any


class EnterpriseMemory:
    def __init__(self) -> None:
        self._records: list[dict[str, Any]] = []

    def record(
        self,
        *,
        kind: str,
        subject_id: str,
        summary: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        kind = (kind or "").lower()
        allowed = {
            "decision",
            "process",
            "ai",
            "user",
            "change",
            "document",
            "communication",
        }
        if kind not in allowed:
            raise ValueError(f"unsupported memory kind: {kind}")
        if not subject_id or not summary:
            raise ValueError("subject_id and summary are required")
        item = {
            "kind": kind,
            "subject_id": subject_id,
            "summary": summary.strip(),
            "payload": dict(payload or {}),
        }
        self._records.append(item)
        return dict(item)

    def history(self, *, subject_id: str | None = None, kind: str | None = None) -> list[dict[str, Any]]:
        items = [dict(r) for r in self._records]
        if subject_id:
            items = [r for r in items if r["subject_id"] == subject_id]
        if kind:
            items = [r for r in items if r["kind"] == kind.lower()]
        return items
