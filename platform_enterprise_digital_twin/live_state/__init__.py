"""Live State Engine — Sprint 24.5."""

from __future__ import annotations

from typing import Any

from platform_enterprise_digital_twin.models import LIVE_METRICS


class LiveStateEngine:
    def snapshot(self, *, metrics: dict[str, Any] | None = None) -> dict[str, Any]:
        metrics = dict(metrics or {})
        state = {k: metrics.get(k, 0 if k not in ("ai_status", "services_status") else "ok") for k in LIVE_METRICS}
        if "ai_status" not in metrics:
            state["ai_status"] = "ok"
        if "services_status" not in metrics:
            state["services_status"] = "ok"
        return {
            "live": True,
            "realtime": True,
            "metrics": state,
            "metric_keys": list(LIVE_METRICS),
        }
