"""Performance profiling — Sprint 21.7."""

from __future__ import annotations

from typing import Any

from platform_performance.models import PROFILE_TARGETS, RESOURCE_DIMENSIONS


class PerformanceProfiler:
    BASELINES = {
        "api": {"cpu": 0.32, "memory": 0.41, "disk": 0.12, "network": 0.28, "hotspot": "serialization"},
        "ai_orchestrator": {"cpu": 0.55, "memory": 0.62, "disk": 0.08, "network": 0.22, "hotspot": "model_routing"},
        "workflow": {"cpu": 0.38, "memory": 0.35, "disk": 0.15, "network": 0.18, "hotspot": "state_persistence"},
        "event_bus": {"cpu": 0.44, "memory": 0.33, "disk": 0.20, "network": 0.48, "hotspot": "queue_fanout"},
        "data_fabric": {"cpu": 0.36, "memory": 0.47, "disk": 0.40, "network": 0.30, "hotspot": "federation_join"},
        "knowledge_platform": {"cpu": 0.50, "memory": 0.58, "disk": 0.25, "network": 0.20, "hotspot": "vector_search"},
        "enterprise_hub": {"cpu": 0.30, "memory": 0.34, "disk": 0.10, "network": 0.25, "hotspot": "route_dispatch"},
    }

    def profile(self, target: str | None = None) -> dict[str, Any]:
        targets = [target] if target else list(PROFILE_TARGETS)
        profiles = []
        bottlenecks = []
        for name in targets:
            if name not in self.BASELINES:
                raise ValueError(f"unknown profile target: {name}")
            data = self.BASELINES[name]
            profiles.append({"target": name, **{d: data[d] for d in RESOURCE_DIMENSIONS}, "hotspot": data["hotspot"]})
            if any(data[d] >= 0.45 for d in RESOURCE_DIMENSIONS):
                bottlenecks.append({"target": name, "hotspot": data["hotspot"]})
        return {
            "profiles": profiles,
            "bottlenecks": bottlenecks,
            "dimensions": list(RESOURCE_DIMENSIONS),
            "count": len(profiles),
        }
