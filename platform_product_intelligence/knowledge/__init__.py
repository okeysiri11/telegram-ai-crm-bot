"""Decision knowledge base — Sprint 22.0."""

from __future__ import annotations

from typing import Any


class DecisionKnowledgeBase:
    def __init__(self) -> None:
        self._entries: list[dict[str, Any]] = []

    def record(self, entry: dict[str, Any]) -> dict[str, Any]:
        record = {
            "discussion": entry.get("discussion", []),
            "ai_conclusions": entry.get("ai_conclusions", []),
            "owner_decision": entry.get("owner_decision"),
            "implementation_results": entry.get("implementation_results"),
            "effectiveness": entry.get("effectiveness"),
            "report_id": entry.get("report_id"),
            "decision_id": entry.get("decision_id"),
        }
        self._entries.append(record)
        return {**record, "stored": True, "history_size": len(self._entries)}

    def history(self, *, limit: int = 50) -> list[dict[str, Any]]:
        return list(self._entries[-limit:])

    def status(self) -> dict[str, Any]:
        return {"entries": len(self._entries)}
