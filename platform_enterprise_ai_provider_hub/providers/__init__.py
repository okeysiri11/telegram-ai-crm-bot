"""AI Provider Registry — Sprint 24.9."""

from __future__ import annotations

from typing import Any

from platform_enterprise_ai_provider_hub.models import PROVIDER_KINDS, PROVIDER_STATUSES


class AIProviderRegistry:
    def register(
        self,
        *,
        provider_id: str,
        name: str,
        kind: str,
        endpoint: str,
        api_version: str = "v1",
        supported_models: list[str] | None = None,
        cost_per_1k: float = 0.0,
        limits: dict[str, Any] | None = None,
        sla: dict[str, Any] | None = None,
        status: str = "active",
        priority: int = 100,
        health_score: float = 1.0,
    ) -> dict[str, Any]:
        if not provider_id or not name or not endpoint:
            raise ValueError("provider_id, name and endpoint are required")
        kind = (kind or "").lower()
        if kind not in PROVIDER_KINDS:
            raise ValueError(f"unsupported provider kind: {kind}")
        status = (status or "active").lower()
        if status not in PROVIDER_STATUSES:
            raise ValueError(f"unsupported status: {status}")
        return {
            "provider_id": provider_id,
            "name": name.strip(),
            "kind": kind,
            "endpoint": endpoint,
            "api_version": api_version,
            "supported_models": list(supported_models or []),
            "cost": float(cost_per_1k),
            "limits": dict(limits or {}),
            "sla": dict(sla or {"uptime_pct": 99.0}),
            "status": status,
            "priority": int(priority),
            "health_score": float(health_score),
            "extensible": True,
        }

    def catalog(self) -> dict[str, Any]:
        return {"supported_kinds": list(PROVIDER_KINDS), "statuses": list(PROVIDER_STATUSES), "extensible": True}
