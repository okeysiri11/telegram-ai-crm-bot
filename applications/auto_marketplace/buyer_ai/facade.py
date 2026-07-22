"""Buyer AI Suite facade — Sprint 13.4."""

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.buyer_ai.negotiation import NegotiationAI
from applications.auto_marketplace.buyer_ai.profile import BuyerProfile
from applications.auto_marketplace.buyer_ai.purchase import BuyingProtection, PurchaseIntelligence
from applications.auto_marketplace.buyer_ai.search import VehicleSearch
from applications.auto_marketplace.buyer_ai.services import BuyerDashboard, OwnershipAssistant, PersonalAssistant
from applications.auto_marketplace.config import DEFAULT_CONFIG
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class BuyerAISuite:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store
        self.profile = BuyerProfile(self.store)
        self.search = VehicleSearch(self.store)
        self.negotiation = NegotiationAI(self.store)
        self.purchase = PurchaseIntelligence(self.store)
        self.protection = BuyingProtection(self.store)
        self.ownership = OwnershipAssistant(self.store)
        self.assistant = PersonalAssistant(self.store)
        self.dashboard = BuyerDashboard(self.store)

    def bootstrap(self) -> dict[str, Any]:
        buyer = self.profile.create(
            name="Alex Buyer",
            budget_max=25000,
            preferred_brands=["Volkswagen", "Honda"],
            preferred_models=["Golf", "Civic"],
            fuel=["gasoline", "hybrid"],
            body_styles=["hatchback", "sedan"],
            regions=["EU"],
        )
        listing = self.search.index_listing(
            vin="WVWZZZ1JZXW000001",
            make="Volkswagen",
            model="Golf",
            year=2020,
            price=18500,
            dealer="Prime Motors",
            fuel="gasoline",
            body_style="hatchback",
            region="EU",
        )
        self.search.index_listing(
            vin="1HGCM82633A000001",
            make="Honda",
            model="Accord",
            year=2019,
            price=17000,
            dealer="City Auto",
            fuel="gasoline",
            body_style="sedan",
            region="EU",
        )
        search = self.search.natural_language_search(query="Volkswagen Golf under 20000", buyer_id=buyer["buyer_id"])
        recs = self.search.recommend(buyer_id=buyer["buyer_id"])
        neg = self.negotiation.start(buyer_id=buyer["buyer_id"], listing_id=listing["listing_id"])
        offer = self.negotiation.generate_offer(neg["negotiation_id"], strategy="fair")
        self.negotiation.generate_counter(neg["negotiation_id"])
        intel = self.purchase.analyze(price=18500, mileage=45000, fuel="gasoline", years=5)
        protection = self.protection.assess(vin="WVWZZZ1JZXW000001", listing_id=listing["listing_id"], listing_price=18500, inspection_ref="ia-ref")
        ownership = self.ownership.create_plan(buyer_id=buyer["buyer_id"], vin="WVWZZZ1JZXW000001")
        self.ownership.add_reminder(ownership["ownership_id"], title="Oil change", due_at="2026-09-01T00:00:00Z")
        self.assistant.ask(mode="purchase", message="Should I buy this Golf?", buyer_id=buyer["buyer_id"])
        board = self.dashboard.render(dashboard_type="buyer", buyer_id=buyer["buyer_id"])
        return {
            "bootstrap": True,
            "buyer_id": buyer["buyer_id"],
            "listing_id": listing["listing_id"],
            "search_id": search["search_id"],
            "recommendation_id": recs["recommendation_id"],
            "negotiation_id": neg["negotiation_id"],
            "offer_id": offer["offer_id"],
            "analysis_id": intel["analysis_id"],
            "protection_id": protection["protection_id"],
            "ownership_id": ownership["ownership_id"],
            "dashboard_id": board["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "profile": self.profile.status(),
            "search": self.search.status(),
            "negotiation": self.negotiation.status(),
            "purchase": self.purchase.status(),
            "protection": self.protection.status(),
            "ownership": self.ownership.status(),
            "assistant": self.assistant.status(),
            "dashboard": self.dashboard.status(),
        }


buyer_ai = BuyerAISuite()
