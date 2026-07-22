from __future__ import annotations

import uuid
from typing import Any

from applications.drone_platform.models.inventory import (
    PurchaseOrder,
    Reservation,
    StockItem,
    Supplier,
    Warehouse,
)
from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


class InventoryService:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def create_warehouse(self, *, name: str, location: str = "", warehouse_id: str | None = None) -> Warehouse:
        wid = warehouse_id or f"wh_{uuid.uuid4().hex[:12]}"
        warehouse = Warehouse(warehouse_id=wid, name=name, location=location)
        self.store.warehouses.save(wid, warehouse)
        return warehouse

    def list_warehouses(self) -> list[Warehouse]:
        return self.store.warehouses.list_all()

    def create_supplier(self, *, name: str, contact: str = "", supplier_id: str | None = None) -> Supplier:
        sid = supplier_id or f"sup_{uuid.uuid4().hex[:12]}"
        supplier = Supplier(supplier_id=sid, name=name, contact=contact)
        self.store.suppliers.save(sid, supplier)
        return supplier

    def list_suppliers(self) -> list[Supplier]:
        return self.store.suppliers.list_all()

    def add_stock(
        self,
        *,
        warehouse_id: str,
        component_type: str,
        sku: str,
        quantity: int,
        serial_numbers: list[str] | None = None,
        batch_id: str = "",
        lifecycle_stage: str = "in_stock",
        stock_id: str | None = None,
    ) -> StockItem:
        if self.store.warehouses.get(warehouse_id) is None:
            raise NotFoundError("warehouse", warehouse_id)
        sid = stock_id or f"stk_{uuid.uuid4().hex[:12]}"
        item = StockItem(
            stock_id=sid,
            warehouse_id=warehouse_id,
            component_type=component_type,
            sku=sku,
            quantity=quantity,
            serial_numbers=list(serial_numbers or []),
            batch_id=batch_id,
            lifecycle_stage=lifecycle_stage,
        )
        self.store.stock_items.save(sid, item)
        return item

    def get_stock(self, stock_id: str) -> StockItem:
        item = self.store.stock_items.get(stock_id)
        if item is None:
            raise NotFoundError("stock", stock_id)
        return item

    def list_stock(self, warehouse_id: str | None = None) -> list[StockItem]:
        items = self.store.stock_items.list_all()
        if warehouse_id:
            return [s for s in items if s.warehouse_id == warehouse_id]
        return items

    def create_purchase_order(
        self,
        *,
        supplier_id: str,
        warehouse_id: str,
        lines: list[dict[str, Any]],
        purchase_order_id: str | None = None,
    ) -> PurchaseOrder:
        if self.store.suppliers.get(supplier_id) is None:
            raise NotFoundError("supplier", supplier_id)
        if self.store.warehouses.get(warehouse_id) is None:
            raise NotFoundError("warehouse", warehouse_id)
        pid = purchase_order_id or f"po_{uuid.uuid4().hex[:12]}"
        order = PurchaseOrder(
            purchase_order_id=pid,
            supplier_id=supplier_id,
            warehouse_id=warehouse_id,
            lines=list(lines),
            status="ordered",
        )
        self.store.purchase_orders.save(pid, order)
        return order

    def list_purchase_orders(self) -> list[PurchaseOrder]:
        return self.store.purchase_orders.list_all()

    def reserve_stock(
        self,
        *,
        stock_id: str,
        quantity: int,
        project_id: str = "",
        reservation_id: str | None = None,
    ) -> Reservation:
        stock = self.get_stock(stock_id)
        available = stock.quantity - stock.reserved
        if quantity <= 0 or quantity > available:
            raise ValidationError("Insufficient available stock for reservation")
        rid = reservation_id or f"rsv_{uuid.uuid4().hex[:12]}"
        reservation = Reservation(
            reservation_id=rid,
            stock_id=stock_id,
            quantity=quantity,
            project_id=project_id,
        )
        stock.reserved += quantity
        self.store.stock_items.save(stock_id, stock)
        self.store.reservations.save(rid, reservation)
        return reservation

    def update_lifecycle(self, stock_id: str, lifecycle_stage: str) -> StockItem:
        stock = self.get_stock(stock_id)
        stock.lifecycle_stage = lifecycle_stage
        self.store.stock_items.save(stock_id, stock)
        return stock

    def list_reservations(self) -> list[Reservation]:
        return self.store.reservations.list_all()


inventory_service = InventoryService()
