"""Go-Live Checklist — Sprint 22.9."""

from __future__ import annotations

from typing import Any

from platform_enterprise_onboarding.models import GO_LIVE_ITEMS


class GoLiveChecklist:
    def evaluate(self, *, completed: dict[str, bool] | None = None) -> dict[str, Any]:
        completed = dict(completed or {})
        items = {k: bool(completed.get(k, False)) for k in GO_LIVE_ITEMS}
        all_done = all(items.values())
        return {
            "items": items,
            "completed_count": sum(1 for v in items.values() if v),
            "total": len(items),
            "passed": all_done,
            "company_status": "Active" if all_done else "Onboarding",
        }
