# Vehicle catalog lifecycle events.

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class VehicleAddedEvent(BaseEvent):
    vehicle_id: str = ""
    vin: str = ""
    dealer_id: str = ""


@dataclass(kw_only=True)
class VehicleUpdatedEvent(BaseEvent):
    vehicle_id: str = ""
    fields: dict[str, Any] | None = None


@dataclass(kw_only=True)
class VehicleReservedEvent(BaseEvent):
    vehicle_id: str = ""
    reservation_id: str = ""
    customer_id: str = ""


@dataclass(kw_only=True)
class VehicleSoldEvent(BaseEvent):
    vehicle_id: str = ""
    deal_id: str = ""
    final_price: float = 0.0


@dataclass(kw_only=True)
class InventoryChangedEvent(BaseEvent):
    warehouse_id: str = ""
    dealer_id: str = ""
    change_type: str = ""
    count_delta: int = 0


@dataclass(kw_only=True)
class MediaUploadedEvent(BaseEvent):
    media_id: str = ""
    vehicle_id: str = ""
    media_type: str = ""
