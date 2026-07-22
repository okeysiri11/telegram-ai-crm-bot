# Marketplace Engine — channel overview and listing orchestration.

from __future__ import annotations

from applications.auto_marketplace.auctions.engine import AuctionsEngine, auctions_engine
from applications.auto_marketplace.listings.engine import ListingsEngine, listings_engine
from applications.auto_marketplace.marketplace.models import MarketplaceChannel, MarketplaceListing


class MarketplaceEngine:
    """Top-level vehicle marketplace surface."""

    def __init__(
        self,
        listings: ListingsEngine | None = None,
        auctions: AuctionsEngine | None = None,
    ) -> None:
        self.listings = listings or listings_engine
        self.auctions = auctions or auctions_engine

    def channels(self) -> list[str]:
        return self.listings.channels()

    def create_listing(self, listing: MarketplaceListing) -> MarketplaceListing:
        return self.listings.create(listing)

    def publish_listing(self, listing_id: str) -> MarketplaceListing:
        return self.listings.publish(listing_id)

    def browse(self, *, channel: str = "", region: str = "") -> list[MarketplaceListing]:
        return self.listings.list_listings(channel=channel or None, status="active", region=region)

    def overview(self) -> dict:
        by_channel = {c.value: 0 for c in MarketplaceChannel}
        for listing in self.listings.list_listings():
            by_channel[listing.channel.value] = by_channel.get(listing.channel.value, 0) + 1
        return {
            "channels": self.channels(),
            "by_channel": by_channel,
            "active": len(self.listings.list_listings(status="active")),
            "auctions_active": self.auctions.metrics()["active"],
        }

    def metrics(self) -> dict:
        return {**self.listings.metrics(), **self.auctions.metrics(), "channels": len(self.channels())}


marketplace_engine = MarketplaceEngine()
