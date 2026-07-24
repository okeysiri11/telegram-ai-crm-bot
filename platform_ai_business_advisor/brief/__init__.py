"""AI Daily Brief — Sprint 22.1."""

from __future__ import annotations

from typing import Any


class DailyBrief:
    def generate(
        self,
        *,
        health: dict[str, Any],
        opportunities: dict[str, Any],
        recommendations: dict[str, Any],
        forecasts: dict[str, Any],
    ) -> dict[str, Any]:
        yesterday = {
            "overall_health": health.get("overall"),
            "industry": health.get("industry"),
            "dimensions_tracked": len(health.get("scores") or []),
        }
        changes = [f"{s['dimension']}={'ok' if s['healthy'] else 'alert'}" for s in health.get("scores") or []]
        problems = list(health.get("problems") or [])
        opps = [o["kind"] for o in opportunities.get("opportunities") or []]
        actions = [r["kind"] for r in recommendations.get("recommendations") or []]
        effect = {
            "revenue_forecast": next((f["value"] for f in forecasts.get("forecasts") or [] if f["kind"] == "revenue"), None),
            "recommended_lifts": [r.get("expected_effect") for r in recommendations.get("recommendations") or []],
        }
        return {
            "yesterday": yesterday,
            "what_changed": changes,
            "problems_found": problems,
            "opportunities_found": opps,
            "recommended_actions": actions,
            "expected_effect": effect,
            "ai_decision_authority": False,
            "requires_owner_review": True,
            "passed": True,
        }
