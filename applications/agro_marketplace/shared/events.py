# Agro Marketplace events — Sprint 8.1.

from __future__ import annotations

from dataclasses import dataclass

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class FarmerRegisteredEvent(BaseEvent):
    farmer_id: str = ""
    email: str = ""
    name: str = ""


@dataclass(kw_only=True)
class ProductCreatedEvent(BaseEvent):
    product_id: str = ""
    farmer_id: str = ""
    name: str = ""


@dataclass(kw_only=True)
class HarvestAddedEvent(BaseEvent):
    harvest_id: str = ""
    farm_id: str = ""
    crop_id: str = ""
    quantity_tons: float = 0.0


@dataclass(kw_only=True)
class OrderCreatedEvent(BaseEvent):
    order_id: str = ""
    buyer_id: str = ""
    product_id: str = ""
    quantity: float = 0.0


@dataclass(kw_only=True)
class ShipmentCreatedEvent(BaseEvent):
    shipment_id: str = ""
    order_id: str = ""
    destination_country: str = ""


@dataclass(kw_only=True)
class ContractSignedEvent(BaseEvent):
    contract_id: str = ""
    order_id: str = ""


@dataclass(kw_only=True)
class ExportStartedEvent(BaseEvent):
    shipment_id: str = ""
    order_id: str = ""
    exporter_id: str = ""


@dataclass(kw_only=True)
class DeliveryCompletedEvent(BaseEvent):
    delivery_id: str = ""
    order_id: str = ""
