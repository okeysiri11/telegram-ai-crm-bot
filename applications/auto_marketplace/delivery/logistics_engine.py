# Logistics delivery bridge — door-to-door / terminal completion hooks.

from __future__ import annotations

import time

from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store
from applications.auto_marketplace.transport.models import ShipmentStatus


class LogisticsDeliveryEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def mark_out_for_delivery(self, shipment_id: str) -> dict:
        shipment = self._store.vehicle_shipments.get(shipment_id)
        if shipment is None:
            from applications.auto_marketplace.shared.exceptions import NotFoundError

            raise NotFoundError("VehicleShipment", shipment_id)
        shipment.status = ShipmentStatus.OUT_FOR_DELIVERY
        shipment.updated_at = time.time()
        shipment.timeline.append({"event": "out_for_delivery", "at": time.time()})
        self._store.vehicle_shipments.save(shipment_id, shipment)
        return shipment.to_dict()

    def complete(self, shipment_id: str) -> dict:
        shipment = self._store.vehicle_shipments.get(shipment_id)
        if shipment is None:
            from applications.auto_marketplace.shared.exceptions import NotFoundError

            raise NotFoundError("VehicleShipment", shipment_id)
        shipment.status = ShipmentStatus.DELIVERED
        shipment.updated_at = time.time()
        shipment.timeline.append({"event": "delivered", "at": time.time()})
        self._store.vehicle_shipments.save(shipment_id, shipment)
        return shipment.to_dict()

    def metrics(self) -> dict:
        items = self._store.vehicle_shipments.list_all()
        return {"delivered": len([s for s in items if s.status == ShipmentStatus.DELIVERED])}


logistics_delivery_engine = LogisticsDeliveryEngine()
