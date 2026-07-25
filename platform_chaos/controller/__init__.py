"""Chaos Controller — Sprint 25.3."""

from __future__ import annotations

from typing import Any

from platform_chaos.models import FAILURE_TYPES


class ChaosController:
    def create_scenario(
        self,
        *,
        scenario_id: str,
        name: str,
        description: str = "",
        target_service: str,
        failure_type: str,
        duration_sec: int = 30,
        recovery_policy: str = "auto",
        expected_result: str = "service_recovers",
        validation_rules: list[str] | None = None,
    ) -> dict[str, Any]:
        if not scenario_id or not name or not target_service:
            raise ValueError("scenario_id, name and target_service are required")
        failure_type = (failure_type or "").lower()
        if failure_type not in FAILURE_TYPES:
            raise ValueError(f"unsupported failure_type: {failure_type}")
        return {
            "scenario_id": scenario_id,
            "name": name.strip(),
            "description": description or None,
            "target_service": target_service,
            "failure_type": failure_type,
            "duration_sec": int(duration_sec),
            "recovery_policy": recovery_policy,
            "expected_result": expected_result,
            "validation_rules": list(validation_rules or ["no_data_loss", "auto_recover"]),
            "status": "ready",
        }
