"""Opportunity Marketing Engine — Sprint 22.5."""

from __future__ import annotations

from typing import Any

from platform_ai_marketing_os.models import OPPORTUNITY_SIGNALS


class OpportunityMarketingEngine:
    def detect(
        self,
        *,
        advisor: dict[str, Any] | None = None,
        booking: dict[str, Any] | None = None,
        dashboard: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        found = []
        advisor = advisor or {}
        booking = booking or {}
        dashboard = dashboard or {}
        if dashboard.get("open_slots", 0) > 0 or advisor.get("open_slots"):
            found.append({"kind": "open_hours", "source": "beauty_dashboard", "severity": "medium"})
        if (dashboard.get("master_load") or 1) < 0.6 or "underloaded_staff" in (advisor.get("opportunities_found") or []):
            found.append({"kind": "underloaded_masters", "source": "ai_business_advisor", "severity": "high"})
        if "revenue_decline" in (advisor.get("opportunities_found") or []) or (dashboard.get("revenue") or 1) < 1:
            found.append({"kind": "revenue_decline", "source": "ai_business_advisor", "severity": "high"})
        if "repeat_visit_decline" in (advisor.get("opportunities_found") or []):
            found.append({"kind": "revisit_decline", "source": "ai_business_advisor", "severity": "medium"})
        if booking.get("waitlist") or (dashboard.get("bookings") or 0) < 3:
            found.append({"kind": "service_underuse", "source": "smart_booking", "severity": "low"})
        if not found:
            found.append({"kind": "open_hours", "source": "beauty_dashboard", "severity": "low"})
        proposals = [
            {
                "signal": s["kind"],
                "proposal": f"campaign_for_{s['kind']}",
                "expected_effect": {"bookings_lift": 0.1, "load_lift": 0.08},
                "requires_owner_approval": True,
                "auto_published": False,
            }
            for s in found
            if s["kind"] in OPPORTUNITY_SIGNALS
        ]
        return {"signals": found, "proposals": proposals, "count": len(found)}
