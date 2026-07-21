# LogisticsService — deliveries and local shipments.

from __future__ import annotations

import time

from events.publisher import publish

from applications.agro_marketplace.shared.events import DeliveryCompletedEvent, ShipmentCreatedEvent
from applications.agro_marketplace.shared.exceptions import NotFoundError
from applications.agro_marketplace.shared.models import Delivery, DeliveryStatus
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class LogisticsService:
    def __init__(self, store: AgroStore | None = None) -> None:
        self._store = store or agro_store

    def list_deliveries(self) -> list[Delivery]:
        return self._store.deliveries.list_all()

    def get_delivery(self, delivery_id: str) -> Delivery:
        delivery = self._store.deliveries.get(delivery_id)
        if delivery is None:
            raise NotFoundError("Delivery", delivery_id)
        return delivery

    async def create_delivery(self, delivery: Delivery) -> Delivery:
        if self._store.orders.get(delivery.order_id) is None:
            raise NotFoundError("Order", delivery.order_id)
        saved = self._store.deliveries.save(delivery.delivery_id, delivery)
        await publish(
            ShipmentCreatedEvent(
                shipment_id=saved.delivery_id,
                order_id=saved.order_id,
                destination_country=saved.destination,
            )
        )
        return saved

    async def complete_delivery(self, delivery_id: str) -> Delivery:
        delivery = self.get_delivery(delivery_id)
        delivery.status = DeliveryStatus.DELIVERED
        delivery.completed_at = time.time()
        saved = self._store.deliveries.save(delivery_id, delivery)
        await publish(DeliveryCompletedEvent(delivery_id=saved.delivery_id, order_id=saved.order_id))
        return saved


logistics_service = LogisticsService()
