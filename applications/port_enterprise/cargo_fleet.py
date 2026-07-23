"""Cargo, shipping companies, and fleet registry."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.port_enterprise.config import DEFAULT_CONFIG
from applications.port_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.port_enterprise.shared.store import PortEnterpriseStore, port_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class CargoManagement:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store
        self.categories = list(DEFAULT_CONFIG.cargo_categories)

    def register(
        self,
        *,
        description: str,
        category: str = "general",
        weight_t: float = 0.0,
        port_id: str = "",
    ) -> dict[str, Any]:
        if not description:
            raise ValidationError("description required")
        if category not in self.categories:
            raise ValidationError(f"category must be one of {self.categories}")
        cid = _id("pe_cargo")
        return self.store.cargo.save(
            cid,
            {
                "cargo_id": cid,
                "description": description,
                "category": category,
                "weight_t": float(weight_t),
                "port_id": port_id,
                "status": "registered",
                "hazardous": category == "hazardous",
                "oversized": category == "oversized",
                "refrigerated": category == "refrigerated",
                "created_at": _now(),
            },
        )

    def track(self, cargo_id: str, *, status: str, location: str = "") -> dict[str, Any]:
        cargo = self.store.cargo.get(cargo_id)
        if cargo is None:
            raise NotFoundError("cargo", cargo_id)
        cargo["status"] = status
        cargo["location"] = location
        cargo["updated_at"] = _now()
        self.store.cargo.save(cargo_id, cargo)
        eid = _id("pe_cevt")
        return self.store.cargo_events.save(
            eid,
            {
                "event_id": eid,
                "cargo_id": cargo_id,
                "status": status,
                "location": location,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "cargo": self.store.cargo.count(),
            "events": self.store.cargo_events.count(),
            "categories": self.categories,
        }


class ShippingCompanies:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def register_line(self, *, name: str, scac: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("shipping line name required")
        lid = _id("pe_line")
        return self.store.shipping_lines.save(
            lid, {"line_id": lid, "name": name, "scac": scac, "created_at": _now()}
        )

    def register_carrier(self, *, name: str, mode: str = "ocean") -> dict[str, Any]:
        if not name:
            raise ValidationError("carrier name required")
        cid = _id("pe_car")
        return self.store.carriers.save(
            cid, {"carrier_id": cid, "name": name, "mode": mode, "created_at": _now()}
        )

    def register_operator(self, *, name: str) -> dict[str, Any]:
        if not name:
            raise ValidationError("operator name required")
        oid = _id("pe_op")
        return self.store.vessel_operators.save(
            oid, {"operator_id": oid, "name": name, "created_at": _now()}
        )

    def register_agency(self, *, name: str, port_id: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("agency name required")
        aid = _id("pe_agy")
        return self.store.agencies.save(
            aid, {"agency_id": aid, "name": name, "port_id": port_id, "created_at": _now()}
        )

    def register_provider(self, *, name: str, service: str = "pilotage") -> dict[str, Any]:
        if not name:
            raise ValidationError("provider name required")
        pid = _id("pe_prov")
        return self.store.service_providers.save(
            pid, {"provider_id": pid, "name": name, "service": service, "created_at": _now()}
        )

    def status(self) -> dict[str, Any]:
        return {
            "shipping_lines": self.store.shipping_lines.count(),
            "carriers": self.store.carriers.count(),
            "operators": self.store.vessel_operators.count(),
            "agencies": self.store.agencies.count(),
            "providers": self.store.service_providers.count(),
        }


class FleetRegistry:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def register_vessel(
        self,
        *,
        name: str,
        imo: str,
        flag: str = "",
        owner: str = "",
        loa_m: float = 0.0,
        dwt: float = 0.0,
        operator_id: str = "",
    ) -> dict[str, Any]:
        if not name or not imo:
            raise ValidationError("name and imo required")
        vid = _id("pe_vsl")
        return self.store.vessels.save(
            vid,
            {
                "vessel_id": vid,
                "name": name,
                "imo": imo,
                "flag": flag,
                "owner": owner,
                "operator_id": operator_id,
                "loa_m": float(loa_m),
                "dwt": float(dwt),
                "status": "active",
                "created_at": _now(),
            },
        )

    def set_status(self, vessel_id: str, *, status: str) -> dict[str, Any]:
        vessel = self.store.vessels.get(vessel_id)
        if vessel is None:
            raise NotFoundError("vessel", vessel_id)
        vessel["status"] = status
        vessel["updated_at"] = _now()
        return self.store.vessels.save(vessel_id, vessel)

    def status(self) -> dict[str, Any]:
        return {"vessels": self.store.vessels.count()}
