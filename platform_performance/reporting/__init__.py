"""Performance certification & reporting — Sprint 21.7."""

from __future__ import annotations

from typing import Any


class PerformanceDashboard:
    def render(self, *, benchmark: dict[str, Any], load: dict[str, Any], stress: dict[str, Any], scale: dict[str, Any], monitor: dict[str, Any]) -> dict[str, Any]:
        certified = all(
            [
                benchmark.get("passed"),
                load.get("pass_rate") == 1.0,
                stress.get("passed"),
                scale.get("passed"),
                monitor.get("passed"),
            ]
        )
        return {
            "sla_passed": benchmark.get("passed"),
            "load_pass_rate": load.get("pass_rate"),
            "stress_max_users": stress.get("max_users"),
            "hpa_enabled": scale.get("k8s_hpa", {}).get("enabled"),
            "monitoring_continuous": monitor.get("continuous"),
            "certified": certified,
            "status": "production_ready" if certified else "needs_tuning",
        }


class PerformanceCertification:
    def certify(self, *, dashboard: dict[str, Any], tuning: dict[str, Any], optimizations: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "certified": dashboard.get("certified", False),
            "status": dashboard.get("status"),
            "benchmarks_ok": dashboard.get("sla_passed"),
            "scalability_ok": dashboard.get("hpa_enabled"),
            "ai_optimized": any(o.get("kind") == "ai" and o.get("passed") for o in optimizations),
            "recommendations": tuning.get("recommendations", []),
            "production_validated": dashboard.get("certified", False),
        }
