# Vehicle Shipping — thin alias helpers around shipments.

from __future__ import annotations

from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class VehicleShippingEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def active(self) -> list:
        return [
            s
            for s in self._store.vehicle_shipments.list_all()
            if s.status.value in {"booked", "dispatched", "in_transit", "out_for_delivery"}
        ]

    def metrics(self) -> dict:
        return {"active_shipments": len(self.active())}


vehicle_shipping_engine = VehicleShippingEngine()
