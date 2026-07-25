"""Optimization Advisor — Sprint 25.2."""

from __future__ import annotations

from typing import Any

from platform_enterprise_performance_testing.models import ADVICE_KINDS


class OptimizationAdvisor:
    def recommend(self, *, bottlenecks: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        bottlenecks = list(bottlenecks or [])
        advice = []
        for b in bottlenecks:
            t = b.get("type")
            if t == "overloaded_service" and b.get("target") == "database":
                advice.append({"kind": "add_index", "detail": "add missing indexes on hot tables"})
                advice.append({"kind": "optimize_sql", "detail": "review slow queries"})
                advice.append({"kind": "increase_connection_pool", "detail": "raise DB pool size"})
            elif t == "overloaded_service" and b.get("target") in ("redis", "ram"):
                advice.append({"kind": "change_caching", "detail": "tune cache TTLs and eviction"})
            elif t == "slow_api":
                advice.append({"kind": "optimize_api", "detail": f"optimize {b.get('target')}"})
            elif t == "heavy_workflow":
                advice.append({"kind": "split_service", "detail": "split heavy workflow steps"})
            elif t == "overloaded_service":
                advice.append({"kind": "scale_module", "detail": f"scale {b.get('target')}"})
        if not advice:
            advice.append({"kind": "optimize_api", "detail": "maintain current baselines"})
        # unique by kind
        seen = set()
        unique = []
        for a in advice:
            if a["kind"] not in seen:
                seen.add(a["kind"])
                unique.append(a)
        return {"recommendations": unique, "kinds": list(ADVICE_KINDS), "count": len(unique)}
