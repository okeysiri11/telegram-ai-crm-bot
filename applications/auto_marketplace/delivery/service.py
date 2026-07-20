# DeliveryService — vehicle delivery scheduling and tracking.

from __future__ import annotations

import time

from applications.auto_marketplace.shared.exceptions import NotFoundError
from applications.auto_marketplace.shared.models import Delivery, DeliveryStatus
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class DeliveryService:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def schedule_delivery(self, delivery: Delivery) -> Delivery:
        delivery.status = DeliveryStatus.SCHEDULED
        return self._store.deliveries.save(delivery.delivery_id, delivery)

    def get_delivery(self, delivery_id: str) -> Delivery:
        delivery = self._store.deliveries.get(delivery_id)
        if delivery is None:
            raise NotFoundError("Delivery", delivery_id)
        return delivery

    def mark_in_transit(self, delivery_id: str) -> Delivery:
        delivery = self.get_delivery(delivery_id)
        delivery.status = DeliveryStatus.IN_TRANSIT
        return self._store.deliveries.save(delivery_id, delivery)

    def mark_delivered(self, delivery_id: str) -> Delivery:
        delivery = self.get_delivery(delivery_id)
        delivery.status = DeliveryStatus.DELIVERED
        delivery.delivered_at = time.time()
        return self._store.deliveries.save(delivery_id, delivery)


delivery_service = DeliveryService()
