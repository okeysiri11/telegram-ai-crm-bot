# Sprint 8.5 — Export, logistics and international trade domain models.

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


def _id() -> str:
    return str(uuid.uuid4())


def _ts() -> float:
    return time.time()


class IncotermCode(str, enum.Enum):
    FOB = "FOB"
    CIF = "CIF"
    CFR = "CFR"
    DAP = "DAP"
    EXW = "EXW"
    DDP = "DDP"


class InternationalShipmentStatus(str, enum.Enum):
    DRAFT = "draft"
    PLANNED = "planned"
    LOADED = "loaded"
    DISPATCHED = "dispatched"
    IN_TRANSIT = "in_transit"
    PORT_ARRIVED = "port_arrived"
    CUSTOMS = "customs"
    CLEARED = "cleared"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    AT_RISK = "at_risk"


class CustomsStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    CLEARED = "cleared"
    REJECTED = "rejected"


class DocumentType(str, enum.Enum):
    BILL_OF_LADING = "bill_of_lading"
    PACKING_LIST = "packing_list"
    COMMERCIAL_INVOICE = "commercial_invoice"
    CERTIFICATE_OF_ORIGIN = "certificate_of_origin"
    PHYTOSANITARY = "phytosanitary_certificate"
    INSURANCE = "insurance_policy"
    CUSTOMS_DECLARATION = "customs_declaration"


@dataclass
class Incoterm:
    code: IncotermCode = IncotermCode.FOB
    name: str = ""
    description: str = ""
    seller_responsibility: str = ""
    buyer_responsibility: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code.value,
            "name": self.name or self.code.value,
            "description": self.description,
            "seller_responsibility": self.seller_responsibility,
            "buyer_responsibility": self.buyer_responsibility,
        }


@dataclass
class Port:
    port_id: str = field(default_factory=_id)
    name: str = ""
    code: str = ""
    country: str = ""
    city: str = ""
    port_type: str = "sea"
    is_active: bool = True
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "port_id": self.port_id,
            "name": self.name,
            "code": self.code,
            "country": self.country,
            "city": self.city,
            "port_type": self.port_type,
            "is_active": self.is_active,
            "created_at": self.created_at,
        }


@dataclass
class Terminal:
    terminal_id: str = field(default_factory=_id)
    port_id: str = ""
    name: str = ""
    terminal_type: str = "container"
    capacity_teu: int = 0
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "terminal_id": self.terminal_id,
            "port_id": self.port_id,
            "name": self.name,
            "terminal_type": self.terminal_type,
            "capacity_teu": self.capacity_teu,
            "created_at": self.created_at,
        }


@dataclass
class Carrier:
    carrier_id: str = field(default_factory=_id)
    name: str = ""
    mode: str = "sea"
    countries: list[str] = field(default_factory=list)
    rating: float = 0.0
    contact_email: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "carrier_id": self.carrier_id,
            "name": self.name,
            "mode": self.mode,
            "countries": list(self.countries),
            "rating": self.rating,
            "contact_email": self.contact_email,
            "created_at": self.created_at,
        }


@dataclass
class Container:
    container_id: str = field(default_factory=_id)
    container_number: str = ""
    container_type: str = "40HC"
    capacity_cbm: float = 67.0
    max_weight_tons: float = 26.0
    used_cbm: float = 0.0
    used_weight_tons: float = 0.0
    status: str = "available"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "container_id": self.container_id,
            "container_number": self.container_number,
            "container_type": self.container_type,
            "capacity_cbm": self.capacity_cbm,
            "max_weight_tons": self.max_weight_tons,
            "used_cbm": self.used_cbm,
            "used_weight_tons": self.used_weight_tons,
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class ContainerLoad:
    load_id: str = field(default_factory=_id)
    container_id: str = ""
    shipment_id: str = ""
    product_id: str = ""
    quantity_tons: float = 0.0
    volume_cbm: float = 0.0
    sealed: bool = False
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "load_id": self.load_id,
            "container_id": self.container_id,
            "shipment_id": self.shipment_id,
            "product_id": self.product_id,
            "quantity_tons": self.quantity_tons,
            "volume_cbm": self.volume_cbm,
            "sealed": self.sealed,
            "created_at": self.created_at,
        }


@dataclass
class ShipmentItem:
    item_id: str = field(default_factory=_id)
    shipment_id: str = ""
    product_id: str = ""
    description: str = ""
    quantity: float = 0.0
    unit: str = "ton"
    unit_value: float = 0.0
    currency: str = "USD"
    hs_code: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "shipment_id": self.shipment_id,
            "product_id": self.product_id,
            "description": self.description,
            "quantity": self.quantity,
            "unit": self.unit,
            "unit_value": self.unit_value,
            "currency": self.currency,
            "hs_code": self.hs_code,
            "total_value": self.quantity * self.unit_value,
        }


@dataclass
class RoutePlan:
    route_id: str = field(default_factory=_id)
    origin_port_id: str = ""
    destination_port_id: str = ""
    via_ports: list[str] = field(default_factory=list)
    estimated_days: int = 0
    distance_nm: float = 0.0
    mode: str = "sea"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "route_id": self.route_id,
            "origin_port_id": self.origin_port_id,
            "destination_port_id": self.destination_port_id,
            "via_ports": list(self.via_ports),
            "estimated_days": self.estimated_days,
            "distance_nm": self.distance_nm,
            "mode": self.mode,
            "created_at": self.created_at,
        }


@dataclass
class FreightOrder:
    freight_id: str = field(default_factory=_id)
    shipment_id: str = ""
    carrier_id: str = ""
    route_id: str = ""
    cost: float = 0.0
    currency: str = "USD"
    status: str = "booked"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "freight_id": self.freight_id,
            "shipment_id": self.shipment_id,
            "carrier_id": self.carrier_id,
            "route_id": self.route_id,
            "cost": self.cost,
            "currency": self.currency,
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class InternationalExportShipment:
    shipment_id: str = field(default_factory=_id)
    order_id: str = ""
    contract_id: str = ""
    exporter_id: str = ""
    buyer_id: str = ""
    origin_country: str = ""
    destination_country: str = ""
    origin_port_id: str = ""
    destination_port_id: str = ""
    carrier_id: str = ""
    route_id: str = ""
    warehouse_id: str = ""
    incoterm: IncotermCode = IncotermCode.FOB
    status: InternationalShipmentStatus = InternationalShipmentStatus.DRAFT
    items: list[str] = field(default_factory=list)
    container_ids: list[str] = field(default_factory=list)
    document_ids: list[str] = field(default_factory=list)
    estimated_departure: float = 0.0
    estimated_arrival: float = 0.0
    actual_departure: float = 0.0
    actual_arrival: float = 0.0
    risk_score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)
    updated_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "shipment_id": self.shipment_id,
            "order_id": self.order_id,
            "contract_id": self.contract_id,
            "exporter_id": self.exporter_id,
            "buyer_id": self.buyer_id,
            "origin_country": self.origin_country,
            "destination_country": self.destination_country,
            "origin_port_id": self.origin_port_id,
            "destination_port_id": self.destination_port_id,
            "carrier_id": self.carrier_id,
            "route_id": self.route_id,
            "warehouse_id": self.warehouse_id,
            "incoterm": self.incoterm.value,
            "status": self.status.value,
            "items": list(self.items),
            "container_ids": list(self.container_ids),
            "document_ids": list(self.document_ids),
            "estimated_departure": self.estimated_departure,
            "estimated_arrival": self.estimated_arrival,
            "actual_departure": self.actual_departure,
            "actual_arrival": self.actual_arrival,
            "risk_score": self.risk_score,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class CustomsDeclaration:
    declaration_id: str = field(default_factory=_id)
    shipment_id: str = ""
    declaration_number: str = ""
    country: str = ""
    status: CustomsStatus = CustomsStatus.DRAFT
    hs_codes: list[str] = field(default_factory=list)
    declared_value: float = 0.0
    currency: str = "USD"
    submitted_at: float = 0.0
    cleared_at: float = 0.0
    notes: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "declaration_id": self.declaration_id,
            "shipment_id": self.shipment_id,
            "declaration_number": self.declaration_number,
            "country": self.country,
            "status": self.status.value,
            "hs_codes": list(self.hs_codes),
            "declared_value": self.declared_value,
            "currency": self.currency,
            "submitted_at": self.submitted_at,
            "cleared_at": self.cleared_at,
            "notes": self.notes,
            "created_at": self.created_at,
        }


@dataclass
class TradeDocument:
    document_id: str = field(default_factory=_id)
    shipment_id: str = ""
    document_type: DocumentType = DocumentType.COMMERCIAL_INVOICE
    title: str = ""
    reference: str = ""
    verified: bool = False
    issuer: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "shipment_id": self.shipment_id,
            "document_type": self.document_type.value,
            "title": self.title,
            "reference": self.reference,
            "verified": self.verified,
            "issuer": self.issuer,
            "payload": dict(self.payload),
            "created_at": self.created_at,
        }


# Typed aliases matching requirement names
BillOfLading = TradeDocument
PackingList = TradeDocument
CommercialInvoice = TradeDocument
CertificateOfOrigin = TradeDocument
PhytosanitaryCertificate = TradeDocument


@dataclass
class InsurancePolicy:
    policy_id: str = field(default_factory=_id)
    shipment_id: str = ""
    insurer: str = ""
    coverage_amount: float = 0.0
    currency: str = "USD"
    premium: float = 0.0
    status: str = "active"
    valid_from: float = field(default_factory=_ts)
    valid_to: float = 0.0
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "shipment_id": self.shipment_id,
            "insurer": self.insurer,
            "coverage_amount": self.coverage_amount,
            "currency": self.currency,
            "premium": self.premium,
            "status": self.status,
            "valid_from": self.valid_from,
            "valid_to": self.valid_to,
            "created_at": self.created_at,
        }


@dataclass
class TrackingEvent:
    event_id: str = field(default_factory=_id)
    shipment_id: str = ""
    event_type: str = ""
    location: str = ""
    status: str = ""
    notes: str = ""
    occurred_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "shipment_id": self.shipment_id,
            "event_type": self.event_type,
            "location": self.location,
            "status": self.status,
            "notes": self.notes,
            "occurred_at": self.occurred_at,
        }


@dataclass
class CountryRequirement:
    requirement_id: str = field(default_factory=_id)
    country: str = ""
    required_documents: list[str] = field(default_factory=list)
    notes: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "requirement_id": self.requirement_id,
            "country": self.country,
            "required_documents": list(self.required_documents),
            "notes": self.notes,
            "created_at": self.created_at,
        }


# Alias for requirement naming
ExportShipment = InternationalExportShipment
