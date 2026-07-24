"""Pilot Checklist — Sprint 23.1."""

from __future__ import annotations

from typing import Any

from platform_enterprise_pilot_readiness.models import PILOT_CHECKLIST_ITEMS


class PilotChecklist:
    def evaluate(self, *, completed: dict[str, bool] | None = None) -> dict[str, Any]:
        completed = dict(completed or {})
        items = {k: bool(completed.get(k, False)) for k in PILOT_CHECKLIST_ITEMS}
        passed = all(items.values())
        return {
            "items": items,
            "completed_count": sum(1 for v in items.values() if v),
            "total": len(items),
            "passed": passed,
            "pilot_access_granted": passed,
        }
