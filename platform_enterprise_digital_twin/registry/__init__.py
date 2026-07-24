"""Enterprise Twin Registry — Sprint 24.5."""

from __future__ import annotations

from typing import Any


class TwinRegistry:
    def create(
        self,
        *,
        company_id: str,
        structure: dict[str, Any] | None = None,
        branches: list[dict[str, Any]] | None = None,
        employees: list[dict[str, Any]] | None = None,
        customers: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        if not company_id:
            raise ValueError("company_id is required")
        return {
            "company_id": company_id,
            "structure": dict(structure or {"type": "enterprise"}),
            "branches": list(branches or []),
            "employees": list(employees or []),
            "customers": list(customers or []),
            "active_processes": [],
            "resources": {},
            "ai_state": {"agents": 0, "status": "idle"},
            "change_history": [{"event": "twin_created"}],
            "version": "2.0",
        }

    def record_change(self, twin: dict[str, Any], *, event: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
        updated = dict(twin)
        hist = list(updated.get("change_history") or [])
        hist.append({"event": event, "details": dict(details or {})})
        updated["change_history"] = hist[-100:]
        return updated
