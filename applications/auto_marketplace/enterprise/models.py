# Sprint 10.8 — enterprise, network, partners, production models.

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from applications.auto_marketplace.config import DEFAULT_CONFIG


def _id() -> str:
    return str(uuid.uuid4())


def _ts() -> float:
    return time.time()


class ConnectorKind(str, enum.Enum):
    ERP = "erp"
    CRM = "crm"
    ACCOUNTING = "accounting"
    GOVERNMENT = "government"
    INSURANCE = "insurance"
    BANKING = "banking"
    DEALER = "dealer"
    AUCTION = "auction"
    FLEET = "fleet"


class PartnerKind(str, enum.Enum):
    DEALER = "dealer"
    SERVICE_CENTER = "service_center"
    TRANSPORT = "transport"
    INSURANCE = "insurance"
    BANK = "bank"
    INSPECTION = "inspection"
    GOVERNMENT = "government"
    EXPORT = "export"
    FLEET_OPERATOR = "fleet_operator"


class CheckStatus(str, enum.Enum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"


@dataclass
class EnterpriseConnector:
    connector_id: str = field(default_factory=_id)
    name: str = ""
    kind: ConnectorKind = ConnectorKind.ERP
    endpoint: str = ""
    status: str = "registered"
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "connector_id": self.connector_id,
            "name": self.name,
            "kind": self.kind.value,
            "endpoint": self.endpoint,
            "status": self.status,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


@dataclass
class CrossPlatformLink:
    link_id: str = field(default_factory=_id)
    source: str = "auto_marketplace"
    target: str = ""
    shared: list[str] = field(default_factory=list)
    status: str = "active"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "link_id": self.link_id,
            "source": self.source,
            "target": self.target,
            "shared": list(self.shared),
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class NetworkPartner:
    partner_id: str = field(default_factory=_id)
    name: str = ""
    kind: PartnerKind = PartnerKind.DEALER
    country: str = ""
    region: str = ""
    rating: float = 0.0
    active: bool = True
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "partner_id": self.partner_id,
            "name": self.name,
            "kind": self.kind.value,
            "country": self.country,
            "region": self.region,
            "rating": self.rating,
            "active": self.active,
            "created_at": self.created_at,
        }


@dataclass
class NetworkListing:
    listing_id: str = field(default_factory=_id)
    vehicle_id: str = ""
    vin: str = ""
    country: str = ""
    region: str = ""
    dealer_id: str = ""
    price: float = 0.0
    currency: str = "USD"
    federated: bool = False
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "listing_id": self.listing_id,
            "vehicle_id": self.vehicle_id,
            "vin": self.vin,
            "country": self.country,
            "region": self.region,
            "dealer_id": self.dealer_id,
            "price": self.price,
            "currency": self.currency,
            "federated": self.federated,
            "created_at": self.created_at,
        }


@dataclass
class ExchangeOffer:
    offer_id: str = field(default_factory=_id)
    from_partner_id: str = ""
    to_partner_id: str = ""
    vehicle_id: str = ""
    price: float = 0.0
    currency: str = "USD"
    status: str = "open"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "offer_id": self.offer_id,
            "from_partner_id": self.from_partner_id,
            "to_partner_id": self.to_partner_id,
            "vehicle_id": self.vehicle_id,
            "price": self.price,
            "currency": self.currency,
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class ValidationCheck:
    check_id: str = field(default_factory=_id)
    name: str = ""
    category: str = ""
    status: CheckStatus = CheckStatus.PASS
    detail: str = ""
    duration_ms: float = 0.0
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "name": self.name,
            "category": self.category,
            "status": self.status.value,
            "detail": self.detail,
            "duration_ms": self.duration_ms,
            "created_at": self.created_at,
        }


@dataclass
class CommercialReleaseReport:
    report_id: str = field(default_factory=_id)
    application_version: str = field(default_factory=lambda: DEFAULT_CONFIG.application_version)
    release_status: str = field(default_factory=lambda: DEFAULT_CONFIG.release_status)
    production_ready: bool = False
    checks: list[ValidationCheck] = field(default_factory=list)
    migration_ok: bool = False
    certified: bool = False
    generated_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "application_version": self.application_version,
            "release_status": self.release_status,
            "production_ready": self.production_ready,
            "checks": [c.to_dict() for c in self.checks],
            "migration_ok": self.migration_ok,
            "certified": self.certified,
            "generated_at": self.generated_at,
        }
