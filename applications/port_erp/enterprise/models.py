# Sprint 9.8 — Enterprise, network, registry, production models.

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


class PartnerType(str, enum.Enum):
    PORT = "ports"
    SHIPPING_LINE = "shipping_lines"
    FORWARDER = "forwarders"
    RAILWAY = "railways"
    TRUCK_FLEET = "truck_fleets"
    CUSTOMS = "customs"
    BANK = "banks"
    INSURANCE = "insurance"
    GOVERNMENT = "government"
    INSPECTION_LAB = "inspection_labs"
    WAREHOUSE = "warehouses"
    TERMINAL_OPERATOR = "terminal_operators"


class IntegrationTarget(str, enum.Enum):
    AGRO_MARKETPLACE = "agro_marketplace"
    AUTO_MARKETPLACE = "auto_marketplace"
    CRM = "crm"
    ERP = "erp"
    WAREHOUSE = "warehouse"
    ACCOUNTING = "accounting"
    FINANCE = "finance"
    AI_WORKFORCE = "ai_workforce"
    DIGITAL_TWIN = "digital_twin"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    IDENTITY = "identity"
    COMMUNICATION_BUS = "communication_bus"


class IntegrationStatus(str, enum.Enum):
    REGISTERED = "registered"
    CONNECTED = "connected"
    DEGRADED = "degraded"
    DISCONNECTED = "disconnected"


class RegistryKind(str, enum.Enum):
    COMPANY = "companies"
    PARTNER = "partners"
    ROUTE = "routes"
    TRADE_LANE = "trade_lanes"
    PORT = "ports"
    TERMINAL = "terminals"
    WAREHOUSE = "warehouses"
    CUSTOMER = "customers"
    SUPPLIER = "suppliers"
    ASSET = "assets"
    CONTAINER = "containers"


class CheckStatus(str, enum.Enum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    SKIP = "skip"


@dataclass
class NetworkPartner:
    partner_id: str = field(default_factory=_id)
    name: str = ""
    partner_type: PartnerType = PartnerType.PORT
    country: str = ""
    region: str = ""
    capabilities: list[str] = field(default_factory=list)
    capacity_teu: float = 0.0
    avg_price: float = 0.0
    reliability_score: float = 0.8
    risk_score: float = 0.2
    is_active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "partner_id": self.partner_id,
            "name": self.name,
            "partner_type": self.partner_type.value,
            "country": self.country,
            "region": self.region,
            "capabilities": list(self.capabilities),
            "capacity_teu": self.capacity_teu,
            "avg_price": self.avg_price,
            "reliability_score": self.reliability_score,
            "risk_score": self.risk_score,
            "is_active": self.is_active,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


@dataclass
class TradeLane:
    lane_id: str = field(default_factory=_id)
    name: str = ""
    origin_port: str = ""
    destination_port: str = ""
    modes: list[str] = field(default_factory=lambda: ["sea"])
    distance_nm: float = 0.0
    transit_days: float = 0.0
    risk_level: str = "low"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "lane_id": self.lane_id,
            "name": self.name,
            "origin_port": self.origin_port,
            "destination_port": self.destination_port,
            "modes": list(self.modes),
            "distance_nm": self.distance_nm,
            "transit_days": self.transit_days,
            "risk_level": self.risk_level,
            "created_at": self.created_at,
        }


@dataclass
class NetworkRoute:
    route_id: str = field(default_factory=_id)
    name: str = ""
    origin: str = ""
    destination: str = ""
    carrier_id: str = ""
    mode: str = "sea"
    price: float = 0.0
    currency: str = "USD"
    capacity_teu: float = 0.0
    eta_hours: float = 0.0
    risk_score: float = 0.2
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "route_id": self.route_id,
            "name": self.name,
            "origin": self.origin,
            "destination": self.destination,
            "carrier_id": self.carrier_id,
            "mode": self.mode,
            "price": self.price,
            "currency": self.currency,
            "capacity_teu": self.capacity_teu,
            "eta_hours": self.eta_hours,
            "risk_score": self.risk_score,
            "created_at": self.created_at,
        }


@dataclass
class RegistryEntry:
    entry_id: str = field(default_factory=_id)
    kind: RegistryKind = RegistryKind.COMPANY
    external_id: str = ""
    name: str = ""
    region: str = ""
    attributes: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "kind": self.kind.value,
            "external_id": self.external_id,
            "name": self.name,
            "region": self.region,
            "attributes": dict(self.attributes),
            "created_at": self.created_at,
        }


@dataclass
class IntegrationLink:
    link_id: str = field(default_factory=_id)
    target: IntegrationTarget = IntegrationTarget.CRM
    endpoint: str = ""
    status: IntegrationStatus = IntegrationStatus.REGISTERED
    last_ping_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "link_id": self.link_id,
            "target": self.target.value,
            "endpoint": self.endpoint,
            "status": self.status.value,
            "last_ping_at": self.last_ping_at,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


@dataclass
class ExchangeOffer:
    offer_id: str = field(default_factory=_id)
    partner_id: str = ""
    origin: str = ""
    destination: str = ""
    capacity_teu: float = 0.0
    price: float = 0.0
    currency: str = "USD"
    valid_until: float = 0.0
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "offer_id": self.offer_id,
            "partner_id": self.partner_id,
            "origin": self.origin,
            "destination": self.destination,
            "capacity_teu": self.capacity_teu,
            "price": self.price,
            "currency": self.currency,
            "valid_until": self.valid_until,
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
class DeploymentProfile:
    profile_id: str = field(default_factory=_id)
    name: str = "production"
    environment: str = "production"
    replicas: int = 1
    region: str = "global"
    feature_flags: dict[str, bool] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "name": self.name,
            "environment": self.environment,
            "replicas": self.replicas,
            "region": self.region,
            "feature_flags": dict(self.feature_flags),
            "created_at": self.created_at,
        }


@dataclass
class ReleaseReport:
    report_id: str = field(default_factory=_id)
    application_version: str = "2.0.0"
    ready: bool = False
    score: float = 0.0
    blockers: list[str] = field(default_factory=list)
    checks: list[dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "application_version": self.application_version,
            "ready": self.ready,
            "score": self.score,
            "blockers": list(self.blockers),
            "checks": list(self.checks),
            "created_at": self.created_at,
        }
