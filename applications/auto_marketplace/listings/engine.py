# Listings Engine — create/publish marketplace vehicle listings.

from __future__ import annotations

import time

from applications.auto_marketplace.marketplace.models import ListingStatus, MarketplaceChannel, MarketplaceListing
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class ListingsEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def create(self, listing: MarketplaceListing) -> MarketplaceListing:
        if not listing.title:
            raise ValidationError("listing title is required")
        if listing.price < 0:
            raise ValidationError("price must be non-negative")
        listing.updated_at = time.time()
        return self._store.marketplace_listings.save(listing.listing_id, listing)

    def get(self, listing_id: str) -> MarketplaceListing:
        listing = self._store.marketplace_listings.get(listing_id)
        if listing is None:
            raise NotFoundError("MarketplaceListing", listing_id)
        return listing

    def list_listings(
        self,
        *,
        channel: str | None = None,
        status: str | None = None,
        dealer_id: str = "",
        region: str = "",
    ) -> list[MarketplaceListing]:
        items = self._store.marketplace_listings.list_all()
        if channel:
            items = [i for i in items if i.channel.value == channel]
        if status:
            items = [i for i in items if i.status.value == status]
        if dealer_id:
            items = [i for i in items if i.dealer_id == dealer_id]
        if region:
            items = [i for i in items if i.region.lower() == region.lower()]
        return items

    def publish(self, listing_id: str) -> MarketplaceListing:
        listing = self.get(listing_id)
        listing.status = ListingStatus.ACTIVE
        listing.updated_at = time.time()
        return self._store.marketplace_listings.save(listing_id, listing)

    def mark_sold(self, listing_id: str) -> MarketplaceListing:
        listing = self.get(listing_id)
        listing.status = ListingStatus.SOLD
        listing.updated_at = time.time()
        return self._store.marketplace_listings.save(listing_id, listing)

    def channels(self) -> list[str]:
        return [c.value for c in MarketplaceChannel]

    def metrics(self) -> dict:
        return {"listings": self._store.marketplace_listings.count()}


listings_engine = ListingsEngine()
