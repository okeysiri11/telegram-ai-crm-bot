# Dealer Network Engine — profiles, verification, ratings, leads, analytics.

from __future__ import annotations

from applications.auto_marketplace.marketplace.models import DealerNetworkProfile, DealerTier
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class DealerNetworkEngine:
    """Dealer network profiles, inventory counts, lead assignment."""

    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store
        self._lead_assignments: list[dict] = []

    def register_profile(self, profile: DealerNetworkProfile) -> DealerNetworkProfile:
        if not profile.dealer_id or not profile.name:
            raise ValidationError("dealer_id and name are required")
        return self._store.dealer_network_profiles.save(profile.dealer_id, profile)

    def get(self, dealer_id: str) -> DealerNetworkProfile:
        profile = self._store.dealer_network_profiles.get(dealer_id)
        if profile is None:
            raise NotFoundError("DealerNetworkProfile", dealer_id)
        return profile

    def list_profiles(self, *, region: str = "", verified_only: bool = False) -> list[DealerNetworkProfile]:
        items = self._store.dealer_network_profiles.list_all()
        if region:
            items = [p for p in items if p.region.lower() == region.lower()]
        if verified_only:
            items = [p for p in items if p.verified]
        return items

    def verify(self, dealer_id: str, *, tier: DealerTier = DealerTier.VERIFIED) -> DealerNetworkProfile:
        profile = self.get(dealer_id)
        profile.verified = True
        profile.tier = tier
        return self._store.dealer_network_profiles.save(dealer_id, profile)

    def rate(self, dealer_id: str, rating: float) -> DealerNetworkProfile:
        profile = self.get(dealer_id)
        total = profile.rating * profile.review_count + rating
        profile.review_count += 1
        profile.rating = round(total / profile.review_count, 2)
        return self._store.dealer_network_profiles.save(dealer_id, profile)

    def add_branch(self, dealer_id: str, branch: dict) -> DealerNetworkProfile:
        profile = self.get(dealer_id)
        profile.branches.append(branch)
        return self._store.dealer_network_profiles.save(dealer_id, profile)

    def add_manager(self, dealer_id: str, manager: dict) -> DealerNetworkProfile:
        profile = self.get(dealer_id)
        profile.managers.append(manager)
        return self._store.dealer_network_profiles.save(dealer_id, profile)

    def sync_inventory(self, dealer_id: str) -> DealerNetworkProfile:
        profile = self.get(dealer_id)
        listings = [
            l for l in self._store.marketplace_listings.list_all()
            if l.dealer_id == dealer_id and l.status.value == "active"
        ]
        profile.inventory_count = len(listings)
        return self._store.dealer_network_profiles.save(dealer_id, profile)

    def assign_lead(self, dealer_id: str, lead_id: str, *, manager_id: str = "") -> dict:
        self.get(dealer_id)
        assignment = {"dealer_id": dealer_id, "lead_id": lead_id, "manager_id": manager_id}
        self._lead_assignments.append(assignment)
        self._store.dealer_lead_assignments.save(f"{dealer_id}:{lead_id}", assignment)
        return assignment

    def analytics(self, dealer_id: str) -> dict:
        profile = self.get(dealer_id)
        listings = [l for l in self._store.marketplace_listings.list_all() if l.dealer_id == dealer_id]
        active = [l for l in listings if l.status.value == "active"]
        sold = [l for l in listings if l.status.value == "sold"]
        assignments = [a for a in self._store.dealer_lead_assignments.list_all() if a.get("dealer_id") == dealer_id]
        return {
            "dealer_id": dealer_id,
            "rating": profile.rating,
            "verified": profile.verified,
            "tier": profile.tier.value,
            "inventory_active": len(active),
            "inventory_sold": len(sold),
            "branches": len(profile.branches),
            "managers": len(profile.managers),
            "leads_assigned": len(assignments),
            "avg_list_price": round(sum(l.price for l in active) / len(active), 2) if active else 0.0,
        }

    def metrics(self) -> dict:
        return {
            "profiles": self._store.dealer_network_profiles.count(),
            "lead_assignments": self._store.dealer_lead_assignments.count(),
        }


dealer_network_engine = DealerNetworkEngine()
