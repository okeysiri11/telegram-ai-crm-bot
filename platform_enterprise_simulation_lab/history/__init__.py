"""Simulation History — Sprint 24.4."""

from __future__ import annotations

from typing import Any


class SimulationHistory:
    def __init__(self) -> None:
        self._items: list[dict[str, Any]] = []

    def save(
        self,
        *,
        scenario_id: str,
        results: dict[str, Any] | None = None,
        decision: str | None = None,
        actual_outcome: float | None = None,
        forecast_accuracy: float | None = None,
    ) -> dict[str, Any]:
        item = {
            "scenario_id": scenario_id,
            "results": dict(results or {}),
            "decision": decision,
            "actual_outcome": actual_outcome,
            "forecast_accuracy": forecast_accuracy,
        }
        self._items.append(item)
        return dict(item)

    def list_all(self) -> list[dict[str, Any]]:
        return [dict(i) for i in self._items]
