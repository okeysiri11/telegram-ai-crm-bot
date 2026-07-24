"""Change Impact View — Sprint 24.5."""

from __future__ import annotations

from typing import Any


class ChangeImpactView:
    def view(
        self,
        *,
        changed_objects: list[str] | None = None,
        affected_processes: list[str] | None = None,
        ai_consumers: list[str] | None = None,
        updated_forecasts: list[str] | None = None,
    ) -> dict[str, Any]:
        return {
            "changed_objects": list(changed_objects or []),
            "affected_processes": list(affected_processes or []),
            "ai_consumers": list(ai_consumers or []),
            "updated_forecasts": list(updated_forecasts or []),
        }
