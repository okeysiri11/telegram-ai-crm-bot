# Marketplace domain facade — Sprint 10.2.

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.auctions.engine import AuctionsEngine, auctions_engine
from applications.auto_marketplace.dealer_network.engine import DealerNetworkEngine, dealer_network_engine
from applications.auto_marketplace.history.engine import HistoryEngine, history_engine
from applications.auto_marketplace.integrations.platform_bridge import PlatformBridge, platform_bridge
from applications.auto_marketplace.listings.engine import ListingsEngine, listings_engine
from applications.auto_marketplace.marketplace.engine import MarketplaceEngine, marketplace_engine
from applications.auto_marketplace.ownership.engine import OwnershipEngine, ownership_engine
from applications.auto_marketplace.valuation.engine import ValuationEngine, valuation_engine
from applications.auto_marketplace.verification.engine import VerificationEngine, verification_engine
from applications.auto_marketplace.vin.engine import VINEngine, vin_engine


class MarketplaceDomainEngine:
    """Sprint 10.2 facade — marketplace, VIN, history, dealers, verification, valuation."""

    def __init__(
        self,
        marketplace: MarketplaceEngine | None = None,
        listings: ListingsEngine | None = None,
        auctions: AuctionsEngine | None = None,
        vin: VINEngine | None = None,
        history: HistoryEngine | None = None,
        dealers: DealerNetworkEngine | None = None,
        verification: VerificationEngine | None = None,
        ownership: OwnershipEngine | None = None,
        valuation: ValuationEngine | None = None,
        platform: PlatformBridge | None = None,
    ) -> None:
        self.marketplace = marketplace or marketplace_engine
        self.listings = listings or listings_engine
        self.auctions = auctions or auctions_engine
        self.vin = vin or vin_engine
        self.history = history or history_engine
        self.dealers = dealers or dealer_network_engine
        self.verification = verification or verification_engine
        self.ownership = ownership or ownership_engine
        self.valuation = valuation or valuation_engine
        self._platform = platform or platform_bridge

    def metrics(self) -> dict[str, Any]:
        return {
            "marketplace": self.marketplace.metrics(),
            "vin": self.vin.metrics(),
            "history": self.history.metrics(),
            "dealers": self.dealers.metrics(),
            "verification": self.verification.metrics(),
            "ownership": self.ownership.metrics(),
            "valuation": self.valuation.metrics(),
        }

    def create_listing(self, listing):
        return self.marketplace.create_listing(listing)

    def publish_listing(self, listing_id: str):
        return self.marketplace.publish_listing(listing_id)

    async def remember_snapshot(self) -> None:
        await self._platform.store_customer_context("marketplace:snapshot", self.metrics())


marketplace_domain_engine = MarketplaceDomainEngine()
