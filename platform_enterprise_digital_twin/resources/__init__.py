"""Resource Monitor — Sprint 24.5."""

from __future__ import annotations

from typing import Any


class ResourceMonitor:
    def monitor(self, *, resources: dict[str, Any] | None = None) -> dict[str, Any]:
        resources = dict(resources or {})
        return {
            "personnel": resources.get("personnel", 0),
            "equipment": resources.get("equipment", 0),
            "materials": resources.get("materials", 0),
            "premises": resources.get("premises", 0),
            "finance": resources.get("finance", 0),
            "compute": resources.get("compute", 0),
            "ok": True,
        }
