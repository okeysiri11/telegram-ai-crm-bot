# Repair Orders — acceptance through delivery.

from __future__ import annotations

import time

from applications.auto_marketplace.service_centers.models import RepairOrder, RepairOrderStatus
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class RepairOrderEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def accept(self, order: RepairOrder) -> RepairOrder:
        if not order.vehicle_id or not order.center_id:
            raise ValidationError("vehicle_id and center_id are required")
        order.status = RepairOrderStatus.ACCEPTED
        order.updated_at = time.time()
        return self._store.repair_orders.save(order.order_id, order)

    def get(self, order_id: str) -> RepairOrder:
        order = self._store.repair_orders.get(order_id)
        if order is None:
            raise NotFoundError("RepairOrder", order_id)
        return order

    def inspect(self, order_id: str, checklist: list[dict]) -> RepairOrder:
        order = self.get(order_id)
        order.checklist = checklist
        order.status = RepairOrderStatus.INSPECTING
        order.updated_at = time.time()
        return self._store.repair_orders.save(order_id, order)

    def estimate(self, order_id: str, amount: float) -> RepairOrder:
        order = self.get(order_id)
        if amount <= 0:
            raise ValidationError("estimate amount must be positive")
        order.estimate_amount = amount
        order.status = RepairOrderStatus.ESTIMATED
        order.updated_at = time.time()
        return self._store.repair_orders.save(order_id, order)

    def approve(self, order_id: str) -> RepairOrder:
        order = self.get(order_id)
        order.approved = True
        order.status = RepairOrderStatus.APPROVED
        order.updated_at = time.time()
        return self._store.repair_orders.save(order_id, order)

    def start(self, order_id: str, *, mechanic_id: str = "", bay_id: str = "") -> RepairOrder:
        order = self.get(order_id)
        if not order.approved:
            raise ValidationError("customer approval required")
        order.mechanic_id = mechanic_id or order.mechanic_id
        order.bay_id = bay_id or order.bay_id
        order.status = RepairOrderStatus.IN_PROGRESS
        order.updated_at = time.time()
        if order.bay_id:
            bay = self._store.repair_bays.get(order.bay_id)
            if bay:
                bay.occupied = True
                self._store.repair_bays.save(bay.bay_id, bay)
        return self._store.repair_orders.save(order_id, order)

    def progress(self, order_id: str, note: str) -> RepairOrder:
        order = self.get(order_id)
        order.progress_notes.append(note)
        order.updated_at = time.time()
        return self._store.repair_orders.save(order_id, order)

    def complete(self, order_id: str) -> RepairOrder:
        order = self.get(order_id)
        order.status = RepairOrderStatus.COMPLETED
        order.updated_at = time.time()
        if order.bay_id:
            bay = self._store.repair_bays.get(order.bay_id)
            if bay:
                bay.occupied = False
                self._store.repair_bays.save(bay.bay_id, bay)
        return self._store.repair_orders.save(order_id, order)

    def deliver(self, order_id: str) -> RepairOrder:
        order = self.get(order_id)
        order.status = RepairOrderStatus.DELIVERED
        order.updated_at = time.time()
        return self._store.repair_orders.save(order_id, order)

    def list_orders(self, *, center_id: str = "", status: str = "") -> list[RepairOrder]:
        items = self._store.repair_orders.list_all()
        if center_id:
            items = [o for o in items if o.center_id == center_id]
        if status:
            items = [o for o in items if o.status.value == status]
        return items

    def metrics(self) -> dict:
        items = self._store.repair_orders.list_all()
        return {
            "repair_orders": len(items),
            "in_progress": len([o for o in items if o.status == RepairOrderStatus.IN_PROGRESS]),
            "delivered": len([o for o in items if o.status == RepairOrderStatus.DELIVERED]),
        }


repair_order_engine = RepairOrderEngine()
