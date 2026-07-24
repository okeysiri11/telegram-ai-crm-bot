"""Scenario Registry — Sprint 24.4."""

from __future__ import annotations

from typing import Any


class ScenarioRegistry:
    def create(
        self,
        *,
        scenario_id: str,
        name: str,
        description: str = "",
        author: str = "platform_owner",
        models: list[str] | None = None,
        status: str = "draft",
    ) -> dict[str, Any]:
        if not scenario_id or not name:
            raise ValueError("scenario_id and name are required")
        return {
            "scenario_id": scenario_id,
            "name": name.strip(),
            "description": description,
            "author": author,
            "models_used": list(models or []),
            "status": status,
            "run_history": [],
        }

    def record_run(self, scenario: dict[str, Any], *, run_id: str, result_summary: str = "") -> dict[str, Any]:
        updated = dict(scenario)
        hist = list(updated.get("run_history") or [])
        hist.append({"run_id": run_id, "summary": result_summary})
        updated["run_history"] = hist[-50:]
        updated["status"] = "ran"
        return updated
