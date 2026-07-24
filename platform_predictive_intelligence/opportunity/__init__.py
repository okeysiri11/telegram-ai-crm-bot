"""Opportunity Detector — Sprint 24.3."""

from __future__ import annotations

from typing import Any


class OpportunityDetector:
    def detect(self, *, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        signals = dict(signals or {})
        opportunities = []
        if float(signals.get("open_slots", 0)) > 5:
            opportunities.append({"type": "idle_capacity", "detail": "free_intervals"})
        if float(signals.get("unused_resources", 0)) > 0:
            opportunities.append({"type": "unused_resources", "detail": "redeploy"})
        if signals.get("underused_service"):
            opportunities.append({"type": "promising_service", "detail": signals["underused_service"]})
        if float(signals.get("promo_headroom", 0)) > 0:
            opportunities.append({"type": "potential_promo", "detail": "lift_available"})
        if not opportunities:
            opportunities.append({"type": "new_revenue", "detail": "upsell_packages"})
        return {"opportunities": opportunities, "count": len(opportunities)}
