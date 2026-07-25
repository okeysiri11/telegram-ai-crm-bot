"""Failure Injector — Sprint 25.3."""

from __future__ import annotations

from typing import Any

from platform_chaos.models import FAILURE_TYPES


class FailureInjector:
    def inject(self, *, scenario: dict[str, Any]) -> dict[str, Any]:
        failure_type = scenario.get("failure_type")
        if failure_type not in FAILURE_TYPES:
            raise ValueError(f"unsupported failure_type: {failure_type}")
        return {
            "injected": True,
            "scenario_id": scenario.get("scenario_id"),
            "target_service": scenario.get("target_service"),
            "failure_type": failure_type,
            "duration_sec": scenario.get("duration_sec", 30),
            "destructive": False,
            "data_loss": False,
            "simulated": True,
        }
