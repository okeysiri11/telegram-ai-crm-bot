"""Bottleneck Analyzer — Sprint 25.2."""

from __future__ import annotations

from typing import Any


class BottleneckAnalyzer:
    def analyze(self, *, resources: dict[str, float], api: dict[str, Any] | None = None, workflow: dict[str, Any] | None = None) -> dict[str, Any]:
        resources = dict(resources or {})
        bottlenecks = []
        for name, val in resources.items():
            if float(val) >= 85:
                bottlenecks.append({"type": "overloaded_service", "target": name, "value": float(val)})
        if api and float(api.get("p95_ms", 0)) > 150:
            bottlenecks.append({"type": "slow_api", "target": api.get("endpoint"), "p95_ms": api.get("p95_ms")})
        if api and float(api.get("max_ms", 0)) > 300:
            bottlenecks.append({"type": "slow_query_or_api", "target": api.get("endpoint"), "max_ms": api.get("max_ms")})
        if workflow and float(workflow.get("duration_ms", 0)) > 1500:
            bottlenecks.append({"type": "heavy_workflow", "duration_ms": workflow.get("duration_ms"), "steps": workflow.get("steps")})
        return {
            "bottlenecks": bottlenecks,
            "count": len(bottlenecks),
            "has_bottlenecks": bool(bottlenecks),
        }
