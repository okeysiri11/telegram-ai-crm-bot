# Global Vehicle Network — cross-country inventory, search, federation.

from __future__ import annotations

from applications.auto_marketplace.enterprise.models import NetworkListing
from applications.auto_marketplace.shared.exceptions import ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class GlobalVehicleNetworkEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def publish(self, listing: NetworkListing) -> NetworkListing:
        if not listing.vehicle_id and not listing.vin:
            raise ValidationError("vehicle_id or vin is required")
        if not listing.country:
            raise ValidationError("country is required")
        return self._store.network_listings.save(listing.listing_id, listing)

    def search(
        self,
        *,
        country: str = "",
        region: str = "",
        max_price: float | None = None,
        federated_only: bool = False,
    ) -> list[NetworkListing]:
        items = self._store.network_listings.list_all()
        if country:
            items = [i for i in items if i.country.upper() == country.upper()]
        if region:
            items = [i for i in items if i.region.lower() == region.lower()]
        if max_price is not None:
            items = [i for i in items if i.price <= max_price]
        if federated_only:
            items = [i for i in items if i.federated]
        return items

    def federate_dealer(self, dealer_id: str, listings: list[NetworkListing]) -> list[NetworkListing]:
        out = []
        for listing in listings:
            listing.dealer_id = dealer_id
            listing.federated = True
            out.append(self.publish(listing))
        return out

    def catalog_by_region(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in self._store.network_listings.list_all():
            key = f"{item.country}/{item.region or 'default'}"
            counts[key] = counts.get(key, 0) + 1
        return counts

    def metrics(self) -> dict:
        items = self._store.network_listings.list_all()
        return {
            "listings": len(items),
            "federated": len([i for i in items if i.federated]),
            "countries": sorted({i.country for i in items if i.country}),
            "regions": self.catalog_by_region(),
        }


global_vehicle_network_engine = GlobalVehicleNetworkEngine()
