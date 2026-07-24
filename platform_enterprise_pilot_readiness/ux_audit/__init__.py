"""UX Audit Engine — Sprint 23.1."""

from __future__ import annotations

from typing import Any

from platform_enterprise_pilot_readiness.models import AUDITED_SURFACES


class UXAuditEngine:
    def audit(self, *, surface: str, metrics: dict[str, Any] | None = None) -> dict[str, Any]:
        surface = (surface or "").lower()
        if surface not in AUDITED_SURFACES:
            raise ValueError(f"unsupported surface: {surface}")
        metrics = dict(metrics or {})
        clicks = int(metrics.get("clicks", 5))
        clarity = float(metrics.get("clarity", 0.7))
        speed_ms = float(metrics.get("speed_ms", 1200))
        transition_logic = float(metrics.get("transition_logic", 0.75))
        repeated_actions = int(metrics.get("repeated_actions", 1))
        score = round(
            max(0.0, min(1.0, (clarity + transition_logic) / 2 - min(0.3, clicks / 40) - min(0.2, repeated_actions / 20))),
            3,
        )
        suggestions = []
        if clicks > 4:
            suggestions.append("reduce_click_depth")
        if clarity < 0.8:
            suggestions.append("clarify_labels")
        if speed_ms > 1000:
            suggestions.append("speed_up_screen")
        if transition_logic < 0.8:
            suggestions.append("simplify_navigation")
        if repeated_actions >= 2:
            suggestions.append("add_shortcut_for_repeated_action")
        return {
            "surface": surface,
            "clicks": clicks,
            "clarity": clarity,
            "speed_ms": speed_ms,
            "transition_logic": transition_logic,
            "repeated_actions": repeated_actions,
            "ux_score": score,
            "ai_suggestions": suggestions,
            "ai_may_act": False,
            "proposes_only": True,
        }

    def audit_all(self, *, metrics_by_surface: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
        metrics_by_surface = metrics_by_surface or {}
        results = [self.audit(surface=s, metrics=metrics_by_surface.get(s)) for s in AUDITED_SURFACES]
        avg = round(sum(r["ux_score"] for r in results) / len(results), 3)
        return {"surfaces": results, "average_ux_score": avg, "proposes_only": True, "ai_may_act": False}
