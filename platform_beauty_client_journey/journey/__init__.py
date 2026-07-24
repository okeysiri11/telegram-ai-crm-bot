"""Customer Journey — Sprint 22.4."""

from __future__ import annotations

from typing import Any

from platform_beauty_client_journey.models import JOURNEY_STAGES


class CustomerJourney:
    def create(
        self,
        *,
        customer_id: str,
        source: str = "organic",
        first_contact: str = "",
    ) -> dict[str, Any]:
        if not customer_id:
            raise ValueError("customer_id is required")
        return {
            "customer_id": customer_id,
            "first_contact": first_contact or "intake",
            "acquisition_source": source,
            "first_booking": None,
            "visits": [],
            "cancellations": [],
            "reschedules": [],
            "purchases": [],
            "certificates": [],
            "memberships": [],
            "ai_recommendations": [],
            "loyalty_level": "new",
            "stages": list(JOURNEY_STAGES),
            "crm_ref": "enterprise_crm",
        }

    def record_event(self, journey: dict[str, Any], *, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        updated = dict(journey)
        if kind == "booking" and not updated.get("first_booking"):
            updated["first_booking"] = payload
        mapping = {
            "visit": "visits",
            "cancellation": "cancellations",
            "reschedule": "reschedules",
            "purchase": "purchases",
            "certificate": "certificates",
            "membership": "memberships",
            "ai_recommendation": "ai_recommendations",
        }
        key = mapping.get(kind)
        if key:
            items = list(updated.get(key) or [])
            items.append(payload)
            updated[key] = items
        visits = len(updated.get("visits") or [])
        if visits >= 5:
            updated["loyalty_level"] = "gold"
        elif visits >= 2:
            updated["loyalty_level"] = "silver"
        elif visits >= 1:
            updated["loyalty_level"] = "bronze"
        return updated
