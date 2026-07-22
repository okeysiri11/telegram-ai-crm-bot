# Global analytics for enterprise release.

from __future__ import annotations

from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class GlobalAnalyticsEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def summary(self) -> dict:
        return {
            "network_listings": self._store.network_listings.count(),
            "partners": self._store.network_partners.count(),
            "connectors": self._store.enterprise_connectors.count(),
            "exchange_offers": self._store.exchange_offers.count(),
            "fleet_vehicles": self._store.fleet_vehicles.count(),
            "vehicle_shipments": self._store.vehicle_shipments.count(),
            "vehicle_transactions": self._store.vehicle_transactions.count(),
        }

    def usage(self) -> dict:
        return {
            "api_domains": [
                "fleet", "rental", "transport", "service", "transactions", "marketplace", "enterprise", "network"
            ],
            "summary": self.summary(),
        }

    def metrics(self) -> dict:
        return self.summary()


global_analytics_engine = GlobalAnalyticsEngine()
