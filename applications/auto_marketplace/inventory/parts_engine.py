# Parts Inventory — warehouses, stock movements, POs, reservations, alerts.

from __future__ import annotations

import time
import uuid

from applications.auto_marketplace.service_centers.models import PartsWarehouse, PurchaseOrder, StockItem
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class PartsInventoryEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def create_warehouse(self, warehouse: PartsWarehouse) -> PartsWarehouse:
        if not warehouse.name:
            raise ValidationError("name is required")
        return self._store.parts_warehouses.save(warehouse.warehouse_id, warehouse)

    def upsert_stock(self, item: StockItem) -> StockItem:
        if item.quantity < 0:
            raise ValidationError("quantity cannot be negative")
        return self._store.parts_stock.save(item.stock_id, item)

    def move_stock(
        self,
        *,
        warehouse_id: str,
        part_id: str,
        delta: int,
        reason: str = "adjustment",
    ) -> StockItem:
        stock = next(
            (s for s in self._store.parts_stock.list_all() if s.warehouse_id == warehouse_id and s.part_id == part_id),
            None,
        )
        if stock is None:
            stock = StockItem(warehouse_id=warehouse_id, part_id=part_id, quantity=0)
        stock.quantity += delta
        if stock.quantity < 0:
            raise ValidationError("insufficient stock")
        self._store.stock_movements.save(
            str(uuid.uuid4()),
            {"warehouse_id": warehouse_id, "part_id": part_id, "delta": delta, "reason": reason, "at": time.time()},
        )
        return self._store.parts_stock.save(stock.stock_id, stock)

    def reserve(self, *, warehouse_id: str, part_id: str, quantity: int) -> dict:
        stock = next(
            (s for s in self._store.parts_stock.list_all() if s.warehouse_id == warehouse_id and s.part_id == part_id),
            None,
        )
        if stock is None or stock.quantity - stock.reserved < quantity:
            raise ValidationError("insufficient available stock")
        stock.reserved += quantity
        self._store.parts_stock.save(stock.stock_id, stock)
        reservation = {
            "reservation_id": str(uuid.uuid4()),
            "warehouse_id": warehouse_id,
            "part_id": part_id,
            "quantity": quantity,
            "status": "reserved",
            "at": time.time(),
        }
        self._store.parts_reservations.save(reservation["reservation_id"], reservation)
        return reservation

    def create_po(self, po: PurchaseOrder) -> PurchaseOrder:
        if not po.supplier_id or not po.lines:
            raise ValidationError("supplier_id and lines are required")
        po.status = "ordered"
        return self._store.parts_purchase_orders.save(po.po_id, po)

    def receive_po(self, po_id: str) -> PurchaseOrder:
        po = self._store.parts_purchase_orders.get(po_id)
        if po is None:
            raise NotFoundError("PurchaseOrder", po_id)
        for line in po.lines:
            self.move_stock(
                warehouse_id=po.warehouse_id,
                part_id=line["part_id"],
                delta=int(line.get("quantity", 0)),
                reason=f"receive:{po_id}",
            )
        po.status = "received"
        return self._store.parts_purchase_orders.save(po_id, po)

    def return_stock(self, *, warehouse_id: str, part_id: str, quantity: int) -> StockItem:
        return self.move_stock(warehouse_id=warehouse_id, part_id=part_id, delta=-abs(quantity), reason="return")

    def low_stock_alerts(self) -> list[dict]:
        return [s.to_dict() for s in self._store.parts_stock.list_all() if s.quantity - s.reserved <= s.min_quantity]

    def metrics(self) -> dict:
        return {
            "warehouses": self._store.parts_warehouses.count(),
            "stock_items": self._store.parts_stock.count(),
            "movements": self._store.stock_movements.count(),
            "purchase_orders": self._store.parts_purchase_orders.count(),
            "low_stock": len(self.low_stock_alerts()),
        }


parts_inventory_engine = PartsInventoryEngine()
