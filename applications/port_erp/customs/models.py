# Sprint 9.4 — Customs, documentation, trade, compliance models.

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


class DocumentType(str, enum.Enum):
    BILL_OF_LADING = "bill_of_lading"
    SEA_WAYBILL = "sea_waybill"
    CMR = "cmr"
    RAIL_WAYBILL = "rail_waybill"
    AIR_WAYBILL = "air_waybill"
    COMMERCIAL_INVOICE = "commercial_invoice"
    PACKING_LIST = "packing_list"
    CERTIFICATE_OF_ORIGIN = "certificate_of_origin"
    PHYTOSANITARY = "phytosanitary_certificate"
    VETERINARY = "veterinary_certificate"
    QUALITY = "quality_certificate"
    INSURANCE = "insurance_certificate"
    EXPORT_DECLARATION = "export_declaration"
    IMPORT_DECLARATION = "import_declaration"
    TRANSIT_DECLARATION = "transit_declaration"
    DANGEROUS_GOODS = "dangerous_goods_declaration"


class DocumentStatus(str, enum.Enum):
    DRAFT = "draft"
    ISSUED = "issued"
    SIGNED = "signed"
    CANCELLED = "cancelled"


class CertificateType(str, enum.Enum):
    ORIGIN = "certificate_of_origin"
    PHYTOSANITARY = "phytosanitary_certificate"
    VETERINARY = "veterinary_certificate"
    QUALITY = "quality_certificate"
    INSURANCE = "insurance_certificate"


class CustomsProcedure(str, enum.Enum):
    EXPORT = "export"
    IMPORT = "import"
    TRANSIT = "transit"
    TEMPORARY_STORAGE = "temporary_storage"


class CustomsStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    RISK_ASSESSMENT = "risk_assessment"
    INSPECTION = "inspection"
    HOLD = "hold"
    RELEASED = "released"
    COMPLETED = "completed"


class CustomsChannel(str, enum.Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


class InspectionType(str, enum.Enum):
    CUSTOMS = "customs_inspection"
    RANDOM = "random_inspection"
    RISK_BASED = "risk_assessment"


class InspectionStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Incoterm(str, enum.Enum):
    EXW = "EXW"
    FCA = "FCA"
    FOB = "FOB"
    CFR = "CFR"
    CIF = "CIF"
    CPT = "CPT"
    CIP = "CIP"
    DAP = "DAP"
    DPU = "DPU"
    DDP = "DDP"


class CargoFlowStage(str, enum.Enum):
    BOOKING = "booking"
    DOCUMENTATION = "documentation"
    CUSTOMS_CLEARANCE = "customs_clearance"
    LOADING = "loading"
    DEPARTURE = "departure"
    TRANSIT = "transit"
    ARRIVAL = "arrival"
    DISCHARGE = "discharge"
    WAREHOUSE = "warehouse"
    DELIVERY = "delivery"
    COMPLETED = "completed"


class ComplianceStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    UNDER_REVIEW = "under_review"


class BrokerCaseStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLEARED = "cleared"
    CLOSED = "closed"


@dataclass
class TradeDocument:
    document_id: str = field(default_factory=_id)
    document_type: DocumentType = DocumentType.BILL_OF_LADING
    title: str = ""
    reference: str = ""
    cargo_id: str = ""
    shipment_id: str = ""
    party_from: str = ""
    party_to: str = ""
    status: DocumentStatus = DocumentStatus.DRAFT
    signed_by: str = ""
    signed_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "document_type": self.document_type.value,
            "title": self.title,
            "reference": self.reference,
            "cargo_id": self.cargo_id,
            "shipment_id": self.shipment_id,
            "party_from": self.party_from,
            "party_to": self.party_to,
            "status": self.status.value,
            "signed_by": self.signed_by,
            "signed_at": self.signed_at,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


@dataclass
class TradeCertificate:
    certificate_id: str = field(default_factory=_id)
    certificate_type: CertificateType = CertificateType.ORIGIN
    title: str = ""
    cargo_id: str = ""
    shipment_id: str = ""
    issuer: str = ""
    status: DocumentStatus = DocumentStatus.DRAFT
    issued_at: float = 0.0
    expires_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "certificate_id": self.certificate_id,
            "certificate_type": self.certificate_type.value,
            "title": self.title,
            "cargo_id": self.cargo_id,
            "shipment_id": self.shipment_id,
            "issuer": self.issuer,
            "status": self.status.value,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


@dataclass
class CustomsDeclaration:
    declaration_id: str = field(default_factory=_id)
    procedure: CustomsProcedure = CustomsProcedure.IMPORT
    cargo_id: str = ""
    shipment_id: str = ""
    broker_id: str = ""
    hs_code: str = ""
    country_of_origin: str = ""
    country_of_destination: str = ""
    declared_value: float = 0.0
    currency: str = "USD"
    status: CustomsStatus = CustomsStatus.DRAFT
    channel: CustomsChannel = CustomsChannel.GREEN
    risk_score: float = 0.0
    hold_reason: str = ""
    created_at: float = field(default_factory=_ts)
    released_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "declaration_id": self.declaration_id,
            "procedure": self.procedure.value,
            "cargo_id": self.cargo_id,
            "shipment_id": self.shipment_id,
            "broker_id": self.broker_id,
            "hs_code": self.hs_code,
            "country_of_origin": self.country_of_origin,
            "country_of_destination": self.country_of_destination,
            "declared_value": self.declared_value,
            "currency": self.currency,
            "status": self.status.value,
            "channel": self.channel.value,
            "risk_score": self.risk_score,
            "hold_reason": self.hold_reason,
            "created_at": self.created_at,
            "released_at": self.released_at,
        }


@dataclass
class InspectionRecord:
    inspection_id: str = field(default_factory=_id)
    declaration_id: str = ""
    cargo_id: str = ""
    inspection_type: InspectionType = InspectionType.CUSTOMS
    status: InspectionStatus = InspectionStatus.SCHEDULED
    channel: CustomsChannel = CustomsChannel.YELLOW
    notes: str = ""
    started_at: float = 0.0
    completed_at: float = 0.0
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "inspection_id": self.inspection_id,
            "declaration_id": self.declaration_id,
            "cargo_id": self.cargo_id,
            "inspection_type": self.inspection_type.value,
            "status": self.status.value,
            "channel": self.channel.value,
            "notes": self.notes,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "created_at": self.created_at,
        }


@dataclass
class TradeShipment:
    shipment_id: str = field(default_factory=_id)
    cargo_id: str = ""
    seller: str = ""
    buyer: str = ""
    origin_country: str = ""
    destination_country: str = ""
    incoterm: Incoterm = Incoterm.FOB
    mode: str = "sea"
    stage: CargoFlowStage = CargoFlowStage.BOOKING
    declared_value: float = 0.0
    currency: str = "USD"
    broker_id: str = ""
    created_at: float = field(default_factory=_ts)
    completed_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "shipment_id": self.shipment_id,
            "cargo_id": self.cargo_id,
            "seller": self.seller,
            "buyer": self.buyer,
            "origin_country": self.origin_country,
            "destination_country": self.destination_country,
            "incoterm": self.incoterm.value,
            "mode": self.mode,
            "stage": self.stage.value,
            "declared_value": self.declared_value,
            "currency": self.currency,
            "broker_id": self.broker_id,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }


@dataclass
class TariffRate:
    tariff_id: str = field(default_factory=_id)
    hs_code: str = ""
    description: str = ""
    duty_rate_pct: float = 0.0
    vat_rate_pct: float = 0.0
    country: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tariff_id": self.tariff_id,
            "hs_code": self.hs_code,
            "description": self.description,
            "duty_rate_pct": self.duty_rate_pct,
            "vat_rate_pct": self.vat_rate_pct,
            "country": self.country,
            "created_at": self.created_at,
        }


@dataclass
class BrokerCase:
    case_id: str = field(default_factory=_id)
    broker_id: str = ""
    shipment_id: str = ""
    declaration_id: str = ""
    status: BrokerCaseStatus = BrokerCaseStatus.OPEN
    notes: str = ""
    created_at: float = field(default_factory=_ts)
    closed_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "broker_id": self.broker_id,
            "shipment_id": self.shipment_id,
            "declaration_id": self.declaration_id,
            "status": self.status.value,
            "notes": self.notes,
            "created_at": self.created_at,
            "closed_at": self.closed_at,
        }


@dataclass
class ComplianceCheck:
    check_id: str = field(default_factory=_id)
    shipment_id: str = ""
    cargo_id: str = ""
    check_type: str = "document_completeness"
    status: ComplianceStatus = ComplianceStatus.PENDING
    findings: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)
    completed_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "shipment_id": self.shipment_id,
            "cargo_id": self.cargo_id,
            "check_type": self.check_type,
            "status": self.status.value,
            "findings": list(self.findings),
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }
