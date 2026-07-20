# Customer Intelligence — profile analysis and behavior insights.

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.ai_sales.integration import ai_sales_platform_bridge
from applications.auto_marketplace.ai_sales.models import CustomerIntelligenceProfile
from applications.auto_marketplace.crm.models import CustomerProfile
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class CustomerIntelligenceService:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def _get_customer(self, customer_id: str) -> CustomerProfile | None:
        return self._store.customer_profiles.get(customer_id)

    async def analyze_profile(self, customer_id: str) -> CustomerIntelligenceProfile:
        customer = self._get_customer(customer_id)
        prefs = customer.preferences if customer else {}
        interactions = [
            i.to_dict() for i in self._store.interactions.list_all() if i.customer_id == customer_id
        ]

        budget_max = float(prefs.get("budget_max", 50000))
        budget_min = float(prefs.get("budget_min", budget_max * 0.6))
        preferred_makes = [str(m) for m in prefs.get("makes", prefs.get("make", "").split(",") if prefs.get("make") else [])]
        if isinstance(prefs.get("make"), str) and prefs.get("make") and not preferred_makes:
            preferred_makes = [prefs["make"]]

        intent = customer.intent_score if customer else 0.0
        analysis = await ai_sales_platform_bridge.reason(
            "Analyze customer purchase intent and preferences",
            {"customer_id": customer_id, "interactions": interactions[-20:]},
        )
        if "intent_score" in analysis:
            intent = float(analysis["intent_score"])

        profile = CustomerIntelligenceProfile(
            customer_id=customer_id,
            purchase_intent=intent,
            budget_min=budget_min,
            budget_max=budget_max,
            preferred_makes=preferred_makes,
            preferred_body_types=[str(b) for b in prefs.get("body_types", [])],
            behavior_score=min(100.0, len(interactions) * 5 + intent * 0.5),
            communication_channels=self._detect_channels(interactions),
            vehicle_preferences={
                "fuel_type": prefs.get("fuel_type", ""),
                "transmission": prefs.get("transmission", ""),
                "year_min": prefs.get("year_min", 2018),
            },
        )
        self._store.intelligence_profiles.save(profile.profile_id, profile)
        return profile

    @staticmethod
    def _detect_channels(interactions: list[dict[str, Any]]) -> list[str]:
        channels: set[str] = set()
        for item in interactions:
            itype = item.get("interaction_type", item.get("type", ""))
            if itype:
                channels.add(str(itype))
        return sorted(channels) or ["web"]

    async def purchase_intent(self, customer_id: str) -> dict[str, Any]:
        profile = await self.analyze_profile(customer_id)
        label = "high" if profile.purchase_intent > 70 else "medium" if profile.purchase_intent > 40 else "low"
        return {"customer_id": customer_id, "intent_score": profile.purchase_intent, "label": label}

    async def estimate_budget(self, customer_id: str) -> dict[str, float]:
        profile = await self.analyze_profile(customer_id)
        return {"budget_min": profile.budget_min, "budget_max": profile.budget_max}

    async def extract_vehicle_preferences(self, customer_id: str) -> dict[str, Any]:
        profile = await self.analyze_profile(customer_id)
        return {
            "preferred_makes": profile.preferred_makes,
            "preferred_body_types": profile.preferred_body_types,
            "vehicle_preferences": profile.vehicle_preferences,
        }

    def communication_history(self, customer_id: str) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for interaction in self._store.interactions.list_all():
            if interaction.customer_id == customer_id:
                items.append(interaction.to_dict())
        for call in self._store.phone_calls.list_all():
            if call.customer_id == customer_id:
                items.append(call.to_dict())
        for email in self._store.email_messages.list_all():
            if email.customer_id == customer_id:
                items.append(email.to_dict())
        items.sort(key=lambda x: x.get("created_at", 0), reverse=True)
        return items

    def get_profile(self, customer_id: str) -> CustomerIntelligenceProfile | None:
        for profile in self._store.intelligence_profiles.list_all():
            if profile.customer_id == customer_id:
                return profile
        return None


customer_intelligence_service = CustomerIntelligenceService()
