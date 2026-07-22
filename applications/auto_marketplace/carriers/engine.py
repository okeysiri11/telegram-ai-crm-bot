# Carrier Network — companies, private, tow, rail, sea, air, drivers, ratings.

from __future__ import annotations

from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store
from applications.auto_marketplace.transport.models import Carrier, CarrierKind


class CarrierNetworkEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def register(self, carrier: Carrier) -> Carrier:
        if not carrier.name:
            raise ValidationError("name is required")
        return self._store.logistics_carriers.save(carrier.carrier_id, carrier)

    def get(self, carrier_id: str) -> Carrier:
        item = self._store.logistics_carriers.get(carrier_id)
        if item is None:
            raise NotFoundError("Carrier", carrier_id)
        return item

    def list_carriers(self, *, kind: str = "", mode: str = "") -> list[Carrier]:
        items = self._store.logistics_carriers.list_all()
        if kind:
            items = [c for c in items if c.kind.value == kind]
        if mode:
            items = [c for c in items if mode in c.modes]
        return items

    def add_driver(self, carrier_id: str, *, name: str, license_id: str = "") -> Carrier:
        carrier = self.get(carrier_id)
        carrier.drivers.append({"name": name, "license_id": license_id, "active": True})
        return self._store.logistics_carriers.save(carrier_id, carrier)

    def rate(self, carrier_id: str, score: float) -> Carrier:
        if not 0 <= score <= 5:
            raise ValidationError("rating must be between 0 and 5")
        carrier = self.get(carrier_id)
        if carrier.rating <= 0:
            carrier.rating = score
        else:
            carrier.rating = round((carrier.rating + score) / 2, 2)
        return self._store.logistics_carriers.save(carrier_id, carrier)

    def recommend(self, *, mode: str = "truck", country: str = "") -> list[Carrier]:
        items = self.list_carriers(mode=mode)
        if country:
            items = [c for c in items if not c.countries or country in c.countries]
        return sorted(items, key=lambda c: -c.rating)

    def metrics(self) -> dict:
        return {
            "carriers": self._store.logistics_carriers.count(),
            "kinds": [k.value for k in CarrierKind],
        }


carrier_network_engine = CarrierNetworkEngine()
