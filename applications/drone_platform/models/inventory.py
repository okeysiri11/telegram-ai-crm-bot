from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Warehouse:
    warehouse_id: str
    name: str
    location: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "warehouse_id": self.warehouse_id,
            "name": self.name,
            "location": self.location,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


@dataclass
class Supplier:
    supplier_id: str
    name: str
    contact: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "supplier_id": self.supplier_id,
            "name": self.name,
            "contact": self.contact,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


@dataclass
class StockItem:
    stock_id: str
    warehouse_id: str
    component_type: str
    sku: str
    quantity: int = 0
    reserved: int = 0
    serial_numbers: list[str] = field(default_factory=list)
    batch_id: str = ""
    lifecycle_stage: str = "in_stock"
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "stock_id": self.stock_id,
            "warehouse_id": self.warehouse_id,
            "component_type": self.component_type,
            "sku": self.sku,
            "quantity": self.quantity,
            "reserved": self.reserved,
            "available": self.quantity - self.reserved,
            "serial_numbers": list(self.serial_numbers),
            "batch_id": self.batch_id,
            "lifecycle_stage": self.lifecycle_stage,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


@dataclass
class PurchaseOrder:
    purchase_order_id: str
    supplier_id: str
    warehouse_id: str
    lines: list[dict[str, Any]] = field(default_factory=list)
    status: str = "draft"
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "purchase_order_id": self.purchase_order_id,
            "supplier_id": self.supplier_id,
            "warehouse_id": self.warehouse_id,
            "lines": list(self.lines),
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class Reservation:
    reservation_id: str
    stock_id: str
    quantity: int
    project_id: str = ""
    status: str = "active"
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "reservation_id": self.reservation_id,
            "stock_id": self.stock_id,
            "quantity": self.quantity,
            "project_id": self.project_id,
            "status": self.status,
            "created_at": self.created_at,
        }
