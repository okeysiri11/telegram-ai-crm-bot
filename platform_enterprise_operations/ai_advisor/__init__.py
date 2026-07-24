"""AI Operations Advisor — Sprint 23.0."""

from __future__ import annotations

from typing import Any


class AIOperationsAdvisor:
    def daily_report(self, *, dashboard: dict[str, Any] | None = None, pilots: list[dict[str, Any]] | None = None, usage: dict[str, Any] | None = None, monitoring: dict[str, Any] | None = None) -> dict[str, Any]:
        dashboard = dashboard or {}
        pilots = list(pilots or [])
        usage = usage or {}
        monitoring = monitoring or {}
        recommendations = [
            "review_degraded_tenants",
            "prioritize_pilot_training",
            "ship_top_feedback_to_epi",
        ]
        if monitoring.get("degraded"):
            recommendations.insert(0, "restore_platform_services")
        if usage.get("incomplete_flows", 0) > 0:
            recommendations.append("fix_incomplete_user_flows")
        return {
            "platform_state": "ok" if monitoring.get("all_ok", True) else "attention",
            "pilot_companies": len(pilots),
            "active_companies": dashboard.get("active_companies", 0),
            "performance_notes": usage.get("avg_operation_ms"),
            "feature_quality": {
                "most_used": usage.get("most_used", []),
                "rarely_used": usage.get("rarely_used", []),
            },
            "development_recommendations": recommendations,
            "ai_may_act": False,
            "proposes_only": True,
            "requires_owner_approval": True,
            "audience": "platform_owner",
        }
