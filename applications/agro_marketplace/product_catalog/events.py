# Sprint 8.2 domain events.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class HarvestRegisteredEvent(BaseEvent):
    harvest_id: str = ""
    farm_id: str = ""
    crop_id: str = ""
    quantity: float = 0.0
    quality_grade: str = ""


@dataclass(kw_only=True)
class CatalogProductCreatedEvent(BaseEvent):
    product_id: str = ""
    name: str = ""
    sku: str = ""
    farmer_id: str = ""


@dataclass(kw_only=True)
class InventoryUpdatedEvent(BaseEvent):
    item_id: str = ""
    product_id: str = ""
    warehouse_id: str = ""
    quantity: float = 0.0
    change_type: str = ""


@dataclass(kw_only=True)
class WarehouseCreatedEvent(BaseEvent):
    warehouse_id: str = ""
    name: str = ""
    region: str = ""


@dataclass(kw_only=True)
class QualityVerifiedEvent(BaseEvent):
    certificate_id: str = ""
    harvest_id: str = ""
    grade: str = ""


@dataclass(kw_only=True)
class BatchStoredEvent(BaseEvent):
    batch_id: str = ""
    lot_id: str = ""
    warehouse_id: str = ""
    quantity: float = 0.0


@dataclass(kw_only=True)
class ShipmentPreparedEvent(BaseEvent):
    movement_id: str = ""
    warehouse_id: str = ""
    product_id: str = ""
    quantity: float = 0.0
    reference: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
