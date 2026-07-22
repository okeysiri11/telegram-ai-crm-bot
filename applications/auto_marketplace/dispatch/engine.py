# Dispatch — assign carrier/driver and release shipments.

from __future__ import annotations

import time

from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store
from applications.auto_marketplace.transport.models import ShipmentStatus


class DispatchEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def dispatch(self, shipment_id: str, *, carrier_id: str, driver_id: str = "") -> dict:
        shipment = self._store.vehicle_shipments.get(shipment_id)
        if shipment is None:
            raise NotFoundError("VehicleShipment", shipment_id)
        if not carrier_id:
            raise ValidationError("carrier_id is required")
        shipment.carrier_id = carrier_id
        shipment.driver_id = driver_id
        shipment.status = ShipmentStatus.DISPATCHED
        shipment.updated_at = time.time()
        shipment.timeline.append({"event": "dispatched", "carrier_id": carrier_id, "at": time.time()})
        self._store.vehicle_shipments.save(shipment_id, shipment)
        job = {"shipment_id": shipment_id, "carrier_id": carrier_id, "driver_id": driver_id, "at": time.time()}
        self._store.dispatch_jobs.save(shipment_id, job)
        return job

    def metrics(self) -> dict:
        return {"dispatch_jobs": self._store.dispatch_jobs.count()}


dispatch_engine = DispatchEngine()
