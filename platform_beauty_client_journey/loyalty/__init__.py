"""Loyalty Trigger Engine — Sprint 22.4."""

from __future__ import annotations

from typing import Any

from platform_beauty_client_journey.models import LOYALTY_TRIGGERS


class LoyaltyTriggerEngine:
    def detect(self, journey: dict[str, Any]) -> dict[str, Any]:
        triggers = []
        visits = journey.get("visits") or []
        memberships = journey.get("memberships") or []
        if not visits:
            triggers.append({"kind": "long_absence", "severity": "medium"})
        if journey.get("loyalty_level") == "new":
            triggers.append({"kind": "procedure_due", "severity": "low"})
        if any(m.get("expired") for m in memberships):
            triggers.append({"kind": "membership_expired", "severity": "high"})
        if journey.get("birthday_today"):
            triggers.append({"kind": "birthday", "severity": "medium"})
        if journey.get("bonuses", 0) > 0 and journey.get("bonuses_expiring"):
            triggers.append({"kind": "bonuses_expiring", "severity": "medium"})
        # ensure at least one marketing handoff opportunity in bootstrap scenarios
        if not triggers:
            triggers.append({"kind": "procedure_due", "severity": "low"})
        offers = [
            {
                "trigger": t["kind"],
                "marketing_offer": f"campaign_for_{t['kind']}",
                "ai_marketing_os_ref": "ai_marketing_os",
                "requires_approval": True,
                "auto_sent": False,
            }
            for t in triggers
            if t["kind"] in LOYALTY_TRIGGERS
        ]
        return {"triggers": triggers, "offers": offers, "count": len(triggers)}
