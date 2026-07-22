# Transport Order Engine — create → assign → dispatch → track → complete → archive.

from __future__ import annotations

import time

from events.publisher import publish

from applications.port_erp.multimodal.events import (
    CarrierAssignedEvent,
    TransportCompletedEvent,
    TransportDelayedEvent,
    TransportStartedEvent,
)
from applications.port_erp.multimodal.models import TransportOrder, TransportOrderStatus, TransportMode
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.store import PortStore, port_store


class TransportOrderEngine:
    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    def create(self, order: TransportOrder) -> TransportOrder:
        if not order.origin or not order.destination:
            raise ValidationError("origin and destination are required")
        order.status = TransportOrderStatus.CREATED
        return self._store.transport_orders.save(order.order_id, order)

    def get(self, order_id: str) -> TransportOrder:
        item = self._store.transport_orders.get(order_id)
        if item is None:
            raise NotFoundError("TransportOrder", order_id)
        return item

    def list_orders(self, *, status: TransportOrderStatus | None = None) -> list[TransportOrder]:
        items = self._store.transport_orders.list_all()
        if status:
            items = [o for o in items if o.status == status]
        return items

    async def assign(self, order_id: str, *, carrier_id: str, fleet_asset_id: str = "") -> TransportOrder:
        if not carrier_id:
            raise ValidationError("carrier_id is required")
        order = self.get(order_id)
        order.carrier_id = carrier_id
        order.fleet_asset_id = fleet_asset_id
        order.status = TransportOrderStatus.ASSIGNED
        saved = self._store.transport_orders.save(order_id, order)
        await publish(
            CarrierAssignedEvent(
                order_id=order_id,
                carrier_id=carrier_id,
                mode=saved.mode.value,
            )
        )
        return saved

    async def dispatch(self, order_id: str) -> TransportOrder:
        order = self.get(order_id)
        if order.status not in (TransportOrderStatus.ASSIGNED, TransportOrderStatus.CREATED):
            raise ValidationError("order must be assigned before dispatch")
        order.status = TransportOrderStatus.DISPATCHED
        order.dispatched_at = time.time()
        saved = self._store.transport_orders.save(order_id, order)
        await publish(
            TransportStartedEvent(
                order_id=order_id,
                booking_id=saved.booking_id,
                mode=saved.mode.value,
            )
        )
        return saved

    def track(self, order_id: str, *, eta: float | None = None) -> TransportOrder:
        order = self.get(order_id)
        order.status = TransportOrderStatus.TRACKING
        if eta is not None:
            order.eta = eta
        return self._store.transport_orders.save(order_id, order)

    async def delay(self, order_id: str, *, delay_minutes: float, reason: str = "") -> TransportOrder:
        order = self.get(order_id)
        order.delay_minutes = delay_minutes
        order.eta = (order.eta or time.time()) + delay_minutes * 60
        saved = self._store.transport_orders.save(order_id, order)
        await publish(
            TransportDelayedEvent(
                order_id=order_id,
                delay_minutes=delay_minutes,
                reason=reason or "delay",
            )
        )
        return saved

    async def complete(self, order_id: str) -> TransportOrder:
        order = self.get(order_id)
        order.status = TransportOrderStatus.COMPLETED
        order.completed_at = time.time()
        saved = self._store.transport_orders.save(order_id, order)
        await publish(
            TransportCompletedEvent(order_id=order_id, booking_id=saved.booking_id)
        )
        return saved

    def archive(self, order_id: str) -> TransportOrder:
        order = self.get(order_id)
        if order.status != TransportOrderStatus.COMPLETED:
            raise ValidationError("only completed orders can be archived")
        order.status = TransportOrderStatus.ARCHIVED
        order.archived_at = time.time()
        return self._store.transport_orders.save(order_id, order)


transport_order_engine = TransportOrderEngine()
